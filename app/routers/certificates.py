from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.certificate import CertificateType
from app.models.user import User
from app.schemas.certificate import CertificateIssueRequest, CertificateRead
from app.services import certificate_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.post("/issue", status_code=status.HTTP_202_ACCEPTED)
def issue_certificates(
    body: CertificateIssueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bulk-issue certificates for every attendee of an event.
    Club admin / college admin only.
    Returns the number of certificates queued for PDF generation.
    """
    count = certificate_service.issue_for_event(
        db, body.event_id, body.certificate_type, current_user
    )
    return {"queued": count, "detail": f"{count} certificate(s) queued for generation"}


@router.get("/verify/{unique_code}", response_model=CertificateRead)
def verify_certificate(unique_code: str, db: Session = Depends(get_db)):
    """
    Public endpoint — verify a certificate by its unique code.
    No authentication required.
    """
    return certificate_service.verify_certificate(db, unique_code)


@router.get("/me", response_model=list[CertificateRead])
def my_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all certificates earned by the current user."""
    return certificate_service.get_my_certificates(db, current_user)


@router.get("/events/{event_id}", response_model=list[CertificateRead])
def event_certificates(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all certificates issued for an event — club admin / college admin only."""
    return certificate_service.get_event_certificates(db, event_id, current_user)
