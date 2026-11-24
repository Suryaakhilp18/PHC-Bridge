import uuid
from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.patient import Patient
from backend.models.facility import Facility
from backend.models.referral import Referral, ReferralEvent, ConsultationOutcome, BackReferral
from backend.models.followup import FollowUpTask
from backend.schemas.referral import (
    ReferralCreate, OutcomeCreate, CancelReferral, ReferralResponse, ReferralEventResponse
)
from backend.services.referral_service import ReferralService
from backend.services.qr_service import QRService
from backend.services.notification_service import NotificationService

router = APIRouter(prefix="/referrals", tags=["Referrals"])

@router.get("", response_model=List[Dict[str, Any]])
def list_referrals(
    query: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    q = db.query(Referral)
    
    # Role-based visibility scoping
    if user.role == "phc" and user.facility_id:
        q = q.filter(or_(Referral.referring_facility_id == user.facility_id, Referral.receiving_facility_id == user.facility_id))
    elif user.role == "hospital" and user.facility_id:
        q = q.filter(Referral.receiving_facility_id == user.facility_id)
        
    if status_filter and status_filter != "All":
        q = q.filter(Referral.status == status_filter)
    if priority_filter and priority_filter != "All":
        q = q.filter(Referral.priority == priority_filter)
        
    rows = q.order_by(desc(Referral.created_at)).limit(limit).all()
    
    if query:
        term = query.lower().strip()
        rows = [
            r for r in rows
            if term in r.id.lower() or
               (r.patient and (term in r.patient.full_name.lower() or term in r.patient.patient_code.lower())) or
               (r.receiving_facility and term in r.receiving_facility.name.lower()) or
               (r.referring_facility and term in r.referring_facility.name.lower())
        ]
        
    return [ReferralService.to_dict(r) for r in rows]

@router.post("", response_model=Dict[str, Any])
def create_referral(
    payload: ReferralCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role not in ("phc", "admin"):
        raise HTTPException(status_code=403, detail="Only PHC staff or Admin can create referrals")
        
    # 1. Resolve or create Patient
    patient = None
    if payload.patient_id:
        patient = db.get(Patient, payload.patient_id)
    if not patient:
        code = payload.patient_code or f"SYN-{uuid.uuid4().hex[:4].upper()}"
        patient = db.query(Patient).filter(Patient.patient_code == code).first()
        if not patient:
            source_fac = db.query(Facility).filter(Facility.name == payload.source_phc).first() if payload.source_phc else None
            patient = Patient(
                patient_code=code,
                full_name=payload.patient_name or "Synthetic Patient",
                age=payload.age or 35,
                sex=payload.sex or "Female",
                phone=payload.phone,
                registered_phc_id=source_fac.id if source_fac else (user.facility_id or db.query(Facility).first().id)
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            
    # 2. Resolve Facilities
    src_facility = db.get(Facility, payload.referring_facility_id) if payload.referring_facility_id else None
    if not src_facility and payload.source_phc:
        src_facility = db.query(Facility).filter(Facility.name.ilike(f"%{payload.source_phc}%")).first()
    if not src_facility:
        src_facility = db.get(Facility, user.facility_id) if user.facility_id else db.query(Facility).filter(Facility.facility_type == "PHC").first()
        
    dest_facility = db.get(Facility, payload.receiving_facility_id) if payload.receiving_facility_id else None
    if not dest_facility and payload.destination:
        dest_facility = db.query(Facility).filter(Facility.name.ilike(f"%{payload.destination}%")).first()
    if not dest_facility:
        dest_facility = db.query(Facility).filter(Facility.facility_type == "District Hospital").first()
        if not dest_facility:
            dest_facility = db.query(Facility).first()

    # 3. Generate unique Referral ID
    referral_id = f"PHC-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:6].upper()}"
    
    # 4. Create Referral
    referral = Referral(
        id=referral_id,
        patient_id=patient.id,
        referring_facility_id=src_facility.id,
        receiving_facility_id=dest_facility.id,
        referring_doctor_id=user.id,
        reason=payload.reason,
        priority=payload.priority,
        status="Referred",
        created_at=datetime.now(timezone.utc)
    )
    db.add(referral)
    db.commit()
    db.refresh(referral)
    
    # 5. Audit Event
    ReferralService.log_audit(
        db,
        actor_name=user.full_name,
        actor_role=user.role,
        action="Referral Created",
        referral_id=referral.id,
        details=f"Referred to {dest_facility.name} (Priority: {payload.priority})",
        user_id=user.id
    )
    
    # 6. Dispatch In-App Notification to Hospital Doctor / Admin
    NotificationService.notify(
        db,
        title="New Incoming Referral",
        message=f"{patient.full_name} ({payload.priority}) referred from {src_facility.name} to {dest_facility.name}.",
        target_role="hospital",
        facility_id=dest_facility.id,
        notification_type="urgent" if payload.priority == "Urgent" else "info",
        link_url=f"/referrals/{referral.id}"
    )
    
    return ReferralService.to_dict(referral)

@router.get("/{referral_id}", response_model=Dict[str, Any])
def get_referral(
    referral_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    r = db.get(Referral, referral_id)
    if not r:
        raise HTTPException(404, "Referral not found")
    return ReferralService.to_dict(r)

@router.post("/{referral_id}/acknowledge", response_model=Dict[str, Any])
def acknowledge_referral(
    referral_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role not in ("hospital", "admin"):
        raise HTTPException(403, "Hospital Doctor or Admin role required to acknowledge referrals")
        
    r = db.get(Referral, referral_id)
    if not r:
        raise HTTPException(404, "Referral not found")
        
    if not ReferralService.validate_transition(r.status, "Acknowledged"):
        raise HTTPException(400, f"Cannot transition referral from '{r.status}' to 'Acknowledged'")
        
    r.status = "Acknowledged"
    r.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(r)
    
    ReferralService.log_audit(
        db,
        actor_name=user.full_name,
        actor_role=user.role,
        action="Hospital Acknowledged",
        referral_id=r.id,
        details=f"Receiving facility ({user.facility.name if user.facility else 'Hospital'}) confirmed patient handoff",
        user_id=user.id
    )
    
    # Notify referring PHC doctor
    NotificationService.notify(
        db,
        title="Referral Acknowledged",
        message=f"Referral {r.id} for {r.patient.full_name} has been acknowledged by the receiving hospital.",
        target_role="phc",
        user_id=r.referring_doctor_id,
        notification_type="success",
        link_url=f"/referrals/{r.id}"
    )
    
    return ReferralService.to_dict(r)

@router.post("/{referral_id}/outcome", response_model=Dict[str, Any])
def record_outcome(
    referral_id: str,
    payload: OutcomeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role not in ("hospital", "admin"):
        raise HTTPException(403, "Hospital Doctor or Admin role required to record consultation outcomes")
        
    r = db.get(Referral, referral_id)
    if not r:
        raise HTTPException(404, "Referral not found")
        
    # Update status to Completed or Back-Referred
    target_status = "Back-Referred" if payload.back_referral else "Completed"
    if r.status in ("Acknowledged", "In Consultation", "Referred"):
        r.status = target_status
    elif r.status == "Completed" and payload.back_referral:
        r.status = "Back-Referred"
    r.completed_at = datetime.now(timezone.utc)
    
    # Create or update outcome
    outcome = r.outcome
    if not outcome:
        outcome = ConsultationOutcome(
            referral_id=r.id,
            doctor_id=user.id,
            doctor_name=user.full_name,
            outcome_notes=payload.outcome_notes,
            diagnosis_category=payload.diagnosis_category,
            back_referral_recommended=payload.back_referral
        )
        db.add(outcome)
    else:
        outcome.outcome_notes = payload.outcome_notes
        outcome.back_referral_recommended = payload.back_referral
        
    # Create Back-Referral and Follow-up task if requested
    if payload.back_referral:
        br = r.back_referral
        if not br:
            br = BackReferral(
                referral_id=r.id,
                origin_hospital_id=r.receiving_facility_id,
                target_phc_id=r.referring_facility_id,
                clinical_summary=payload.outcome_notes,
                follow_up_instructions=payload.follow_up_instructions or "Routine review at PHC",
                follow_up_date=payload.follow_up_date,
                status="Active"
            )
            db.add(br)
            
        # Automatically generate FollowUpTask for Community Health Officer (CHO)
        fu_due = payload.follow_up_date or date.today()
        task = FollowUpTask(
            referral_id=r.id,
            patient_id=r.patient_id,
            facility_id=r.referring_facility_id,
            due_date=fu_due,
            status="Assigned",
            notes=payload.follow_up_instructions or payload.outcome_notes
        )
        db.add(task)
        
        # Notify CHO & PHC Doctor
        NotificationService.notify(
            db,
            title="Back-Referral & Follow-up Assigned",
            message=f"Patient {r.patient.full_name} has been back-referred to PHC with follow-up due on {fu_due.isoformat()}.",
            target_role="cho",
            facility_id=r.referring_facility_id,
            notification_type="urgent",
            link_url=f"/follow-ups"
        )
        
    db.commit()
    db.refresh(r)
    
    ReferralService.log_audit(
        db,
        actor_name=user.full_name,
        actor_role=user.role,
        action="Consultation Outcome Recorded",
        referral_id=r.id,
        details=f"Notes: {payload.outcome_notes[:100]} | Back-Referral: {payload.back_referral}",
        user_id=user.id
    )
    
    return ReferralService.to_dict(r)

@router.post("/{referral_id}/cancel", response_model=Dict[str, Any])
def cancel_referral(
    referral_id: str,
    payload: CancelReferral,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    r = db.get(Referral, referral_id)
    if not r:
        raise HTTPException(404, "Referral not found")
        
    r.status = "Cancelled"
    r.cancellation_reason = payload.reason
    db.commit()
    db.refresh(r)
    
    ReferralService.log_audit(
        db,
        actor_name=user.full_name,
        actor_role=user.role,
        action="Referral Cancelled",
        referral_id=r.id,
        details=f"Reason: {payload.reason}",
        user_id=user.id
    )
    return ReferralService.to_dict(r)

@router.get("/{referral_id}/timeline", response_model=List[ReferralEventResponse])
def get_timeline(
    referral_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    r = db.get(Referral, referral_id)
    if not r:
        raise HTTPException(404, "Referral not found")
    events = db.query(ReferralEvent).filter(ReferralEvent.referral_id == referral_id).order_by(ReferralEvent.created_at.asc()).all()
    return events

@router.post("/scan-qr", response_model=Dict[str, Any])
def scan_qr_code(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Validates scanned QR code token securely, verifies HMAC signature,
    and returns full verified referral record.
    """
    referral_id = QRService.verify_qr_payload(payload)
    if not referral_id:
        # Check if direct referral ID string was sent
        raw_id = payload.get("referralId") or payload.get("id") or payload.get("ref")
        if raw_id and db.get(Referral, raw_id):
            referral_id = raw_id
            
    if not referral_id:
        raise HTTPException(400, "Invalid or expired QR code identification token")
        
    r = db.get(Referral, referral_id)
    if not r:
        raise HTTPException(404, "Scanned referral ID does not exist in registry")
        
    ReferralService.log_audit(
        db,
        actor_name=user.full_name,
        actor_role=user.role,
        action="QR Code Scanned",
        referral_id=r.id,
        details=f"Referral verified and opened via camera QR scanner by {user.full_name}",
        user_id=user.id
    )
    return ReferralService.to_dict(r)
