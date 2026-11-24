import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    # Role-based governance:
    # "state_admin", "district_admin", "phc", "hospital", "cho", "admin"
    role = Column(String, nullable=False, index=True)
    facility_id = Column(String, ForeignKey("facilities.id"), nullable=True)
    district = Column(String, nullable=True, index=True)  # Scoped for district administrators
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    facility = relationship("Facility", back_populates="users")
    notifications = relationship("Notification", back_populates="user")
