from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from .base import BaseAgent, AgentResult, Success, Degraded, Failed
from ..models.document import (
    Document, DocumentType, DocumentQuality, ClassifiedDocument, WrongDocument
)
from ..models.decision import VerificationResult, VerificationStatus
from ..models.trace import VerificationTrace, AgentStatus, RuleEvaluation
from ..services.llm_service import LLMService
from ..services.policy_service import PolicyService


class VerificationInput:
    def __init__(self, claim_category: str, documents: List[Document]):
        self.claim_category = claim_category
        self.documents = documents


class DocumentVerificationAgent(BaseAgent[VerificationInput, VerificationResult]):
    def __init__(self, llm_service: Optional[LLMService] = None, policy_service: Optional[PolicyService] = None):
        super().__init__("DocumentVerificationAgent")
        self.llm_service = llm_service or LLMService()
        self.policy_service = policy_service or PolicyService()
    
    def _create_trace(self, step_id: str, input_summary: dict) -> VerificationTrace:
        from datetime import datetime
        return VerificationTrace(
            step_id=step_id,
            agent_name=self.name,
            timestamp=datetime.utcnow(),
            input_summary=input_summary
        )
    
    async def _process(self, input_data: VerificationInput, trace: VerificationTrace) -> VerificationResult:
        trace.documents_processed = len(input_data.documents)
        classified_docs: List[ClassifiedDocument] = []
        unreadable_docs: List[str] = []
        
        for doc in input_data.documents:
            if doc.actual_type and doc.content:
                doc_type = self._map_type_string(doc.actual_type)
                quality = DocumentQuality.GOOD
                if doc.quality:
                    quality = DocumentQuality(doc.quality) if doc.quality in ["GOOD", "PARTIAL", "UNREADABLE"] else DocumentQuality.GOOD
                
                classified = ClassifiedDocument(
                    file_id=doc.file_id,
                    file_name=doc.file_name,
                    file_path=doc.file_path,
                    detected_type=doc_type,
                    readability=quality,
                    confidence=0.95
                )
                classified_docs.append(classified)
                
                if quality == DocumentQuality.UNREADABLE:
                    unreadable_docs.append(doc.file_name)
                
                trace.documents_classified.append({
                    "file_id": doc.file_id,
                    "detected_type": doc_type.value,
                    "readability": quality.value,
                    "confidence": 0.95,
                    "source": "provided_metadata"
                })
            elif doc.file_path:
                try:
                    image_base64 = self.llm_service.encode_image_to_base64(doc.file_path)
                    classification, llm_call = await self.llm_service.classify_document(image_base64)
                    trace.llm_calls.append(llm_call)
                    
                    doc_type = self._map_type_string(classification.get("type", "UNKNOWN"))
                    readability = self._map_readability(classification.get("readability", "GOOD"))
                    confidence = classification.get("confidence", 0.5)
                    
                    classified = ClassifiedDocument(
                        file_id=doc.file_id,
                        file_name=doc.file_name,
                        file_path=doc.file_path,
                        detected_type=doc_type,
                        readability=readability,
                        confidence=confidence
                    )
                    classified_docs.append(classified)
                    
                    if readability == DocumentQuality.UNREADABLE:
                        unreadable_docs.append(doc.file_name)
                    
                    trace.documents_classified.append({
                        "file_id": doc.file_id,
                        "detected_type": doc_type.value,
                        "readability": readability.value,
                        "confidence": confidence,
                        "source": "llm_classification"
                    })
                except Exception as e:
                    self.logger.error(f"Failed to classify document {doc.file_id}: {e}")
                    classified = ClassifiedDocument(
                        file_id=doc.file_id,
                        file_name=doc.file_name,
                        file_path=doc.file_path,
                        detected_type=DocumentType.UNKNOWN,
                        readability=DocumentQuality.UNREADABLE,
                        confidence=0.0
                    )
                    classified_docs.append(classified)
                    unreadable_docs.append(doc.file_name)
                    trace.errors.append(f"Classification failed for {doc.file_name}: {str(e)}")
            else:
                doc_type = self._map_type_string(doc.actual_type) if doc.actual_type else DocumentType.UNKNOWN
                quality = DocumentQuality(doc.quality) if doc.quality and doc.quality in ["GOOD", "PARTIAL", "UNREADABLE"] else DocumentQuality.GOOD
                
                classified = ClassifiedDocument(
                    file_id=doc.file_id,
                    file_name=doc.file_name,
                    detected_type=doc_type,
                    readability=quality,
                    confidence=0.8
                )
                classified_docs.append(classified)
                
                if quality == DocumentQuality.UNREADABLE:
                    unreadable_docs.append(doc.file_name)
        
        if unreadable_docs:
            unreadable_list = ", ".join(unreadable_docs)
            error_msg = f"The following document(s) are unreadable and cannot be processed: {unreadable_list}. " \
                        f"Please re-upload a clearer image or scan of these document(s)."
            
            trace.decision_factors.append(f"Unreadable documents detected: {unreadable_list}")
            
            return VerificationResult(
                status=VerificationStatus.UNREADABLE,
                documents_classified=classified_docs,
                error_message=error_msg,
                confidence=0.3,
                trace=trace
            )
        
        requirements = self.policy_service.get_document_requirements(input_data.claim_category)
        required_types = requirements.get("required", [])
        
        detected_types = {doc.detected_type.value for doc in classified_docs}
        
        missing_docs = []
        for req_type in required_types:
            if req_type not in detected_types:
                missing_docs.append(req_type)
        
        trace.rules_evaluated.append(RuleEvaluation(
            rule_name="document_requirements",
            rule_description=f"Check required documents for {input_data.claim_category}",
            passed=len(missing_docs) == 0,
            details=f"Required: {required_types}, Found: {list(detected_types)}, Missing: {missing_docs}"
        ))
        
        if missing_docs:
            uploaded_types = [doc.detected_type.value for doc in classified_docs]
            uploaded_str = ", ".join(uploaded_types) if uploaded_types else "none"
            missing_str = ", ".join(missing_docs)
            
            error_msg = f"Document verification failed for {input_data.claim_category} claim. " \
                        f"You uploaded: {uploaded_str}. " \
                        f"Required but missing: {missing_str}. " \
                        f"Please upload the missing document(s) to proceed with your claim."
            
            wrong_docs = []
            for doc in classified_docs:
                if doc.detected_type.value not in required_types:
                    for missing in missing_docs:
                        wrong_docs.append(WrongDocument(
                            file_id=doc.file_id,
                            file_name=doc.file_name,
                            uploaded_type=doc.detected_type,
                            required_type=DocumentType(missing)
                        ))
                        break
            
            trace.decision_factors.append(f"Missing required documents: {missing_docs}")
            
            return VerificationResult(
                status=VerificationStatus.INVALID,
                documents_classified=classified_docs,
                missing_documents=missing_docs,
                wrong_documents=wrong_docs,
                error_message=error_msg,
                confidence=0.9,
                trace=trace
            )
        
        avg_confidence = sum(doc.confidence for doc in classified_docs) / len(classified_docs) if classified_docs else 1.0
        
        trace.decision_factors.append("All required documents present and readable")
        trace.confidence_contribution = avg_confidence
        
        return VerificationResult(
            status=VerificationStatus.VALID,
            documents_classified=classified_docs,
            confidence=avg_confidence,
            trace=trace
        )
    
    def _map_type_string(self, type_str: Optional[str]) -> DocumentType:
        if not type_str:
            return DocumentType.UNKNOWN
        
        type_mapping = {
            "PRESCRIPTION": DocumentType.PRESCRIPTION,
            "HOSPITAL_BILL": DocumentType.HOSPITAL_BILL,
            "PHARMACY_BILL": DocumentType.PHARMACY_BILL,
            "LAB_REPORT": DocumentType.LAB_REPORT,
            "DISCHARGE_SUMMARY": DocumentType.DISCHARGE_SUMMARY,
            "DENTAL_REPORT": DocumentType.DENTAL_REPORT,
        }
        return type_mapping.get(type_str.upper(), DocumentType.UNKNOWN)
    
    def _map_readability(self, readability_str: str) -> DocumentQuality:
        readability_mapping = {
            "GOOD": DocumentQuality.GOOD,
            "PARTIAL": DocumentQuality.PARTIAL,
            "UNREADABLE": DocumentQuality.UNREADABLE,
        }
        return readability_mapping.get(readability_str.upper(), DocumentQuality.GOOD)
    
    async def _handle_failure(self, input_data: VerificationInput, error: Exception, trace: VerificationTrace) -> Optional[VerificationResult]:
        trace.warnings.append(f"Verification degraded due to error: {str(error)}")
        
        classified_docs = []
        for doc in input_data.documents:
            doc_type = self._map_type_string(doc.actual_type) if doc.actual_type else DocumentType.UNKNOWN
            classified = ClassifiedDocument(
                file_id=doc.file_id,
                file_name=doc.file_name,
                detected_type=doc_type,
                readability=DocumentQuality.PARTIAL,
                confidence=0.3
            )
            classified_docs.append(classified)
        
        return VerificationResult(
            status=VerificationStatus.VALID,
            documents_classified=classified_docs,
            confidence=0.3,
            trace=trace
        )
