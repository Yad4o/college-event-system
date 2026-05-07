import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class BudgetItemCategory(str, enum.Enum):
    venue = "venue"
    food = "food"
    printing = "printing"
    prizes = "prizes"
    logistics = "logistics"
    miscellaneous = "miscellaneous"


class Budget(Base):
    """One budget record per event (or per club for general funds)."""
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    # Either event-specific or club-level (one must be set, not both)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, unique=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    total_allocated = Column(Float, nullable=False, default=0.0)
    total_spent = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    event = relationship("Event", back_populates="budget")
    club = relationship("Club", back_populates="budgets")
    items = relationship("BudgetItem", back_populates="budget", cascade="all, delete-orphan")


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False, index=True)
    category = Column(Enum(BudgetItemCategory), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    receipt_url = Column(String, nullable=True)    # uploaded proof of expense
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    budget = relationship("Budget", back_populates="items")


class Sponsor(Base):
    __tablename__ = "sponsors"

    id = Column(Integer, primary_key=True, index=True)
    # Sponsors can be linked to a club (recurring) or a specific event (one-time)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    company_name = Column(String, nullable=False)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    amount_sponsored = Column(Float, nullable=True)
    logo_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    club = relationship("Club", back_populates="sponsors")
    event = relationship("Event", back_populates="sponsors")
