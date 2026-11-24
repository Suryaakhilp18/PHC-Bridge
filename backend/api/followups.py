from datetime import datetime, timezone, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.followup import FollowUpTask
from backend.models.referral import Referral
from backend.schemas.followup import FollowUpResponse, FollowUpUpdate
from backend.services.referral_service import ReferralService

router = APIRouter(tags=["Follow-ups"])

@router.get("/followups", response_model=List[FollowUpResponse])
def list_followups(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    q = db.query(FollowUpTask)
    if user.role == "cho" and user.facility_id:
        q = q.filter(FollowUpTask.facility_id == user.facility_id)
        
    if status_filter and status_filter != "All":
        q = q.filter(FollowUpTask.status == status_filter)
        
    tasks = q.order_by(FollowUpTask.due_date.asc()).all()
    results = []
    for t in tasks:
        # Check overdue dynamically
        is_overdue = t.due_date < date.today() and t.status != "Completed"
        task_status = "Overdue" if is_overdue else t.status
        results.append(FollowUpResponse(
            id=t.id,
            referral_id=t.referral_id,
            patient_id=t.patient_id,
            patient_name=t.patient.full_name if t.patient else "Unknown",
            patient_code=t.patient.patient_code if t.patient else "",
            facility_name=t.facility.name if t.facility else "PHC",
            assigned_to_name=t.assigned_to_name or user.full_name,
            due_date=t.due_date,
            status=task_status,
            notes=t.notes,
            completion_notes=t.completion_notes,
            completed_at=t.completed_at,
            created_at=t.created_at
        ))
    return results

@router.patch("/followups/{task_id}", response_model=FollowUpResponse)
def update_followup(
    task_id: str,
    payload: FollowUpUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    t = db.get(FollowUpTask, task_id)
    if not t:
        raise HTTPException(404, "Follow-up task not found")
        
    if payload.status:
        t.status = payload.status
        if payload.status == "Completed":
            t.completed_at = datetime.now(timezone.utc)
    if payload.completion_notes:
        t.completion_notes = payload.completion_notes
    if payload.notes:
        t.notes = payload.notes
    if payload.reschedule_date:
        t.due_date = payload.reschedule_date
        
    db.commit()
    db.refresh(t)
    
    ReferralService.log_audit(
        db,
        actor_name=user.full_name,
        actor_role=user.role,
        action="Follow-up Updated",
        referral_id=t.referral_id,
        details=f"Status: {t.status} | Note: {payload.completion_notes or payload.notes or ''}",
        user_id=user.id
    )
    
    return FollowUpResponse(
        id=t.id,
        referral_id=t.referral_id,
        patient_id=t.patient_id,
        patient_name=t.patient.full_name if t.patient else "Unknown",
        patient_code=t.patient.patient_code if t.patient else "",
        facility_name=t.facility.name if t.facility else "PHC",
        assigned_to_name=t.assigned_to_name or user.full_name,
        due_date=t.due_date,
        status=t.status,
        notes=t.notes,
        completion_notes=t.completion_notes,
        completed_at=t.completed_at,
        created_at=t.created_at
    )

# Legacy endpoints for frontend backwards-compatibility
@router.post("/referrals/{referral_id}/follow-up/complete")
def complete_followup_legacy(
    referral_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    r = db.get(Referral, referral_id)
    if not r:
        raise HTTPException(404, "Referral not found")
    for t in r.follow_up_tasks:
        t.status = "Completed"
        t.completed_at = datetime.now(timezone.utc)
    db.commit()
    ReferralService.log_audit(
        db,
        actor_name=user.full_name,
        actor_role=user.role,
        action="Follow-up Completed",
        referral_id=r.id,
        details="Community health worker marked patient follow-up complete",
        user_id=user.id
    )
    return ReferralService.to_dict(r)
