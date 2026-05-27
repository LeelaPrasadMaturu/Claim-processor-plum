from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import date


class DocumentType(str, Enum):
    PRESCRIPTION = "PRESCRIPTION"
    HOSPITAL_BILL = "HOSPITAL_BILL"
    PHARMACY_BILL = "PHARMACY_BILL"
    LAB_REPORT = "LAB_REPORT"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    DENTAL_REPORT = "DENTAL_REPORT"
    UNKNOWN = "UNKNOWN"


class DocumentQuality(str, Enum):
    GOOD = "GOOD"
    PARTIAL = "PARTIAL"
    UNREADABLE = "UNREADABLE"


class Document(BaseModel):
    file_id: str
    file_name: str
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    actual_type: Optional[str] = None
    quality: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    patient_name_on_doc: Optional[str] = None


class ClassifiedDocument(BaseModel):
    file_id: str
    file_name: str
    file_path: Optional[str] = None
    detected_type: DocumentType
    readability: DocumentQuality
    confidence: float = Field(ge=0.0, le=1.0)


class WrongDocument(BaseModel):
    file_id: str
    file_name: str
    uploaded_type: DocumentType
    required_type: DocumentType


class PrescriptionData(BaseModel):
    doctor_name: Optional[str] = None
    doctor_registration: Optional[str] = None
    specialization: Optional[str] = None
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    date: Optional[str] = None
    diagnosis: Optional[str] = None
    secondary_diagnosis: Optional[str] = None
    medicines: List[str] = Field(default_factory=list)
    tests_ordered: List[str] = Field(default_factory=list)
    hospital_name: Optional[str] = None
    treatment: Optional[str] = None


class LineItem(BaseModel):
    description: str
    amount: float
    quantity: Optional[int] = 1


class BillData(BaseModel):
    hospital_name: Optional[str] = None
    bill_number: Optional[str] = None
    date: Optional[str] = None
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    referring_doctor: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    gst_amount: Optional[float] = None
    total: Optional[float] = None
    payment_mode: Optional[str] = None
    gstin: Optional[str] = None


class LabReportData(BaseModel):
    lab_name: Optional[str] = None
    nabl_status: Optional[bool] = None
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    referring_doctor: Optional[str] = None
    sample_date: Optional[str] = None
    report_date: Optional[str] = None
    test_name: Optional[str] = None
    test_results: List[Dict[str, Any]] = Field(default_factory=list)
    remarks: Optional[str] = None
    pathologist_name: Optional[str] = None
    pathologist_registration: Optional[str] = None
