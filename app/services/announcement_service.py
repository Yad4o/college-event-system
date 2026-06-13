"""
Announcement service — covers Phase 27 (club) and Phase 28 (platform-wide).

Club announcements:
  - get_club_announcements   — members only; pinned first
  - create_announcement      — club president only
  - update_announcement      — club president only
  - delete_announcement      — club president only

Platform-wide announcements (club_id IS NULL):
  - get_platform_announcements — any authenticated user
  - create_platform_announcement — college_admin only

Phase 32 addition:
  - create_announcement notifies all club members of the new post.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.announcement import Announcement
from app.models.club import ClubMembership, ClubMemberRole
from app.models.user import User, UserRole
from app.schemas.announcement import AnnouncementCreate, AnnouncementRead, AnnouncementUpdate
from app.utils.club_repo import get_club_by_id, is_member


# ── internal helpers ──────────────────────────────────────────────────────────

def _to_read(ann: Announcement) -> AnnouncementRead:
    return AnnouncementRead(
        id=ann.id,
        club_id=ann.club_id,
        title=ann.title,
        body=ann.body,
        is_pinned=ann.is_pinned,
        created_at=ann.created_at,
        author_name=ann.author.full_name if ann.author else None,
    )


def _assert_club_exists(db: Session, club_id: int):
    club = get_club_by_id(db, club_id)
    if not club or club.is_suspended:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")
    return club


def _assert_president(db: Session, user: User, club_id: int) -> None:
    """Allow college_admin or the club's president."""
    if user.role == UserRole.college_admin:
        return
    membership = (
        db.query(ClubMembership)
        .filter(
            ClubMembership.user_id == user.id,
            ClubMembership.club_id == club_id,
            ClubMembership.role == ClubMemberRole.president,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the club president or college admin can manage announcements",
        )


def _get_own_announcement(db: Session, ann_id: int, club_id: int) -> Announcement:
    ann = (
        db.query(Announcement)
        .filter(Announcement.id == ann_id, Announcement.club_id == club_id)
        .first()
    )
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    return ann


# ── Phase 27 — club announcements ─────────────────────────────────────────────

def get_club_announcements(
    db: Session, club_id: int, current_user: User
) -> list[AnnouncementRead]:
    _assert_club_exists(db, club_id)

    if not is_member(db, current_user.id, club_id) and current_user.role != UserRole.college_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this club to view its announcements",
        )

    rows = (
        db.query(Announcement)
        .filter(Announcement.club_id == club_id, Announcement.is_published == True)
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
        .all()
    )
    return [_to_read(r) for r in rows]


def create_announcement(
    db: Session, club_id: int, data: AnnouncementCreate, current_user: User
) -> AnnouncementRead:
    club = _assert_club_exists(db, club_id)
    _assert_president(db, current_user, club_id)

    ann = Announcement(
        club_id=club_id,
        author_id=current_user.id,
        title=data.title,
        body=data.body,
        is_pinned=data.is_pinned,
    )
    db.add(ann)
    db.flush()  # get ann.id; flush so notifications are in same transaction

    # Phase 32 — notify all club members of the new announcement
    try:
        member_ids = [
            row.user_id
            for row in db.query(ClubMembership.user_id)
            .filter(ClubMembership.club_id == club_id)
            .all()
            if row.user_id != current_user.id  # no self-notification
        ]
        if member_ids:
            from app.services.notification_service import notify_club_announcement
            notify_club_announcement(db, member_ids, club.name, data.title, club_id)
    except Exception:
        pass  # notification failure must never abort the announcement creation

    db.commit()
    db.refresh(ann)
    return _to_read(ann)


def update_announcement(
    db: Session, club_id: int, ann_id: int, data: AnnouncementUpdate, current_user: User
) -> AnnouncementRead:
    _assert_club_exists(db, club_id)
    _assert_president(db, current_user, club_id)
    ann = _get_own_announcement(db, ann_id, club_id)

    if data.title is not None:
        ann.title = data.title
    if data.body is not None:
        ann.body = data.body
    if data.is_pinned is not None:
        ann.is_pinned = data.is_pinned

    db.commit()
    db.refresh(ann)
    return _to_read(ann)


def delete_announcement(
    db: Session, club_id: int, ann_id: int, current_user: User
) -> None:
    _assert_club_exists(db, club_id)
    _assert_president(db, current_user, club_id)
    ann = _get_own_announcement(db, ann_id, club_id)
    db.delete(ann)
    db.commit()


# ── Phase 28 — platform-wide announcements ────────────────────────────────────

def get_platform_announcements(db: Session) -> list[AnnouncementRead]:
    """Any authenticated user can read platform announcements."""
    rows = (
        db.query(Announcement)
        .filter(Announcement.club_id == None, Announcement.is_published == True)  # noqa: E711
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
        .all()
    )
    return [_to_read(r) for r in rows]


def create_platform_announcement(
    db: Session, data: AnnouncementCreate, current_user: User
) -> AnnouncementRead:
    if current_user.role != UserRole.college_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only college admins can post platform-wide announcements",
        )

    ann = Announcement(
        club_id=None,
        author_id=current_user.id,
        title=data.title,
        body=data.body,
        is_pinned=data.is_pinned,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return _to_read(ann)
