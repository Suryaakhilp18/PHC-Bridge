from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.database import engine, Base, get_db
from backend.core.security import create_access_token
from backend.models.user import User
from backend.models.facility import Facility
from backend.seed import seed_database

# API Routers
from backend.api.auth import router as auth_router
from backend.api.patients import router as patients_router
from backend.api.referrals import router as referrals_router
from backend.api.followups import router as followups_router
from backend.api.notifications import router as notifications_router
from backend.api.analytics import router as analytics_router
from backend.api.ai import router as ai_router
from backend.api.sync import router as sync_router
from backend.api.interop import router as interop_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and seed demonstration data on startup
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield

app = FastAPI(
    title="PHC Bridge Enterprise API",
    version=settings.VERSION,
    description="AI-Powered Offline-First Patient Referral & Continuity-of-Care Coordination Platform.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount Modular Routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(patients_router, prefix="/api")
app.include_router(referrals_router, prefix="/api")
app.include_router(followups_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(sync_router, prefix="/api")
app.include_router(interop_router, prefix="/api")

# Service Health Endpoint
@app.get("/")
def health_check():
    return {
        "service": "PHC Bridge Platform",
        "version": settings.VERSION,
        "status": "online",
        "architecture": "modular-enterprise",
        "synthetic_data_only": True
    }

# Backward compatibility route for legacy prototype instant role-based login
class LegacyLogin(BaseModel):
    role: str

@app.post("/api/login")
def legacy_login(payload: LegacyLogin, db: Session = Depends(get_db)):
    role = payload.role.lower().strip()
    user = db.query(User).filter(User.role == role).first()
    if not user:
        # Fallback to create or find by username
        user = db.query(User).filter(User.username == role).first()
    if not user:
        raise HTTPException(400, f"Role or demo account '{role}' not found")
        
    token = create_access_token(data={"sub": user.id, "role": user.role, "name": user.full_name})
    return {
        "token": token,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.full_name,
            "username": user.username,
            "role": user.role,
            "facility": user.facility.name if user.facility else "General Healthcare Network",
            "facility_id": user.facility_id
        }
    }
