from pydantic import BaseModel, model_validator
from datetime import datetime
from app.models.recruitment import RecruitmentApplicationStatus


class DriveCreate(BaseModel):
    title: str
    description: str | None = None
    open_roles: list[str] = []
    # Each entry is a plain question string, e.g. "Why do you want to join?"
    form_questions: list[str] = []
    opens_at: datetime
    closes_at: datetime

    @model_validator(mode="after")
    def closes_after_opens(self):
        if self.closes_at <= self.opens_at:
            raise ValueError("closes_at must be after opens_at")
        return self


class DriveUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    open_roles: list[str] | None = None
    form_questions: list[str] | None = None
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    is_active: bool | None = None


class DriveRead(BaseModel):
    id: int
    club_id: int
    title: str
    description: str | None = None
    open_roles: list[str]
    form_questions: list[str]
    opens_at: datetime
    closes_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class ApplicationCreate(BaseModel):
    desired_role: str | None = None
    # One answer string per question, in the same order as form_questions
    answers: list[str] = []


class ApplicationRead(BaseModel):
    id: int
    drive_id: int
    applicant_id: int
    desired_role: str | None = None
    answers: list[str]
    status: RecruitmentApplicationStatus
    applied_at: datetime

    model_config = {"from_attributes": True}


class ApplicationStatusUpdate(BaseModel):
    status: RecruitmentApplicationStatus
    reviewer_notes: str | None = None
