from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import date, datetime
from .document import Document


class ClaimCategory(str, Enum):
    CONSULTATION = "CONSULTATION"
    DIAGNOSTIC = "DIAGNOSTIC"
    PHARMACY = "PHARMACY"
    DENTAL = "DENTAL"
    VISION = "VISION"
    ALTERNATIVE_MEDICINE = "ALTERNATIVE_MEDICINE"


class ClaimStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class PreviousClaim(BaseModel):
    claim_id: str
    date: str
    amount: float
    provider: Optional[str] = None


class ClaimSubmission(BaseModel):
    member_id: str
    policy_id: str = "PLUM_GHI_2024"
    claim_category: ClaimCategory
    treatment_date: str
    claimed_amount: float
    hospital_name: Optional[str] = None
    ytd_claims_amount: float = 0.0
    claims_history: List[PreviousClaim] = Field(default_factory=list)
    simulate_component_failure: bool = False


class Claim(BaseModel):
    claim_id: str
    member_id: str
    policy_id: str
    claim_category: ClaimCategory
    treatment_date: str
    claimed_amount: float
    hospital_name: Optional[str] = None
    ytd_claims_amount: float = 0.0
    claims_history: List[PreviousClaim] = Field(default_factory=list)
    documents: List[Document] = Field(default_factory=list)
    status: ClaimStatus = ClaimStatus.SUBMITTED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    simulate_component_failure: bool = False


class Member(BaseModel):
    member_id: str
    name: str
    date_of_birth: str
    gender: str
    relationship: str
    join_date: str
    dependents: List[str] = Field(default_factory=list)
    primary_member_id: Optional[str] = None
