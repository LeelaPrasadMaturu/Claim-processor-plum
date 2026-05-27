from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from .trace import ClaimTrace, VerificationTrace, ExtractionTrace, PolicyTrace, FraudTrace
from .document import ClassifiedDocument, WrongDocument, PrescriptionData, BillData, LabReportData


class DecisionType(str, Enum):
    APPROVED = "APPROVED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class VerificationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    UNREADABLE = "UNREADABLE"


class VerificationResult(BaseModel):
    status: VerificationStatus
    documents_classified: List[ClassifiedDocument] = Field(default_factory=list)
    missing_documents: List[str] = Field(default_factory=list)
    wrong_documents: List[WrongDocument] = Field(default_factory=list)
    error_message: Optional[str] = None
    confidence: float = 1.0
    trace: Optional[VerificationTrace] = None


class ExtractionResult(BaseModel):
    prescription_data: Optional[PrescriptionData] = None
    bill_data: Optional[BillData] = None
    lab_report_data: Optional[LabReportData] = None
    patient_names_found: List[str] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    extraction_warnings: List[str] = Field(default_factory=list)
    trace: Optional[ExtractionTrace] = None


class ViolationCode(str, Enum):
    WAITING_PERIOD = "WAITING_PERIOD"
    EXCLUSION = "EXCLUSION"
    EXCLUDED_CONDITION = "EXCLUDED_CONDITION"
    PRE_AUTH_MISSING = "PRE_AUTH_MISSING"
    PER_CLAIM_EXCEEDED = "PER_CLAIM_EXCEEDED"
    ANNUAL_LIMIT_EXCEEDED = "ANNUAL_LIMIT_EXCEEDED"
    SUB_LIMIT_EXCEEDED = "SUB_LIMIT_EXCEEDED"


class PolicyViolation(BaseModel):
    code: ViolationCode
    message: str
    details: Optional[Dict[str, Any]] = None


class AdjustmentType(str, Enum):
    NETWORK_DISCOUNT = "NETWORK_DISCOUNT"
    COPAY = "COPAY"
    SUB_LIMIT = "SUB_LIMIT"
    LINE_ITEM_EXCLUSION = "LINE_ITEM_EXCLUSION"


class Adjustment(BaseModel):
    type: AdjustmentType
    description: str
    amount: float
    original_amount: Optional[float] = None


class PolicyValidationResult(BaseModel):
    is_eligible: bool
    violations: List[PolicyViolation] = Field(default_factory=list)
    adjustments: List[Adjustment] = Field(default_factory=list)
    eligible_amount: float = 0.0
    trace: Optional[PolicyTrace] = None


class FraudFlagType(str, Enum):
    SAME_DAY_CLAIMS = "SAME_DAY_CLAIMS"
    HIGH_VALUE = "HIGH_VALUE"
    MONTHLY_LIMIT_EXCEEDED = "MONTHLY_LIMIT_EXCEEDED"
    DOCUMENT_ALTERATION = "DOCUMENT_ALTERATION"
    SUSPICIOUS_PATTERN = "SUSPICIOUS_PATTERN"


class FraudFlag(BaseModel):
    type: FraudFlagType
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    details: Optional[Dict[str, Any]] = None


class FraudDetectionResult(BaseModel):
    fraud_score: float = Field(ge=0.0, le=1.0, default=0.0)
    flags: List[FraudFlag] = Field(default_factory=list)
    requires_manual_review: bool = False
    trace: Optional[FraudTrace] = None


class LineItemDecision(BaseModel):
    description: str
    claimed_amount: float
    approved_amount: float
    status: Literal["APPROVED", "REJECTED", "PARTIAL"]
    reason: Optional[str] = None


class DecisionReason(BaseModel):
    code: str
    message: str
    category: Literal["APPROVAL", "REJECTION", "ADJUSTMENT", "WARNING"]


class ClaimDecision(BaseModel):
    claim_id: str
    decision: DecisionType
    approved_amount: float = 0.0
    rejected_amount: float = 0.0
    confidence_score: float = Field(ge=0.0, le=1.0, default=1.0)
    reasons: List[DecisionReason] = Field(default_factory=list)
    line_item_breakdown: Optional[List[LineItemDecision]] = None
    recommendations: Optional[List[str]] = Field(default_factory=list)
    full_trace: Optional[ClaimTrace] = None
    
    verification_result: Optional[VerificationResult] = None
    extraction_result: Optional[ExtractionResult] = None
    policy_result: Optional[PolicyValidationResult] = None
    fraud_result: Optional[FraudDetectionResult] = None
