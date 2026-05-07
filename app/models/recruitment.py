import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RecruitmentApplicationStatus(str, enum.Enum):
    applied = "applied"
    shortlisted = "shortlisted"
    rejected = "rejected"
    selected = "selected"


class RecruitmentDrive(Base):
    """A club's open recruitment window (e.g., Sem 1 2025 recruitment)."""
    __tablename__ = "recruitment_drives"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    # Roles they are recruiting for, e.g., ["core_member", "volunteer"]
    open_roles = Column(JSON, nullable=True)
    # Questions shown on the application form, e.g., ["Why do you want to join?"]
    form_questions = Column(JSON, nullable=True)
    opens_at = Column(DateTime(timezone=True), nullable=False)
    closes_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    club = relationship("Club", back_populates="recruitment_drives")
    applications = relationship("RecruitmentApplication", back_populates="drive", cascade="all, delete-orphan")


class RecruitmentApplication(Base):
    __tablename__ = "recruitment_applications"

    id = Column(Integer, primary_key=True, index=True)
    drive_id = Column(Integer, ForeignKey("recruitment_drives.id"), nullable=False, index=True)
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    desired_role = Column(String, nullable=True)
    # Answers to the form_questions in order, stored as JSON array of strings
    answers = Column(JSON, nullable=True)
    status = Column(Enum(RecruitmentApplicationStatus), default=RecruitmentApplicationStatus.applied)
    reviewer_notes = Column(Text, nullable=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    drive = relationship("RecruitmentDrive", back_populates="applications")
    applicant = relationship("User", back_populates="recruitment_applications")
