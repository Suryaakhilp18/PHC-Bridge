from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.referral import Referral
from backend.models.audit import AIInteractionLog
from backend.schemas.ai import (
    QualityCheckRequest, QualityCheckResponse,
    SummarizeRequest, SummarizeResponse,
    OperationsQueryRequest, OperationsQueryResponse,
    TranslateRequest, TranslateResponse
)
from backend.ai.referral_assistant import ReferralQualityAssistant
from backend.ai.journey_summarizer import JourneySummarizer
from backend.ai.operations_assistant import OperationsAssistant
from backend.ai.translation_assistant import TranslationAssistant

router = APIRouter(prefix="/ai", tags=["AI Intelligence Engine"])

@router.post("/quality-check", response_model=QualityCheckResponse)
def quality_check(
    payload: QualityCheckRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = ReferralQualityAssistant.analyze_referral(
        reason=payload.reason,
        priority=payload.priority,
        destination=payload.destination,
        age=payload.age,
        sex=payload.sex
    )
    # Log interaction
    log = AIInteractionLog(
        user_id=user.id,
        module="quality_check",
        input_prompt=f"Priority: {payload.priority} | Reason: {payload.reason}",
        output_response=f"Score: {result['score']} | Clarity: {result['clarity_assessment']}"
    )
    db.add(log)
    db.commit()
    return QualityCheckResponse(**result)

@router.post("/summarize", response_model=SummarizeResponse)
def summarize_journey(
    payload: SummarizeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    r = db.get(Referral, payload.referral_id)
    if not r:
        raise HTTPException(404, "Referral not found")
        
    result = JourneySummarizer.summarize_journey(r)
    log = AIInteractionLog(
        user_id=user.id,
        module="journey_summarizer",
        input_prompt=f"Referral {r.id}",
        output_response=result["ai_generated_summary"]
    )
    db.add(log)
    db.commit()
    return SummarizeResponse(**result)

@router.post("/operations-query", response_model=OperationsQueryResponse)
def operations_query(
    payload: OperationsQueryRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = OperationsAssistant.answer_query(payload.query, db)
    log = AIInteractionLog(
        user_id=user.id,
        module="operations_assistant",
        input_prompt=payload.query,
        output_response=result["answer"]
    )
    db.add(log)
    db.commit()
    return OperationsQueryResponse(**result)

@router.post("/translate", response_model=TranslateResponse)
def translate_instruction(
    payload: TranslateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = TranslationAssistant.translate(payload.text, payload.target_language)
    return TranslateResponse(**result)
