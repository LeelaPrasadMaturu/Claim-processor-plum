# Health Insurance Claims Processing System - Architecture Document

## Overview

This document describes the architecture of the multi-agent Health Insurance Claims Processing System built for Plum. The system automates the review of health insurance claims by processing uploaded documents, validating against policy rules, detecting fraud signals, and producing explainable decisions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend Layer                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Web UI (HTML/CSS/JS)                                            │   │
│  │  - Claim Submission Form                                         │   │
│  │  - Decision Review Dashboard                                     │   │
│  │  - Test Runner Interface                                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            API Layer                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI Server                                                  │   │
│  │  - POST /api/claims        Submit claim with documents           │   │
│  │  - POST /api/claims/json   Submit claim with embedded data       │   │
│  │  - GET  /api/claims/policy Get policy information                │   │
│  │  - GET  /api/claims/members List members                         │   │
│  │  - POST /api/decisions/run-all-tests Run evaluation              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Orchestration Layer                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ClaimOrchestrator                                               │   │
│  │  - Coordinates agent execution pipeline                          │   │
│  │  - Implements graceful degradation                               │   │
│  │  - Manages component failures                                    │   │
│  │  - Aggregates traces                                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  TraceService                                                    │   │
│  │  - Creates and manages claim traces                              │   │
│  │  - Aggregates agent traces                                       │   │
│  │  - Calculates overall confidence                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Multi-Agent Layer                               │
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │  Document        │  │  Document        │  │  Policy          │      │
│  │  Verification    │──│  Extraction      │──│  Validation      │      │
│  │  Agent           │  │  Agent           │  │  Agent           │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│           │                    │                     │                  │
│           │                    │                     ▼                  │
│           │                    │            ┌──────────────────┐        │
│           │                    │            │  Fraud Detection │        │
│           │                    │            │  Agent           │        │
│           │                    │            └──────────────────┘        │
│           │                    │                     │                  │
│           └────────────────────┴─────────────────────┘                  │
│                                    │                                    │
│                                    ▼                                    │
│                         ┌──────────────────┐                            │
│                         │  Decision Engine │                            │
│                         │  Agent           │                            │
│                         └──────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│     External Services        │    │      Storage Layer           │
│  ┌────────────────────────┐  │    │  ┌────────────────────────┐  │
│  │  OpenAI GPT-4o Vision  │  │    │  │  MongoDB               │  │
│  │  - Document classify   │  │    │  │  - Claims              │  │
│  │  - Data extraction     │  │    │  │  - Decisions           │  │
│  └────────────────────────┘  │    │  │  - Traces              │  │
└──────────────────────────────┘    │  └────────────────────────┘  │
                                    │  ┌────────────────────────┐  │
                                    │  │  File Storage          │  │
                                    │  │  - Uploaded documents  │  │
                                    │  └────────────────────────┘  │
                                    └──────────────────────────────┘
```

## Agent Pipeline Flow

### 1. Document Verification Agent

**Purpose**: Validates that the correct document types are uploaded for the claim category.

**Processing Flow**:
1. Receive claim category and uploaded documents
2. For each document:
   - If file content provided (test mode): Use metadata directly
   - If file path provided: Use OpenAI Vision to classify document type
   - Assess readability (GOOD, PARTIAL, UNREADABLE)
3. Compare detected types against required documents for category
4. Generate specific error messages if documents are wrong or missing

**Early Stop Conditions**:
- Missing required documents → INVALID status with specific message
- Unreadable documents → UNREADABLE status with re-upload request

### 2. Document Extraction Agent

**Purpose**: Extracts structured data from verified documents.

**Processing Flow**:
1. Receive classified documents
2. For each document type:
   - PRESCRIPTION: Extract doctor, patient, diagnosis, medicines, tests
   - HOSPITAL_BILL: Extract hospital, patient, line items, total
   - LAB_REPORT: Extract lab, patient, test results, pathologist
3. Collect all patient names found across documents
4. Flag name mismatches for fraud check

**Output**: Structured data objects with confidence scores per field

### 3. Policy Validation Agent

**Purpose**: Validates claim against policy rules.

**Checks Performed**:
1. **Member Validation**: Verify member exists in policy roster
2. **Waiting Period**: Check if member has completed waiting periods for specific conditions
3. **Exclusions**: Check if diagnosis/procedures are excluded
4. **Pre-Authorization**: Check if procedures require pre-auth above threshold
5. **Limits**: Check per-claim and sub-limits (category-specific)

**Adjustments Calculated**:
- Network hospital discount (applied first)
- Co-pay percentage (applied on discounted amount)
- Line-item exclusions (for dental)

### 4. Fraud Detection Agent

**Purpose**: Identifies suspicious patterns requiring manual review.

**Signals Checked**:
1. **Same-Day Claims**: Multiple claims on same date (limit: 2)
2. **High Value**: Claims above ₹25,000 threshold
3. **Monthly Claims**: Excessive claims in same month (limit: 6)
4. **Name Mismatch**: Different patient names across documents
5. **Multiple Providers**: Many different providers on same day

**Output**: Fraud score (0-1) and flags with severity levels

### 5. Decision Engine Agent

**Purpose**: Combines all results to produce final decision.

**Decision Logic**:
1. Check verification result → Early stop if INVALID/UNREADABLE
2. Check extraction result → Early stop if patient name mismatch
3. Check fraud result → Route to MANUAL_REVIEW if high fraud score
4. Check policy violations → REJECTED if hard violations
5. Apply adjustments → Calculate final approved amount
6. Determine decision type: APPROVED, PARTIAL, REJECTED, or MANUAL_REVIEW

## Graceful Degradation

The system is designed to continue processing even when components fail:

```python
class BaseAgent:
    async def execute(self, input_data) -> AgentResult:
        try:
            result = await self._process(input_data, trace)
            return Success(result, trace)
        except Exception as e:
            fallback = await self._handle_failure(input_data, e, trace)
            if fallback:
                return Degraded(fallback, str(e), trace)
            return Failed(str(e), trace)
```

**Degradation Behaviors**:
- **Verification Failure**: Continue with partial classification
- **Extraction Failure**: Continue with minimal data
- **Policy Failure**: Continue with full claimed amount
- **Fraud Failure**: Flag for manual review
- **Multiple Failures**: Reduce confidence score proportionally

## Observability System

Every agent produces a trace object containing:

```python
class TraceStep:
    step_id: str
    agent_name: str
    timestamp: datetime
    duration_ms: int
    status: AgentStatus  # SUCCESS, DEGRADED, FAILED
    input_summary: dict
    output_summary: dict
    llm_calls: List[LLMCall]
    rules_evaluated: List[RuleEvaluation]
    decision_factors: List[str]
    confidence_contribution: float
    errors: List[str]
```

The ClaimTrace aggregates all step traces:

```python
class ClaimTrace:
    claim_id: str
    started_at: datetime
    completed_at: datetime
    total_duration_ms: int
    steps: List[TraceStep]
    component_failures: List[str]
    overall_confidence: float
```

## Design Decisions

### Why Multi-Agent Architecture?

1. **Separation of Concerns**: Each agent has a single responsibility
2. **Testability**: Agents can be tested in isolation
3. **Graceful Degradation**: Individual failures don't crash the system
4. **Explainability**: Each agent contributes to the decision trace
5. **Extensibility**: New agents can be added without modifying existing ones

### Why Not Microservices?

For this use case, a monolithic multi-agent design was chosen because:
- Lower operational complexity
- Easier local development
- No network overhead between agents
- Simpler deployment

### LLM Integration Strategy

OpenAI GPT-4o Vision is used for:
1. Document classification
2. Data extraction from images

**Error Handling**:
- Timeout: Return partial results with reduced confidence
- API failure: Fall back to metadata-based classification
- Invalid response: Parse what's possible, mark rest as null

## Limitations and Future Improvements

### Current Limitations

1. **No Real Document Storage**: Documents are processed in-memory for tests
2. **Single LLM Provider**: Only OpenAI is implemented
3. **No Caching**: Each claim is processed from scratch
4. **Simple Fraud Detection**: Rule-based only, no ML models
5. **No Batch Processing**: Claims processed one at a time

### Improvements for 10x Scale

1. **Async Processing Queue**:
   - Use Celery/RQ for background processing
   - Redis for job queue and caching

2. **Multi-Provider LLM**:
   - Add fallback to Claude/Gemini
   - Load balancing across providers

3. **Document Processing Pipeline**:
   - Pre-processing service for OCR
   - Document storage in S3/GCS
   - Caching of extraction results

4. **ML-Based Fraud Detection**:
   - Train model on historical fraud data
   - Real-time scoring API

5. **Horizontal Scaling**:
   - Kubernetes deployment
   - Auto-scaling based on queue depth
   - Read replicas for MongoDB

6. **Enhanced Observability**:
   - Integration with Datadog/New Relic
   - Custom dashboards for claims metrics
   - Alerting on anomalies

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend | Python/FastAPI | Best AI/ML ecosystem, async support |
| LLM | OpenAI GPT-4o | Best vision capabilities for documents |
| Database | MongoDB | Flexible schema for documents and traces |
| Frontend | HTML/CSS/JS | Simple, no build step, fast to develop |

## Running the System

### Prerequisites
- Python 3.9+
- MongoDB (optional, runs without persistence)
- OpenAI API key (for actual document processing)

### Setup
```bash
cd claims-processor/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Server
```bash
cd claims-processor/backend
uvicorn app.main:app --reload --port 8000
```

### Run Tests
```bash
cd claims-processor/backend
python -m tests.test_eval
```

### Environment Variables
```
OPENAI_API_KEY=sk-...
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=claims_processor
UPLOAD_DIR=./uploads
```
