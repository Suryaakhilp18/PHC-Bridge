import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from backend.core.database import Base

class Facility(Base):
    __tablename__ = "facilities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    # AP Public Healthcare Hierarchy:
    # "Sub-Centre / AAM", "PHC", "UPHC", "CHC", "Area Hospital", "District Hospital", "Teaching Hospital"
    facility_type = Column(String, nullable=False, index=True)
    district = Column(String, nullable=False, index=True)  # e.g., NTR, Guntur, Visakhapatnam, Tirupati
    mandal = Column(String, nullable=True, index=True)      # e.g., Vijayawada Urban, Mangalagiri, Chandragiri
    state = Column(String, default="Andhra Pradesh")
    hfr_id = Column(String, unique=True, nullable=True, index=True)  # National Health Facility Registry ID
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    users = relationship("User", back_populates="facility")
    patients = relationship("Patient", back_populates="registered_phc")
