from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Any
from app.models.event import EventType, RSVPStatus


class EventCreate(BaseModel):
    club_id: int
    title: str
    description: str | None = None
    event_type: EventType = EventType.open
    tags: list[str] | None = None
    venue: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    seat_limit: int | None = None
    is_hidden: bool = False
    is_approved: bool | None = None

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end_at and self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class EventRead(BaseModel):
    id: int
    club_id: int
    title: str
    description: str | None = None
    event_type: EventType
    tags: list[str] | None = None
    venue: str | None = None
    poster_image_url: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    seat_limit: int | None = None
    is_cancelled: bool
    is_hidden: bool
    is_approved: bool
    qr_token: str | None = None
    rsvp_count: int = 0
    waitlist_count: int = 0

    model_config = {"from_attributes": True}


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    venue: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    seat_limit: int | None = None
    is_hidden: bool | None = None
    is_approved: bool | None = None
    is_cancelled: bool | None = None
    tags: list[str] | None = None


class RsvpRead(BaseModel):
    id: int
    event_id: int
    user_id: int
    status: RSVPStatus
    waitlist_position: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
