import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class EventType(str, enum.Enum):
    open = "open"               # any student can RSVP
    club_only = "club_only"     # only club members
    invite_only = "invite_only"


class RSVPStatus(str, enum.Enum):
    confirmed = "confirmed"
    waitlisted = "waitlisted"
    cancelled = "cancelled"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(Enum(EventType), default=EventType.open, nullable=False)
    tags = Column(JSON, nullable=True)              # ["technical", "workshop"]
    venue = Column(String, nullable=True)
    poster_image_url = Column(String, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=True)
    seat_limit = Column(Integer, nullable=True)     # None = unlimited
    is_cancelled = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)
    qr_token = Column(String, nullable=True, unique=True)   # signed token for QR attendance

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    club = relationship("Club", back_populates="events")
    rsvps = relationship("EventRSVP", back_populates="event", cascade="all, delete-orphan")
    attendance_records = relationship("EventAttendance", back_populates="event", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="event", cascade="all, delete-orphan")
    photos = relationship("EventPhoto", back_populates="event", cascade="all, delete-orphan")
    feedback = relationship("EventFeedback", back_populates="event", cascade="all, delete-orphan")
    budget = relationship("Budget", back_populates="event", uselist=False)
    sponsors = relationship("Sponsor", back_populates="event")


class EventRSVP(Base):
    __tablename__ = "event_rsvps"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(RSVPStatus), default=RSVPStatus.confirmed)
    waitlist_position = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="rsvps")
    user = relationship("User", foreign_keys=[user_id], back_populates="rsvps")


class EventAttendance(Base):
    """Marked when a student scans the event QR code on the day."""
    __tablename__ = "event_attendance"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    marked_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="attendance_records")
    user = relationship("User", foreign_keys=[user_id], back_populates="attendance_records")


class EventPhoto(Base):
    __tablename__ = "event_photos"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    url = Column(String, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="photos")
    # explicit foreign_keys required — table has two FKs to users
    uploader = relationship("User", foreign_keys=[uploaded_by])


class EventFeedback(Base):
    __tablename__ = "event_feedback"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)        # 1-5
    comment = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="feedback")
    user = relationship("User", foreign_keys=[user_id])
