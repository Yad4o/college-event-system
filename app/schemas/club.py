from pydantic import BaseModel
from typing import Any
from datetime import datetime
from app.models.club import JoinType, ClubMemberRole, ClubApplicationStatus


class ClubCreate(BaseModel):
    name: str
    description: str | None = None
    domain: str | None = None
    join_type: JoinType = JoinType.open
    social_links: dict[str, Any] | None = None


class ClubRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    domain: str | None = None
    logo_url: str | None = None
    join_type: JoinType
    is_active: bool
    is_suspended: bool
    member_count: int = 0
    my_role: ClubMemberRole | None = None

    model_config = {"from_attributes": True}


class ClubUpdate(BaseModel):
    description: str | None = None
    domain: str | None = None
    logo_url: str | None = None
    social_links: dict[str, Any] | None = None
    join_type: JoinType | None = None


class MembershipRead(BaseModel):
    user_id: int
    club_id: int
    role: ClubMemberRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class JoinRequestRead(BaseModel):
    id: int
    applicant_id: int
    club_name: str
    status: ClubApplicationStatus
    created_at: datetime

    model_config = {"from_attributes": True}
