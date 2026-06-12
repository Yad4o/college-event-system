"""
Tests for Phase 23 — QR attendance scan endpoints.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from passlib.context import CryptContext

from app.models.club import Club, ClubMembership, ClubMemberRole, JoinType
from app.models.event import Event, EventRSVP, RSVPStatus
from app.models.user import User, UserRole
from app.utils.qr import generate_event_qr_token

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_user(db, email: str, role: UserRole = UserRole.student) -> User:
    u = User(
        email=email,
        full_name="Attendance Tester",
        password_hash=_pwd.hash("password123"),
        role=role,
        is_email_verified=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _token(client, user: User) -> str:
    resp = client.post("/auth/login", json={"email": user.email, "password": "password123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(client, user: User) -> dict:
    return {"Authorization": f"Bearer {_token(client, user)}"}


def _make_club(db, owner: User, name: str = "Attendance Club") -> Club:
    club = Club(name=name, domain="technical", join_type=JoinType.open)
    db.add(club)
    db.flush()
    db.add(ClubMembership(user_id=owner.id, club_id=club.id, role=ClubMemberRole.president))
    db.commit()
    db.refresh(club)
    return club


def _make_event(db, club: Club, hours: float = 0) -> Event:
    """Create an event starting `hours` from now (0 = right now = scannable)."""
    start = datetime.now(timezone.utc) + timedelta(hours=hours)
    event = Event(
        club_id=club.id,
        title="Scan Test Event",
        start_at=start,
    )
    db.add(event)
    db.flush()
    event.qr_token = generate_event_qr_token(event.id)
    db.commit()
    db.refresh(event)
    return event


def _confirmed_rsvp(db, event: Event, user: User) -> EventRSVP:
    rsvp = EventRSVP(event_id=event.id, user_id=user.id, status=RSVPStatus.confirmed)
    db.add(rsvp)
    db.commit()
    return rsvp


# ── scan — happy path ─────────────────────────────────────────────────────────

def test_scan_marks_attendance(client: TestClient, db_session, test_user, test_admin):
    club  = _make_club(db_session, test_admin, "Happy Club")
    event = _make_event(db_session, club)
    _confirmed_rsvp(db_session, event, test_user)

    resp = client.post(
        "/attendance/scan",
        json={"qr_token": event.qr_token},
        headers=_auth(client, test_user),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["event_id"] == event.id
    assert body["user_id"] == test_user.id
    assert "marked_at" in body


def test_scan_returns_attendance_read_schema(client: TestClient, db_session, test_user, test_admin):
    club  = _make_club(db_session, test_admin, "Schema Club")
    event = _make_event(db_session, club)
    _confirmed_rsvp(db_session, event, test_user)

    body = client.post(
        "/attendance/scan",
        json={"qr_token": event.qr_token},
        headers=_auth(client, test_user),
    ).json()

    # All AttendanceRead fields present
    for field in ("id", "event_id", "user_id", "marked_at"):
        assert field in body, f"Missing field: {field}"


# ── scan — error paths ────────────────────────────────────────────────────────

def test_scan_invalid_token_returns_401(client: TestClient, test_user):
    resp = client.post(
        "/attendance/scan",
        json={"qr_token": "this.is.not.valid"},
        headers=_auth(client, test_user),
    )
    assert resp.status_code == 401


def test_scan_no_rsvp_returns_403(client: TestClient, db_session, test_user, test_admin):
    """User has no RSVP — scan must be rejected with 403."""
    club  = _make_club(db_session, test_admin, "No RSVP Club")
    event = _make_event(db_session, club)
    # Deliberately do NOT create an RSVP for test_user

    resp = client.post(
        "/attendance/scan",
        json={"qr_token": event.qr_token},
        headers=_auth(client, test_user),
    )
    assert resp.status_code == 403


def test_scan_waitlisted_rsvp_returns_403(client: TestClient, db_session, test_user, test_admin):
    """Waitlisted RSVP is not confirmed — scan must be rejected."""
    club  = _make_club(db_session, test_admin, "Waitlist Scan Club")
    event = _make_event(db_session, club)
    rsvp  = EventRSVP(event_id=event.id, user_id=test_user.id, status=RSVPStatus.waitlisted)
    db_session.add(rsvp)
    db_session.commit()

    resp = client.post(
        "/attendance/scan",
        json={"qr_token": event.qr_token},
        headers=_auth(client, test_user),
    )
    assert resp.status_code == 403


def test_scan_duplicate_returns_409(client: TestClient, db_session, test_user, test_admin):
    """Scanning twice for the same event must return 409."""
    club  = _make_club(db_session, test_admin, "Dup Scan Club")
    event = _make_event(db_session, club)
    _confirmed_rsvp(db_session, event, test_user)

    client.post("/attendance/scan", json={"qr_token": event.qr_token}, headers=_auth(client, test_user))
    resp = client.post("/attendance/scan", json={"qr_token": event.qr_token}, headers=_auth(client, test_user))
    assert resp.status_code == 409


def test_scan_requires_auth(client: TestClient, db_session, test_user, test_admin):
    club  = _make_club(db_session, test_admin, "Auth Scan Club")
    event = _make_event(db_session, club)
    resp  = client.post("/attendance/scan", json={"qr_token": event.qr_token})
    assert resp.status_code == 401


# ── GET /events/{id}/attendance ───────────────────────────────────────────────

def test_get_event_attendance_as_club_admin(client: TestClient, db_session, test_user, test_admin):
    club  = _make_club(db_session, test_admin, "List Attendance Club")
    event = _make_event(db_session, club)

    # Two attendees scan in
    for i, email in enumerate(["att_a@test.com", "att_b@test.com"]):
        u = _make_user(db_session, email)
        _confirmed_rsvp(db_session, event, u)
        client.post("/attendance/scan", json={"qr_token": event.qr_token}, headers=_auth(client, u))

    resp = client.get(f"/events/{event.id}/attendance", headers=_auth(client, test_admin, ))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_event_attendance_as_non_admin_forbidden(client: TestClient, db_session, test_user, test_admin):
    club  = _make_club(db_session, test_admin, "Forbidden Attendance Club")
    event = _make_event(db_session, club)

    outsider = _make_user(db_session, "outsider_att@test.com")
    resp = client.get(f"/events/{event.id}/attendance", headers=_auth(client, outsider))
    assert resp.status_code == 403


def test_get_event_attendance_nonexistent_event(client: TestClient, test_user):
    resp = client.get("/events/99999/attendance", headers=_auth(client, test_user))
    assert resp.status_code == 404


# ── GET /users/me/attendance ──────────────────────────────────────────────────

def test_my_attendance_empty(client: TestClient, test_user):
    resp = client.get("/users/me/attendance", headers=_auth(client, test_user))
    assert resp.status_code == 200
    assert resp.json() == []


def test_my_attendance_shows_scanned_events(client: TestClient, db_session, test_user, test_admin):
    club   = _make_club(db_session, test_admin, "My Attendance Club")
    event1 = _make_event(db_session, club)
    event2 = _make_event(db_session, club)

    for ev in (event1, event2):
        _confirmed_rsvp(db_session, ev, test_user)
        client.post("/attendance/scan", json={"qr_token": ev.qr_token}, headers=_auth(client, test_user))

    resp = client.get("/users/me/attendance", headers=_auth(client, test_user))
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    event_ids = {r["event_id"] for r in resp.json()}
    assert event_ids == {event1.id, event2.id}


def test_my_attendance_only_shows_own_records(client: TestClient, db_session, test_user, test_admin):
    """Other users' scans must not bleed into /users/me/attendance."""
    club  = _make_club(db_session, test_admin, "Isolation Club")
    event = _make_event(db_session, club)

    other = _make_user(db_session, "other_att@test.com")
    _confirmed_rsvp(db_session, event, other)
    client.post("/attendance/scan", json={"qr_token": event.qr_token}, headers=_auth(client, other))

    # test_user has no RSVP — their history should be empty
    resp = client.get("/users/me/attendance", headers=_auth(client, test_user))
    assert resp.status_code == 200
    assert resp.json() == []


def test_my_attendance_requires_auth(client: TestClient):
    resp = client.get("/users/me/attendance")
    assert resp.status_code == 401
