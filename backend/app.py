from datetime import datetime, date, timedelta
from enum import Enum
import os, uuid
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, DateTime, Date, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./phc_bridge.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

app = FastAPI(title="PHC Bridge API", version="1.0.0",
              description="Synthetic-data prototype for referral coordination.")
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

DEMO_USERS = {
    "phc": {"name": "Dr. Meera Rao", "role": "phc", "facility": "Lakshmi Nagar PHC"},
    "hospital": {"name": "Dr. Arjun Kumar", "role": "hospital", "facility": "District General Hospital"},
    "cho": {"name": "Sravani", "role": "cho", "facility": "Lakshmi Nagar PHC"},
    "admin": {"name": "System Administrator", "role": "admin", "facility": "District Health Office"},
}
TOKENS = {}

class Referral(Base):
    __tablename__ = "referrals"
    id = Column(String, primary_key=True, index=True)
    patient_name = Column(String, nullable=False)
    age = Column(String, nullable=False)
    sex = Column(String, nullable=False)
    patient_code = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=True)
    source_phc = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    priority = Column(String, nullable=False, default="Routine")
    status = Column(String, nullable=False, default="Referred")
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    outcome = Column(Text, nullable=True)
    back_referral = Column(Boolean, default=False)
    follow_up_date = Column(Date, nullable=True)
    follow_up_note = Column(Text, nullable=True)
    follow_up_status = Column(String, default="Not assigned")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    referral_id = Column(String, index=True, nullable=False)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def current_user(authorization: Optional[str] = Header(default=None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    if not token or token not in TOKENS:
        raise HTTPException(status_code=401, detail="Please sign in again.")
    return TOKENS[token]

class LoginIn(BaseModel):
    role: str

class ReferralIn(BaseModel):
    patient_name: str = Field(min_length=2, max_length=100)
    age: str
    sex: str
    patient_code: str
    phone: Optional[str] = None
    source_phc: str
    destination: str
    reason: str = Field(min_length=3)
    priority: str = "Routine"

class OutcomeIn(BaseModel):
    outcome: str = Field(min_length=3)
    back_referral: bool = False
    follow_up_date: Optional[date] = None
    follow_up_note: Optional[str] = None

class FollowUpIn(BaseModel):
    follow_up_date: date
    follow_up_note: str
    follow_up_status: str = "Assigned"

def log_event(db, referral_id, actor, action, details=""):
    db.add(AuditEvent(referral_id=referral_id, actor=actor, action=action, details=details))
    db.commit()

def referral_dict(r):
    return {
        "id": r.id, "patient_name": r.patient_name, "age": r.age, "sex": r.sex,
        "patient_code": r.patient_code, "phone": r.phone, "source_phc": r.source_phc,
        "destination": r.destination, "reason": r.reason, "priority": r.priority,
        "status": r.status, "created_at": r.created_at.isoformat() if r.created_at else None,
        "acknowledged_at": r.acknowledged_at.isoformat() if r.acknowledged_at else None,
        "outcome": r.outcome, "back_referral": r.back_referral,
        "follow_up_date": r.follow_up_date.isoformat() if r.follow_up_date else None,
        "follow_up_note": r.follow_up_note, "follow_up_status": r.follow_up_status
    }

@app.on_event("startup")
def seed_demo_data():
    db = SessionLocal()
    try:
        if db.query(Referral).count() == 0:
            samples = [
                Referral(id="PHC-2026-00124", patient_name="Ananya Devi", age="34", sex="Female",
                    patient_code="SYN-1001", source_phc="Lakshmi Nagar PHC", destination="District General Hospital",
                    reason="Needs further evaluation for persistent abdominal pain.", priority="Urgent",
                    status="Acknowledged", created_at=datetime.utcnow()-timedelta(hours=5),
                    acknowledged_at=datetime.utcnow()-timedelta(hours=3)),
                Referral(id="PHC-2026-00123", patient_name="Ravi Teja", age="52", sex="Male",
                    patient_code="SYN-1002", source_phc="Lakshmi Nagar PHC", destination="District General Hospital",
                    reason="Requires specialist assessment for recurring joint pain.", priority="Routine",
                    status="Referred", created_at=datetime.utcnow()-timedelta(hours=8)),
                Referral(id="PHC-2026-00122", patient_name="Fatima Begum", age="27", sex="Female",
                    patient_code="SYN-1003", source_phc="Kothuru PHC", destination="District General Hospital",
                    reason="Further assessment requested by attending medical officer.", priority="Routine",
                    status="Completed", outcome="Consultation completed; return to PHC for scheduled review.",
                    back_referral=True, follow_up_date=date.today()+timedelta(days=7),
                    follow_up_note="Review as advised by hospital team.", follow_up_status="Assigned",
                    created_at=datetime.utcnow()-timedelta(days=1))
            ]
            db.add_all(samples); db.commit()
            for r in samples:
                db.add(AuditEvent(referral_id=r.id, actor="System", action="Referral created", details="Synthetic demo record"))
            db.commit()
    finally: db.close()

@app.get("/")
def root():
    return {"service": "PHC Bridge API", "status": "online", "synthetic_data_only": True}

@app.post("/api/login")
def login(payload: LoginIn):
    if payload.role not in DEMO_USERS: raise HTTPException(400, "Unknown demo role")
    token = str(uuid.uuid4())
    TOKENS[token] = DEMO_USERS[payload.role]
    return {"token": token, "user": DEMO_USERS[payload.role]}

@app.get("/api/referrals")
def list_referrals(db: Session = Depends(get_db), user=Depends(current_user)):
    rows = db.query(Referral).order_by(Referral.created_at.desc()).all()
    return [referral_dict(r) for r in rows]

@app.post("/api/referrals")
def create_referral(payload: ReferralIn, db: Session = Depends(get_db), user=Depends(current_user)):
    if user["role"] not in ("phc", "admin"): raise HTTPException(403, "Only PHC staff can create referrals")
    referral_id = f"PHC-{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}"
    r = Referral(id=referral_id, **payload.model_dump(), status="Referred")
    db.add(r); db.commit(); db.refresh(r)
    log_event(db, r.id, user["name"], "Referral created", f"Sent to {r.destination}")
    return referral_dict(r)

@app.post("/api/referrals/{referral_id}/acknowledge")
def acknowledge(referral_id: str, db: Session = Depends(get_db), user=Depends(current_user)):
    if user["role"] not in ("hospital", "admin"): raise HTTPException(403, "Hospital role required")
    r = db.get(Referral, referral_id)
    if not r: raise HTTPException(404, "Referral not found")
    r.status = "Acknowledged"; r.acknowledged_at = datetime.utcnow()
    db.commit(); log_event(db, r.id, user["name"], "Hospital acknowledged", "Receiving facility confirmed receipt")
    return referral_dict(r)

@app.post("/api/referrals/{referral_id}/outcome")
def record_outcome(referral_id: str, payload: OutcomeIn, db: Session = Depends(get_db), user=Depends(current_user)):
    if user["role"] not in ("hospital", "admin"): raise HTTPException(403, "Hospital role required")
    r = db.get(Referral, referral_id)
    if not r: raise HTTPException(404, "Referral not found")
    r.outcome = payload.outcome; r.status = "Completed"
    r.back_referral = payload.back_referral
    r.follow_up_date = payload.follow_up_date
    r.follow_up_note = payload.follow_up_note
    r.follow_up_status = "Assigned" if payload.follow_up_date else "Not assigned"
    db.commit(); log_event(db, r.id, user["name"], "Outcome recorded", payload.outcome)
    if payload.back_referral: log_event(db, r.id, user["name"], "Back-referral created", payload.follow_up_note or "Return to PHC for continuity")
    return referral_dict(r)

@app.post("/api/referrals/{referral_id}/follow-up")
def assign_followup(referral_id: str, payload: FollowUpIn, db: Session = Depends(get_db), user=Depends(current_user)):
    if user["role"] not in ("cho", "phc", "admin"): raise HTTPException(403, "PHC / CHO role required")
    r = db.get(Referral, referral_id)
    if not r: raise HTTPException(404, "Referral not found")
    r.follow_up_date = payload.follow_up_date
    r.follow_up_note = payload.follow_up_note
    r.follow_up_status = payload.follow_up_status
    db.commit(); log_event(db, r.id, user["name"], "Follow-up updated", payload.follow_up_note)
    return referral_dict(r)

@app.post("/api/referrals/{referral_id}/follow-up/complete")
def complete_followup(referral_id: str, db: Session = Depends(get_db), user=Depends(current_user)):
    if user["role"] not in ("cho", "phc", "admin"): raise HTTPException(403, "PHC / CHO role required")
    r = db.get(Referral, referral_id)
    if not r: raise HTTPException(404, "Referral not found")
    r.follow_up_status = "Completed"; db.commit()
    log_event(db, r.id, user["name"], "Follow-up completed", "Follow-up marked complete")
    return referral_dict(r)

@app.get("/api/referrals/{referral_id}/timeline")
def timeline(referral_id: str, db: Session = Depends(get_db), user=Depends(current_user)):
    if not db.get(Referral, referral_id): raise HTTPException(404, "Referral not found")
    events = db.query(AuditEvent).filter(AuditEvent.referral_id == referral_id).order_by(AuditEvent.created_at.asc()).all()
    return [{"actor": e.actor, "action": e.action, "details": e.details, "created_at": e.created_at.isoformat()} for e in events]

@app.post("/api/sync")
def sync_offline(items: List[ReferralIn], db: Session = Depends(get_db), user=Depends(current_user)):
    if user["role"] not in ("phc", "admin"): raise HTTPException(403, "PHC role required to sync new referrals")
    created = []
    for payload in items:
        referral_id = f"PHC-{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}"
        r = Referral(id=referral_id, **payload.model_dump(), status="Referred")
        db.add(r); db.commit(); db.refresh(r)
        log_event(db, r.id, user["name"], "Offline referral synced", "Created from local offline queue")
        created.append(referral_dict(r))
    return {"synced": len(created), "referrals": created}

@app.get("/api/metrics")
def metrics(db: Session = Depends(get_db), user=Depends(current_user)):
    rows = db.query(Referral).all()
    return {
        "total": len(rows),
        "pending": sum(r.status == "Referred" for r in rows),
        "acknowledged": sum(r.status == "Acknowledged" for r in rows),
        "completed": sum(r.status == "Completed" for r in rows),
        "followups_due": sum(bool(r.follow_up_date and r.follow_up_status != "Completed" and r.follow_up_date <= date.today()) for r in rows),
        "back_referrals": sum(bool(r.back_referral) for r in rows)
    }
