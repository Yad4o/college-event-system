from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_users: int
    total_clubs: int
    active_clubs: int
    suspended_clubs: int
    total_events: int
    upcoming_events: int
    total_rsvps: int
    total_attendance: int
    total_certificates_issued: int


class BudgetReportItem(BaseModel):
    club_id: int
    club_name: str
    total_allocated: float
    total_spent: float

    model_config = {"from_attributes": True}


class UserRoleUpdate(BaseModel):
    role: str
