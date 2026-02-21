# app/main/bell.py
# This file contains the logic for the notification bell in the navbar.
from flask_login import current_user
from app.models import UserNotification
from sqlalchemy.orm import joinedload
from .routes import main


@main.context_processor
def inject_notifications():
    if not current_user.is_authenticated:
        return {"notifications": [], "unread_count": 0}

    notifications = (
        UserNotification.query
        .options(joinedload(UserNotification.notification))
        .filter_by(user_id=current_user.user_id, is_read=False)
        .order_by(UserNotification.id.desc())
        .limit(10)
        .all()
    )

    unread_count = UserNotification.query.filter_by(
        user_id=current_user.user_id,
        is_read=False
    ).count()

    formatted = [
        {
            "id": n.id,
            "message": n.notification.message,
            "link": n.notification.link or "#"
        }
        for n in notifications
    ]

    return {
        "notifications": formatted,
        "unread_count": unread_count
    }
