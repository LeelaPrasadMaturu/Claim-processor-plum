from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict

from .base import BaseAgent, AgentResult, Success, Degraded, Failed
from ..models.claim import PreviousClaim
from ..models.decision import (
    FraudDetectionResult, FraudFlag, FraudFlagType, ExtractionResult
)
from ..models.trace import FraudTrace, RuleEvaluation
from ..services.policy_service import PolicyService


class FraudDetectionInput:
    def __init__(
        self,
        member_id: str,
        claim_date: str,
        claimed_amount: float,
        claims_history: List[PreviousClaim],
        extracted_data: ExtractionResult
    ):
        self.member_id = member_id
        self.claim_date = claim_date
        self.claimed_amount = claimed_amount
        self.claims_history = claims_history
        self.extracted_data = extracted_data


class FraudDetectionAgent(BaseAgent[FraudDetectionInput, FraudDetectionResult]):
    def __init__(self, policy_service: Optional[PolicyService] = None):
        super().__init__("FraudDetectionAgent")
        self.policy_service = policy_service or PolicyService()
        self.thresholds = self.policy_service.get_fraud_thresholds()
    
    def _create_trace(self, step_id: str, input_summary: dict) -> FraudTrace:
        from datetime import datetime
        return FraudTrace(
            step_id=step_id,
            agent_name=self.name,
            timestamp=datetime.utcnow(),
            input_summary=input_summary
        )
    
    async def _process(self, input_data: FraudDetectionInput, trace: FraudTrace) -> FraudDetectionResult:
        flags: List[FraudFlag] = []
        fraud_score = 0.0
        signals_checked = 0
        
        same_day_claims = [
            claim for claim in input_data.claims_history
            if claim.date == input_data.claim_date
        ]
        signals_checked += 1
        
        same_day_limit = self.thresholds.get("same_day_claims_limit", 2)
        if len(same_day_claims) >= same_day_limit:
            fraud_score += 0.4
            flags.append(FraudFlag(
                type=FraudFlagType.SAME_DAY_CLAIMS,
                description=f"Member has submitted {len(same_day_claims) + 1} claims on {input_data.claim_date}. "
                            f"This is the {len(same_day_claims) + 1}th claim today, exceeding the normal limit of {same_day_limit} same-day claims.",
                severity="HIGH",
                details={
                    "same_day_claim_count": len(same_day_claims) + 1,
                    "limit": same_day_limit,
                    "previous_claims": [
                        {"claim_id": c.claim_id, "amount": c.amount, "provider": c.provider}
                        for c in same_day_claims
                    ]
                }
            ))
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="same_day_claims",
                rule_description=f"Check if member has exceeded {same_day_limit} claims per day",
                passed=False,
                details=f"Found {len(same_day_claims)} existing claims on same day"
            ))
            trace.fraud_indicators.append({
                "type": "SAME_DAY_CLAIMS",
                "score_contribution": 0.4,
                "details": f"{len(same_day_claims) + 1} claims on {input_data.claim_date}"
            })
        else:
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="same_day_claims",
                rule_description=f"Check if member has exceeded {same_day_limit} claims per day",
                passed=True,
                details=f"Found {len(same_day_claims)} existing claims on same day (within limit)"
            ))
        
        high_value_threshold = self.thresholds.get("high_value_claim_threshold", 25000)
        signals_checked += 1
        
        if input_data.claimed_amount > high_value_threshold:
            fraud_score += 0.2
            flags.append(FraudFlag(
                type=FraudFlagType.HIGH_VALUE,
                description=f"Claim amount ₹{input_data.claimed_amount:,.0f} exceeds high-value threshold of ₹{high_value_threshold:,.0f}.",
                severity="MEDIUM",
                details={
                    "claimed_amount": input_data.claimed_amount,
                    "threshold": high_value_threshold
                }
            ))
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="high_value_claim",
                rule_description=f"Check if claim exceeds ₹{high_value_threshold:,.0f}",
                passed=False,
                details=f"Claim amount ₹{input_data.claimed_amount:,.0f} is high value"
            ))
            trace.fraud_indicators.append({
                "type": "HIGH_VALUE",
                "score_contribution": 0.2,
                "details": f"Amount ₹{input_data.claimed_amount:,.0f} > threshold ₹{high_value_threshold:,.0f}"
            })
        else:
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="high_value_claim",
                rule_description=f"Check if claim exceeds ₹{high_value_threshold:,.0f}",
                passed=True,
                details=f"Claim amount ₹{input_data.claimed_amount:,.0f} is within normal range"
            ))
        
        claim_month = input_data.claim_date[:7]
        monthly_claims = [
            claim for claim in input_data.claims_history
            if claim.date.startswith(claim_month)
        ]
        signals_checked += 1
        
        monthly_limit = self.thresholds.get("monthly_claims_limit", 6)
        if len(monthly_claims) >= monthly_limit:
            fraud_score += 0.25
            flags.append(FraudFlag(
                type=FraudFlagType.MONTHLY_LIMIT_EXCEEDED,
                description=f"Member has submitted {len(monthly_claims) + 1} claims this month, "
                            f"exceeding the expected limit of {monthly_limit}.",
                severity="MEDIUM",
                details={
                    "monthly_claim_count": len(monthly_claims) + 1,
                    "limit": monthly_limit,
                    "month": claim_month
                }
            ))
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="monthly_claims_limit",
                rule_description=f"Check if member has exceeded {monthly_limit} claims per month",
                passed=False,
                details=f"Found {len(monthly_claims)} existing claims this month"
            ))
        else:
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="monthly_claims_limit",
                rule_description=f"Check if member has exceeded {monthly_limit} claims per month",
                passed=True,
                details=f"Found {len(monthly_claims)} claims this month (within limit)"
            ))
        
        if input_data.extracted_data.patient_names_found and len(input_data.extracted_data.patient_names_found) > 1:
            fraud_score += 0.3
            flags.append(FraudFlag(
                type=FraudFlagType.SUSPICIOUS_PATTERN,
                description=f"Documents contain different patient names: {input_data.extracted_data.patient_names_found}. "
                            f"This may indicate mixed documents or potential fraud.",
                severity="HIGH",
                details={
                    "patient_names": input_data.extracted_data.patient_names_found
                }
            ))
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="patient_name_mismatch",
                rule_description="Check if documents have consistent patient names",
                passed=False,
                details=f"Multiple patient names found: {input_data.extracted_data.patient_names_found}"
            ))
            trace.fraud_indicators.append({
                "type": "NAME_MISMATCH",
                "score_contribution": 0.3,
                "details": f"Names found: {input_data.extracted_data.patient_names_found}"
            })
        else:
            signals_checked += 1
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="patient_name_mismatch",
                rule_description="Check if documents have consistent patient names",
                passed=True,
                details="Patient names are consistent across documents"
            ))
        
        if same_day_claims:
            providers = defaultdict(int)
            for claim in same_day_claims:
                if claim.provider:
                    providers[claim.provider] += 1
            
            if len(providers) >= 3:
                fraud_score += 0.15
                flags.append(FraudFlag(
                    type=FraudFlagType.SUSPICIOUS_PATTERN,
                    description=f"Multiple different providers ({len(providers)}) visited on the same day.",
                    severity="MEDIUM",
                    details={
                        "providers": dict(providers),
                        "date": input_data.claim_date
                    }
                ))
                trace.fraud_indicators.append({
                    "type": "MULTIPLE_PROVIDERS",
                    "score_contribution": 0.15,
                    "details": f"{len(providers)} different providers on same day"
                })
        
        fraud_score = min(fraud_score, 1.0)
        
        manual_review_threshold = self.thresholds.get("fraud_score_manual_review_threshold", 0.80)
        auto_review_amount = self.thresholds.get("auto_manual_review_above", 25000)
        
        requires_manual_review = (
            fraud_score >= manual_review_threshold or
            input_data.claimed_amount > auto_review_amount or
            any(flag.severity == "HIGH" for flag in flags)
        )
        
        trace.signals_checked = signals_checked
        trace.flags_raised = len(flags)
        trace.confidence_contribution = 1.0 - (fraud_score * 0.5)
        
        if requires_manual_review:
            trace.decision_factors.append(f"Manual review required: fraud_score={fraud_score:.2f}, flags={len(flags)}")
        else:
            trace.decision_factors.append(f"No manual review needed: fraud_score={fraud_score:.2f}")
        
        return FraudDetectionResult(
            fraud_score=fraud_score,
            flags=flags,
            requires_manual_review=requires_manual_review,
            trace=trace
        )
    
    async def _handle_failure(self, input_data: FraudDetectionInput, error: Exception, trace: FraudTrace) -> Optional[FraudDetectionResult]:
        trace.warnings.append(f"Fraud detection degraded due to error: {str(error)}")
        
        return FraudDetectionResult(
            fraud_score=0.5,
            flags=[FraudFlag(
                type=FraudFlagType.SUSPICIOUS_PATTERN,
                description="Fraud detection encountered an error - recommend manual review",
                severity="MEDIUM",
                details={"error": str(error)}
            )],
            requires_manual_review=True,
            trace=trace
        )
