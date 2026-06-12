"""
Badge business logic — create badge definitions, award badges to users.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.certificate import Badge, UserBadge
from app.models.user import User, UserRole
from app.schemas.badge import BadgeCreate, BadgeRead, UserBadgeRead
from app.utils.user_repo import get_user_by_id


def _require_admin_or_club_admin(user: User) -> None:
    if user.role not in (UserRole.college_admin, UserRole.club_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only club admins and college admins can award badges",
        )


# ── Badge definitions ─────────────────────────────────────────────────────────

def create_badge(db: Session, data: BadgeCreate, current_user: User) -> BadgeRead:
    """college_admin only — define a new badge."""
    if current_user.role != UserRole.college_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only college admins can create badge definitions",
        )
    badge = Badge(
        name=data.name,
        description=data.description,
        icon_url=data.icon_url,
        criteria_description=data.criteria,
    )
    db.add(badge)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A badge with that name already exists",
        )
    db.refresh(badge)
    return BadgeRead.model_validate(badge)


def list_badges(db: Session) -> list[BadgeRead]:
    badges = db.query(Badge).order_by(Badge.name).all()
    return [BadgeRead.model_validate(b) for b in badges]


# ── Awarding ──────────────────────────────────────────────────────────────────

def award_badge(
    db: Session,
    recipient_id: int,
    badge_id: int,
    current_user: User,
) -> UserBadgeRead:
    """club_admin or college_admin can award any badge to any user."""
    _require_admin_or_club_admin(current_user)

    recipient = get_user_by_id(db, recipient_id)
    if not recipient or not recipient.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    badge = db.get(Badge, badge_id)
    if not badge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Badge not found")

    # Prevent duplicate awards of the same badge to the same user
    existing = (
        db.query(UserBadge)
        .filter(UserBadge.user_id == recipient_id, UserBadge.badge_id == badge_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has this badge",
        )

    ub = UserBadge(user_id=recipient_id, badge_id=badge_id)
    db.add(ub)
    db.commit()
    db.refresh(ub)
    # Eagerly load badge for the response schema
    ub.badge  # noqa: B018 — trigger lazy load before session close
    return _ub_to_read(ub)


def get_my_badges(db: Session, current_user: User) -> list[UserBadgeRead]:
    rows = (
        db.query(UserBadge)
        .filter(UserBadge.user_id == current_user.id)
        .order_by(UserBadge.awarded_at.desc())
        .all()
    )
    return [_ub_to_read(r) for r in rows]


# ── helpers ───────────────────────────────────────────────────────────────────

def _ub_to_read(ub: UserBadge) -> UserBadgeRead:
    return UserBadgeRead(
        badge=BadgeRead.model_validate(ub.badge),
        awarded_at=ub.awarded_at,
        awarded_by_id=None,  # model has no awarded_by column; kept for API compat
    )
