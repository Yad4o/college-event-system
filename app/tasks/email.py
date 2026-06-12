"""
Celery tasks for transactional emails.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.worker import celery_app
from app.config import settings


def _send_smtp(to: str, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAILS_FROM_EMAIL
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAILS_FROM_EMAIL, to, msg.as_string())


@celery_app.task(name="tasks.send_verification_email", bind=True, max_retries=3)
def send_verification_email(self, to: str, token: str) -> None:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    html = f"""
    <p>Hi,</p>
    <p>Please verify your {settings.APP_NAME} account by clicking the link below:</p>
    <p><a href="{verify_url}">{verify_url}</a></p>
    <p>This link does not expire until you register again.</p>
    """
    try:
        _send_smtp(to, f"Verify your {settings.APP_NAME} account", html)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.send_password_reset_email", bind=True, max_retries=3)
def send_password_reset_email(self, to: str, token: str) -> None:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    html = f"""
    <p>Hi,</p>
    <p>A password reset was requested for your {settings.APP_NAME} account.</p>
    <p><a href="{reset_url}">Reset your password</a></p>
    <p>This link expires in 1 hour. If you did not request this, ignore this email.</p>
    """
    try:
        _send_smtp(to, f"Reset your {settings.APP_NAME} password", html)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.send_waitlist_promotion_email", bind=True, max_retries=3)
def send_waitlist_promotion_email(self, to: str, event_title: str, event_id: int) -> None:
    """Notify a waitlisted user that they have been promoted to confirmed."""
    event_url = f"{settings.FRONTEND_URL}/events/{event_id}"
    html = f"""
    <p>Great news!</p>
    <p>A spot has opened up for <strong>{event_title}</strong> and your RSVP has been
    confirmed. You are now registered to attend.</p>
    <p><a href="{event_url}">View event details</a></p>
    """
    try:
        _send_smtp(to, f"You're in! Your RSVP for {event_title} is confirmed", html)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
