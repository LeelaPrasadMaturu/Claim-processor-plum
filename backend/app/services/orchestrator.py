from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

from ..models.claim import Claim, ClaimStatus
from ..models.document import Document, DocumentType
from ..models.decision import (
    ClaimDecision, DecisionType, VerificationResult, VerificationStatus,
    ExtractionResult, PolicyValidationResult, FraudDetectionResult
)
from ..models.trace import ClaimTrace, TraceStep, ComponentFailure, VerificationTrace, ExtractionTrace, PolicyTrace, FraudTrace

from ..agents.document_verifier import DocumentVerificationAgent, VerificationInput
from ..agents.document_extractor import DocumentExtractionAgent, ExtractionInput
from ..agents.policy_validator import PolicyValidationAgent, PolicyValidationInput
from ..agents.fraud_detector import FraudDetectionAgent, FraudDetectionInput
from ..agents.decision_engine import DecisionEngineAgent, DecisionInput

from .llm_service import LLMService
from .policy_service import PolicyService
from .trace_service import TraceService

logger = logging.getLogger(__name__)


class ClaimOrchestrator:
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        policy_service: Optional[PolicyService] = None,
        trace_service: Optional[TraceService] = None
    ):
        self.llm_service = llm_service or LLMService()
        self.policy_service = policy_service or PolicyService()
        self.trace_service = trace_service or TraceService()
        
        self.doc_verifier = DocumentVerificationAgent(self.llm_service, self.policy_service)
        self.doc_extractor = DocumentExtractionAgent(self.llm_service)
        self.policy_validator = PolicyValidationAgent(self.policy_service)
        self.fraud_detector = FraudDetectionAgent(self.policy_service)
        self.decision_engine = DecisionEngineAgent()
    
    async def process_claim(self, claim: Claim) -> ClaimDecision:
        logger.info(f"Processing claim {claim.claim_id}")
        
        claim_trace = self.trace_service.create_trace(claim.claim_id)
        component_failures: List[ComponentFailure] = []
        
        verification_result: Optional[VerificationResult] = None
        extraction_result: Optional[ExtractionResult] = None
        policy_result: Optional[PolicyValidationResult] = None
        fraud_result: Optional[FraudDetectionResult] = None
        
        try:
            if claim.simulate_component_failure:
                raise Exception("Simulated component failure for testing")
            
            verification_input = VerificationInput(
                claim_category=claim.claim_category.value,
                documents=claim.documents
            )
            
            ver_result = await self.doc_verifier.execute(verification_input)
            
            if ver_result.success and ver_result.data:
                verification_result = ver_result.data
                if ver_result.trace:
                    self.trace_service.add_step(claim.claim_id, ver_result.trace)
                
                if ver_result.degraded:
                    component_failures.append(ComponentFailure(
                        component_name="DocumentVerificationAgent",
                        error_type="DEGRADED",
                        error_message=ver_result.error or "Unknown degradation"
                    ))
                
                if verification_result.status in [VerificationStatus.INVALID, VerificationStatus.UNREADABLE]:
                    logger.info(f"Claim {claim.claim_id}: Early stop due to verification failure")
                    return await self._make_decision(
                        claim, verification_result, None, None, None, component_failures
                    )
            else:
                logger.error(f"Verification failed: {ver_result.error}")
                component_failures.append(ComponentFailure(
                    component_name="DocumentVerificationAgent",
                    error_type="FAILED",
                    error_message=ver_result.error or "Verification failed"
                ))
        except Exception as e:
            logger.error(f"Verification exception: {e}")
            component_failures.append(ComponentFailure(
                component_name="DocumentVerificationAgent",
                error_type="EXCEPTION",
                error_message=str(e)
            ))
        
        try:
            if claim.simulate_component_failure:
                raise Exception("Simulated extraction failure for testing")
            
            if verification_result and verification_result.documents_classified:
                document_contents = {}
                for doc in claim.documents:
                    if doc.content:
                        document_contents[doc.file_id] = doc.content
                
                extraction_input = ExtractionInput(
                    documents=verification_result.documents_classified,
                    document_contents=document_contents
                )
                
                ext_result = await self.doc_extractor.execute(extraction_input)
                
                if ext_result.success and ext_result.data:
                    extraction_result = ext_result.data
                    if ext_result.trace:
                        self.trace_service.add_step(claim.claim_id, ext_result.trace)
                    
                    if ext_result.degraded:
                        component_failures.append(ComponentFailure(
                            component_name="DocumentExtractionAgent",
                            error_type="DEGRADED",
                            error_message=ext_result.error or "Unknown degradation"
                        ))
                    
                    if extraction_result.patient_names_found and len(extraction_result.patient_names_found) > 1:
                        logger.info(f"Claim {claim.claim_id}: Patient name mismatch detected")
                        return await self._make_decision(
                            claim, verification_result, extraction_result, None, None, component_failures
                        )
                else:
                    logger.error(f"Extraction failed: {ext_result.error}")
                    component_failures.append(ComponentFailure(
                        component_name="DocumentExtractionAgent",
                        error_type="FAILED",
                        error_message=ext_result.error or "Extraction failed"
                    ))
                    extraction_result = ExtractionResult(
                        patient_names_found=[],
                        confidence_scores={},
                        extraction_warnings=["Extraction failed - using minimal data"]
                    )
        except Exception as e:
            logger.error(f"Extraction exception: {e}")
            component_failures.append(ComponentFailure(
                component_name="DocumentExtractionAgent",
                error_type="EXCEPTION",
                error_message=str(e)
            ))
            extraction_result = ExtractionResult(
                patient_names_found=[],
                confidence_scores={},
                extraction_warnings=[f"Extraction failed: {str(e)}"]
            )
        
        try:
            hospital_name = claim.hospital_name
            if not hospital_name and extraction_result and extraction_result.bill_data:
                hospital_name = extraction_result.bill_data.hospital_name
            
            policy_input = PolicyValidationInput(
                member_id=claim.member_id,
                claim_category=claim.claim_category.value,
                treatment_date=claim.treatment_date,
                claimed_amount=claim.claimed_amount,
                extracted_data=extraction_result or ExtractionResult(
                    patient_names_found=[],
                    confidence_scores={},
                    extraction_warnings=[]
                ),
                ytd_claims_amount=claim.ytd_claims_amount,
                hospital_name=hospital_name
            )
            
            pol_result = await self.policy_validator.execute(policy_input)
            
            if pol_result.success and pol_result.data:
                policy_result = pol_result.data
                if pol_result.trace:
                    self.trace_service.add_step(claim.claim_id, pol_result.trace)
                
                if pol_result.degraded:
                    component_failures.append(ComponentFailure(
                        component_name="PolicyValidationAgent",
                        error_type="DEGRADED",
                        error_message=pol_result.error or "Unknown degradation"
                    ))
            else:
                logger.error(f"Policy validation failed: {pol_result.error}")
                component_failures.append(ComponentFailure(
                    component_name="PolicyValidationAgent",
                    error_type="FAILED",
                    error_message=pol_result.error or "Policy validation failed"
                ))
        except Exception as e:
            logger.error(f"Policy validation exception: {e}")
            component_failures.append(ComponentFailure(
                component_name="PolicyValidationAgent",
                error_type="EXCEPTION",
                error_message=str(e)
            ))
        
        try:
            fraud_input = FraudDetectionInput(
                member_id=claim.member_id,
                claim_date=claim.treatment_date,
                claimed_amount=claim.claimed_amount,
                claims_history=claim.claims_history,
                extracted_data=extraction_result or ExtractionResult(
                    patient_names_found=[],
                    confidence_scores={},
                    extraction_warnings=[]
                )
            )
            
            fraud_res = await self.fraud_detector.execute(fraud_input)
            
            if fraud_res.success and fraud_res.data:
                fraud_result = fraud_res.data
                if fraud_res.trace:
                    self.trace_service.add_step(claim.claim_id, fraud_res.trace)
                
                if fraud_res.degraded:
                    component_failures.append(ComponentFailure(
                        component_name="FraudDetectionAgent",
                        error_type="DEGRADED",
                        error_message=fraud_res.error or "Unknown degradation"
                    ))
            else:
                logger.error(f"Fraud detection failed: {fraud_res.error}")
                component_failures.append(ComponentFailure(
                    component_name="FraudDetectionAgent",
                    error_type="FAILED",
                    error_message=fraud_res.error or "Fraud detection failed"
                ))
        except Exception as e:
            logger.error(f"Fraud detection exception: {e}")
            component_failures.append(ComponentFailure(
                component_name="FraudDetectionAgent",
                error_type="EXCEPTION",
                error_message=str(e)
            ))
        
        return await self._make_decision(
            claim, verification_result, extraction_result, policy_result, fraud_result, component_failures
        )
    
    async def _make_decision(
        self,
        claim: Claim,
        verification_result: Optional[VerificationResult],
        extraction_result: Optional[ExtractionResult],
        policy_result: Optional[PolicyValidationResult],
        fraud_result: Optional[FraudDetectionResult],
        component_failures: List[ComponentFailure]
    ) -> ClaimDecision:
        decision_input = DecisionInput(
            claim_id=claim.claim_id,
            claimed_amount=claim.claimed_amount,
            verification_result=verification_result,
            extraction_result=extraction_result,
            policy_result=policy_result,
            fraud_result=fraud_result,
            component_failures=component_failures
        )
        
        dec_result = await self.decision_engine.execute(decision_input)
        
        if dec_result.success and dec_result.data:
            decision = dec_result.data
            if dec_result.trace:
                self.trace_service.add_step(claim.claim_id, dec_result.trace)
            
            confidence_factors = []
            if verification_result:
                confidence_factors.append(verification_result.confidence)
            if extraction_result and extraction_result.confidence_scores:
                avg_ext = sum(extraction_result.confidence_scores.values()) / len(extraction_result.confidence_scores)
                confidence_factors.append(avg_ext)
            if policy_result and policy_result.trace:
                confidence_factors.append(policy_result.trace.confidence_contribution)
            if fraud_result:
                confidence_factors.append(1.0 - fraud_result.fraud_score)
            
            overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
            
            if component_failures:
                overall_confidence *= 0.7
            
            claim_trace = self.trace_service.complete_trace(claim.claim_id, overall_confidence)
            decision.full_trace = claim_trace
            
            return decision
        else:
            logger.error(f"Decision engine failed: {dec_result.error}")
            
            return ClaimDecision(
                claim_id=claim.claim_id,
                decision=DecisionType.MANUAL_REVIEW,
                approved_amount=0.0,
                rejected_amount=0.0,
                confidence_score=0.1,
                reasons=[],
                recommendations=["System error - manual review required"],
                verification_result=verification_result,
                extraction_result=extraction_result,
                policy_result=policy_result,
                fraud_result=fraud_result
            )
