from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.badge import BadgeCreate, BadgeRead, UserBadgeRead
from app.services import badge_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/badges", tags=["Badges"])


@router.post("", response_model=BadgeRead, status_code=status.HTTP_201_CREATED)
def create_badge(
    data: BadgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new badge definition — college_admin only."""
    return badge_service.create_badge(db, data, current_user)


@router.get("", response_model=list[BadgeRead])
def list_badges(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all badge definitions (any authenticated user)."""
    return badge_service.list_badges(db)


@router.post("/users/{user_id}", response_model=UserBadgeRead, status_code=status.HTTP_201_CREATED)
def award_badge(
    user_id: int,
    badge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Award a badge to a user.
    Requires club_admin or college_admin role.
    Pass the badge to award as a query parameter: ?badge_id=<id>
    """
    return badge_service.award_badge(db, user_id, badge_id, current_user)


@router.get("/me", response_model=list[UserBadgeRead])
def my_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all badges earned by the current user."""
    return badge_service.get_my_badges(db, current_user)
