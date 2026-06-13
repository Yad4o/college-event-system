from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.recruitment import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStatusUpdate,
    DriveCreate,
    DriveRead,
    DriveUpdate,
)
from app.services import recruitment_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/clubs/{club_id}/recruitment", tags=["Recruitment"])


# ── Drives ─────────────────────────────────────────────────────────────────────

@router.post("/drives", response_model=DriveRead, status_code=status.HTTP_201_CREATED)
def create_drive(
    club_id: int,
    data: DriveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a recruitment drive — club president or college_admin only."""
    return recruitment_service.create_drive(db, club_id, data, current_user)


@router.get("/drives", response_model=list[DriveRead])
def list_drives(
    club_id: int,
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all recruitment drives for a club (any authenticated user)."""
    return recruitment_service.get_drives(db, club_id, active_only)


@router.get("/drives/{drive_id}", response_model=DriveRead)
def get_drive(
    club_id: int,
    drive_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get a single recruitment drive."""
    return recruitment_service.get_drive(db, drive_id)


@router.patch("/drives/{drive_id}", response_model=DriveRead)
def update_drive(
    club_id: int,
    drive_id: int,
    data: DriveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a recruitment drive — club president or college_admin only."""
    return recruitment_service.update_drive(db, drive_id, data, current_user)


@router.post("/drives/{drive_id}/close", response_model=DriveRead)
def close_drive(
    club_id: int,
    drive_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Close a recruitment drive — club president or college_admin only."""
    return recruitment_service.close_drive(db, drive_id, current_user)


# ── Applications ───────────────────────────────────────────────────────────────

@router.post(
    "/drives/{drive_id}/apply",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def apply(
    club_id: int,
    drive_id: int,
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit an application for a recruitment drive.
    The window must currently be open (opens_at <= now <= closes_at).
    """
    return recruitment_service.apply(db, drive_id, data, current_user)


@router.get("/drives/{drive_id}/applications", response_model=list[ApplicationRead])
def list_applications(
    club_id: int,
    drive_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List applications for a drive.
    Club president / college_admin sees all; students see only their own.
    """
    return recruitment_service.get_applications(db, drive_id, current_user)


@router.patch(
    "/drives/{drive_id}/applications/{app_id}",
    response_model=ApplicationRead,
)
def update_application_status(
    club_id: int,
    drive_id: int,
    app_id: int,
    data: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the status of an application (shortlisted / selected / rejected).
    Club president or college_admin only.
    """
    return recruitment_service.update_application_status(
        db, drive_id, app_id, data, current_user
    )
