from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

class FollowUpUpdate(BaseModel):
    notes: Optional[str] = None
    completion_notes: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(Assigned|In Progress|Completed|Overdue)$")
    reschedule_date: Optional[date] = None

class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    referral_id: str
    patient_id: str
    patient_name: str
    patient_code: str
    facility_name: str
    assigned_to_name: Optional[str] = None
    due_date: date
    status: str
    notes: Optional[str] = None
    completion_notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
