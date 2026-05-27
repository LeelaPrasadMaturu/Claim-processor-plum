# Health Insurance Claims Processing System

A multi-agent AI system for automating health insurance claims processing with full explainability and traceability.

## Table of Contents

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)

---

## Overview

This system processes health insurance claims through a multi-agent pipeline:

1. **Document Verification Agent** - Validates uploaded documents using GPT-4 Vision
2. **Document Extraction Agent** - Extracts structured data from medical documents
3. **Policy Validation Agent** - Checks claims against policy rules (limits, exclusions, waiting periods)
4. **Fraud Detection Agent** - Identifies suspicious patterns for manual review
5. **Decision Engine Agent** - Synthesizes all outputs into a final decision with full trace

---

## System Requirements

### Required

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.9 or higher | Backend runtime |
| pip | Latest | Package management |

### Optional (Recommended)

| Component | Version | Purpose |
|-----------|---------|---------|
| MongoDB | 4.4+ | Persistent storage |
| OpenAI API Key | - | GPT-4 Vision for document processing |

### Verify Installation

```bash
# Check Python version
python3 --version
# Expected: Python 3.9.x or higher

# Check pip
pip3 --version
```

---

## Installation

### Step 1: Clone/Navigate to Project

```bash
cd "Plum Assignment - 12-04-2026/claims-processor"
```

### Step 2: Create Python Virtual Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Verify activation (should show venv path)
which python
```

### Step 3: Install Dependencies

```bash
# Ensure you're in the backend directory with venv activated
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencies installed:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `openai` - GPT-4 Vision API
- `motor` - Async MongoDB driver
- `pydantic` - Data validation
- `pydantic-settings` - Configuration management
- `python-multipart` - File upload handling
- `aiofiles` - Async file operations
- `Pillow` - Image processing

### Step 4: Create Environment Configuration

```bash
# From the backend directory
cp ../.env.example .env
```

Edit the `.env` file:

```bash
# Open with your preferred editor
nano .env
# or
code .env
```

---

## Configuration

### Environment Variables

Create/edit `.env` file in the `backend` directory:

```env
# OpenAI Configuration (Required for real document processing)
OPENAI_API_KEY=sk-your-openai-api-key-here

# MongoDB Configuration (Optional - system works without it)
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=claims_processor

# File Upload Directory
UPLOAD_DIR=./uploads

# Logging Level
LOG_LEVEL=INFO
```

### Configuration Options

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | No* | None | Your OpenAI API key for GPT-4 Vision |
| `MONGODB_URI` | No | mongodb://localhost:27017 | MongoDB connection string |
| `DATABASE_NAME` | No | claims_processor | Database name |
| `UPLOAD_DIR` | No | ./uploads | Directory for uploaded files |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

*Without OpenAI API key, the system runs in degraded mode with mock LLM responses.

### MongoDB Setup (Optional)

**Option 1: Local MongoDB**

```bash
# macOS (using Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Verify MongoDB is running
mongosh --eval "db.runCommand({ping:1})"
```

**Option 2: Docker MongoDB**

```bash
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

**Option 3: MongoDB Atlas (Cloud)**

1. Create free cluster at https://www.mongodb.com/atlas
2. Get connection string
3. Update `MONGODB_URI` in `.env`

```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net
```

### OpenAI API Key Setup

1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Add to `.env` file:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
```

**Note:** GPT-4 Vision API requires a paid OpenAI account with access to gpt-4o model.

---

## Running the Application

### Development Mode

```bash
# Navigate to backend directory
cd claims-processor/backend

# Activate virtual environment
source venv/bin/activate

# Start server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Will watch for changes in these directories: ['.../backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx]
INFO:     Started server process [xxxxx]
INFO:     Application startup complete.
```

### Access the Application

Open your browser and navigate to:

| URL | Description |
|-----|-------------|
| http://localhost:8000 | Main Application UI |
| http://localhost:8000/docs | Swagger API Documentation |
| http://localhost:8000/redoc | ReDoc API Documentation |

### Login Credentials

> **Note (time constraint):** Due to the assignment timeline, authentication is implemented as a **frontend-only demo** with hardcoded users—there is no backend auth service, JWT, or database-backed user store. This keeps setup simple for reviewers while still demonstrating a login/signup flow. For production, this would be replaced with proper server-side authentication.

The UI requires sign-in before accessing the app. Use any of these **pre-configured accounts**:

| Email | Password | Role |
|-------|----------|------|
| `admin@plumhq.com` | `admin123` | Administrator |
| `agent@plumhq.com` | `agent123` | Agent |
| `demo@plumhq.com` | `demo123` | Viewer |

**Sign up (optional):** You can also create a new account from the Sign up page:

| Field | Value |
|-------|-------|
| Invite code | `PLUM2024` |
| Password | Minimum 6 characters |

New sign-ups are saved in the browser’s `localStorage` only (not on the server) and can log in on the same machine afterward.

**Logout:** Use the **Logout** button in the top-right navbar to return to the login screen.

### Production Mode

```bash
# Without auto-reload, with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Testing

### Run All Test Cases

**From the UI:**
1. Open http://localhost:8000
2. Click "Run Tests" in navigation
3. Click "Run All Tests" button
4. Watch the multi-agent pipeline process each test case

**From Command Line:**

```bash
cd claims-processor/backend
source venv/bin/activate
python -m tests.test_eval
```

**Expected Output:**

```
================================================================================
CLAIMS PROCESSOR - TEST EVALUATION
================================================================================

Running 12 test cases...

[TC001] Wrong Document Type ............................ PASSED
[TC002] Unreadable Document ............................ PASSED
[TC003] Patient Name Mismatch .......................... PASSED
[TC004] Clean Consultation Claim ....................... PASSED
[TC005] Waiting Period Violation ....................... PASSED
[TC006] Dental Partial Approval ........................ PASSED
[TC007] Pre-Authorization Required ..................... PASSED
[TC008] Per-Claim Limit Exceeded ....................... PASSED
[TC009] Multiple Same-Day Claims ....................... PASSED
[TC010] Network Hospital Discount ...................... PASSED
[TC011] Component Failure Graceful Degradation ......... PASSED
[TC012] Excluded Treatment ............................. PASSED

================================================================================
SUMMARY
================================================================================
Total: 12 | Passed: 12 | Failed: 0
Pass Rate: 100.0%
```

### Test Cases Overview

| Case | Scenario | Expected Outcome |
|------|----------|------------------|
| TC001 | Wrong document uploaded | REJECTED - Document type mismatch |
| TC002 | Unreadable document | REJECTED - Document quality issue |
| TC003 | Documents for different patients | REJECTED - Patient name mismatch |
| TC004 | Clean consultation claim (₹1,500) | APPROVED - ₹1,350 (10% co-pay) |
| TC005 | Diabetes during waiting period | REJECTED - Waiting period violation |
| TC006 | Dental with cosmetic procedure | PARTIAL - ₹8,000 (cosmetic excluded) |
| TC007 | MRI without pre-authorization | REJECTED - Pre-auth required |
| TC008 | Per-claim limit exceeded | REJECTED - Limit exceeded |
| TC009 | Multiple same-day claims | MANUAL_REVIEW - Fraud signal |
| TC010 | Network hospital claim | APPROVED - ₹3,240 (20% discount + 10% co-pay) |
| TC011 | Component failure | APPROVED - Degraded confidence |
| TC012 | Excluded treatment (obesity) | REJECTED - Treatment exclusion |

---

## Project Structure

```
claims-processor/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── config.py               # Settings and configuration
│   │   │
│   │   ├── agents/                 # Multi-agent implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base agent class
│   │   │   ├── document_verifier.py
│   │   │   ├── document_extractor.py
│   │   │   ├── policy_validator.py
│   │   │   ├── fraud_detector.py
│   │   │   └── decision_engine.py
│   │   │
│   │   ├── models/                 # Pydantic data models
│   │   │   ├── __init__.py
│   │   │   ├── claim.py
│   │   │   ├── document.py
│   │   │   ├── decision.py
│   │   │   └── trace.py
│   │   │
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── llm_service.py      # OpenAI GPT-4 Vision
│   │   │   ├── policy_service.py   # Policy rules engine
│   │   │   ├── trace_service.py    # Observability
│   │   │   └── orchestrator.py     # Agent coordination
│   │   │
│   │   ├── api/                    # API routes
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── claims.py
│   │   │       └── decisions.py
│   │   │
│   │   └── db/                     # Database layer
│   │       ├── __init__.py
│   │       ├── mongodb.py
│   │       └── repositories.py
│   │
│   ├── tests/
│   │   └── test_eval.py            # Evaluation script
│   │
│   ├── policy_terms.json           # Policy configuration
│   ├── test_cases.json             # 12 test scenarios
│   ├── requirements.txt            # Python dependencies
│   └── venv/                       # Virtual environment
│
├── frontend/
│   ├── index.html                  # Main HTML
│   ├── css/
│   │   └── styles.css              # Styling
│   └── js/
│       └── app.js                  # Frontend logic
│
├── .env.example                    # Environment template
├── ARCHITECTURE.md                 # System design document
├── COMPONENT_CONTRACTS.md          # Interface specifications
└── README.md                       # This file
```

---

## API Reference

### Claims API

**Submit Claim with Documents**

```bash
POST /api/claims
Content-Type: multipart/form-data

# Form fields:
# - member_id: string
# - claim_category: CONSULTATION|DIAGNOSTIC|PHARMACY|DENTAL|VISION|ALTERNATIVE_MEDICINE
# - treatment_date: YYYY-MM-DD
# - claimed_amount: number
# - hospital_name: string (optional)
# - ytd_claims_amount: number (optional)
# - documents: file[] (multiple files)
```

**Example using cURL:**

```bash
curl -X POST http://localhost:8000/api/claims \
  -F "member_id=MEM001" \
  -F "claim_category=CONSULTATION" \
  -F "treatment_date=2024-03-15" \
  -F "claimed_amount=1500" \
  -F "hospital_name=Apollo Hospitals" \
  -F "documents=@prescription.jpg" \
  -F "documents=@bill.pdf"
```

**Get Policy Information**

```bash
GET /api/claims/policy
```

**Get Members List**

```bash
GET /api/claims/members
```

### Decisions API

**Run All Test Cases**

```bash
POST /api/decisions/run-all-tests
```

**Response:**

```json
{
  "summary": {
    "total": 12,
    "passed": 12,
    "failed": 0
  },
  "results": [
    {
      "case_id": "TC001",
      "case_name": "Wrong Document Type",
      "passed": true,
      "expected_decision": "REJECTED",
      "actual_decision": "REJECTED",
      "decision": { ... }
    }
  ]
}
```

---

## Architecture

### Multi-Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                            │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Document    │───>│  Document    │───>│   Policy     │      │
│  │  Verifier    │    │  Extractor   │    │  Validator   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         v                   v                   v               │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                    Shared State                       │      │
│  └──────────────────────────────────────────────────────┘      │
│         │                   │                   │               │
│         v                   v                   v               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │    Fraud     │───>│   Decision   │───>│    Final     │      │
│  │   Detector   │    │   Engine     │    │   Decision   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Graceful Degradation**: System continues processing when components fail
2. **Full Traceability**: Every decision includes complete audit trail
3. **Dynamic Policy Rules**: All rules loaded from `policy_terms.json`
4. **No Hardcoding**: Coverage limits, exclusions, waiting periods are configurable

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Troubleshooting

### Common Issues

**Port already in use**

```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

**Module not found: 'app'**

```bash
# Make sure you're in the backend directory
cd claims-processor/backend

# Verify virtual environment is activated
which python
# Should show: .../backend/venv/bin/python
```

**OpenAI API Error**

```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check .env file exists and has key
cat .env | grep OPENAI
```

**MongoDB Connection Failed**

```bash
# Check if MongoDB is running
mongosh --eval "db.runCommand({ping:1})"

# Or run without MongoDB (uses in-memory storage)
# Just remove MONGODB_URI from .env
```

**Permission Denied on uploads**

```bash
# Create uploads directory with proper permissions
mkdir -p uploads
chmod 755 uploads
```

### Logs

Check application logs for debugging:

```bash
# Set debug logging
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload --port 8000
```

---

## License

This project is part of Plum's AI Engineer hiring assignment.
