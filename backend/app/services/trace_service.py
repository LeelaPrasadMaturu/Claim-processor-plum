from typing import Optional, List
from datetime import datetime
import time

from ..models.trace import ClaimTrace, TraceStep, ComponentFailure


class TraceService:
    def __init__(self):
        self.traces = {}
    
    def create_trace(self, claim_id: str) -> ClaimTrace:
        trace = ClaimTrace(
            claim_id=claim_id,
            started_at=datetime.utcnow()
        )
        self.traces[claim_id] = trace
        return trace
    
    def add_step(self, claim_id: str, step: TraceStep) -> None:
        if claim_id in self.traces:
            self.traces[claim_id].steps.append(step)
    
    def add_component_failure(self, claim_id: str, failure: ComponentFailure) -> None:
        if claim_id in self.traces:
            self.traces[claim_id].component_failures.append(failure.component_name)
    
    def complete_trace(self, claim_id: str, overall_confidence: float) -> Optional[ClaimTrace]:
        if claim_id not in self.traces:
            return None
        
        trace = self.traces[claim_id]
        trace.completed_at = datetime.utcnow()
        trace.total_duration_ms = sum(step.duration_ms for step in trace.steps)
        trace.overall_confidence = overall_confidence
        
        return trace
    
    def get_trace(self, claim_id: str) -> Optional[ClaimTrace]:
        return self.traces.get(claim_id)
