from fastapi import APIRouter, HTTPException
from typing import List, Optional
import json
from pathlib import Path

from ...services.policy_service import PolicyService
from ...services.orchestrator import ClaimOrchestrator
from ...models.claim import Claim, ClaimCategory, PreviousClaim
from ...models.document import Document
from ...models.decision import ClaimDecision

router = APIRouter(prefix="/decisions", tags=["Decisions"])

orchestrator = ClaimOrchestrator()


@router.get("/test-cases")
async def get_test_cases():
    test_cases_path = Path(__file__).parent.parent.parent.parent / "test_cases.json"
    
    if not test_cases_path.exists():
        raise HTTPException(status_code=404, detail="Test cases file not found")
    
    with open(test_cases_path, "r") as f:
        return json.load(f)


@router.post("/run-test/{case_id}", response_model=ClaimDecision)
async def run_test_case(case_id: str):
    test_cases_path = Path(__file__).parent.parent.parent.parent / "test_cases.json"
    
    with open(test_cases_path, "r") as f:
        data = json.load(f)
    
    test_case = None
    for tc in data.get("test_cases", []):
        if tc["case_id"] == case_id:
            test_case = tc
            break
    
    if not test_case:
        raise HTTPException(status_code=404, detail=f"Test case {case_id} not found")
    
    input_data = test_case["input"]
    
    documents = []
    for doc_data in input_data.get("documents", []):
        documents.append(Document(
            file_id=doc_data.get("file_id", ""),
            file_name=doc_data.get("file_name", "unknown"),
            actual_type=doc_data.get("actual_type"),
            quality=doc_data.get("quality"),
            content=doc_data.get("content"),
            patient_name_on_doc=doc_data.get("patient_name_on_doc")
        ))
    
    history = []
    for h in input_data.get("claims_history", []):
        history.append(PreviousClaim(
            claim_id=h.get("claim_id", ""),
            date=h.get("date", ""),
            amount=h.get("amount", 0),
            provider=h.get("provider")
        ))
    
    claim = Claim(
        claim_id=f"TEST_{case_id}",
        member_id=input_data.get("member_id", ""),
        policy_id=input_data.get("policy_id", "PLUM_GHI_2024"),
        claim_category=ClaimCategory(input_data.get("claim_category", "CONSULTATION")),
        treatment_date=input_data.get("treatment_date", ""),
        claimed_amount=input_data.get("claimed_amount", 0),
        hospital_name=input_data.get("hospital_name"),
        ytd_claims_amount=input_data.get("ytd_claims_amount", 0.0),
        claims_history=history,
        documents=documents,
        simulate_component_failure=input_data.get("simulate_component_failure", False)
    )
    
    decision = await orchestrator.process_claim(claim)
    
    return decision


@router.post("/run-all-tests")
async def run_all_test_cases():
    test_cases_path = Path(__file__).parent.parent.parent.parent / "test_cases.json"
    
    with open(test_cases_path, "r") as f:
        data = json.load(f)
    
    results = []
    
    for test_case in data.get("test_cases", []):
        case_id = test_case["case_id"]
        input_data = test_case["input"]
        expected = test_case["expected"]
        
        documents = []
        for doc_data in input_data.get("documents", []):
            documents.append(Document(
                file_id=doc_data.get("file_id", ""),
                file_name=doc_data.get("file_name", "unknown"),
                actual_type=doc_data.get("actual_type"),
                quality=doc_data.get("quality"),
                content=doc_data.get("content"),
                patient_name_on_doc=doc_data.get("patient_name_on_doc")
            ))
        
        history = []
        for h in input_data.get("claims_history", []):
            history.append(PreviousClaim(
                claim_id=h.get("claim_id", ""),
                date=h.get("date", ""),
                amount=h.get("amount", 0),
                provider=h.get("provider")
            ))
        
        claim = Claim(
            claim_id=f"TEST_{case_id}",
            member_id=input_data.get("member_id", ""),
            policy_id=input_data.get("policy_id", "PLUM_GHI_2024"),
            claim_category=ClaimCategory(input_data.get("claim_category", "CONSULTATION")),
            treatment_date=input_data.get("treatment_date", ""),
            claimed_amount=input_data.get("claimed_amount", 0),
            hospital_name=input_data.get("hospital_name"),
            ytd_claims_amount=input_data.get("ytd_claims_amount", 0.0),
            claims_history=history,
            documents=documents,
            simulate_component_failure=input_data.get("simulate_component_failure", False)
        )
        
        try:
            decision = await orchestrator.process_claim(claim)
            
            passed = True
            notes = []
            
            expected_decision = expected.get("decision")
            if expected_decision and decision.decision.value != expected_decision:
                passed = False
                notes.append(f"Expected decision '{expected_decision}', got '{decision.decision.value}'")
            
            expected_amount = expected.get("approved_amount")
            if expected_amount is not None:
                if abs(decision.approved_amount - expected_amount) > 1:
                    passed = False
                    notes.append(f"Expected amount ₹{expected_amount}, got ₹{decision.approved_amount}")
            
            if expected.get("rejection_reasons"):
                found_reasons = {r.code for r in decision.reasons if r.category == "REJECTION"}
                expected_reasons = set(expected["rejection_reasons"])
                if not expected_reasons.issubset(found_reasons):
                    if decision.decision.value != expected_decision:
                        notes.append(f"Missing rejection reasons: {expected_reasons - found_reasons}")
            
            results.append({
                "case_id": case_id,
                "case_name": test_case["case_name"],
                "passed": passed,
                "expected_decision": expected_decision,
                "actual_decision": decision.decision.value,
                "expected_amount": expected_amount,
                "actual_amount": decision.approved_amount,
                "confidence_score": decision.confidence_score,
                "notes": notes,
                "decision": decision.model_dump()
            })
            
        except Exception as e:
            results.append({
                "case_id": case_id,
                "case_name": test_case["case_name"],
                "passed": False,
                "error": str(e)
            })
    
    passed_count = sum(1 for r in results if r.get("passed", False))
    
    return {
        "summary": {
            "total": len(results),
            "passed": passed_count,
            "failed": len(results) - passed_count
        },
        "results": results
    }
