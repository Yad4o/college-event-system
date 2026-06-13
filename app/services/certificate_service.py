"""
Certificate issuance service.

Phase 25 logic:
  - issue_for_event  — bulk-issue certs for all attendees of an event
  - verify_certificate — public lookup by unique_code
  - get_my_certificates — current user's cert list
  - get_event_certificates — club admin view of all certs for an event

Phase 32 addition:
  - notify_certificate_ready called from the Celery task (app/tasks/certificate.py)
    after the PDF is uploaded, so the hook lives there — not here — to keep the
    service free of async task coupling.
"""

import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.certificate import Certificate, CertificateType
from app.models.club import ClubMembership, ClubMemberRole
from app.models.event import EventAttendance
from app.models.user import User, UserRole
from app.schemas.certificate import CertificateRead
from app.utils.event_repo import get_event_by_id


# ── internal helpers ──────────────────────────────────────────────────────────

def _assert_club_admin(db: Session, user: User, club_id: int) -> None:
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
            detail="Only the club president or college admin can issue certificates",
        )


# ── public API ────────────────────────────────────────────────────────────────

def issue_for_event(
    db: Session,
    event_id: int,
    cert_type: CertificateType,
    current_user: User,
) -> int:
    """
    Bulk-issue certificates for every attendee of *event_id*.

    - Skips users who already have a certificate of the same type for this event.
    - Dispatches a Celery task per new certificate to render + upload the PDF.
      The task calls notify_certificate_ready after successful upload (Phase 32).
    - Returns the count of newly created certificates.
    """
    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    _assert_club_admin(db, current_user, event.club_id)

    attendance_rows = (
        db.query(EventAttendance)
        .filter(EventAttendance.event_id == event_id)
        .all()
    )
    if not attendance_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No attendance records found for this event",
        )

    created = 0
    for row in attendance_rows:
        existing = (
            db.query(Certificate)
            .filter(
                Certificate.event_id == event_id,
                Certificate.user_id == row.user_id,
                Certificate.certificate_type == cert_type,
            )
            .first()
        )
        if existing:
            continue  # already issued — skip

        unique_code = secrets.token_urlsafe(12)
        cert = Certificate(
            event_id=event_id,
            user_id=row.user_id,
            certificate_type=cert_type,
            unique_code=unique_code,
            pdf_url=None,  # filled in by the Celery task
        )
        db.add(cert)
        db.flush()  # get cert.id before dispatching task

        try:
            from app.tasks.certificate import generate_certificate_pdf
            generate_certificate_pdf.delay(cert.id)
        except Exception:
            pass  # task dispatch failure must not abort the DB transaction

        created += 1

    db.commit()
    return created


def verify_certificate(db: Session, unique_code: str) -> CertificateRead:
    """Public endpoint — anyone can look up a certificate by its unique_code."""
    cert = (
        db.query(Certificate)
        .filter(Certificate.unique_code == unique_code)
        .first()
    )
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )
    return CertificateRead.model_validate(cert)


def get_my_certificates(db: Session, current_user: User) -> list[CertificateRead]:
    certs = (
        db.query(Certificate)
        .filter(Certificate.user_id == current_user.id)
        .order_by(Certificate.issued_at.desc())
        .all()
    )
    return [CertificateRead.model_validate(c) for c in certs]


def get_event_certificates(
    db: Session, event_id: int, current_user: User
) -> list[CertificateRead]:
    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    _assert_club_admin(db, current_user, event.club_id)

    certs = (
        db.query(Certificate)
        .filter(Certificate.event_id == event_id)
        .order_by(Certificate.issued_at.asc())
        .all()
    )
    return [CertificateRead.model_validate(c) for c in certs]
