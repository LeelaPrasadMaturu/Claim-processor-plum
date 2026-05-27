# Component Contracts

This document defines the interface contracts for each significant component in the Health Insurance Claims Processing System. These contracts are precise enough that another engineer could reimplement any component without reading its code.

---

## 1. Document Verification Agent

### Purpose
Validates that correct document types are uploaded for the claim category and assesses document readability.

### Input

```python
class VerificationInput:
    claim_category: str     # "CONSULTATION", "PHARMACY", "DIAGNOSTIC", "DENTAL", "VISION", "ALTERNATIVE_MEDICINE"
    documents: List[Document]

class Document:
    file_id: str            # Unique identifier
    file_name: str          # Original filename
    file_path: str | None   # Path to file (for actual processing)
    mime_type: str | None   # MIME type
    actual_type: str | None # Pre-classified type (for testing)
    quality: str | None     # Pre-assessed quality (for testing)
    content: dict | None    # Embedded content (for testing)
```

### Output

```python
class VerificationResult:
    status: "VALID" | "INVALID" | "UNREADABLE"
    documents_classified: List[ClassifiedDocument]
    missing_documents: List[str]        # Required doc types not found
    wrong_documents: List[WrongDocument]
    error_message: str | None           # User-facing specific error
    confidence: float                   # 0.0 - 1.0
    trace: VerificationTrace

class ClassifiedDocument:
    file_id: str
    file_name: str
    file_path: str | None
    detected_type: DocumentType         # PRESCRIPTION, HOSPITAL_BILL, etc.
    readability: DocumentQuality        # GOOD, PARTIAL, UNREADABLE
    confidence: float                   # 0.0 - 1.0

class WrongDocument:
    file_id: str
    file_name: str
    uploaded_type: DocumentType
    required_type: DocumentType
```

### Errors

| Error | Condition | Recovery |
|-------|-----------|----------|
| DocumentUnreadableError | Document cannot be read/parsed | Return UNREADABLE status |
| DocumentClassificationError | LLM cannot classify document | Mark as UNKNOWN type |
| LLMTimeoutError | OpenAI API timeout | Fall back to metadata |

### Document Requirements by Category

| Category | Required | Optional |
|----------|----------|----------|
| CONSULTATION | PRESCRIPTION, HOSPITAL_BILL | LAB_REPORT, DIAGNOSTIC_REPORT |
| DIAGNOSTIC | PRESCRIPTION, LAB_REPORT, HOSPITAL_BILL | DISCHARGE_SUMMARY |
| PHARMACY | PRESCRIPTION, PHARMACY_BILL | - |
| DENTAL | HOSPITAL_BILL | PRESCRIPTION, DENTAL_REPORT |
| VISION | PRESCRIPTION, HOSPITAL_BILL | - |
| ALTERNATIVE_MEDICINE | PRESCRIPTION, HOSPITAL_BILL | - |

---

## 2. Document Extraction Agent

### Purpose
Extracts structured information from verified documents using LLM vision capabilities.

### Input

```python
class ExtractionInput:
    documents: List[ClassifiedDocument]     # From verification agent
    document_contents: dict | None          # Pre-extracted content (for testing)
```

### Output

```python
class ExtractionResult:
    prescription_data: PrescriptionData | None
    bill_data: BillData | None
    lab_report_data: LabReportData | None
    patient_names_found: List[str]          # All patient names across docs
    confidence_scores: dict[str, float]     # Per-document confidence
    extraction_warnings: List[str]          # Partial extraction warnings
    trace: ExtractionTrace

class PrescriptionData:
    doctor_name: str | None
    doctor_registration: str | None         # Format: XX/XXXXX/YYYY
    specialization: str | None
    patient_name: str | None
    patient_age: int | None
    patient_gender: "M" | "F" | None
    date: str | None                        # YYYY-MM-DD
    diagnosis: str | None
    secondary_diagnosis: str | None
    medicines: List[str]
    tests_ordered: List[str]
    hospital_name: str | None
    treatment: str | None

class BillData:
    hospital_name: str | None
    bill_number: str | None
    date: str | None
    patient_name: str | None
    patient_age: int | None
    patient_gender: str | None
    referring_doctor: str | None
    line_items: List[LineItem]
    subtotal: float | None
    gst_amount: float | None
    total: float
    payment_mode: str | None
    gstin: str | None

class LineItem:
    description: str
    amount: float
    quantity: int = 1

class LabReportData:
    lab_name: str | None
    nabl_status: bool | None
    patient_name: str | None
    patient_age: int | None
    patient_gender: str | None
    referring_doctor: str | None
    sample_date: str | None
    report_date: str | None
    test_name: str | None
    test_results: List[dict]                # {test, result, unit, normal_range}
    remarks: str | None
    pathologist_name: str | None
    pathologist_registration: str | None
```

### Errors

| Error | Condition | Recovery |
|-------|-----------|----------|
| ExtractionFailedError | Cannot extract any data | Return empty result |
| PartialExtractionWarning | Some fields unreadable | Return partial with warning |

---

## 3. Policy Validation Agent

### Purpose
Validates claim against policy rules including waiting periods, exclusions, limits, and pre-authorization requirements.

### Input

```python
class PolicyValidationInput:
    member_id: str
    claim_category: str
    treatment_date: str                     # YYYY-MM-DD
    claimed_amount: float
    extracted_data: ExtractionResult
    ytd_claims_amount: float = 0.0          # Year-to-date claims
    hospital_name: str | None
```

### Output

```python
class PolicyValidationResult:
    is_eligible: bool
    violations: List[PolicyViolation]
    adjustments: List[Adjustment]
    eligible_amount: float
    trace: PolicyTrace

class PolicyViolation:
    code: ViolationCode
    message: str                            # User-readable message
    details: dict | None                    # Additional context

class ViolationCode(Enum):
    WAITING_PERIOD = "WAITING_PERIOD"
    EXCLUSION = "EXCLUSION"
    EXCLUDED_CONDITION = "EXCLUDED_CONDITION"
    PRE_AUTH_MISSING = "PRE_AUTH_MISSING"
    PER_CLAIM_EXCEEDED = "PER_CLAIM_EXCEEDED"
    ANNUAL_LIMIT_EXCEEDED = "ANNUAL_LIMIT_EXCEEDED"
    SUB_LIMIT_EXCEEDED = "SUB_LIMIT_EXCEEDED"

class Adjustment:
    type: AdjustmentType
    description: str
    amount: float                           # Amount deducted
    original_amount: float | None

class AdjustmentType(Enum):
    NETWORK_DISCOUNT = "NETWORK_DISCOUNT"
    COPAY = "COPAY"
    SUB_LIMIT = "SUB_LIMIT"
    LINE_ITEM_EXCLUSION = "LINE_ITEM_EXCLUSION"
```

### Validation Rules

| Rule | Check | Hard Reject |
|------|-------|-------------|
| Waiting Period | `days_since_join < waiting_days` | Yes |
| Exclusion | Diagnosis/procedure in exclusion list | Sometimes* |
| Pre-Authorization | High-value procedure without auth | Yes |
| Per-Claim Limit | Amount > ₹5,000 (excl. dental/vision) | Yes |
| Sub-Limit | Amount > category sub-limit | No (cap amount) |
| Annual Limit | YTD + Amount > ₹50,000 | No (cap amount) |

*Line-item exclusions in dental allow partial approval

### Adjustment Order

1. **Network Discount** (20% if network hospital) → Applied first
2. **Co-pay** (varies by category) → Applied on discounted amount

Example:
```
Claimed: ₹4,500
Network Discount (20%): -₹900 → ₹3,600
Co-pay (10%): -₹360 → ₹3,240 final
```

---

## 4. Fraud Detection Agent

### Purpose
Identifies suspicious patterns that require manual review.

### Input

```python
class FraudDetectionInput:
    member_id: str
    claim_date: str                         # YYYY-MM-DD
    claimed_amount: float
    claims_history: List[PreviousClaim]
    extracted_data: ExtractionResult

class PreviousClaim:
    claim_id: str
    date: str
    amount: float
    provider: str | None
```

### Output

```python
class FraudDetectionResult:
    fraud_score: float                      # 0.0 - 1.0
    flags: List[FraudFlag]
    requires_manual_review: bool
    trace: FraudTrace

class FraudFlag:
    type: FraudFlagType
    description: str
    severity: "LOW" | "MEDIUM" | "HIGH"
    details: dict | None

class FraudFlagType(Enum):
    SAME_DAY_CLAIMS = "SAME_DAY_CLAIMS"
    HIGH_VALUE = "HIGH_VALUE"
    MONTHLY_LIMIT_EXCEEDED = "MONTHLY_LIMIT_EXCEEDED"
    DOCUMENT_ALTERATION = "DOCUMENT_ALTERATION"
    SUSPICIOUS_PATTERN = "SUSPICIOUS_PATTERN"
```

### Fraud Signals

| Signal | Threshold | Score Contribution | Severity |
|--------|-----------|-------------------|----------|
| Same-day claims | > 2 | +0.4 | HIGH |
| High value | > ₹25,000 | +0.2 | MEDIUM |
| Monthly claims | > 6 | +0.25 | MEDIUM |
| Name mismatch | Any | +0.3 | HIGH |
| Multiple providers | > 3 same day | +0.15 | MEDIUM |

### Manual Review Trigger
`requires_manual_review = true` when:
- `fraud_score >= 0.80` OR
- `claimed_amount > ₹25,000` OR
- Any flag has `severity == "HIGH"`

---

## 5. Decision Engine Agent

### Purpose
Combines all agent results to produce final decision with explanation.

### Input

```python
class DecisionInput:
    claim_id: str
    claimed_amount: float
    verification_result: VerificationResult | None
    extraction_result: ExtractionResult | None
    policy_result: PolicyValidationResult | None
    fraud_result: FraudDetectionResult | None
    component_failures: List[ComponentFailure]

class ComponentFailure:
    component_name: str
    error_type: str
    error_message: str
    recoverable: bool = True
```

### Output

```python
class ClaimDecision:
    claim_id: str
    decision: DecisionType                  # APPROVED, PARTIAL, REJECTED, MANUAL_REVIEW
    approved_amount: float
    rejected_amount: float
    confidence_score: float                 # 0.0 - 1.0
    reasons: List[DecisionReason]
    line_item_breakdown: List[LineItemDecision] | None
    recommendations: List[str] | None
    full_trace: ClaimTrace | None
    
    # Embedded results for transparency
    verification_result: VerificationResult | None
    extraction_result: ExtractionResult | None
    policy_result: PolicyValidationResult | None
    fraud_result: FraudDetectionResult | None

class DecisionType(Enum):
    APPROVED = "APPROVED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"

class DecisionReason:
    code: str
    message: str
    category: "APPROVAL" | "REJECTION" | "ADJUSTMENT" | "WARNING"

class LineItemDecision:
    description: str
    claimed_amount: float
    approved_amount: float
    status: "APPROVED" | "REJECTED" | "PARTIAL"
    reason: str | None
```

### Decision Logic

```
START
  │
  ▼
Verification INVALID? ──Yes──► REJECTED (doc error)
  │ No
  ▼
Verification UNREADABLE? ──Yes──► REJECTED (unreadable)
  │ No
  ▼
Patient name mismatch? ──Yes──► REJECTED (name mismatch)
  │ No
  ▼
Fraud requires review? ──Yes──► MANUAL_REVIEW
  │ No
  ▼
Hard policy violation? ──Yes──► REJECTED (policy)
  │ No
  ▼
Any line items excluded? ──Yes──► PARTIAL
  │ No
  ▼
APPROVED
```

### Confidence Score Calculation

```python
confidence = mean([
    verification_result.confidence,
    mean(extraction_result.confidence_scores.values()),
    policy_result.trace.confidence_contribution,
    1.0 - fraud_result.fraud_score
])

if component_failures:
    confidence *= 0.7
```

---

## 6. Claim Orchestrator

### Purpose
Coordinates the execution of all agents in sequence with graceful degradation.

### Input

```python
class Claim:
    claim_id: str
    member_id: str
    policy_id: str = "PLUM_GHI_2024"
    claim_category: ClaimCategory
    treatment_date: str
    claimed_amount: float
    hospital_name: str | None
    ytd_claims_amount: float = 0.0
    claims_history: List[PreviousClaim]
    documents: List[Document]
    simulate_component_failure: bool = False    # For testing
```

### Output

```python
ClaimDecision  # As defined above
```

### Pipeline Flow

```
Claim
  │
  ▼
┌─────────────────────┐
│ DocumentVerification│
│ Agent               │
└─────────────────────┘
  │
  │ INVALID/UNREADABLE? ──► Early return
  │
  ▼
┌─────────────────────┐
│ DocumentExtraction  │
│ Agent               │
└─────────────────────┘
  │
  │ Name mismatch? ──► Early return
  │
  ▼
┌─────────────────────┐
│ PolicyValidation    │
│ Agent               │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ FraudDetection      │
│ Agent               │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ DecisionEngine      │
│ Agent               │
└─────────────────────┘
  │
  ▼
ClaimDecision
```

### Error Handling

Each agent call is wrapped in try/catch:
- On success: Continue pipeline
- On degraded: Record failure, continue with partial result
- On failure: Record failure, continue with fallback/skip

---

## API Contracts

### POST /api/claims

Submit claim with file uploads.

**Request**: `multipart/form-data`
```
member_id: string (required)
policy_id: string (default: "PLUM_GHI_2024")
claim_category: string (required)
treatment_date: string (required, YYYY-MM-DD)
claimed_amount: number (required)
hospital_name: string (optional)
ytd_claims_amount: number (default: 0)
claims_history: string (JSON array, optional)
simulate_component_failure: boolean (default: false)
documents: File[] (required)
```

**Response**: `ClaimDecision` (JSON)

### POST /api/claims/json

Submit claim with embedded document data (for testing).

**Request**: JSON
```json
{
  "member_id": "EMP001",
  "claim_category": "CONSULTATION",
  "treatment_date": "2024-11-01",
  "claimed_amount": 1500,
  "documents": [
    {
      "file_id": "F001",
      "actual_type": "PRESCRIPTION",
      "content": { ... }
    }
  ]
}
```

**Response**: `ClaimDecision` (JSON)

### POST /api/decisions/run-all-tests

Run all 12 test cases.

**Response**:
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
      "passed": true,
      "expected_decision": "REJECTED",
      "actual_decision": "REJECTED",
      ...
    }
  ]
}
```
