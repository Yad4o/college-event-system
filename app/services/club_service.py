"""
Club business logic.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.club import (
    Club, ClubMembership, ClubMemberRole, ClubJoinRequest,
    ClubApplicationStatus, JoinType,
)
from app.models.user import User, UserRole
from app.schemas.club import ClubCreate, ClubRead, ClubUpdate, MembershipRead, JoinRequestRead
from app.utils.club_repo import (
    get_club_by_id,
    get_clubs as _get_clubs,
    create_club as _create_club,
    get_member_count,
    get_membership,
    get_join_request,
    get_join_request_by_id,
    get_pending_join_requests,
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


def _assert_club_admin(db: Session, user: User, club_id: int) -> None:
    if user.role == UserRole.college_admin:
        return
    membership = get_membership(db, user.id, club_id)
    if not membership or membership.role != ClubMemberRole.president:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def get_clubs(db: Session, skip: int = 0, limit: int = 20, domain: str | None = None) -> list[ClubRead]:
    return [_to_read(db, c) for c in _get_clubs(db, skip=skip, limit=limit, domain=domain)]


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
    _assert_club_admin(db, current_user, club_id)
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


# ── Membership & Join Requests ────────────────────────────────────────────────

def join_club(db: Session, club_id: int, current_user: User):
    club = get_club_by_id(db, club_id)
    if not club or not club.is_active or club.is_suspended:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")

    if get_membership(db, current_user.id, club_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member")

    if club.join_type == JoinType.open:
        membership = ClubMembership(
            user_id=current_user.id,
            club_id=club_id,
            role=ClubMemberRole.member,
        )
        db.add(membership)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member")
        db.refresh(membership)
        return MembershipRead.model_validate(membership)

    else:  # invite_only — create join request
        existing = get_join_request(db, current_user.id, club_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Join request already submitted")
        req = ClubJoinRequest(user_id=current_user.id, club_id=club_id)
        db.add(req)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Join request already submitted")
        db.refresh(req)
        return JoinRequestRead.model_validate(req)


def list_join_requests(db: Session, club_id: int, current_user: User) -> list[JoinRequestRead]:
    _assert_club_admin(db, current_user, club_id)
    requests = get_pending_join_requests(db, club_id)
    return [JoinRequestRead.model_validate(r) for r in requests]


def decide_join_request(
    db: Session, club_id: int, request_id: int, decision: str, current_user: User
):
    _assert_club_admin(db, current_user, club_id)

    req = get_join_request_by_id(db, request_id)
    if not req or req.club_id != club_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Join request not found")
    if req.status != ClubApplicationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request already decided")

    if decision == "approved":
        req.status = ClubApplicationStatus.approved
        membership = ClubMembership(
            user_id=req.user_id,
            club_id=club_id,
            role=ClubMemberRole.member,
        )
        db.add(membership)
    elif decision == "rejected":
        req.status = ClubApplicationStatus.rejected
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="decision must be approved or rejected")

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member")

    db.refresh(req)
    return JoinRequestRead.model_validate(req)


def remove_member(db: Session, club_id: int, user_id: int, current_user: User) -> None:
    # club president can remove members; college_admin can remove anyone
    if current_user.role != UserRole.college_admin:
        _assert_club_admin(db, current_user, club_id)

    membership = get_membership(db, user_id, club_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Prevent removing the last president
    if membership.role == ClubMemberRole.president:
        president_count = (
            db.query(ClubMembership)
            .filter(
                ClubMembership.club_id == club_id,
                ClubMembership.role == ClubMemberRole.president,
            )
            .count()
        )
        if president_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last president",
            )

    db.delete(membership)
    db.commit()
