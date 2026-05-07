import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    club_admin = "club_admin"
    faculty_advisor = "faculty_advisor"
    college_admin = "college_admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)

    # Student-specific profile fields
    branch = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)        # comma-separated
    profile_picture = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    email_verify_token = Column(String, nullable=True)
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    memberships = relationship("ClubMembership", back_populates="user", cascade="all, delete-orphan")
    club_applications = relationship("ClubApplication", back_populates="applicant", cascade="all, delete-orphan")
    rsvps = relationship("EventRSVP", back_populates="user", cascade="all, delete-orphan")
    attendance_records = relationship("EventAttendance", back_populates="user", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    recruitment_applications = relationship("RecruitmentApplication", back_populates="applicant", cascade="all, delete-orphan")
