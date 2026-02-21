# models.py

import uuid
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.dialects.postgresql import UUID
import os
from dotenv import load_dotenv
load_dotenv()

schema_name=os.getenv("schema_name", "app_db")  # default matches migration schema creation


def current_ist_time():
    return datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None, microsecond=0)

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {'schema': schema_name}  # Change schema name if needed

    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=True)
    user_created_on = db.Column(db.DateTime, default=current_ist_time, nullable=False)
    last_modified_on = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    theme = db.Column(db.String(10), default='system')
    file_permission = db.Column(db.String(10), default='none') 

    def get_id(self):
        return str(self.user_id)

class SupportTicket(db.Model):
    # Deprecated: kept for legacy reads until migration is complete.
    # New ticketing system should use a different model; remove this class and
    # drop the table in a future migration once clients have moved off it.
    # (Original table used for email-based support tickets.)
    __tablename__ = "SupportTicket"
    __table_args__ = {'schema': schema_name}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(f"{schema_name}.users.user_id"),
        nullable=True)
    email = db.Column(db.String(255), nullable=True)

    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="open")

    def __repr__(self):
        return f"<SupportTicket {self.id} - {self.subject}>"
    
class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = {'schema': schema_name}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255))
    is_global = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=current_ist_time)


class UserNotification(db.Model):
    __tablename__ = "user_notifications"
    __table_args__ = (
        db.UniqueConstraint(
            'user_id',
            'notification_id',
            name='unique_user_notification'
        ),
        {'schema': schema_name}  # MUST be last
    )

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(f"{schema_name}.users.user_id"),
        nullable=False
    )

    notification_id = db.Column(
        db.Integer,
        db.ForeignKey(f"{schema_name}.notifications.id"),
        nullable=False
    )

    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)

    notification = db.relationship("Notification")
