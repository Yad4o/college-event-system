from pydantic import BaseModel
from datetime import datetime


class AnnouncementCreate(BaseModel):
    title: str
    body: str
    is_pinned: bool = False


class AnnouncementUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    is_pinned: bool | None = None


class AnnouncementRead(BaseModel):
    id: int
    club_id: int | None  # None for platform-wide announcements
    title: str
    body: str
    is_pinned: bool
    created_at: datetime
    author_name: str | None = None  # populated by service layer

    model_config = {"from_attributes": True}
