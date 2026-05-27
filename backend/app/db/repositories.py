from typing import Optional, List, Dict, Any
from datetime import datetime
from .mongodb import get_database
from ..models.claim import Claim, ClaimStatus
from ..models.decision import ClaimDecision


class ClaimRepository:
    @staticmethod
    async def create(claim: Claim) -> str:
        db = get_database()
        claim_dict = claim.model_dump()
        claim_dict["created_at"] = datetime.utcnow()
        await db.claims.insert_one(claim_dict)
        return claim.claim_id
    
    @staticmethod
    async def get_by_id(claim_id: str) -> Optional[Dict[str, Any]]:
        db = get_database()
        return await db.claims.find_one({"claim_id": claim_id})
    
    @staticmethod
    async def update_status(claim_id: str, status: ClaimStatus) -> bool:
        db = get_database()
        result = await db.claims.update_one(
            {"claim_id": claim_id},
            {"$set": {"status": status.value, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def save_decision(claim_id: str, decision: ClaimDecision) -> bool:
        db = get_database()
        result = await db.claims.update_one(
            {"claim_id": claim_id},
            {
                "$set": {
                    "decision": decision.model_dump(),
                    "status": ClaimStatus.COMPLETED.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    async def list_claims(
        member_id: Optional[str] = None,
        status: Optional[ClaimStatus] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        db = get_database()
        query = {}
        if member_id:
            query["member_id"] = member_id
        if status:
            query["status"] = status.value
        
        cursor = db.claims.find(query).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    @staticmethod
    async def get_claims_for_member_on_date(member_id: str, date: str) -> List[Dict[str, Any]]:
        db = get_database()
        cursor = db.claims.find({
            "member_id": member_id,
            "treatment_date": date
        })
        return await cursor.to_list(length=100)
