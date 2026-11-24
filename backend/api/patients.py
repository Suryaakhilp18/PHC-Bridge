import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.patient import Patient
from backend.models.facility import Facility
from backend.models.user import User
from backend.schemas.patient import PatientCreate, PatientResponse

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("", response_model=List[PatientResponse])
def list_patients(
    query: Optional[str] = Query(None),
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    q = db.query(Patient)
    if query:
        term = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Patient.full_name.ilike(term),
                Patient.patient_code.ilike(term),
                Patient.phone.ilike(term)
            )
        )
    patients = q.order_by(Patient.created_at.desc()).limit(limit).all()
    
    results = []
    for p in patients:
        results.append(PatientResponse(
            id=p.id,
            patient_code=p.patient_code,
            full_name=p.full_name,
            age=p.age,
            sex=p.sex,
            phone=p.phone,
            address=p.address,
            registered_phc_id=p.registered_phc_id,
            registered_phc_name=p.registered_phc.name if p.registered_phc else None,
            registered_date=p.registered_date,
            created_at=p.created_at,
            referral_count=len(p.referrals)
        ))
    return results

@router.post("", response_model=PatientResponse)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role not in ("phc", "admin"):
        raise HTTPException(403, "Only PHC staff or Admin can register patients")
        
    phc_id = payload.registered_phc_id or user.facility_id
    if not phc_id:
        facility = db.query(Facility).first()
        phc_id = facility.id if facility else str(uuid.uuid4())
        
    code = payload.patient_code or f"SYN-{uuid.uuid4().hex[:4].upper()}"
    patient = Patient(
        patient_code=code,
        full_name=payload.full_name,
        age=payload.age,
        sex=payload.sex,
        phone=payload.phone,
        address=payload.address,
        registered_phc_id=phc_id
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    return PatientResponse(
        id=patient.id,
        patient_code=patient.patient_code,
        full_name=patient.full_name,
        age=patient.age,
        sex=patient.sex,
        phone=patient.phone,
        address=patient.address,
        registered_phc_id=patient.registered_phc_id,
        registered_phc_name=patient.registered_phc.name if patient.registered_phc else None,
        registered_date=patient.registered_date,
        created_at=patient.created_at,
        referral_count=0
    )

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "Patient record not found")
    return PatientResponse(
        id=p.id,
        patient_code=p.patient_code,
        full_name=p.full_name,
        age=p.age,
        sex=p.sex,
        phone=p.phone,
        address=p.address,
        registered_phc_id=p.registered_phc_id,
        registered_phc_name=p.registered_phc.name if p.registered_phc else None,
        registered_date=p.registered_date,
        created_at=p.created_at,
        referral_count=len(p.referrals)
    )
