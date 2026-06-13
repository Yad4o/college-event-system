"""
Sponsor service — Phase 31.

Access rules
------------
- college_admin        : full CRUD on any sponsor
- club president       : CRUD on sponsors for their club / its events
- everyone else        : read-only (get_sponsors)

A sponsor must be linked to exactly one of event_id or club_id.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.budget import Sponsor
from app.models.club import ClubMembership, ClubMemberRole
from app.models.user import User, UserRole
from app.schemas.sponsor import SponsorCreate, SponsorRead, SponsorUpdate
from app.utils.club_repo import get_club_by_id
from app.utils.event_repo import get_event_by_id


# ── access helpers ────────────────────────────────────────────────────────────

def _resolve_club_id_for_sponsor(db: Session, sponsor: Sponsor) -> int:
    """Return the club that effectively owns this sponsorship."""
    if sponsor.club_id:
        return sponsor.club_id
    event = get_event_by_id(db, sponsor.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.club_id


def _assert_write_access(db: Session, user: User, club_id: int) -> None:
    """college_admin or club president may write."""
    if user.role == UserRole.college_admin:
        return
    mem = (
        db.query(ClubMembership)
        .filter(
            ClubMembership.user_id == user.id,
            ClubMembership.club_id == club_id,
            ClubMembership.role == ClubMemberRole.president,
        )
        .first()
    )
    if not mem:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the club president or college admin can manage sponsors",
        )


def _get_sponsor_or_404(db: Session, sponsor_id: int) -> Sponsor:
    s = db.get(Sponsor, sponsor_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sponsor not found")
    return s


# ── public API ────────────────────────────────────────────────────────────────

def add_sponsor(db: Session, data: SponsorCreate, current_user: User) -> SponsorRead:
    # Exactly one target
    if (data.event_id is None) == (data.club_id is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide exactly one of event_id or club_id",
        )

    # Validate target exists; derive club_id for access check
    if data.event_id:
        event = get_event_by_id(db, data.event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        owning_club_id = event.club_id
    else:
        club = get_club_by_id(db, data.club_id)
        if not club or club.is_suspended:
            raise HTTPException(status_code=404, detail="Club not found")
        owning_club_id = data.club_id

    _assert_write_access(db, current_user, owning_club_id)

    sponsor = Sponsor(
        company_name=data.company_name,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        amount_sponsored=data.amount_sponsored,
        logo_url=data.logo_url,
        notes=data.notes,
        event_id=data.event_id,
        club_id=data.club_id,
    )
    db.add(sponsor)
    db.commit()
    db.refresh(sponsor)
    return SponsorRead.model_validate(sponsor)


def get_sponsors(
    db: Session,
    event_id: int | None = None,
    club_id: int | None = None,
) -> list[SponsorRead]:
    """Public read — anyone authenticated can list sponsors."""
    q = db.query(Sponsor)
    if event_id is not None:
        q = q.filter(Sponsor.event_id == event_id)
    if club_id is not None:
        q = q.filter(Sponsor.club_id == club_id)
    return [SponsorRead.model_validate(s) for s in q.order_by(Sponsor.created_at.desc()).all()]


def update_sponsor(
    db: Session, sponsor_id: int, data: SponsorUpdate, current_user: User
) -> SponsorRead:
    sponsor = _get_sponsor_or_404(db, sponsor_id)
    owning_club_id = _resolve_club_id_for_sponsor(db, sponsor)
    _assert_write_access(db, current_user, owning_club_id)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(sponsor, field, value)

    db.commit()
    db.refresh(sponsor)
    return SponsorRead.model_validate(sponsor)


def delete_sponsor(db: Session, sponsor_id: int, current_user: User) -> None:
    sponsor = _get_sponsor_or_404(db, sponsor_id)
    owning_club_id = _resolve_club_id_for_sponsor(db, sponsor)
    _assert_write_access(db, current_user, owning_club_id)
    db.delete(sponsor)
    db.commit()

