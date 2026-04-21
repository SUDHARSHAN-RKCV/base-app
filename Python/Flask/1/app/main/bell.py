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

    # Always do a proper count instead of assuming from limit
    unread_count = UserNotification.query.filter_by(
        user_id=current_user.user_id,
        is_read=False
    ).count()

    # Still limit display to 10 for performance
    notifications = (
        UserNotification.query
        .options(joinedload(UserNotification.notification))
        .filter_by(user_id=current_user.user_id, is_read=False)
        .order_by(UserNotification.id.desc())
        .limit(10)
        .all()
    )

    # skip any rows where the relationship failed to load
    formatted = []
    for n in notifications:
        if not getattr(n, 'notification', None):
            continue
        formatted.append({
            "id": n.id,
            "message": n.notification.message,
            "link": n.notification.link or "#"
        })

    return {
        "notifications": formatted,
        "unread_count": unread_count
    }
