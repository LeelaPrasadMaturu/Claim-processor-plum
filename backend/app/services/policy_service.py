import json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
from pathlib import Path

from ..config import get_settings
from ..models.claim import Member, ClaimCategory
from ..models.decision import (
    PolicyViolation, ViolationCode, Adjustment, AdjustmentType
)


class PolicyService:
    def __init__(self):
        self.policy_data = self._load_policy()
    
    def _load_policy(self) -> Dict[str, Any]:
        settings = get_settings()
        policy_path = Path(settings.policy_terms_path)
        
        if not policy_path.exists():
            policy_path = Path(__file__).parent.parent.parent / "policy_terms.json"
        
        with open(policy_path, "r") as f:
            return json.load(f)
    
    def get_member(self, member_id: str) -> Optional[Member]:
        for member_data in self.policy_data.get("members", []):
            if member_data["member_id"] == member_id:
                return Member(**member_data)
        return None
    
    def get_document_requirements(self, category: str) -> Dict[str, List[str]]:
        return self.policy_data.get("document_requirements", {}).get(category, {
            "required": [],
            "optional": []
        })
    
    def check_waiting_period(
        self,
        member: Member,
        diagnosis: str,
        treatment_date: str
    ) -> Optional[PolicyViolation]:
        join_date = datetime.strptime(member.join_date, "%Y-%m-%d").date()
        treat_date = datetime.strptime(treatment_date, "%Y-%m-%d").date()
        days_since_join = (treat_date - join_date).days
        
        waiting_periods = self.policy_data.get("waiting_periods", {})
        initial_waiting = waiting_periods.get("initial_waiting_period_days", 30)
        
        if days_since_join < initial_waiting:
            return PolicyViolation(
                code=ViolationCode.WAITING_PERIOD,
                message=f"Initial waiting period of {initial_waiting} days not completed. "
                        f"Member joined on {member.join_date}. Eligible from "
                        f"{(join_date + __import__('datetime').timedelta(days=initial_waiting)).strftime('%Y-%m-%d')}.",
                details={"waiting_days": initial_waiting, "days_completed": days_since_join}
            )
        
        specific_conditions = waiting_periods.get("specific_conditions", {})
        diagnosis_lower = diagnosis.lower() if diagnosis else ""
        
        condition_mapping = {
            "diabetes": ["diabetes", "t2dm", "type 2 diabetes", "diabetic"],
            "hypertension": ["hypertension", "htn", "high blood pressure"],
            "thyroid_disorders": ["thyroid", "hypothyroid", "hyperthyroid"],
            "obesity_treatment": ["obesity", "bariatric", "weight loss"],
            "maternity": ["maternity", "pregnancy", "prenatal"],
            "mental_health": ["mental", "psychiatric", "depression", "anxiety"],
            "hernia": ["hernia"],
            "cataract": ["cataract"],
            "joint_replacement": ["joint replacement", "knee replacement", "hip replacement"]
        }
        
        for condition_key, keywords in condition_mapping.items():
            if any(kw in diagnosis_lower for kw in keywords):
                waiting_days = specific_conditions.get(condition_key, 0)
                if waiting_days > 0 and days_since_join < waiting_days:
                    eligible_date = join_date + __import__('datetime').timedelta(days=waiting_days)
                    return PolicyViolation(
                        code=ViolationCode.WAITING_PERIOD,
                        message=f"Waiting period for {condition_key.replace('_', ' ')} is {waiting_days} days. "
                                f"Member joined on {member.join_date}. Eligible for {condition_key.replace('_', ' ')}-related claims from "
                                f"{eligible_date.strftime('%Y-%m-%d')}.",
                        details={
                            "condition": condition_key,
                            "waiting_days": waiting_days,
                            "days_completed": days_since_join,
                            "eligible_from": eligible_date.strftime("%Y-%m-%d")
                        }
                    )
        
        return None
    
    def check_exclusions(
        self,
        diagnosis: str,
        procedures: List[str],
        category: str
    ) -> List[PolicyViolation]:
        violations = []
        exclusions = self.policy_data.get("exclusions", {})
        
        general_exclusions = exclusions.get("conditions", [])
        diagnosis_lower = diagnosis.lower() if diagnosis else ""
        
        exclusion_keywords = {
            "obesity": ["obesity", "bariatric", "weight loss", "diet program", "bmi"],
            "cosmetic": ["cosmetic", "aesthetic", "whitening", "bleaching", "veneers"],
            "experimental": ["experimental"],
            "self-inflicted": ["self-inflicted", "self inflicted"],
            "substance abuse": ["substance abuse", "alcohol", "drug abuse"],
            "infertility": ["infertility", "ivf", "assisted reproduction"]
        }
        
        for excl_name, keywords in exclusion_keywords.items():
            if any(kw in diagnosis_lower for kw in keywords):
                violations.append(PolicyViolation(
                    code=ViolationCode.EXCLUDED_CONDITION,
                    message=f"Treatment for {excl_name} is excluded under the policy.",
                    details={"exclusion_type": excl_name, "matched_in": "diagnosis"}
                ))
        
        if category == "DENTAL":
            dental_exclusions = exclusions.get("dental_exclusions", [])
            dental_category = self.policy_data.get("opd_categories", {}).get("dental", {})
            excluded_procedures = dental_category.get("excluded_procedures", [])
            
            for procedure in procedures:
                proc_lower = procedure.lower()
                for excluded in excluded_procedures:
                    if excluded.lower() in proc_lower or proc_lower in excluded.lower():
                        violations.append(PolicyViolation(
                            code=ViolationCode.EXCLUSION,
                            message=f"'{procedure}' is a cosmetic/excluded dental procedure.",
                            details={"procedure": procedure, "exclusion_type": "dental_cosmetic"}
                        ))
        
        if category == "VISION":
            vision_exclusions = exclusions.get("vision_exclusions", [])
            for procedure in procedures:
                proc_lower = procedure.lower()
                if any(excl.lower() in proc_lower for excl in vision_exclusions):
                    violations.append(PolicyViolation(
                        code=ViolationCode.EXCLUSION,
                        message=f"'{procedure}' is an excluded vision procedure.",
                        details={"procedure": procedure, "exclusion_type": "vision"}
                    ))
        
        return violations
    
    def check_pre_auth(
        self,
        category: str,
        amount: float,
        procedures: List[str]
    ) -> Optional[PolicyViolation]:
        pre_auth = self.policy_data.get("pre_authorization", {})
        required_for = pre_auth.get("required_for", [])
        
        category_config = self.policy_data.get("opd_categories", {}).get(category.lower(), {})
        pre_auth_threshold = category_config.get("pre_auth_threshold", float('inf'))
        high_value_tests = category_config.get("high_value_tests_requiring_pre_auth", [])
        
        for procedure in procedures:
            proc_lower = procedure.lower()
            for test in high_value_tests:
                if test.lower() in proc_lower:
                    if amount > pre_auth_threshold:
                        return PolicyViolation(
                            code=ViolationCode.PRE_AUTH_MISSING,
                            message=f"Pre-authorization is required for {test} when amount exceeds ₹{pre_auth_threshold:,.0f}. "
                                    f"Your claim amount is ₹{amount:,.0f}. Please obtain pre-authorization and resubmit.",
                            details={
                                "procedure": test,
                                "threshold": pre_auth_threshold,
                                "claimed_amount": amount
                            }
                        )
        
        return None
    
    def check_limits(
        self,
        category: str,
        amount: float,
        ytd_amount: float
    ) -> List[PolicyViolation]:
        violations = []
        coverage = self.policy_data.get("coverage", {})
        category_config = self.policy_data.get("opd_categories", {}).get(category.lower(), {})
        
        categories_with_own_limits = ["dental", "vision", "alternative_medicine"]
        
        per_claim_limit = coverage.get("per_claim_limit", float('inf'))
        if category.lower() not in categories_with_own_limits and amount > per_claim_limit:
            violations.append(PolicyViolation(
                code=ViolationCode.PER_CLAIM_EXCEEDED,
                message=f"Claimed amount ₹{amount:,.0f} exceeds the per-claim limit of ₹{per_claim_limit:,.0f}.",
                details={"claimed": amount, "limit": per_claim_limit}
            ))
        
        annual_opd_limit = coverage.get("annual_opd_limit", float('inf'))
        if ytd_amount + amount > annual_opd_limit:
            remaining = max(0, annual_opd_limit - ytd_amount)
            violations.append(PolicyViolation(
                code=ViolationCode.ANNUAL_LIMIT_EXCEEDED,
                message=f"This claim would exceed your annual OPD limit. "
                        f"Annual limit: ₹{annual_opd_limit:,.0f}, Already used: ₹{ytd_amount:,.0f}, "
                        f"Remaining: ₹{remaining:,.0f}.",
                details={"annual_limit": annual_opd_limit, "ytd_used": ytd_amount, "remaining": remaining}
            ))
        
        sub_limit = category_config.get("sub_limit", float('inf'))
        if amount > sub_limit:
            violations.append(PolicyViolation(
                code=ViolationCode.SUB_LIMIT_EXCEEDED,
                message=f"Claimed amount exceeds the {category} sub-limit of ₹{sub_limit:,.0f}.",
                details={"claimed": amount, "sub_limit": sub_limit, "category": category}
            ))
        
        return violations
    
    def calculate_adjustments(
        self,
        category: str,
        amount: float,
        hospital_name: Optional[str],
        line_items: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[float, List[Adjustment]]:
        adjustments = []
        current_amount = amount
        
        network_hospitals = self.policy_data.get("network_hospitals", [])
        category_config = self.policy_data.get("opd_categories", {}).get(category.lower(), {})
        
        network_discount_percent = category_config.get("network_discount_percent", 0)
        if hospital_name and any(nh.lower() in hospital_name.lower() for nh in network_hospitals):
            discount = current_amount * (network_discount_percent / 100)
            if discount > 0:
                adjustments.append(Adjustment(
                    type=AdjustmentType.NETWORK_DISCOUNT,
                    description=f"Network hospital discount ({network_discount_percent}%)",
                    amount=discount,
                    original_amount=current_amount
                ))
                current_amount -= discount
        
        copay_percent = category_config.get("copay_percent", 0)
        if copay_percent > 0:
            copay = current_amount * (copay_percent / 100)
            adjustments.append(Adjustment(
                type=AdjustmentType.COPAY,
                description=f"Co-pay ({copay_percent}%)",
                amount=copay,
                original_amount=current_amount
            ))
            current_amount -= copay
        
        return current_amount, adjustments
    
    def get_covered_dental_procedures(self) -> List[str]:
        dental_config = self.policy_data.get("opd_categories", {}).get("dental", {})
        return dental_config.get("covered_procedures", [])
    
    def get_excluded_dental_procedures(self) -> List[str]:
        dental_config = self.policy_data.get("opd_categories", {}).get("dental", {})
        return dental_config.get("excluded_procedures", [])
    
    def get_fraud_thresholds(self) -> Dict[str, Any]:
        return self.policy_data.get("fraud_thresholds", {
            "same_day_claims_limit": 2,
            "monthly_claims_limit": 6,
            "high_value_claim_threshold": 25000,
            "auto_manual_review_above": 25000,
            "fraud_score_manual_review_threshold": 0.80
        })
    
    def is_network_hospital(self, hospital_name: str) -> bool:
        if not hospital_name:
            return False
        network_hospitals = self.policy_data.get("network_hospitals", [])
        return any(nh.lower() in hospital_name.lower() for nh in network_hospitals)
