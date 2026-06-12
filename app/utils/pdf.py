"""
PDF certificate rendering using Jinja2 + WeasyPrint.
"""

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML  # type: ignore

from app.config import settings

# Resolve template directory relative to this file:
# app/utils/pdf.py  →  ../templates/
_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=True,
)


def render_certificate_pdf(
    student_name: str,
    event_title: str,
    event_date: str,
    certificate_type: str,
    unique_code: str,
) -> bytes:
    """
    Render a certificate to PDF bytes.

    Parameters
    ----------
    student_name     Full name of the recipient.
    event_title      Title of the event.
    event_date       Human-readable date string, e.g. "14 June 2025".
    certificate_type One of: participation, volunteer, winner, organizer.
    unique_code      Short verification code stored on the Certificate row.

    Returns
    -------
    bytes  Raw PDF binary content ready for upload or file writing.
    """
    template = _jinja_env.get_template("certificate.html")
    html_content = template.render(
        student_name=student_name,
        event_title=event_title,
        event_date=event_date,
        certificate_type=certificate_type,
        unique_code=unique_code,
        app_name=settings.APP_NAME,
    )
    return HTML(string=html_content).write_pdf()
