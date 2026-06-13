from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.admin import BudgetReportItem, DashboardStats, UserRoleUpdate
from app.schemas.club import ClubRead
from app.schemas.auth import UserRead
from app.services import admin_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return admin_service.get_stats(db, current_user)


@router.get("/clubs", response_model=list[ClubRead])
def list_all_clubs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clubs = admin_service.get_all_clubs(db, current_user)
    from app.utils.club_repo import get_member_count
    result = []
    for c in clubs:
        count = get_member_count(db, c.id)
        read = ClubRead.model_validate(c)
        read.member_count = count
        result.append(read)
    return result


@router.patch("/clubs/{club_id}/suspend", response_model=ClubRead)
def toggle_suspension(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    club = admin_service.toggle_club_suspension(db, club_id, current_user)
    from app.utils.club_repo import get_member_count
    read = ClubRead.model_validate(club)
    read.member_count = get_member_count(db, club.id)
    return read


@router.get("/users", response_model=list[UserRead])
def list_all_users(
    role: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = admin_service.get_all_users(db, current_user, role, skip, limit)
    return [UserRead.model_validate(u) for u in users]


@router.patch("/users/{user_id}/role", response_model=UserRead)
def change_role(
    user_id: int,
    data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = admin_service.change_user_role(db, user_id, data.role, current_user)
    return UserRead.model_validate(user)


@router.get("/budget-report", response_model=list[BudgetReportItem])
def budget_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return admin_service.get_budget_report(db, current_user)
