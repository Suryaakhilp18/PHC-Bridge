from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.notification import Notification
from backend.schemas.notification import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    limit: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    notifs = db.query(Notification).filter(
        or_(
            Notification.user_id == user.id,
            Notification.target_role == user.role,
            Notification.target_role == None
        )
    ).order_by(desc(Notification.created_at)).limit(limit).all()
    return notifs

@router.post("/{notification_id}/read")
def mark_read(
    notification_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    n = db.get(Notification, notification_id)
    if not n:
        raise HTTPException(404, "Notification not found")
    n.is_read = True
    db.commit()
    return {"status": "success"}

@router.post("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    notifs = db.query(Notification).filter(
        or_(
            Notification.user_id == user.id,
            Notification.target_role == user.role
        )
    ).all()
    for n in notifs:
        n.is_read = True
    db.commit()
    return {"marked": len(notifs)}
