from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict

class ReferralCreate(BaseModel):
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = "Female"
    patient_code: Optional[str] = None
    phone: Optional[str] = None
    source_phc: Optional[str] = None
    destination: Optional[str] = None
    referring_facility_id: Optional[str] = None
    receiving_facility_id: Optional[str] = None
    reason: str = Field(..., min_length=3)
    priority: str = Field(default="Routine", pattern="^(Routine|Urgent|Emergency)$")

class OutcomeCreate(BaseModel):
    outcome_notes: str = Field(..., min_length=3)
    diagnosis_category: Optional[str] = None
    back_referral: bool = False
    follow_up_date: Optional[date] = None
    follow_up_instructions: Optional[str] = None

class CancelReferral(BaseModel):
    reason: str = Field(..., min_length=3)

class ReferralEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    actor_name: str
    actor_role: str
    action: str
    details: Optional[str] = None
    created_at: datetime

class ReferralResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    patient_id: str
    patient_name: str
    age: int
    sex: str
    patient_code: str
    phone: Optional[str] = None
    source_phc: str
    destination: str
    referring_doctor_name: Optional[str] = None
    reason: str
    priority: str
    status: str
    cancellation_reason: Optional[str] = None
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    outcome: Optional[str] = None
    back_referral: bool = False
    follow_up_date: Optional[date] = None
    follow_up_note: Optional[str] = None
    follow_up_status: Optional[str] = None
    qr_token: Optional[str] = None
    events: Optional[List[ReferralEventResponse]] = []
