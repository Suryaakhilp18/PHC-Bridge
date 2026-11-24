from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.notification import Notification

class NotificationService:
    @staticmethod
    def notify(
        db: Session,
        title: str,
        message: str,
        target_role: Optional[str] = None,
        user_id: Optional[str] = None,
        facility_id: Optional[str] = None,
        notification_type: str = "info",
        link_url: Optional[str] = None
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            target_role=target_role,
            facility_id=facility_id,
            title=title,
            message=message,
            notification_type=notification_type,
            link_url=link_url,
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif
