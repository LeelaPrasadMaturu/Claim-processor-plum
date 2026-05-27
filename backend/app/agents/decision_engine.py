from typing import List, Optional, Dict, Any
from datetime import datetime

from .base import BaseAgent, AgentResult, Success, Degraded, Failed
from ..models.decision import (
    ClaimDecision, DecisionType, DecisionReason, LineItemDecision,
    VerificationResult, VerificationStatus, ExtractionResult,
    PolicyValidationResult, FraudDetectionResult, ViolationCode, AdjustmentType
)
from ..models.trace import TraceStep, ClaimTrace, ComponentFailure, RuleEvaluation


class DecisionInput:
    def __init__(
        self,
        claim_id: str,
        claimed_amount: float,
        verification_result: Optional[VerificationResult],
        extraction_result: Optional[ExtractionResult],
        policy_result: Optional[PolicyValidationResult],
        fraud_result: Optional[FraudDetectionResult],
        component_failures: List[ComponentFailure]
    ):
        self.claim_id = claim_id
        self.claimed_amount = claimed_amount
        self.verification_result = verification_result
        self.extraction_result = extraction_result
        self.policy_result = policy_result
        self.fraud_result = fraud_result
        self.component_failures = component_failures


class DecisionEngineAgent(BaseAgent[DecisionInput, ClaimDecision]):
    def __init__(self):
        super().__init__("DecisionEngineAgent")
    
    async def _process(self, input_data: DecisionInput, trace: TraceStep) -> ClaimDecision:
        reasons: List[DecisionReason] = []
        recommendations: List[str] = []
        confidence_factors: List[float] = []
        
        if input_data.verification_result:
            if input_data.verification_result.status == VerificationStatus.INVALID:
                trace.decision_factors.append("Early stop: Document verification failed")
                
                reasons.append(DecisionReason(
                    code="DOC_VERIFICATION_FAILED",
                    message=input_data.verification_result.error_message or "Document verification failed",
                    category="REJECTION"
                ))
                
                return ClaimDecision(
                    claim_id=input_data.claim_id,
                    decision=DecisionType.REJECTED,
                    approved_amount=0.0,
                    rejected_amount=input_data.claimed_amount,
                    confidence_score=input_data.verification_result.confidence,
                    reasons=reasons,
                    recommendations=["Please upload the correct documents and resubmit your claim."],
                    verification_result=input_data.verification_result,
                    extraction_result=input_data.extraction_result,
                    policy_result=input_data.policy_result,
                    fraud_result=input_data.fraud_result
                )
            
            if input_data.verification_result.status == VerificationStatus.UNREADABLE:
                trace.decision_factors.append("Early stop: Documents unreadable")
                
                reasons.append(DecisionReason(
                    code="DOC_UNREADABLE",
                    message=input_data.verification_result.error_message or "One or more documents are unreadable",
                    category="REJECTION"
                ))
                
                return ClaimDecision(
                    claim_id=input_data.claim_id,
                    decision=DecisionType.REJECTED,
                    approved_amount=0.0,
                    rejected_amount=input_data.claimed_amount,
                    confidence_score=0.3,
                    reasons=reasons,
                    recommendations=["Please re-upload clearer images of the unreadable documents."],
                    verification_result=input_data.verification_result,
                    extraction_result=input_data.extraction_result,
                    policy_result=input_data.policy_result,
                    fraud_result=input_data.fraud_result
                )
            
            confidence_factors.append(input_data.verification_result.confidence)
        
        if input_data.extraction_result:
            if len(input_data.extraction_result.patient_names_found) > 1:
                trace.decision_factors.append("Early stop: Patient name mismatch in documents")
                
                names = input_data.extraction_result.patient_names_found
                reasons.append(DecisionReason(
                    code="PATIENT_NAME_MISMATCH",
                    message=f"Documents belong to different patients. Found names: {', '.join(names)}. "
                            f"All documents must belong to the same patient.",
                    category="REJECTION"
                ))
                
                return ClaimDecision(
                    claim_id=input_data.claim_id,
                    decision=DecisionType.REJECTED,
                    approved_amount=0.0,
                    rejected_amount=input_data.claimed_amount,
                    confidence_score=0.9,
                    reasons=reasons,
                    recommendations=[
                        f"The prescription shows patient name '{names[0]}' but the bill shows '{names[1] if len(names) > 1 else 'different name'}'.",
                        "Please ensure all documents are for the same patient and resubmit."
                    ],
                    verification_result=input_data.verification_result,
                    extraction_result=input_data.extraction_result,
                    policy_result=input_data.policy_result,
                    fraud_result=input_data.fraud_result
                )
            
            if input_data.extraction_result.confidence_scores:
                avg_extraction_conf = sum(input_data.extraction_result.confidence_scores.values()) / len(input_data.extraction_result.confidence_scores)
                confidence_factors.append(avg_extraction_conf)
        
        if input_data.fraud_result and input_data.fraud_result.requires_manual_review:
            trace.decision_factors.append("Routing to manual review due to fraud signals")
            
            for flag in input_data.fraud_result.flags:
                reasons.append(DecisionReason(
                    code=f"FRAUD_FLAG_{flag.type.value}",
                    message=flag.description,
                    category="WARNING"
                ))
            
            recommendations.append("This claim has been flagged for manual review due to unusual patterns.")
            for flag in input_data.fraud_result.flags:
                recommendations.append(f"• {flag.type.value}: {flag.description}")
            
            return ClaimDecision(
                claim_id=input_data.claim_id,
                decision=DecisionType.MANUAL_REVIEW,
                approved_amount=0.0,
                rejected_amount=0.0,
                confidence_score=1.0 - input_data.fraud_result.fraud_score,
                reasons=reasons,
                recommendations=recommendations,
                verification_result=input_data.verification_result,
                extraction_result=input_data.extraction_result,
                policy_result=input_data.policy_result,
                fraud_result=input_data.fraud_result
            )
        
        if input_data.policy_result:
            if not input_data.policy_result.is_eligible and input_data.policy_result.violations:
                hard_rejections = [
                    v for v in input_data.policy_result.violations
                    if v.code in [
                        ViolationCode.WAITING_PERIOD,
                        ViolationCode.PRE_AUTH_MISSING,
                        ViolationCode.PER_CLAIM_EXCEEDED,
                        ViolationCode.EXCLUDED_CONDITION
                    ]
                ]
                
                if hard_rejections:
                    trace.decision_factors.append(f"Rejected due to policy violations: {[v.code.value for v in hard_rejections]}")
                    
                    for violation in input_data.policy_result.violations:
                        reasons.append(DecisionReason(
                            code=violation.code.value,
                            message=violation.message,
                            category="REJECTION"
                        ))
                    
                    if any(v.code == ViolationCode.WAITING_PERIOD for v in hard_rejections):
                        recommendations.append("Your claim was rejected due to the waiting period. "
                                             "Please check the eligibility date mentioned and resubmit after that date.")
                    if any(v.code == ViolationCode.PRE_AUTH_MISSING for v in hard_rejections):
                        recommendations.append("This procedure requires pre-authorization. "
                                             "Please contact us to obtain pre-authorization before your next similar treatment.")
                    if any(v.code == ViolationCode.PER_CLAIM_EXCEEDED for v in hard_rejections):
                        recommendations.append("You may split larger treatments into separate claims "
                                             "within the per-claim limit, where medically appropriate.")
                    
                    return ClaimDecision(
                        claim_id=input_data.claim_id,
                        decision=DecisionType.REJECTED,
                        approved_amount=0.0,
                        rejected_amount=input_data.claimed_amount,
                        confidence_score=0.95,
                        reasons=reasons,
                        recommendations=recommendations,
                        verification_result=input_data.verification_result,
                        extraction_result=input_data.extraction_result,
                        policy_result=input_data.policy_result,
                        fraud_result=input_data.fraud_result
                    )
        
        line_item_breakdown = None
        approved_amount = input_data.claimed_amount
        rejected_amount = 0.0
        
        if input_data.policy_result:
            approved_amount = input_data.policy_result.eligible_amount
            
            for adjustment in input_data.policy_result.adjustments:
                if adjustment.type == AdjustmentType.LINE_ITEM_EXCLUSION:
                    rejected_amount += adjustment.amount
                    reasons.append(DecisionReason(
                        code="LINE_ITEM_EXCLUDED",
                        message=adjustment.description,
                        category="REJECTION"
                    ))
                else:
                    reasons.append(DecisionReason(
                        code=adjustment.type.value,
                        message=f"{adjustment.description}: ₹{adjustment.amount:,.2f} deducted",
                        category="ADJUSTMENT"
                    ))
            
            if input_data.extraction_result and input_data.extraction_result.bill_data:
                line_item_breakdown = []
                excluded_items = {
                    adj.description.split("'")[1] if "'" in adj.description else ""
                    for adj in input_data.policy_result.adjustments
                    if adj.type == AdjustmentType.LINE_ITEM_EXCLUSION
                }
                
                for item in input_data.extraction_result.bill_data.line_items:
                    is_excluded = any(
                        excl.lower() in item.description.lower()
                        for excl in excluded_items if excl
                    )
                    
                    if is_excluded:
                        line_item_breakdown.append(LineItemDecision(
                            description=item.description,
                            claimed_amount=item.amount,
                            approved_amount=0.0,
                            status="REJECTED",
                            reason="Excluded procedure under policy"
                        ))
                    else:
                        line_item_breakdown.append(LineItemDecision(
                            description=item.description,
                            claimed_amount=item.amount,
                            approved_amount=item.amount,
                            status="APPROVED"
                        ))
            
            confidence_factors.append(0.95)
        
        if input_data.component_failures:
            trace.decision_factors.append(f"Processing completed with {len(input_data.component_failures)} component failures")
            
            for failure in input_data.component_failures:
                reasons.append(DecisionReason(
                    code="COMPONENT_FAILURE",
                    message=f"{failure.component_name} encountered an error: {failure.error_message}",
                    category="WARNING"
                ))
            
            confidence_factors = [f * 0.7 for f in confidence_factors]
            recommendations.append("Note: Some verification steps could not be completed. "
                                 "Manual review is recommended to confirm this decision.")
        
        if rejected_amount > 0 and approved_amount > 0:
            decision_type = DecisionType.PARTIAL
            trace.decision_factors.append(f"Partial approval: ₹{approved_amount:,.2f} approved, ₹{rejected_amount:,.2f} rejected")
        elif approved_amount > 0:
            decision_type = DecisionType.APPROVED
            trace.decision_factors.append(f"Full approval: ₹{approved_amount:,.2f}")
            reasons.append(DecisionReason(
                code="CLAIM_APPROVED",
                message=f"Claim approved for ₹{approved_amount:,.2f}",
                category="APPROVAL"
            ))
        else:
            decision_type = DecisionType.REJECTED
            trace.decision_factors.append("Rejected: No eligible amount")
        
        final_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        if input_data.component_failures:
            final_confidence *= 0.7
            recommendations.append("Confidence reduced due to incomplete processing.")
        
        trace.confidence_contribution = final_confidence
        
        return ClaimDecision(
            claim_id=input_data.claim_id,
            decision=decision_type,
            approved_amount=approved_amount,
            rejected_amount=rejected_amount,
            confidence_score=final_confidence,
            reasons=reasons,
            line_item_breakdown=line_item_breakdown,
            recommendations=recommendations if recommendations else None,
            verification_result=input_data.verification_result,
            extraction_result=input_data.extraction_result,
            policy_result=input_data.policy_result,
            fraud_result=input_data.fraud_result
        )
    
    async def _handle_failure(self, input_data: DecisionInput, error: Exception, trace: TraceStep) -> Optional[ClaimDecision]:
        trace.warnings.append(f"Decision engine degraded due to error: {str(error)}")
        
        return ClaimDecision(
            claim_id=input_data.claim_id,
            decision=DecisionType.MANUAL_REVIEW,
            approved_amount=0.0,
            rejected_amount=0.0,
            confidence_score=0.2,
            reasons=[DecisionReason(
                code="DECISION_ENGINE_ERROR",
                message=f"Decision engine encountered an error: {str(error)}",
                category="WARNING"
            )],
            recommendations=["Manual review required due to system error."],
            verification_result=input_data.verification_result,
            extraction_result=input_data.extraction_result,
            policy_result=input_data.policy_result,
            fraud_result=input_data.fraud_result
        )
