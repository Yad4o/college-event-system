from pydantic import BaseModel
from datetime import datetime
from app.models.club import ClubApplicationStatus


class NewClubApplicationCreate(BaseModel):
    club_name: str
    description: str | None = None
    domain: str | None = None
    faculty_advisor_email: str | None = None


class NewClubApplicationRead(BaseModel):
    id: int
    applicant_id: int
    club_name: str
    description: str | None = None
    domain: str | None = None
    faculty_advisor_email: str | None = None
    status: ClubApplicationStatus
    admin_remarks: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NewClubApplicationReview(BaseModel):
    decision: str          # "approved" or "rejected"
    admin_remarks: str | None = None
