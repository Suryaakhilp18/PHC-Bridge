from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.referral import Referral
from backend.models.facility import Facility
from backend.interop.fhir_adapter import FHIRAdapter
from backend.interop.abdm_adapter import ABDMAdapter

router = APIRouter(prefix="/interop", tags=["Healthcare Interoperability (ABDM & FHIR R4)"])

@router.get("/fhir/referral/{referral_id}")
def get_fhir_referral_bundle(
    referral_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Exports the complete referral record and lifecycle events as an official HL7 FHIR R4
    Document Bundle conforming to Ayushman Bharat Digital Mission (ABDM) specifications.
    """
    r = db.get(Referral, referral_id)
    if not r:
        raise HTTPException(404, "Referral record not found")
        
    bundle = FHIRAdapter.generate_referral_bundle(r)
    return bundle

@router.get("/abdm/status")
def get_abdm_status(user: User = Depends(get_current_user)):
    """
    Returns ABDM Gateway sandbox configuration, registered HIP/HIU credentials,
    and interoperability profiles.
    """
    return ABDMAdapter.get_bridge_configuration()

@router.get("/facilities/directory")
def get_facilities_directory(
    district: str = None,
    facility_type: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Provides authoritative Health Facility Registry (HFR) listing across Andhra Pradesh.
    """
    q = db.query(Facility)
    if district and district != "All":
        q = q.filter(Facility.district == district)
    if facility_type and facility_type != "All":
        q = q.filter(Facility.facility_type == facility_type)
        
    facilities = q.order_by(Facility.district, Facility.name).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "facility_type": f.facility_type,
            "district": f.district,
            "mandal": f.mandal,
            "hfr_id": f.hfr_id,
            "phone": f.phone
        } for f in facilities
    ]
