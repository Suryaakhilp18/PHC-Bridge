import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.core.database import Base

class FollowUpTask(Base):
    __tablename__ = "follow_up_tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    referral_id = Column(String, ForeignKey("referrals.id"), nullable=False, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    assigned_to_id = Column(String, ForeignKey("users.id"), nullable=True)
    assigned_to_name = Column(String, nullable=True)
    facility_id = Column(String, ForeignKey("facilities.id"), nullable=False)
    
    due_date = Column(Date, nullable=False, index=True)
    status = Column(String, default="Assigned", nullable=False)  # Assigned, In Progress, Completed, Overdue
    notes = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    referral = relationship("Referral", back_populates="follow_up_tasks")
    patient = relationship("Patient")
    facility = relationship("Facility")
