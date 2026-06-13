from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.sponsor import SponsorCreate, SponsorRead, SponsorUpdate
from app.services import sponsor_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/sponsors", tags=["Sponsors"])


@router.post("", response_model=SponsorRead, status_code=status.HTTP_201_CREATED)
def add_sponsor(
    data: SponsorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a sponsor to an event or a club.
    Provide exactly one of event_id or club_id.
    Club president or college_admin only.
    """
    return sponsor_service.add_sponsor(db, data, current_user)


@router.get("", response_model=list[SponsorRead])
def list_sponsors(
    event_id: int | None = None,
    club_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List sponsors, optionally filtered by event_id and/or club_id.
    Accessible to all authenticated users.
    """
    return sponsor_service.get_sponsors(db, event_id=event_id, club_id=club_id)


@router.patch("/{sponsor_id}", response_model=SponsorRead)
def update_sponsor(
    sponsor_id: int,
    data: SponsorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update sponsor details. Club president or college_admin only."""
    return sponsor_service.update_sponsor(db, sponsor_id, data, current_user)


@router.delete("/{sponsor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sponsor(
    sponsor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a sponsor. Club president or college_admin only."""
    sponsor_service.delete_sponsor(db, sponsor_id, current_user)

