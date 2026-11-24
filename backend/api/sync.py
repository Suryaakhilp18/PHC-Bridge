import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.patient import Patient
from backend.models.facility import Facility
from backend.models.referral import Referral
from backend.services.referral_service import ReferralService

router = APIRouter(tags=["Sync Engine"])

@router.post("/sync")
def sync_offline_queue(
    items: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Idempotent bulk synchronization of offline created referrals.
    Protects against duplicate submissions and preserves server-authoritative state.
    """
    if user.role not in ("phc", "admin"):
        raise HTTPException(403, "PHC staff or Admin role required to sync referrals")
        
    synced = []
    skipped = 0
    
    for item in items:
        # Check idempotency / existing referral code or ID
        existing_id = item.get("id")
        if existing_id and db.get(Referral, existing_id):
            skipped += 1
            continue
            
        code = item.get("patient_code") or f"SYN-{uuid.uuid4().hex[:4].upper()}"
        patient = db.query(Patient).filter(Patient.patient_code == code).first()
        if not patient:
            patient = Patient(
                patient_code=code,
                full_name=item.get("patient_name", "Synthetic Patient"),
                age=int(item.get("age", 30)),
                sex=item.get("sex", "Female"),
                phone=item.get("phone"),
                registered_phc_id=user.facility_id or db.query(Facility).first().id
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            
        src_fac = db.get(Facility, user.facility_id) if user.facility_id else db.query(Facility).first()
        dest_name = item.get("destination", "District General Hospital")
        dest_fac = db.query(Facility).filter(Facility.name.ilike(f"%{dest_name}%")).first() or db.query(Facility).first()
        
        referral_id = existing_id or f"PHC-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:6].upper()}"
        referral = Referral(
            id=referral_id,
            patient_id=patient.id,
            referring_facility_id=src_fac.id,
            receiving_facility_id=dest_fac.id,
            referring_doctor_id=user.id,
            reason=item.get("reason", "Offline referral recorded"),
            priority=item.get("priority", "Routine"),
            status="Referred",
            created_at=datetime.now(timezone.utc)
        )
        db.add(referral)
        db.commit()
        db.refresh(referral)
        
        ReferralService.log_audit(
            db,
            actor_name=user.full_name,
            actor_role=user.role,
            action="Offline Referral Synced",
            referral_id=referral.id,
            details=f"Synchronized from local IndexedDB offline queue to {dest_fac.name}",
            user_id=user.id
        )
        synced.append(ReferralService.to_dict(referral))
        
    return {
        "synced": len(synced),
        "skipped_duplicates": skipped,
        "referrals": synced,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
