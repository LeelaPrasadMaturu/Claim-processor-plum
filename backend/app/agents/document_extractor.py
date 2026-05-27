from typing import List, Optional, Dict, Any, Set
from datetime import datetime
import uuid

from .base import BaseAgent, AgentResult, Success, Degraded, Failed
from ..models.document import (
    DocumentType, ClassifiedDocument, PrescriptionData, BillData, LabReportData, LineItem
)
from ..models.decision import ExtractionResult
from ..models.trace import ExtractionTrace, AgentStatus, RuleEvaluation
from ..services.llm_service import LLMService


class ExtractionInput:
    def __init__(self, documents: List[ClassifiedDocument], document_contents: Optional[Dict[str, Dict]] = None):
        self.documents = documents
        self.document_contents = document_contents or {}


class DocumentExtractionAgent(BaseAgent[ExtractionInput, ExtractionResult]):
    def __init__(self, llm_service: Optional[LLMService] = None):
        super().__init__("DocumentExtractionAgent")
        self.llm_service = llm_service or LLMService()
    
    def _create_trace(self, step_id: str, input_summary: dict) -> ExtractionTrace:
        from datetime import datetime
        return ExtractionTrace(
            step_id=step_id,
            agent_name=self.name,
            timestamp=datetime.utcnow(),
            input_summary=input_summary
        )
    
    async def _process(self, input_data: ExtractionInput, trace: ExtractionTrace) -> ExtractionResult:
        prescription_data = None
        bill_data = None
        lab_report_data = None
        patient_names: Set[str] = set()
        confidence_scores: Dict[str, float] = {}
        warnings: List[str] = []
        fields_extracted = 0
        fields_failed = 0
        
        for doc in input_data.documents:
            if doc.file_id in input_data.document_contents:
                content = input_data.document_contents[doc.file_id]
                
                if doc.detected_type == DocumentType.PRESCRIPTION:
                    prescription_data = self._parse_prescription_content(content)
                    if prescription_data.patient_name:
                        patient_names.add(prescription_data.patient_name)
                    confidence_scores["prescription"] = 0.95
                    fields_extracted += self._count_fields(prescription_data)
                    
                elif doc.detected_type == DocumentType.HOSPITAL_BILL:
                    bill_data = self._parse_bill_content(content)
                    if bill_data.patient_name:
                        patient_names.add(bill_data.patient_name)
                    confidence_scores["bill"] = 0.95
                    fields_extracted += self._count_fields(bill_data)
                    
                elif doc.detected_type == DocumentType.PHARMACY_BILL:
                    bill_data = self._parse_bill_content(content)
                    if bill_data.patient_name:
                        patient_names.add(bill_data.patient_name)
                    confidence_scores["pharmacy_bill"] = 0.95
                    fields_extracted += self._count_fields(bill_data)
                    
                elif doc.detected_type == DocumentType.LAB_REPORT:
                    lab_report_data = self._parse_lab_content(content)
                    if lab_report_data.patient_name:
                        patient_names.add(lab_report_data.patient_name)
                    confidence_scores["lab_report"] = 0.95
                    fields_extracted += self._count_fields(lab_report_data)
                
                trace.extraction_details[doc.file_id] = {
                    "type": doc.detected_type.value,
                    "source": "provided_content",
                    "success": True
                }
                continue
            
            if not doc.file_path:
                warnings.append(f"No file path for document {doc.file_id}, skipping extraction")
                fields_failed += 1
                continue
            
            try:
                image_base64 = self.llm_service.encode_image_to_base64(doc.file_path)
                
                if doc.detected_type == DocumentType.PRESCRIPTION:
                    extracted, llm_call = await self.llm_service.extract_prescription_data(image_base64)
                    trace.llm_calls.append(llm_call)
                    
                    if "error" not in extracted:
                        prescription_data = PrescriptionData(
                            doctor_name=extracted.get("doctor_name"),
                            doctor_registration=extracted.get("doctor_registration"),
                            specialization=extracted.get("specialization"),
                            patient_name=extracted.get("patient_name"),
                            patient_age=extracted.get("patient_age"),
                            patient_gender=extracted.get("patient_gender"),
                            date=extracted.get("date"),
                            diagnosis=extracted.get("diagnosis"),
                            secondary_diagnosis=extracted.get("secondary_diagnosis"),
                            medicines=extracted.get("medicines", []),
                            tests_ordered=extracted.get("tests_ordered", []),
                            hospital_name=extracted.get("hospital_name"),
                            treatment=extracted.get("treatment")
                        )
                        if prescription_data.patient_name:
                            patient_names.add(prescription_data.patient_name)
                        
                        conf_scores = extracted.get("confidence_scores", {})
                        confidence_scores["prescription"] = conf_scores.get("overall", 0.7)
                        fields_extracted += self._count_fields(prescription_data)
                    else:
                        warnings.append(f"Prescription extraction failed: {extracted.get('error')}")
                        fields_failed += 1
                
                elif doc.detected_type in [DocumentType.HOSPITAL_BILL, DocumentType.PHARMACY_BILL]:
                    extracted, llm_call = await self.llm_service.extract_bill_data(image_base64)
                    trace.llm_calls.append(llm_call)
                    
                    if "error" not in extracted:
                        line_items = [
                            LineItem(
                                description=item.get("description", "Unknown"),
                                amount=item.get("amount", 0),
                                quantity=item.get("quantity", 1)
                            )
                            for item in extracted.get("line_items", [])
                        ]
                        
                        bill_data = BillData(
                            hospital_name=extracted.get("hospital_name"),
                            bill_number=extracted.get("bill_number"),
                            date=extracted.get("date"),
                            patient_name=extracted.get("patient_name"),
                            patient_age=extracted.get("patient_age"),
                            patient_gender=extracted.get("patient_gender"),
                            referring_doctor=extracted.get("referring_doctor"),
                            line_items=line_items,
                            subtotal=extracted.get("subtotal"),
                            gst_amount=extracted.get("gst_amount"),
                            total=extracted.get("total", 0),
                            payment_mode=extracted.get("payment_mode"),
                            gstin=extracted.get("gstin")
                        )
                        if bill_data.patient_name:
                            patient_names.add(bill_data.patient_name)
                        
                        conf_scores = extracted.get("confidence_scores", {})
                        confidence_scores["bill"] = conf_scores.get("overall", 0.7)
                        fields_extracted += self._count_fields(bill_data)
                    else:
                        warnings.append(f"Bill extraction failed: {extracted.get('error')}")
                        fields_failed += 1
                
                elif doc.detected_type == DocumentType.LAB_REPORT:
                    extracted, llm_call = await self.llm_service.extract_lab_report_data(image_base64)
                    trace.llm_calls.append(llm_call)
                    
                    if "error" not in extracted:
                        lab_report_data = LabReportData(
                            lab_name=extracted.get("lab_name"),
                            nabl_status=extracted.get("nabl_status"),
                            patient_name=extracted.get("patient_name"),
                            patient_age=extracted.get("patient_age"),
                            patient_gender=extracted.get("patient_gender"),
                            referring_doctor=extracted.get("referring_doctor"),
                            sample_date=extracted.get("sample_date"),
                            report_date=extracted.get("report_date"),
                            test_name=extracted.get("test_name"),
                            test_results=extracted.get("test_results", []),
                            remarks=extracted.get("remarks"),
                            pathologist_name=extracted.get("pathologist_name"),
                            pathologist_registration=extracted.get("pathologist_registration")
                        )
                        if lab_report_data.patient_name:
                            patient_names.add(lab_report_data.patient_name)
                        
                        conf_scores = extracted.get("confidence_scores", {})
                        confidence_scores["lab_report"] = conf_scores.get("overall", 0.7)
                        fields_extracted += self._count_fields(lab_report_data)
                    else:
                        warnings.append(f"Lab report extraction failed: {extracted.get('error')}")
                        fields_failed += 1
                
                trace.extraction_details[doc.file_id] = {
                    "type": doc.detected_type.value,
                    "source": "llm_extraction",
                    "success": True
                }
                
            except Exception as e:
                self.logger.error(f"Failed to extract from document {doc.file_id}: {e}")
                warnings.append(f"Extraction failed for {doc.file_name}: {str(e)}")
                fields_failed += 1
                trace.extraction_details[doc.file_id] = {
                    "type": doc.detected_type.value,
                    "source": "llm_extraction",
                    "success": False,
                    "error": str(e)
                }
        
        trace.fields_extracted = fields_extracted
        trace.fields_failed = fields_failed
        
        patient_names_list = list(patient_names)
        if len(patient_names_list) > 1:
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="patient_name_consistency",
                rule_description="Check if all documents belong to the same patient",
                passed=False,
                details=f"Found multiple patient names: {patient_names_list}"
            ))
            warnings.append(f"Documents may belong to different patients: {patient_names_list}")
        elif len(patient_names_list) == 1:
            trace.rules_evaluated.append(RuleEvaluation(
                rule_name="patient_name_consistency",
                rule_description="Check if all documents belong to the same patient",
                passed=True,
                details=f"Consistent patient name: {patient_names_list[0]}"
            ))
        
        overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.5
        trace.confidence_contribution = overall_confidence
        
        return ExtractionResult(
            prescription_data=prescription_data,
            bill_data=bill_data,
            lab_report_data=lab_report_data,
            patient_names_found=patient_names_list,
            confidence_scores=confidence_scores,
            extraction_warnings=warnings,
            trace=trace
        )
    
    def _parse_prescription_content(self, content: Dict[str, Any]) -> PrescriptionData:
        return PrescriptionData(
            doctor_name=content.get("doctor_name"),
            doctor_registration=content.get("doctor_registration"),
            specialization=content.get("specialization"),
            patient_name=content.get("patient_name"),
            patient_age=content.get("patient_age"),
            patient_gender=content.get("patient_gender"),
            date=content.get("date"),
            diagnosis=content.get("diagnosis"),
            secondary_diagnosis=content.get("secondary_diagnosis"),
            medicines=content.get("medicines", []),
            tests_ordered=content.get("tests_ordered", []),
            hospital_name=content.get("hospital_name"),
            treatment=content.get("treatment")
        )
    
    def _parse_bill_content(self, content: Dict[str, Any]) -> BillData:
        line_items = []
        for item in content.get("line_items", []):
            line_items.append(LineItem(
                description=item.get("description", "Unknown"),
                amount=item.get("amount", 0),
                quantity=item.get("quantity", 1)
            ))
        
        return BillData(
            hospital_name=content.get("hospital_name"),
            bill_number=content.get("bill_number"),
            date=content.get("date"),
            patient_name=content.get("patient_name"),
            patient_age=content.get("patient_age"),
            patient_gender=content.get("patient_gender"),
            referring_doctor=content.get("referring_doctor"),
            line_items=line_items,
            subtotal=content.get("subtotal"),
            gst_amount=content.get("gst_amount"),
            total=content.get("total", 0),
            payment_mode=content.get("payment_mode"),
            gstin=content.get("gstin")
        )
    
    def _parse_lab_content(self, content: Dict[str, Any]) -> LabReportData:
        return LabReportData(
            lab_name=content.get("lab_name"),
            nabl_status=content.get("nabl_status"),
            patient_name=content.get("patient_name"),
            patient_age=content.get("patient_age"),
            patient_gender=content.get("patient_gender"),
            referring_doctor=content.get("referring_doctor"),
            sample_date=content.get("sample_date"),
            report_date=content.get("report_date"),
            test_name=content.get("test_name"),
            test_results=content.get("test_results", []),
            remarks=content.get("remarks"),
            pathologist_name=content.get("pathologist_name"),
            pathologist_registration=content.get("pathologist_registration")
        )
    
    def _count_fields(self, data: Any) -> int:
        if data is None:
            return 0
        count = 0
        for field_name, field_value in data.model_dump().items():
            if field_value is not None:
                if isinstance(field_value, list):
                    count += len(field_value)
                else:
                    count += 1
        return count
    
    async def _handle_failure(self, input_data: ExtractionInput, error: Exception, trace: ExtractionTrace) -> Optional[ExtractionResult]:
        trace.warnings.append(f"Extraction degraded due to error: {str(error)}")
        
        return ExtractionResult(
            patient_names_found=[],
            confidence_scores={"overall": 0.2},
            extraction_warnings=[f"Extraction failed with fallback: {str(error)}"],
            trace=trace
        )
