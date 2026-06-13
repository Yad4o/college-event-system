from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, AnnouncementRead, AnnouncementUpdate
from app.services import announcement_service
from app.utils.deps import get_current_user

router = APIRouter(tags=["Announcements"])


# ── Phase 27 — club-scoped announcements ─────────────────────────────────────

@router.get("/clubs/{club_id}/announcements", response_model=list[AnnouncementRead])
def list_club_announcements(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all published announcements for a club — members only, pinned first."""
    return announcement_service.get_club_announcements(db, club_id, current_user)


@router.post(
    "/clubs/{club_id}/announcements",
    response_model=AnnouncementRead,
    status_code=status.HTTP_201_CREATED,
)
def create_club_announcement(
    club_id: int,
    data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an announcement for a club — club president or college_admin only."""
    return announcement_service.create_announcement(db, club_id, data, current_user)


@router.patch(
    "/clubs/{club_id}/announcements/{ann_id}",
    response_model=AnnouncementRead,
)
def update_club_announcement(
    club_id: int,
    ann_id: int,
    data: AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a club announcement — club president or college_admin only."""
    return announcement_service.update_announcement(db, club_id, ann_id, data, current_user)


@router.delete(
    "/clubs/{club_id}/announcements/{ann_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_club_announcement(
    club_id: int,
    ann_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a club announcement — club president or college_admin only."""
    announcement_service.delete_announcement(db, club_id, ann_id, current_user)


# ── Phase 28 — platform-wide announcements ────────────────────────────────────

@router.get("/announcements/platform", response_model=list[AnnouncementRead])
def list_platform_announcements(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Read platform-wide announcements — any authenticated user."""
    return announcement_service.get_platform_announcements(db)


@router.post(
    "/announcements/platform",
    response_model=AnnouncementRead,
    status_code=status.HTTP_201_CREATED,
)
def create_platform_announcement(
    data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Post a platform-wide announcement — college_admin only."""
    return announcement_service.create_platform_announcement(db, data, current_user)
