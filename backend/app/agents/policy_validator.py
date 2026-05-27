from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from .base import BaseAgent, AgentResult, Success, Degraded, Failed
from ..models.claim import Member
from ..models.decision import (
    PolicyValidationResult, PolicyViolation, ViolationCode,
    Adjustment, AdjustmentType, ExtractionResult, LineItemDecision
)
from ..models.trace import PolicyTrace, RuleEvaluation
from ..services.policy_service import PolicyService


class PolicyValidationInput:
    def __init__(
        self,
        member_id: str,
        claim_category: str,
        treatment_date: str,
        claimed_amount: float,
        extracted_data: ExtractionResult,
        ytd_claims_amount: float = 0.0,
        hospital_name: Optional[str] = None
    ):
        self.member_id = member_id
        self.claim_category = claim_category
        self.treatment_date = treatment_date
        self.claimed_amount = claimed_amount
        self.extracted_data = extracted_data
        self.ytd_claims_amount = ytd_claims_amount
        self.hospital_name = hospital_name


class PolicyValidationAgent(BaseAgent[PolicyValidationInput, PolicyValidationResult]):
    def __init__(self, policy_service: Optional[PolicyService] = None):
        super().__init__("PolicyValidationAgent")
        self.policy_service = policy_service or PolicyService()
    
    def _create_trace(self, step_id: str, input_summary: dict) -> PolicyTrace:
        from datetime import datetime
        return PolicyTrace(
            step_id=step_id,
            agent_name=self.name,
            timestamp=datetime.utcnow(),
            input_summary=input_summary
        )
    
    async def _process(self, input_data: PolicyValidationInput, trace: PolicyTrace) -> PolicyValidationResult:
        violations: List[PolicyViolation] = []
        adjustments: List[Adjustment] = []
        rules_checked = 0
        
        member = self.policy_service.get_member(input_data.member_id)
        if not member:
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="member_validation",
                rule_description="Verify member exists in policy",
                passed=False,
                details=f"Member {input_data.member_id} not found"
            ))
            return PolicyValidationResult(
                is_eligible=False,
                violations=[PolicyViolation(
                    code=ViolationCode.EXCLUSION,
                    message=f"Member {input_data.member_id} not found in policy roster."
                )],
                eligible_amount=0.0,
                trace=trace
            )
        
        trace.rules_evaluated.append(RuleEvaluation(
            rule_name="member_validation",
            rule_description="Verify member exists in policy",
            passed=True,
            details=f"Member {member.name} ({member.member_id}) validated"
        ))
        rules_checked += 1
        
        diagnosis = self._get_diagnosis(input_data.extracted_data)
        waiting_violation = self.policy_service.check_waiting_period(
            member, diagnosis, input_data.treatment_date
        )
        rules_checked += 1
        
        if waiting_violation:
            violations.append(waiting_violation)
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="waiting_period",
                rule_description="Check if waiting period has elapsed for condition",
                passed=False,
                details=waiting_violation.message
            ))
        else:
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="waiting_period",
                rule_description="Check if waiting period has elapsed for condition",
                passed=True,
                details=f"No waiting period violation for diagnosis: {diagnosis}"
            ))
        
        procedures = self._get_procedures(input_data.extracted_data, input_data.claim_category)
        exclusion_violations = self.policy_service.check_exclusions(
            diagnosis, procedures, input_data.claim_category
        )
        rules_checked += 1
        
        if exclusion_violations:
            violations.extend(exclusion_violations)
            for ev in exclusion_violations:
                trace.rules_evaluated.append(RuleEvaluation(
                    rule_name="exclusion_check",
                    rule_description="Check if treatment/procedure is excluded",
                    passed=False,
                    details=ev.message
                ))
        else:
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="exclusion_check",
                rule_description="Check if treatment/procedure is excluded",
                passed=True,
                details=f"No exclusions for diagnosis: {diagnosis}, procedures: {procedures}"
            ))
        
        pre_auth_violation = self.policy_service.check_pre_auth(
            input_data.claim_category,
            input_data.claimed_amount,
            procedures
        )
        rules_checked += 1
        
        if pre_auth_violation:
            violations.append(pre_auth_violation)
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="pre_authorization",
                rule_description="Check if pre-authorization is required",
                passed=False,
                details=pre_auth_violation.message
            ))
        else:
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="pre_authorization",
                rule_description="Check if pre-authorization is required",
                passed=True,
                details="No pre-authorization required"
            ))
        
        amount_for_limits = input_data.claimed_amount
        line_adjustments = []
        
        if input_data.claim_category == "DENTAL" and input_data.extracted_data.bill_data:
            amount_for_limits, line_adjustments = self._process_dental_line_items(
                input_data.extracted_data.bill_data.line_items,
                trace
            )
            adjustments.extend(line_adjustments)
            
            if amount_for_limits < input_data.claimed_amount:
                trace.decision_factors.append(
                    f"Dental: Covered amount ₹{amount_for_limits:,.0f} (excluded ₹{input_data.claimed_amount - amount_for_limits:,.0f})"
                )
        
        limit_violations = self.policy_service.check_limits(
            input_data.claim_category,
            amount_for_limits,
            input_data.ytd_claims_amount
        )
        rules_checked += 1
        
        if limit_violations:
            violations.extend(limit_violations)
            for lv in limit_violations:
                trace.rules_evaluated.append(RuleEvaluation(
                    rule_name="limit_check",
                    rule_description="Check claim against policy limits",
                    passed=False,
                    details=lv.message
                ))
        else:
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="limit_check",
                rule_description="Check claim against policy limits",
                passed=True,
                details=f"Claim amount ₹{amount_for_limits:,.0f} within limits"
            ))
        
        trace.rules_checked = rules_checked
        trace.violations_found = len(violations)
        
        hard_reject_codes = [
            ViolationCode.WAITING_PERIOD,
            ViolationCode.PRE_AUTH_MISSING,
            ViolationCode.PER_CLAIM_EXCEEDED,
            ViolationCode.EXCLUDED_CONDITION
        ]
        
        has_hard_reject = any(v.code in hard_reject_codes for v in violations)
        has_only_line_exclusions = (
            all(v.code == ViolationCode.EXCLUSION for v in violations) and 
            input_data.claim_category == "DENTAL" and
            amount_for_limits > 0
        )
        
        if has_hard_reject and not has_only_line_exclusions:
            trace.decision_factors.append(f"Hard rejection due to: {[v.code.value for v in violations]}")
            return PolicyValidationResult(
                is_eligible=False,
                violations=violations,
                adjustments=adjustments,
                eligible_amount=0.0,
                trace=trace
            )
        
        hospital = input_data.hospital_name
        if not hospital and input_data.extracted_data.bill_data:
            hospital = input_data.extracted_data.bill_data.hospital_name
        
        eligible_amount = amount_for_limits
        
        if input_data.claim_category != "DENTAL":
            eligible_amount, calc_adjustments = self.policy_service.calculate_adjustments(
                input_data.claim_category,
                input_data.claimed_amount,
                hospital
            )
            adjustments.extend(calc_adjustments)
            
            for adj in calc_adjustments:
                trace.adjustments_applied.append({
                    "type": adj.type.value,
                    "description": adj.description,
                    "amount": adj.amount
                })
                trace.decision_factors.append(f"Applied {adj.type.value}: -₹{adj.amount:,.2f}")
        
        trace.confidence_contribution = 0.95 if not violations else 0.7
        
        return PolicyValidationResult(
            is_eligible=len(violations) == 0 or all(
                v.code == ViolationCode.EXCLUSION and "cosmetic" in v.message.lower()
                for v in violations
            ),
            violations=violations,
            adjustments=adjustments,
            eligible_amount=eligible_amount,
            trace=trace
        )
    
    def _get_diagnosis(self, extracted_data: ExtractionResult) -> str:
        if extracted_data.prescription_data and extracted_data.prescription_data.diagnosis:
            return extracted_data.prescription_data.diagnosis
        if extracted_data.prescription_data and extracted_data.prescription_data.treatment:
            return extracted_data.prescription_data.treatment
        return ""
    
    def _get_procedures(self, extracted_data: ExtractionResult, category: str) -> List[str]:
        procedures = []
        
        if extracted_data.prescription_data:
            if extracted_data.prescription_data.tests_ordered:
                procedures.extend(extracted_data.prescription_data.tests_ordered)
            if extracted_data.prescription_data.treatment:
                procedures.append(extracted_data.prescription_data.treatment)
        
        if extracted_data.bill_data:
            for item in extracted_data.bill_data.line_items:
                procedures.append(item.description)
        
        if extracted_data.lab_report_data and extracted_data.lab_report_data.test_name:
            procedures.append(extracted_data.lab_report_data.test_name)
        
        return procedures
    
    def _process_dental_line_items(
        self,
        line_items: List,
        trace: PolicyTrace
    ) -> Tuple[float, List[Adjustment]]:
        adjustments = []
        covered_procedures = self.policy_service.get_covered_dental_procedures()
        excluded_procedures = self.policy_service.get_excluded_dental_procedures()
        
        total_approved = 0.0
        
        for item in line_items:
            item_desc = item.description.lower()
            is_excluded = any(excl.lower() in item_desc for excl in excluded_procedures)
            is_covered = any(cov.lower() in item_desc for cov in covered_procedures)
            
            if is_excluded:
                adjustments.append(Adjustment(
                    type=AdjustmentType.LINE_ITEM_EXCLUSION,
                    description=f"'{item.description}' is an excluded cosmetic procedure",
                    amount=item.amount,
                    original_amount=item.amount
                ))
                trace.rules_evaluated.append(RuleEvaluation(
                    rule_name="dental_line_item",
                    rule_description=f"Check if '{item.description}' is covered",
                    passed=False,
                    details=f"Excluded procedure - ₹{item.amount:,.0f} not covered"
                ))
            else:
                total_approved += item.amount
                trace.rules_evaluated.append(RuleEvaluation(
                    rule_name="dental_line_item",
                    rule_description=f"Check if '{item.description}' is covered",
                    passed=True,
                    details=f"Covered procedure - ₹{item.amount:,.0f} approved"
                ))
        
        return total_approved, adjustments
    
    async def _handle_failure(self, input_data: PolicyValidationInput, error: Exception, trace: PolicyTrace) -> Optional[PolicyValidationResult]:
        trace.warnings.append(f"Policy validation degraded due to error: {str(error)}")
        
        return PolicyValidationResult(
            is_eligible=True,
            violations=[],
            adjustments=[],
            eligible_amount=input_data.claimed_amount,
            trace=trace
        )
