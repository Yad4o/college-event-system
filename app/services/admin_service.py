from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.certificate import Certificate
from app.models.club import Club, ClubMembership
from app.models.event import Event, EventAttendance, EventRSVP
from app.models.user import User, UserRole
from app.schemas.admin import BudgetReportItem, DashboardStats


def _now():
    return datetime.now(timezone.utc)


def _assert_admin(user: User) -> None:
    if user.role != UserRole.college_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="college_admin only")


# ── Phase 35 ──────────────────────────────────────────────────────────────────

def get_stats(db: Session, current_user: User) -> DashboardStats:
    _assert_admin(current_user)
    now = _now()

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_clubs = db.query(func.count(Club.id)).scalar() or 0
    active_clubs = db.query(func.count(Club.id)).filter(
        Club.is_active == True, Club.is_suspended == False
    ).scalar() or 0
    suspended_clubs = db.query(func.count(Club.id)).filter(Club.is_suspended == True).scalar() or 0
    total_events = db.query(func.count(Event.id)).scalar() or 0
    upcoming_events = db.query(func.count(Event.id)).filter(
        Event.start_at > now, Event.is_cancelled == False
    ).scalar() or 0
    total_rsvps = db.query(func.count(EventRSVP.id)).scalar() or 0
    total_attendance = db.query(func.count(EventAttendance.id)).scalar() or 0
    total_certificates_issued = db.query(func.count(Certificate.id)).scalar() or 0

    return DashboardStats(
        total_users=total_users,
        total_clubs=total_clubs,
        active_clubs=active_clubs,
        suspended_clubs=suspended_clubs,
        total_events=total_events,
        upcoming_events=upcoming_events,
        total_rsvps=total_rsvps,
        total_attendance=total_attendance,
        total_certificates_issued=total_certificates_issued,
    )


# ── Phase 36 ──────────────────────────────────────────────────────────────────

def get_all_clubs(db: Session, current_user: User) -> list[Club]:
    _assert_admin(current_user)
    return db.query(Club).order_by(Club.name.asc()).all()


def toggle_club_suspension(db: Session, club_id: int, current_user: User) -> Club:
    _assert_admin(current_user)
    club = db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    club.is_suspended = not club.is_suspended
    db.commit()
    db.refresh(club)
    return club


def get_all_users(
    db: Session, current_user: User, role: str | None, skip: int, limit: int
) -> list[User]:
    _assert_admin(current_user)
    q = db.query(User)
    if role:
        try:
            q = q.filter(User.role == UserRole(role))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid role: {role}")
    return q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()


def change_user_role(db: Session, user_id: int, new_role: str, current_user: User) -> User:
    _assert_admin(current_user)
    try:
        role_enum = UserRole(new_role)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid role: {new_role}")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent demoting the last college_admin
    if user.role == UserRole.college_admin and role_enum != UserRole.college_admin:
        admin_count = db.query(func.count(User.id)).filter(
            User.role == UserRole.college_admin
        ).scalar() or 0
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last college_admin",
            )

    user.role = role_enum
    db.commit()
    db.refresh(user)
    return user


def get_budget_report(db: Session, current_user: User) -> list[BudgetReportItem]:
    _assert_admin(current_user)
    rows = (
        db.query(
            Club.id.label("club_id"),
            Club.name.label("club_name"),
            func.coalesce(func.sum(Budget.total_allocated), 0.0).label("total_allocated"),
            func.coalesce(func.sum(Budget.total_spent), 0.0).label("total_spent"),
        )
        .outerjoin(Budget, Budget.club_id == Club.id)
        .group_by(Club.id, Club.name)
        .order_by(Club.name.asc())
        .all()
    )
    return [
        BudgetReportItem(
            club_id=r.club_id,
            club_name=r.club_name,
            total_allocated=round(r.total_allocated, 2),
            total_spent=round(r.total_spent, 2),
        )
        for r in rows
    ]
