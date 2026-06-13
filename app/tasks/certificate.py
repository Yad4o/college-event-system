"""
Celery task: generate a PDF certificate and upload it to Cloudinary.
Phase 32: notify the user in-app once the PDF is available.
"""

import secrets
from datetime import timezone

from app.worker import celery_app


@celery_app.task(name="tasks.generate_certificate_pdf", bind=True, max_retries=3)
def generate_certificate_pdf(self, certificate_id: int) -> None:
    """
    1. Load Certificate + related User + Event from DB.
    2. Render PDF with WeasyPrint.
    3. Upload to Cloudinary (folder: certificates/).
    4. Persist the secure URL back to the Certificate row.
    5. (Phase 32) Create an in-app notification for the user.
    """
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models.certificate import Certificate
    from app.utils.pdf import render_certificate_pdf

    db: Session = SessionLocal()
    try:
        cert = db.get(Certificate, certificate_id)
        if not cert:
            return  # already deleted or never created

        user = cert.user
        event = cert.event

        event_date = event.start_at.astimezone(timezone.utc).strftime("%-d %B %Y")

        pdf_bytes = render_certificate_pdf(
            student_name=user.full_name,
            event_title=event.title,
            event_date=event_date,
            certificate_type=cert.certificate_type.value,
            unique_code=cert.unique_code or secrets.token_urlsafe(12),
        )

        # Upload to Cloudinary
        try:
            import cloudinary.uploader  # type: ignore

            result = cloudinary.uploader.upload(
                pdf_bytes,
                folder="certificates",
                public_id=f"cert_{certificate_id}",
                resource_type="raw",
                format="pdf",
            )
            cert.pdf_url = result.get("secure_url")
        except Exception as upload_err:
            import logging
            logging.getLogger(__name__).warning(
                "Cloudinary upload failed for cert %s: %s", certificate_id, upload_err
            )

        # Phase 32 — in-app notification now that the PDF URL is set
        try:
            from app.services.notification_service import notify_certificate_ready
            notify_certificate_ready(db, user.id, event.title, cert.unique_code)
        except Exception:
            pass  # notification failure must never abort the task

        db.commit()
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
