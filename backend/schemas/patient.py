from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

class PatientCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    age: int = Field(..., ge=0, le=125)
    sex: str = Field(..., pattern="^(Female|Male|Other|Prefer not to say)$")
    patient_code: Optional[str] = None  # Auto-generated if not provided
    phone: Optional[str] = None
    address: Optional[str] = None
    registered_phc_id: Optional[str] = None

class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    patient_code: str
    full_name: str
    age: int
    sex: str
    phone: Optional[str] = None
    address: Optional[str] = None
    registered_phc_id: str
    registered_phc_name: Optional[str] = None
    registered_date: date
    created_at: datetime
    referral_count: Optional[int] = 0
