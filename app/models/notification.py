import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class NotificationType(str, enum.Enum):
    event_reminder = "event_reminder"
    rsvp_confirmed = "rsvp_confirmed"
    rsvp_waitlisted = "rsvp_waitlisted"
    certificate_ready = "certificate_ready"
    club_announcement = "club_announcement"
    recruitment_update = "recruitment_update"
    general = "general"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    notification_type = Column(Enum(NotificationType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    # Optional deep-link data — e.g., {"event_id": 5} or {"club_id": 2}
    link_url = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")
