from pydantic import BaseModel
from datetime import datetime


class SponsorCreate(BaseModel):
    company_name: str
    contact_name: str | None = None
    contact_email: str | None = None
    amount_sponsored: float | None = None
    logo_url: str | None = None
    notes: str | None = None
    # Exactly one of event_id or club_id must be provided
    event_id: int | None = None
    club_id: int | None = None


class SponsorUpdate(BaseModel):
    company_name: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    amount_sponsored: float | None = None
    logo_url: str | None = None
    notes: str | None = None


class SponsorRead(BaseModel):
    id: int
    company_name: str
    contact_name: str | None = None
    contact_email: str | None = None
    amount_sponsored: float | None = None
    logo_url: str | None = None
    notes: str | None = None
    event_id: int | None = None
    club_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

