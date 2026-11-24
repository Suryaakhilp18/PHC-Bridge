import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, DateTime, Date, Text, Boolean, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from backend.core.database import Base

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(String, primary_key=True, index=True)  # e.g., AP-2026-XXXXXX or PHC-2026-XXXXXX
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    referring_facility_id = Column(String, ForeignKey("facilities.id"), nullable=False, index=True)
    receiving_facility_id = Column(String, ForeignKey("facilities.id"), nullable=False, index=True)
    referring_doctor_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Clinical and administrative details
    reason = Column(Text, nullable=False)
    priority = Column(String, default="Routine", nullable=False)  # Routine, Urgent, Emergency
    status = Column(String, default="Referred", nullable=False, index=True)
    # SLA Response target in hours: Emergency: 1h, Urgent: 4h, Routine: 24h
    sla_hours = Column(Float, default=24.0)
    cancellation_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    in_consultation_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", back_populates="referrals")
    referring_facility = relationship("Facility", foreign_keys=[referring_facility_id])
    receiving_facility = relationship("Facility", foreign_keys=[receiving_facility_id])
    referring_doctor = relationship("User", foreign_keys=[referring_doctor_id])
    
    events = relationship("ReferralEvent", back_populates="referral", cascade="all, delete-orphan", order_by="ReferralEvent.created_at.asc()")
    outcome = relationship("ConsultationOutcome", uselist=False, back_populates="referral", cascade="all, delete-orphan")
    back_referral = relationship("BackReferral", uselist=False, back_populates="referral", cascade="all, delete-orphan")
    follow_up_tasks = relationship("FollowUpTask", back_populates="referral", cascade="all, delete-orphan")

class ReferralEvent(Base):
    __tablename__ = "referral_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    referral_id = Column(String, ForeignKey("referrals.id"), nullable=False, index=True)
    actor_id = Column(String, nullable=True)
    actor_name = Column(String, nullable=False)
    actor_role = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    referral = relationship("Referral", back_populates="events")

class ConsultationOutcome(Base):
    __tablename__ = "consultation_outcomes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    referral_id = Column(String, ForeignKey("referrals.id"), unique=True, nullable=False)
    doctor_id = Column(String, ForeignKey("users.id"), nullable=False)
    doctor_name = Column(String, nullable=False)
    outcome_notes = Column(Text, nullable=False)
    diagnosis_category = Column(String, nullable=True)
    back_referral_recommended = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    referral = relationship("Referral", back_populates="outcome")

class BackReferral(Base):
    __tablename__ = "back_referrals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    referral_id = Column(String, ForeignKey("referrals.id"), unique=True, nullable=False)
    origin_hospital_id = Column(String, ForeignKey("facilities.id"), nullable=False)
    target_phc_id = Column(String, ForeignKey("facilities.id"), nullable=False)
    clinical_summary = Column(Text, nullable=False)
    follow_up_instructions = Column(Text, nullable=False)
    follow_up_date = Column(Date, nullable=True)
    status = Column(String, default="Active")  # Active, Completed, Cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    referral = relationship("Referral", back_populates="back_referral")
