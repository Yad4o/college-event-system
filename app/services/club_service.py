"""
Club business logic.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.club import Club, ClubMembership, ClubMemberRole, ClubApplicationStatus
from app.models.user import User, UserRole
from app.schemas.club import ClubCreate, ClubRead, ClubUpdate
from app.utils.club_repo import (
    get_club_by_id,
    get_clubs as _get_clubs,
    create_club as _create_club,
    get_member_count,
    is_member,
    get_membership,
)


def _to_read(db: Session, club: Club) -> ClubRead:
    count = get_member_count(db, club.id)
    return ClubRead(
        id=club.id,
        name=club.name,
        description=club.description,
        domain=club.domain,
        logo_url=club.logo_url,
        join_type=club.join_type,
        is_active=club.is_active,
        is_suspended=club.is_suspended,
        member_count=count,
    )


def get_clubs(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    domain: str | None = None,
) -> list[ClubRead]:
    clubs = _get_clubs(db, skip=skip, limit=limit, domain=domain)
    return [_to_read(db, c) for c in clubs]


def get_club(db: Session, club_id: int) -> ClubRead:
    club = get_club_by_id(db, club_id)
    if not club or not club.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")
    return _to_read(db, club)


def create_club(db: Session, data: ClubCreate, current_user: User) -> ClubRead:
    if current_user.role != UserRole.college_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    club = _create_club(db, data, current_user.id)
    return _to_read(db, club)


def update_club(db: Session, club_id: int, data: ClubUpdate, current_user: User) -> ClubRead:
    club = get_club_by_id(db, club_id)
    if not club or not club.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")

    # club_admin (president) of this club OR college_admin
    if current_user.role != UserRole.college_admin:
        membership = get_membership(db, current_user.id, club_id)
        if not membership or membership.role != ClubMemberRole.president:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(club, field, value)
    db.commit()
    db.refresh(club)
    return _to_read(db, club)


def suspend_club(db: Session, club_id: int, current_user: User) -> ClubRead:
    if current_user.role != UserRole.college_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    club = get_club_by_id(db, club_id)
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")
    club.is_suspended = not club.is_suspended
    db.commit()
    db.refresh(club)
    return _to_read(db, club)


def delete_club(db: Session, club_id: int, current_user: User) -> None:
    if current_user.role != UserRole.college_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    club = get_club_by_id(db, club_id)
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")
    club.is_active = False
    db.commit()
