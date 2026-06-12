from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.club_application import (
    NewClubApplicationCreate,
    NewClubApplicationRead,
    NewClubApplicationReview,
)
from app.services import club_application_service as svc
from app.utils.deps import get_current_user

router = APIRouter(prefix="/club-applications", tags=["Club Applications"])


@router.post("", response_model=NewClubApplicationRead, status_code=201)
def apply(
    data: NewClubApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Any authenticated user can apply to register a new club."""
    return svc.apply_new_club(db, data, current_user)


@router.get("", response_model=list[NewClubApplicationRead])
def list_applications(
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all club applications (college_admin only). Filter by ?status=pending|approved|rejected."""
    return svc.list_applications(db, current_user, status_filter=status)


@router.patch("/{app_id}", response_model=NewClubApplicationRead)
def review(
    app_id: int,
    body: NewClubApplicationReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve or reject a club application (college_admin only)."""
    return svc.review_application(db, app_id, body, current_user)
