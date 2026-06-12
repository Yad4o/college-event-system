from pydantic import BaseModel
from datetime import datetime


class BadgeCreate(BaseModel):
    name: str
    description: str | None = None
    icon_url: str | None = None
    criteria: str | None = None  # human-readable criteria description


class BadgeRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    icon_url: str | None = None

    model_config = {"from_attributes": True}


class UserBadgeRead(BaseModel):
    badge: BadgeRead
    awarded_at: datetime
    awarded_by_id: int | None = None  # id of the user who awarded it

    model_config = {"from_attributes": True}
