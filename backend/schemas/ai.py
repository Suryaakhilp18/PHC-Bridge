from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class QualityCheckRequest(BaseModel):
    reason: str
    priority: str
    destination: str
    age: int
    sex: str

class QualityCheckResponse(BaseModel):
    score: int  # 0 to 100 quality score
    missing_fields: List[str]
    clarity_assessment: str
    suggested_wording: str
    recommendations: List[str]

class SummarizeRequest(BaseModel):
    referral_id: str

class SummarizeResponse(BaseModel):
    referral_id: str
    patient_summary: str
    timeline_facts: List[Dict[str, Any]]
    ai_generated_summary: str
    pending_actions: List[str]

class OperationsQueryRequest(BaseModel):
    query: str

class OperationsQueryResponse(BaseModel):
    question: str
    answer: str
    supporting_metrics: Dict[str, Any]
    sql_intent: str

class TranslateRequest(BaseModel):
    text: str
    target_language: str = Field(..., pattern="^(telugu|hindi|english)$")

class TranslateResponse(BaseModel):
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    disclaimer: str
