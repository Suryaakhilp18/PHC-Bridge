import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.core.database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_code = Column(String, unique=True, index=True, nullable=False)  # e.g., SYN-1001
    full_name = Column(String, nullable=False, index=True)
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)  # Female, Male, Other
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    registered_phc_id = Column(String, ForeignKey("facilities.id"), nullable=False)
    registered_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    registered_phc = relationship("Facility", back_populates="patients")
    referrals = relationship("Referral", back_populates="patient", cascade="all, delete-orphan")
