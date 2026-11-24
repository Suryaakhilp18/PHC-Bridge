import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from backend.core.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    referral_id = Column(String, index=True, nullable=True)
    user_id = Column(String, nullable=True)
    actor = Column(String, nullable=False)
    role = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class AIInteractionLog(Base):
    __tablename__ = "ai_interactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)
    module = Column(String, nullable=False)  # quality_check, summarizer, operations, translation
    input_prompt = Column(Text, nullable=False)
    output_response = Column(Text, nullable=False)
    model_name = Column(String, default="rule-engine-v2")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
