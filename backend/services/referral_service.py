import uuid
import json
from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.models.referral import Referral, ReferralEvent, ConsultationOutcome, BackReferral
from backend.models.patient import Patient
from backend.models.facility import Facility
from backend.models.followup import FollowUpTask
from backend.models.audit import AuditEvent
from backend.services.notification_service import NotificationService
from backend.services.qr_service import QRService

# Validated State Transition Graph
VALID_TRANSITIONS = {
    "Draft": ["Referred", "Cancelled"],
    "Referred": ["Acknowledged", "Cancelled"],
    "Acknowledged": ["In Consultation", "Completed", "Cancelled"],
    "In Consultation": ["Completed", "Cancelled"],
    "Completed": ["Back-Referred"],  # Back referral can be appended to completed
    "Back-Referred": [],
    "Cancelled": []
}

class ReferralService:
    @staticmethod
    def log_audit(
        db: Session,
        actor_name: str,
        actor_role: str,
        action: str,
        referral_id: Optional[str] = None,
        details: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        event = AuditEvent(
            referral_id=referral_id,
            user_id=user_id,
            actor=actor_name,
            role=actor_role,
            action=action,
            details=details,
            created_at=datetime.now(timezone.utc)
        )
        db.add(event)
        if referral_id:
            ref_event = ReferralEvent(
                referral_id=referral_id,
                actor_id=user_id,
                actor_name=actor_name,
                actor_role=actor_role,
                action=action,
                details=details,
                created_at=datetime.now(timezone.utc)
            )
            db.add(ref_event)
        db.commit()

    @staticmethod
    def validate_transition(current_status: str, target_status: str) -> bool:
        allowed = VALID_TRANSITIONS.get(current_status, [])
        return target_status in allowed

    @staticmethod
    def to_dict(r: Referral) -> Dict[str, Any]:
        qr_payload = QRService.generate_qr_payload(r.id)
        
        # Determine follow up info
        fu_date = None
        fu_note = None
        fu_status = "Not assigned"
        if r.follow_up_tasks:
            latest_fu = sorted(r.follow_up_tasks, key=lambda x: x.created_at, reverse=True)[0]
            fu_date = latest_fu.due_date.isoformat() if latest_fu.due_date else None
            fu_note = latest_fu.notes or latest_fu.completion_notes
            fu_status = latest_fu.status

        outcome_text = r.outcome.outcome_notes if r.outcome else None
        has_back_ref = bool(r.back_referral)

        return {
            "id": r.id,
            "patient_id": r.patient.id if r.patient else "",
            "patient_name": r.patient.full_name if r.patient else "Unknown",
            "age": r.patient.age if r.patient else 0,
            "sex": r.patient.sex if r.patient else "Other",
            "patient_code": r.patient.patient_code if r.patient else "",
            "phone": r.patient.phone if r.patient else "",
            "source_phc": r.referring_facility.name if r.referring_facility else "PHC",
            "destination": r.receiving_facility.name if r.receiving_facility else "Hospital",
            "referring_doctor_name": r.referring_doctor.full_name if r.referring_doctor else "",
            "reason": r.reason,
            "priority": r.priority,
            "status": r.status,
            "cancellation_reason": r.cancellation_reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "acknowledged_at": r.acknowledged_at.isoformat() if r.acknowledged_at else None,
            "outcome": outcome_text,
            "back_referral": has_back_ref,
            "follow_up_date": fu_date,
            "follow_up_note": fu_note,
            "follow_up_status": fu_status,
            "qr_token": json.dumps(qr_payload),
            "events": [
                {
                    "id": e.id,
                    "actor_name": e.actor_name,
                    "actor_role": e.actor_role,
                    "action": e.action,
                    "details": e.details,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                } for e in r.events
            ]
        }
