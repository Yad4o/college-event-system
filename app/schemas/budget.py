from pydantic import BaseModel, model_validator
from datetime import datetime
from app.models.budget import BudgetItemCategory


class BudgetCreate(BaseModel):
    total_allocated: float
    notes: str | None = None
    # Exactly one of event_id or club_id must be supplied
    event_id: int | None = None
    club_id: int | None = None

    @model_validator(mode="after")
    def exactly_one_target(self):
        if (self.event_id is None) == (self.club_id is None):
            raise ValueError("Provide exactly one of event_id or club_id, not both or neither")
        return self


class BudgetUpdate(BaseModel):
    total_allocated: float | None = None
    notes: str | None = None


class BudgetItemCreate(BaseModel):
    category: BudgetItemCategory
    description: str
    amount: float
    receipt_url: str | None = None  # pre-signed Cloudinary URL uploaded by client


class BudgetItemUpdate(BaseModel):
    category: BudgetItemCategory | None = None
    description: str | None = None
    amount: float | None = None
    receipt_url: str | None = None


class BudgetItemRead(BaseModel):
    id: int
    category: BudgetItemCategory
    description: str
    amount: float
    receipt_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BudgetRead(BaseModel):
    id: int
    event_id: int | None = None
    club_id: int | None = None
    total_allocated: float
    total_spent: float          # kept in sync by the service layer
    notes: str | None = None
    items: list[BudgetItemRead] = []
    created_at: datetime

    model_config = {"from_attributes": True}
