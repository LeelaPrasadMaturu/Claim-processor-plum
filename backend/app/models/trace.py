from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class LLMCall(BaseModel):
    model: str
    prompt_summary: str
    response_summary: str
    tokens_used: Optional[int] = None
    latency_ms: int
    success: bool


class RuleEvaluation(BaseModel):
    rule_name: str
    rule_description: str
    passed: bool
    details: Optional[str] = None


class TraceStep(BaseModel):
    step_id: str
    agent_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: int = 0
    status: AgentStatus = AgentStatus.SUCCESS
    input_summary: Dict[str, Any] = Field(default_factory=dict)
    output_summary: Dict[str, Any] = Field(default_factory=dict)
    llm_calls: List[LLMCall] = Field(default_factory=list)
    rules_evaluated: List[RuleEvaluation] = Field(default_factory=list)
    decision_factors: List[str] = Field(default_factory=list)
    confidence_contribution: float = 1.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class VerificationTrace(TraceStep):
    documents_processed: int = 0
    documents_classified: List[Dict[str, Any]] = Field(default_factory=list)


class ExtractionTrace(TraceStep):
    fields_extracted: int = 0
    fields_failed: int = 0
    extraction_details: Dict[str, Any] = Field(default_factory=dict)


class PolicyTrace(TraceStep):
    rules_checked: int = 0
    violations_found: int = 0
    adjustments_applied: List[Dict[str, Any]] = Field(default_factory=list)


class FraudTrace(TraceStep):
    signals_checked: int = 0
    flags_raised: int = 0
    fraud_indicators: List[Dict[str, Any]] = Field(default_factory=list)


class ClaimTrace(BaseModel):
    claim_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_duration_ms: int = 0
    steps: List[TraceStep] = Field(default_factory=list)
    component_failures: List[str] = Field(default_factory=list)
    overall_confidence: float = 1.0


class ComponentFailure(BaseModel):
    component_name: str
    error_type: str
    error_message: str
    recoverable: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)
