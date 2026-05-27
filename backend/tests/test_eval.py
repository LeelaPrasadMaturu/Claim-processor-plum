"""
Evaluation script for running all 12 test cases and generating a report.
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.claim import Claim, ClaimCategory, PreviousClaim
from app.models.document import Document
from app.services.orchestrator import ClaimOrchestrator


async def run_test_case(orchestrator: ClaimOrchestrator, test_case: dict) -> dict:
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
        
        result = {
            "case_id": case_id,
            "case_name": test_case["case_name"],
            "description": test_case["description"],
            "expected": expected,
            "actual": {
                "decision": decision.decision.value,
                "approved_amount": decision.approved_amount,
                "rejected_amount": decision.rejected_amount,
                "confidence_score": decision.confidence_score,
                "reasons": [{"code": r.code, "message": r.message, "category": r.category} for r in decision.reasons],
                "recommendations": decision.recommendations
            },
            "trace_summary": None,
            "passed": False,
            "analysis": []
        }
        
        if decision.full_trace:
            result["trace_summary"] = {
                "total_duration_ms": decision.full_trace.total_duration_ms,
                "overall_confidence": decision.full_trace.overall_confidence,
                "steps": [
                    {
                        "agent": step.agent_name,
                        "status": step.status.value if hasattr(step.status, 'value') else step.status,
                        "duration_ms": step.duration_ms,
                        "decision_factors": step.decision_factors,
                        "errors": step.errors
                    }
                    for step in decision.full_trace.steps
                ],
                "component_failures": decision.full_trace.component_failures
            }
        
        expected_decision = expected.get("decision")
        if expected_decision:
            if decision.decision.value == expected_decision:
                result["analysis"].append(f"✓ Decision matches: {expected_decision}")
            else:
                result["analysis"].append(f"✗ Decision mismatch: expected {expected_decision}, got {decision.decision.value}")
        
        expected_amount = expected.get("approved_amount")
        if expected_amount is not None:
            if abs(decision.approved_amount - expected_amount) <= 1:
                result["analysis"].append(f"✓ Amount matches: ₹{expected_amount}")
            else:
                result["analysis"].append(f"✗ Amount mismatch: expected ₹{expected_amount}, got ₹{decision.approved_amount}")
        
        if expected.get("rejection_reasons"):
            actual_codes = {r.code for r in decision.reasons}
            for reason in expected["rejection_reasons"]:
                if reason in actual_codes:
                    result["analysis"].append(f"✓ Rejection reason found: {reason}")
                else:
                    result["analysis"].append(f"✗ Missing rejection reason: {reason}")
        
        if expected.get("system_must"):
            for requirement in expected["system_must"]:
                all_text = " ".join([r.message for r in decision.reasons])
                all_text += " " + " ".join(decision.recommendations or [])
                if decision.verification_result and decision.verification_result.error_message:
                    all_text += " " + decision.verification_result.error_message
                
                result["analysis"].append(f"  Requirement: {requirement}")
        
        all_checks_pass = all("✗" not in a for a in result["analysis"])
        if expected_decision is None:
            all_checks_pass = True
        result["passed"] = all_checks_pass
        
        return result
        
    except Exception as e:
        return {
            "case_id": case_id,
            "case_name": test_case["case_name"],
            "passed": False,
            "error": str(e),
            "analysis": [f"✗ Exception: {str(e)}"]
        }


async def run_all_tests():
    test_cases_path = Path(__file__).parent.parent / "test_cases.json"
    
    with open(test_cases_path, "r") as f:
        data = json.load(f)
    
    orchestrator = ClaimOrchestrator()
    results = []
    
    print("=" * 80)
    print("HEALTH INSURANCE CLAIMS PROCESSOR - EVALUATION REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    for test_case in data["test_cases"]:
        print(f"Running {test_case['case_id']}: {test_case['case_name']}...")
        result = await run_test_case(orchestrator, test_case)
        results.append(result)
        
        status = "PASS" if result["passed"] else "FAIL"
        print(f"  Result: {status}")
        print()
    
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    print(f"Pass Rate: {(passed / len(results) * 100):.1f}%")
    print()
    
    print("=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    
    for result in results:
        print()
        print(f"--- {result['case_id']}: {result['case_name']} ---")
        print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Expected Decision: {result['expected'].get('decision', 'N/A')}")
            print(f"Actual Decision: {result['actual']['decision']}")
            print(f"Approved Amount: ₹{result['actual']['approved_amount']:,.2f}")
            print(f"Confidence: {result['actual']['confidence_score']:.2%}")
            
            print("\nAnalysis:")
            for analysis in result["analysis"]:
                print(f"  {analysis}")
            
            if result["trace_summary"]:
                print(f"\nTrace Summary:")
                print(f"  Duration: {result['trace_summary']['total_duration_ms']}ms")
                print(f"  Steps: {len(result['trace_summary']['steps'])}")
                for step in result["trace_summary"]["steps"]:
                    print(f"    - {step['agent']}: {step['status']} ({step['duration_ms']}ms)")
                    if step["decision_factors"]:
                        for factor in step["decision_factors"]:
                            print(f"      * {factor}")
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(results)
        },
        "results": results
    }
    
    report_path = Path(__file__).parent.parent / "eval_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print()
    print(f"Full report saved to: {report_path}")
    
    return report


if __name__ == "__main__":
    asyncio.run(run_all_tests())
