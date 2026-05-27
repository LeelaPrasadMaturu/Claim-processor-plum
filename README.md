# Health Insurance Claims Processing System

A multi-agent system for automating health insurance claims processing, built for Plum's AI Engineer assignment.

## Features

- **Multi-Agent Architecture**: 5 specialized agents working in pipeline
- **Document Verification**: Validates uploaded documents against requirements
- **Data Extraction**: Uses OpenAI GPT-4o Vision for document processing
- **Policy Validation**: Checks waiting periods, exclusions, limits, pre-authorization
- **Fraud Detection**: Identifies suspicious patterns for manual review
- **Full Observability**: Complete trace of every decision
- **Graceful Degradation**: Continues processing when components fail

## Quick Start

### Prerequisites

- Python 3.9+
- MongoDB (optional - runs without persistence)
- OpenAI API key (for actual document processing)

### Setup

```bash
# Navigate to backend
cd claims-processor/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Run the Server

```bash
cd claims-processor/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

### Run Tests

```bash
cd claims-processor/backend
source venv/bin/activate
python -m tests.test_eval
```

Expected output: **12/12 tests passing (100%)**

## Project Structure

```
claims-processor/
├── backend/
│   ├── app/
│   │   ├── agents/           # Multi-agent implementations
│   │   │   ├── base.py
│   │   │   ├── document_verifier.py
│   │   │   ├── document_extractor.py
│   │   │   ├── policy_validator.py
│   │   │   ├── fraud_detector.py
│   │   │   └── decision_engine.py
│   │   ├── models/           # Pydantic data models
│   │   ├── services/         # Business logic services
│   │   ├── api/              # FastAPI routes
│   │   └── db/               # Database layer
│   ├── tests/
│   │   └── test_eval.py      # Evaluation script
│   ├── policy_terms.json     # Policy configuration
│   ├── test_cases.json       # 12 test scenarios
│   └── requirements.txt
├── frontend/                 # Simple HTML/JS UI
├── ARCHITECTURE.md           # System design document
├── COMPONENT_CONTRACTS.md    # Interface specifications
└── README.md
```

## Test Cases

| Case | Scenario | Expected |
|------|----------|----------|
| TC001 | Wrong document uploaded | Stop with specific error |
| TC002 | Unreadable document | Request re-upload |
| TC003 | Documents for different patients | Reject with name mismatch |
| TC004 | Clean consultation claim | Approve with co-pay |
| TC005 | Diabetes during waiting period | Reject (waiting period) |
| TC006 | Dental with cosmetic procedure | Partial approval |
| TC007 | MRI without pre-authorization | Reject (pre-auth required) |
| TC008 | Per-claim limit exceeded | Reject (limit exceeded) |
| TC009 | Multiple same-day claims | Manual review (fraud signal) |
| TC010 | Network hospital claim | Approve with discount + co-pay |
| TC011 | Component failure | Continue with degraded confidence |
| TC012 | Excluded treatment (obesity) | Reject (exclusion) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/claims` | Submit claim with document uploads |
| POST | `/api/claims/json` | Submit claim with embedded data |
| GET | `/api/claims/members` | List all members |
| GET | `/api/claims/policy` | Get policy information |
| POST | `/api/decisions/run-all-tests` | Run evaluation suite |
| GET | `/api/health` | Health check |

## Documentation

- [Architecture Document](ARCHITECTURE.md) - System design and decisions
- [Component Contracts](COMPONENT_CONTRACTS.md) - Interface specifications

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, FastAPI |
| LLM | OpenAI GPT-4o Vision |
| Database | MongoDB (optional) |
| Frontend | HTML, CSS, JavaScript |

## Trade-offs Made

1. **Monolithic over Microservices**: Simpler deployment, easier development
2. **In-memory over Persistent Storage**: Faster for demo, no DB dependency
3. **Rule-based over ML Fraud Detection**: Deterministic, explainable
4. **Single LLM Provider**: Simpler implementation, can add fallbacks later

## Evaluation Results

```
================================================================================
SUMMARY
================================================================================
Total: 12 | Passed: 12 | Failed: 0
Pass Rate: 100.0%
```

## License

This project is part of Plum's AI Engineer hiring assignment.
