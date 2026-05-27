from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
import uuid
import json
import os
import aiofiles
from datetime import datetime

from ...models.claim import Claim, ClaimSubmission, ClaimStatus, ClaimCategory, PreviousClaim
from ...models.document import Document
from ...models.decision import ClaimDecision
from ...services.orchestrator import ClaimOrchestrator
from ...services.policy_service import PolicyService
from ...config import get_settings

router = APIRouter(prefix="/claims", tags=["Claims"])

orchestrator = ClaimOrchestrator()
policy_service = PolicyService()


@router.post("", response_model=ClaimDecision)
async def submit_claim(
    member_id: str = Form(...),
    policy_id: str = Form(default="PLUM_GHI_2024"),
    claim_category: str = Form(...),
    treatment_date: str = Form(...),
    claimed_amount: float = Form(...),
    hospital_name: Optional[str] = Form(default=None),
    ytd_claims_amount: float = Form(default=0.0),
    claims_history: Optional[str] = Form(default=None),
    simulate_component_failure: bool = Form(default=False),
    documents: List[UploadFile] = File(...)
):
    settings = get_settings()
    claim_id = f"CLM_{uuid.uuid4().hex[:8].upper()}"
    
    saved_documents: List[Document] = []
    
    for doc in documents:
        file_id = f"F_{uuid.uuid4().hex[:6].upper()}"
        file_ext = doc.filename.split(".")[-1] if "." in doc.filename else "jpg"
        file_path = os.path.join(settings.upload_dir, f"{file_id}.{file_ext}")
        
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        async with aiofiles.open(file_path, "wb") as f:
            content = await doc.read()
            await f.write(content)
        
        saved_documents.append(Document(
            file_id=file_id,
            file_name=doc.filename,
            file_path=file_path,
            mime_type=doc.content_type
        ))
    
    history = []
    if claims_history:
        try:
            history_data = json.loads(claims_history)
            history = [PreviousClaim(**h) for h in history_data]
        except:
            pass
    
    claim = Claim(
        claim_id=claim_id,
        member_id=member_id,
        policy_id=policy_id,
        claim_category=ClaimCategory(claim_category),
        treatment_date=treatment_date,
        claimed_amount=claimed_amount,
        hospital_name=hospital_name,
        ytd_claims_amount=ytd_claims_amount,
        claims_history=history,
        documents=saved_documents,
        simulate_component_failure=simulate_component_failure
    )
    
    decision = await orchestrator.process_claim(claim)
    
    return decision


@router.post("/json", response_model=ClaimDecision)
async def submit_claim_json(submission: dict):
    claim_id = f"CLM_{uuid.uuid4().hex[:8].upper()}"
    
    documents = []
    for doc_data in submission.get("documents", []):
        documents.append(Document(
            file_id=doc_data.get("file_id", f"F_{uuid.uuid4().hex[:6].upper()}"),
            file_name=doc_data.get("file_name", "unknown"),
            actual_type=doc_data.get("actual_type"),
            quality=doc_data.get("quality"),
            content=doc_data.get("content"),
            patient_name_on_doc=doc_data.get("patient_name_on_doc")
        ))
    
    history = []
    for h in submission.get("claims_history", []):
        history.append(PreviousClaim(
            claim_id=h.get("claim_id", ""),
            date=h.get("date", ""),
            amount=h.get("amount", 0),
            provider=h.get("provider")
        ))
    
    claim = Claim(
        claim_id=claim_id,
        member_id=submission.get("member_id", ""),
        policy_id=submission.get("policy_id", "PLUM_GHI_2024"),
        claim_category=ClaimCategory(submission.get("claim_category", "CONSULTATION")),
        treatment_date=submission.get("treatment_date", ""),
        claimed_amount=submission.get("claimed_amount", 0),
        hospital_name=submission.get("hospital_name"),
        ytd_claims_amount=submission.get("ytd_claims_amount", 0.0),
        claims_history=history,
        documents=documents,
        simulate_component_failure=submission.get("simulate_component_failure", False)
    )
    
    decision = await orchestrator.process_claim(claim)
    
    return decision


@router.get("/members/{member_id}")
async def get_member(member_id: str):
    member = policy_service.get_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail=f"Member {member_id} not found")
    return member


@router.get("/members")
async def list_members():
    return policy_service.policy_data.get("members", [])


@router.get("/policy")
async def get_policy():
    return {
        "policy_id": policy_service.policy_data.get("policy_id"),
        "policy_name": policy_service.policy_data.get("policy_name"),
        "coverage": policy_service.policy_data.get("coverage"),
        "opd_categories": policy_service.policy_data.get("opd_categories"),
        "document_requirements": policy_service.policy_data.get("document_requirements"),
        "network_hospitals": policy_service.policy_data.get("network_hospitals")
    }
