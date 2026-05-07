import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class JoinType(str, enum.Enum):
    open = "open"           # anyone can join
    invite_only = "invite_only"


class ClubMemberRole(str, enum.Enum):
    president = "president"
    vice_president = "vice_president"
    core_member = "core_member"
    volunteer = "volunteer"
    member = "member"


class ClubApplicationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    domain = Column(String, nullable=True)          # technical, cultural, sports, etc.
    logo_url = Column(String, nullable=True)
    social_links = Column(JSON, nullable=True)       # {"instagram": "...", "linkedin": "..."}
    join_type = Column(Enum(JoinType), default=JoinType.open, nullable=False)
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    faculty_advisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    memberships = relationship("ClubMembership", back_populates="club", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="club", cascade="all, delete-orphan")
    announcements = relationship("Announcement", back_populates="club", cascade="all, delete-orphan")
    recruitment_drives = relationship("RecruitmentDrive", back_populates="club", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="club", cascade="all, delete-orphan")
    sponsors = relationship("Sponsor", back_populates="club")


class ClubMembership(Base):
    __tablename__ = "club_memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False, index=True)
    role = Column(Enum(ClubMemberRole), default=ClubMemberRole.member, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="memberships")
    club = relationship("Club", back_populates="memberships")


class ClubApplication(Base):
    """A student's request to register a brand-new club."""
    __tablename__ = "club_applications"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    club_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String, nullable=True)
    faculty_advisor_email = Column(String, nullable=True)
    status = Column(Enum(ClubApplicationStatus), default=ClubApplicationStatus.pending)
    admin_remarks = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    applicant = relationship("User", foreign_keys=[applicant_id], back_populates="club_applications")
