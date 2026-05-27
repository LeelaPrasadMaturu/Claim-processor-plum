from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Any, Dict
from dataclasses import dataclass
from datetime import datetime
import time
import uuid
import logging

from ..models.trace import TraceStep, AgentStatus

T = TypeVar('T')
R = TypeVar('R')

logger = logging.getLogger(__name__)


@dataclass
class AgentResult(Generic[R]):
    success: bool
    data: Optional[R]
    error: Optional[str]
    degraded: bool
    trace: Optional[TraceStep]


class Success(AgentResult[R]):
    def __init__(self, data: R, trace: Optional[TraceStep] = None):
        super().__init__(success=True, data=data, error=None, degraded=False, trace=trace)


class Degraded(AgentResult[R]):
    def __init__(self, data: R, message: str, trace: Optional[TraceStep] = None):
        super().__init__(success=True, data=data, error=message, degraded=True, trace=trace)


class Failed(AgentResult[R]):
    def __init__(self, error: str, recoverable: bool = True, trace: Optional[TraceStep] = None):
        super().__init__(success=False, data=None, error=error, degraded=False, trace=trace)
        self.recoverable = recoverable


class BaseAgent(ABC, Generic[T, R]):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
    
    def _create_trace(self, step_id: str, input_summary: Dict[str, Any]) -> TraceStep:
        return TraceStep(
            step_id=step_id,
            agent_name=self.name,
            timestamp=datetime.utcnow(),
            input_summary=input_summary
        )
    
    async def execute(self, input_data: T) -> AgentResult[R]:
        step_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        trace = self._create_trace(step_id, self._summarize_input(input_data))
        
        try:
            self.logger.info(f"Starting execution: {step_id}")
            result = await self._process(input_data, trace)
            
            duration_ms = int((time.time() - start_time) * 1000)
            trace.duration_ms = duration_ms
            trace.status = AgentStatus.SUCCESS
            trace.output_summary = self._summarize_output(result)
            
            self.logger.info(f"Completed execution: {step_id} in {duration_ms}ms")
            return Success(result, trace)
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            trace.duration_ms = duration_ms
            trace.status = AgentStatus.FAILED
            trace.errors.append(str(e))
            
            self.logger.error(f"Execution failed: {step_id} - {str(e)}")
            
            fallback = await self._handle_failure(input_data, e, trace)
            if fallback is not None:
                trace.status = AgentStatus.DEGRADED
                return Degraded(fallback, str(e), trace)
            
            return Failed(str(e), recoverable=True, trace=trace)
    
    @abstractmethod
    async def _process(self, input_data: T, trace: TraceStep) -> R:
        pass
    
    async def _handle_failure(self, input_data: T, error: Exception, trace: TraceStep) -> Optional[R]:
        return None
    
    def _summarize_input(self, input_data: T) -> Dict[str, Any]:
        if hasattr(input_data, 'model_dump'):
            return {"type": type(input_data).__name__, "preview": str(input_data)[:200]}
        return {"type": type(input_data).__name__, "preview": str(input_data)[:200]}
    
    def _summarize_output(self, output: R) -> Dict[str, Any]:
        if hasattr(output, 'model_dump'):
            return {"type": type(output).__name__, "preview": str(output)[:200]}
        return {"type": type(output).__name__, "preview": str(output)[:200]}
