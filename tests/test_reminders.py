"""
Tests for Phase 22 — send_event_reminders Celery task.

Strategy: call the task function synchronously (no broker needed) with
unittest.mock to intercept send_reminder_email.delay, then assert the
right calls were made.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, call

import pytest
from passlib.context import CryptContext

from app.models.club import Club, ClubMembership, ClubMemberRole, JoinType
from app.models.event import Event, EventRSVP, RSVPStatus
from app.models.user import User, UserRole
from app.tasks.reminders import send_event_reminders

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── fixtures ──────────────────────────────────────────────────────────────────

def _make_user(db, email: str) -> User:
    u = User(
        email=email,
        full_name="Reminder User",
        password_hash=_pwd.hash("pw"),
        role=UserRole.student,
        is_email_verified=True,
    )
    db.add(u)
    db.flush()
    return u


def _make_club(db, owner: User) -> Club:
    club = Club(name=f"Club-{owner.id}", domain="technical", join_type=JoinType.open)
    db.add(club)
    db.flush()
    db.add(ClubMembership(user_id=owner.id, club_id=club.id, role=ClubMemberRole.president))
    db.flush()
    return club


def _make_event(db, club: Club, hours_from_now: float, cancelled: bool = False) -> Event:
    start = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    event = Event(
        club_id=club.id,
        title=f"Event in {hours_from_now}h",
        start_at=start,
        is_cancelled=cancelled,
    )
    db.add(event)
    db.flush()
    return event


def _rsvp(db, event: Event, user: User, status: RSVPStatus = RSVPStatus.confirmed) -> EventRSVP:
    r = EventRSVP(event_id=event.id, user_id=user.id, status=status)
    db.add(r)
    db.flush()
    return r


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# The task opens its own SessionLocal, so we patch that to return our
# test session instead — keeps everything in the rolled-back transaction.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class _FakeSession:
    """Wraps the real test db_session so close() is a no-op."""
    def __init__(self, session):
        self._s = session
    def query(self, *a, **kw):
        return self._s.query(*a, **kw)
    def close(self):
        pass  # don't close — the fixture manages the transaction


def _patch_session(db_session):
    """Context manager that swaps SessionLocal() for our test session."""
    return patch(
        "app.tasks.reminders.SessionLocal",
        return_value=_FakeSession(db_session),
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_reminder_dispatched_for_event_in_window(db_session):
    """Event at now+24h with two confirmed RSVPs → two emails dispatched."""
    owner = _make_user(db_session, "owner22@test.com")
    club  = _make_club(db_session, owner)
    event = _make_event(db_session, club, hours_from_now=24)
    u1    = _make_user(db_session, "att1@test.com")
    u2    = _make_user(db_session, "att2@test.com")
    _rsvp(db_session, event, u1)
    _rsvp(db_session, event, u2)
    db_session.commit()

    with _patch_session(db_session),          patch("app.tasks.reminders.send_reminder_email") as mock_email:

        result = send_event_reminders()

    assert result["events_processed"] == 1
    assert result["emails_dispatched"] == 2
    assert mock_email.delay.call_count == 2

    called_emails = {c.args[0] for c in mock_email.delay.call_args_list}
    assert called_emails == {u1.email, u2.email}


def test_reminder_not_dispatched_outside_window(db_session):
    """Event 48h from now is outside the 23-25h window — no emails."""
    owner = _make_user(db_session, "owner_far@test.com")
    club  = _make_club(db_session, owner)
    event = _make_event(db_session, club, hours_from_now=48)
    u1    = _make_user(db_session, "far_att@test.com")
    _rsvp(db_session, event, u1)
    db_session.commit()

    with _patch_session(db_session),          patch("app.tasks.reminders.send_reminder_email") as mock_email:

        result = send_event_reminders()

    assert result["events_processed"] == 0
    assert result["emails_dispatched"] == 0
    mock_email.delay.assert_not_called()


def test_cancelled_event_skipped(db_session):
    """Cancelled event in the 24h window must not generate emails."""
    owner = _make_user(db_session, "owner_cancel@test.com")
    club  = _make_club(db_session, owner)
    event = _make_event(db_session, club, hours_from_now=24, cancelled=True)
    u1    = _make_user(db_session, "cancel_att@test.com")
    _rsvp(db_session, event, u1)
    db_session.commit()

    with _patch_session(db_session),          patch("app.tasks.reminders.send_reminder_email") as mock_email:

        result = send_event_reminders()

    assert result["events_processed"] == 0
    mock_email.delay.assert_not_called()


def test_waitlisted_rsvp_not_reminded(db_session):
    """Only confirmed RSVPs get reminders — waitlisted users are skipped."""
    owner    = _make_user(db_session, "owner_wl@test.com")
    club     = _make_club(db_session, owner)
    event    = _make_event(db_session, club, hours_from_now=24)
    confirmed = _make_user(db_session, "confirmed_rem@test.com")
    waitlisted = _make_user(db_session, "waitlisted_rem@test.com")
    _rsvp(db_session, event, confirmed,  status=RSVPStatus.confirmed)
    _rsvp(db_session, event, waitlisted, status=RSVPStatus.waitlisted)
    db_session.commit()

    with _patch_session(db_session),          patch("app.tasks.reminders.send_reminder_email") as mock_email:

        result = send_event_reminders()

    assert result["emails_dispatched"] == 1
    assert mock_email.delay.call_count == 1
    assert mock_email.delay.call_args.args[0] == confirmed.email


def test_no_rsvps_no_emails(db_session):
    """Event in window but nobody RSVPed → zero emails, no crash."""
    owner = _make_user(db_session, "owner_empty@test.com")
    club  = _make_club(db_session, owner)
    _make_event(db_session, club, hours_from_now=24)
    db_session.commit()

    with _patch_session(db_session),          patch("app.tasks.reminders.send_reminder_email") as mock_email:

        result = send_event_reminders()

    assert result["events_processed"] == 1
    assert result["emails_dispatched"] == 0
    mock_email.delay.assert_not_called()


def test_multiple_events_in_window(db_session):
    """Two events in the window → emails for both fan out correctly."""
    owner  = _make_user(db_session, "owner_multi@test.com")
    club   = _make_club(db_session, owner)
    event1 = _make_event(db_session, club, hours_from_now=23.5)
    event2 = _make_event(db_session, club, hours_from_now=24.5)
    u1 = _make_user(db_session, "multi1@test.com")
    u2 = _make_user(db_session, "multi2@test.com")
    _rsvp(db_session, event1, u1)
    _rsvp(db_session, event2, u2)
    db_session.commit()

    with _patch_session(db_session),          patch("app.tasks.reminders.send_reminder_email") as mock_email:

        result = send_event_reminders()

    assert result["events_processed"] == 2
    assert result["emails_dispatched"] == 2
