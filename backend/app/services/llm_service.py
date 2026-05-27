import base64
import json
import time
from typing import Optional, Dict, Any, List
import logging

from ..config import get_settings
from ..models.trace import LLMCall

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.client = None
        self.model = "gpt-4o"
        
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    async def classify_document(self, image_base64: str) -> tuple[Dict[str, Any], LLMCall]:
        if not self.client:
            return {
                "type": "UNKNOWN",
                "readability": "PARTIAL",
                "confidence": 0.5,
                "error": "OpenAI client not initialized"
            }, LLMCall(
                model=self.model,
                prompt_summary="Document classification (skipped)",
                response_summary="No API key",
                latency_ms=0,
                success=False
            )
        
        prompt = """Analyze this medical document image and classify it.

Return a JSON object with:
{
    "type": "PRESCRIPTION" | "HOSPITAL_BILL" | "PHARMACY_BILL" | "LAB_REPORT" | "DISCHARGE_SUMMARY" | "DENTAL_REPORT" | "UNKNOWN",
    "readability": "GOOD" | "PARTIAL" | "UNREADABLE",
    "confidence": 0.0 to 1.0,
    "detected_elements": ["list of elements you can see"],
    "issues": ["any issues with document quality"]
}

Classification criteria:
- PRESCRIPTION: Has Rx symbol, doctor name/registration, medicines listed
- HOSPITAL_BILL: Has itemized charges, total amount, hospital/clinic name
- PHARMACY_BILL: Has medicine names with batch/expiry, pharmacy name, drug license
- LAB_REPORT: Has test results with normal ranges, lab name, pathologist signature
- DISCHARGE_SUMMARY: Hospital discharge document with admission/discharge dates
- DENTAL_REPORT: Dental examination findings, procedure details

Readability criteria:
- GOOD: All text clearly readable
- PARTIAL: Some text obscured but key fields visible
- UNREADABLE: Cannot extract meaningful information

Return ONLY valid JSON, no markdown."""

        start_time = time.time()
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            
            llm_call = LLMCall(
                model=self.model,
                prompt_summary="Document classification request",
                response_summary=f"Type: {result.get('type')}, Readability: {result.get('readability')}",
                tokens_used=response.usage.total_tokens if response.usage else None,
                latency_ms=latency_ms,
                success=True
            )
            
            return result, llm_call
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Document classification failed: {e}")
            
            llm_call = LLMCall(
                model=self.model,
                prompt_summary="Document classification request",
                response_summary=f"Error: {str(e)}",
                latency_ms=latency_ms,
                success=False
            )
            
            return {
                "type": "UNKNOWN",
                "readability": "UNREADABLE",
                "confidence": 0.0,
                "error": str(e)
            }, llm_call
    
    async def extract_prescription_data(self, image_base64: str) -> tuple[Dict[str, Any], LLMCall]:
        prompt = """Extract information from this medical prescription.

Return a JSON object with:
{
    "doctor_name": "string or null",
    "doctor_registration": "string or null (format: XX/XXXXX/YYYY)",
    "specialization": "string or null",
    "patient_name": "string or null",
    "patient_age": number or null,
    "patient_gender": "M" | "F" | null,
    "date": "YYYY-MM-DD or null",
    "diagnosis": "string or null",
    "secondary_diagnosis": "string or null",
    "medicines": ["list of medicine names with dosage"],
    "tests_ordered": ["list of tests ordered"],
    "hospital_name": "string or null",
    "treatment": "string or null",
    "confidence_scores": {
        "doctor_name": 0.0-1.0,
        "patient_name": 0.0-1.0,
        "diagnosis": 0.0-1.0,
        "overall": 0.0-1.0
    }
}

For unreadable fields, return null.
Return ONLY valid JSON, no markdown."""

        return await self._extract_with_prompt(prompt, image_base64, "Prescription extraction")
    
    async def extract_bill_data(self, image_base64: str) -> tuple[Dict[str, Any], LLMCall]:
        prompt = """Extract information from this hospital/clinic bill.

Return a JSON object with:
{
    "hospital_name": "string or null",
    "bill_number": "string or null",
    "date": "YYYY-MM-DD or null",
    "patient_name": "string or null",
    "patient_age": number or null,
    "patient_gender": "M" | "F" | null,
    "referring_doctor": "string or null",
    "line_items": [
        {"description": "string", "amount": number, "quantity": number}
    ],
    "subtotal": number or null,
    "gst_amount": number or null,
    "total": number,
    "payment_mode": "string or null",
    "gstin": "string or null",
    "confidence_scores": {
        "hospital_name": 0.0-1.0,
        "patient_name": 0.0-1.0,
        "total": 0.0-1.0,
        "overall": 0.0-1.0
    }
}

For unreadable fields, return null. Be precise with amounts.
Return ONLY valid JSON, no markdown."""

        return await self._extract_with_prompt(prompt, image_base64, "Bill extraction")
    
    async def extract_lab_report_data(self, image_base64: str) -> tuple[Dict[str, Any], LLMCall]:
        prompt = """Extract information from this lab/diagnostic report.

Return a JSON object with:
{
    "lab_name": "string or null",
    "nabl_status": true | false | null,
    "patient_name": "string or null",
    "patient_age": number or null,
    "patient_gender": "M" | "F" | null,
    "referring_doctor": "string or null",
    "sample_date": "YYYY-MM-DD or null",
    "report_date": "YYYY-MM-DD or null",
    "test_name": "string or null",
    "test_results": [
        {"test": "string", "result": "string", "unit": "string", "normal_range": "string"}
    ],
    "remarks": "string or null",
    "pathologist_name": "string or null",
    "pathologist_registration": "string or null",
    "confidence_scores": {
        "patient_name": 0.0-1.0,
        "test_results": 0.0-1.0,
        "overall": 0.0-1.0
    }
}

Return ONLY valid JSON, no markdown."""

        return await self._extract_with_prompt(prompt, image_base64, "Lab report extraction")
    
    async def _extract_with_prompt(self, prompt: str, image_base64: str, operation: str) -> tuple[Dict[str, Any], LLMCall]:
        if not self.client:
            return {"error": "OpenAI client not initialized"}, LLMCall(
                model=self.model,
                prompt_summary=operation + " (skipped)",
                response_summary="No API key",
                latency_ms=0,
                success=False
            )
        
        start_time = time.time()
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            
            llm_call = LLMCall(
                model=self.model,
                prompt_summary=operation,
                response_summary=f"Extracted {len(result)} fields",
                tokens_used=response.usage.total_tokens if response.usage else None,
                latency_ms=latency_ms,
                success=True
            )
            
            return result, llm_call
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"{operation} failed: {e}")
            
            llm_call = LLMCall(
                model=self.model,
                prompt_summary=operation,
                response_summary=f"Error: {str(e)}",
                latency_ms=latency_ms,
                success=False
            )
            
            return {"error": str(e)}, llm_call
    
    @staticmethod
    def encode_image_to_base64(file_path: str) -> str:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
