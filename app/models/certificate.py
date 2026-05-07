import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CertificateType(str, enum.Enum):
    participation = "participation"
    volunteer = "volunteer"
    winner = "winner"
    organizer = "organizer"


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    certificate_type = Column(Enum(CertificateType), default=CertificateType.participation, nullable=False)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    pdf_url = Column(String, nullable=True)          # Cloudinary or local path after generation
    unique_code = Column(String, unique=True, nullable=True)  # for verification URL

    event = relationship("Event", back_populates="certificates")
    user = relationship("User", back_populates="certificates")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(String, nullable=True)
    # Criteria stored as plain text description; actual awarding logic lives in the service layer
    criteria_description = Column(Text, nullable=True)

    user_badges = relationship("UserBadge", back_populates="badge")


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    awarded_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="user_badges")
