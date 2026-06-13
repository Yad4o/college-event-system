from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    # NULL  → platform-wide announcement (college_admin only, Phase 28)
    # set   → club-scoped announcement   (club president, Phase 27)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_pinned = Column(Boolean, default=False)
    is_published = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    club = relationship("Club", back_populates="announcements", foreign_keys=[club_id])
    author = relationship("User")
