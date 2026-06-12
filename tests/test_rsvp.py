"""
Tests for Phase 21 — RSVP and waitlist endpoints.
"""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from passlib.context import CryptContext

from app.models.club import Club, ClubMembership, ClubMemberRole, JoinType
from app.models.user import User, UserRole

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_user(db, email, role=UserRole.student) -> User:
    u = User(
        email=email,
        full_name="Test Person",
        password_hash=_pwd.hash("password123"),
        role=role,
        is_email_verified=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _token(client, user):
    resp = client.post("/auth/login", json={"email": user.email, "password": "password123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(client, user):
    return {"Authorization": f"Bearer {_token(client, user)}"}


def _make_club(db, owner_id, name="RSVP Test Club") -> Club:
    club = Club(name=name, domain="technical", join_type=JoinType.open)
    db.add(club)
    db.flush()
    db.add(ClubMembership(user_id=owner_id, club_id=club.id, role=ClubMemberRole.president))
    db.commit()
    db.refresh(club)
    return club


def _future(hours: int = 48) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _make_event(client, user, club_id, seat_limit=10, title="Test Event") -> int:
    payload = {
        "club_id": club_id,
        "title": title,
        "start_at": _future(48),
        "end_at": _future(52),
        "seat_limit": seat_limit,
    }
    resp = client.post("/events", json=payload, headers=_auth(client, user))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── RSVP confirmed ────────────────────────────────────────────────────────────

def test_rsvp_confirmed_when_seats_available(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id)
    event_id = _make_event(client, test_user, club.id, seat_limit=5)

    attendee = _make_user(db_session, "attendee@test.com")
    resp = client.post(f"/events/{event_id}/rsvp", headers=_auth(client, attendee))

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "confirmed"
    assert body["event_id"] == event_id
    assert body["user_id"] == attendee.id
    assert body["waitlist_position"] is None


def test_rsvp_increments_rsvp_count(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Count Club")
    event_id = _make_event(client, test_user, club.id)

    attendee = _make_user(db_session, "counter@test.com")
    client.post(f"/events/{event_id}/rsvp", headers=_auth(client, attendee))

    event = client.get(f"/events/{event_id}", headers=_auth(client, test_user)).json()
    assert event["rsvp_count"] == 1


# ── waitlist ──────────────────────────────────────────────────────────────────

def test_rsvp_waitlisted_when_full(client: TestClient, db_session, test_user):
    """seat_limit=1 — second RSVP must land on waitlist."""
    club = _make_club(db_session, test_user.id, name="Tiny Club")
    event_id = _make_event(client, test_user, club.id, seat_limit=1)

    first = _make_user(db_session, "first@test.com")
    second = _make_user(db_session, "second@test.com")

    r1 = client.post(f"/events/{event_id}/rsvp", headers=_auth(client, first))
    assert r1.json()["status"] == "confirmed"

    r2 = client.post(f"/events/{event_id}/rsvp", headers=_auth(client, second))
    assert r2.status_code == 201
    body = r2.json()
    assert body["status"] == "waitlisted"
    assert body["waitlist_position"] == 1


def test_waitlist_positions_increment(client: TestClient, db_session, test_user):
    """Multiple waitlisted users get sequential positions."""
    club = _make_club(db_session, test_user.id, name="Queue Club")
    event_id = _make_event(client, test_user, club.id, seat_limit=1)

    first = _make_user(db_session, "wl_first@test.com")
    second = _make_user(db_session, "wl_second@test.com")
    third = _make_user(db_session, "wl_third@test.com")

    client.post(f"/events/{event_id}/rsvp", headers=_auth(client, first))   # confirmed
    r2 = client.post(f"/events/{event_id}/rsvp", headers=_auth(client, second))  # waitlist pos 1
    r3 = client.post(f"/events/{event_id}/rsvp", headers=_auth(client, third))   # waitlist pos 2

    assert r2.json()["waitlist_position"] == 1
    assert r3.json()["waitlist_position"] == 2


def test_unlimited_seats_never_waitlisted(client: TestClient, db_session, test_user):
    """seat_limit=None means unlimited — all RSVPs must be confirmed."""
    club = _make_club(db_session, test_user.id, name="Unlimited Club")
    payload = {
        "club_id": club.id,
        "title": "Unlimited Event",
        "start_at": _future(48),
    }
    event_id = client.post("/events", json=payload, headers=_auth(client, test_user)).json()["id"]

    for i in range(5):
        u = _make_user(db_session, f"unlimited{i}@test.com")
        r = client.post(f"/events/{event_id}/rsvp", headers=_auth(client, u))
        assert r.json()["status"] == "confirmed"


# ── duplicate RSVP ────────────────────────────────────────────────────────────

def test_duplicate_rsvp_returns_409(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Dup Club")
    event_id = _make_event(client, test_user, club.id)

    attendee = _make_user(db_session, "dup@test.com")
    client.post(f"/events/{event_id}/rsvp", headers=_auth(client, attendee))
    resp = client.post(f"/events/{event_id}/rsvp", headers=_auth(client, attendee))
    assert resp.status_code == 409


# ── cancelled event ───────────────────────────────────────────────────────────

def test_rsvp_cancelled_event_returns_400(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Dead Club")
    event_id = _make_event(client, test_user, club.id)
    client.patch(f"/events/{event_id}/cancel", headers=_auth(client, test_user))

    attendee = _make_user(db_session, "late@test.com")
    resp = client.post(f"/events/{event_id}/rsvp", headers=_auth(client, attendee))
    assert resp.status_code == 400


# ── cancel RSVP & waitlist promotion ─────────────────────────────────────────

def test_cancel_rsvp_promotes_first_waitlisted(client: TestClient, db_session, test_user):
    """Cancel a confirmed RSVP — first waitlisted person gets promoted."""
    club = _make_club(db_session, test_user.id, name="Promote Club")
    event_id = _make_event(client, test_user, club.id, seat_limit=1)

    confirmed_user = _make_user(db_session, "confirmed@test.com")
    waiter = _make_user(db_session, "waiter@test.com")

    client.post(f"/events/{event_id}/rsvp", headers=_auth(client, confirmed_user))  # fills the seat
    client.post(f"/events/{event_id}/rsvp", headers=_auth(client, waiter))          # goes to waitlist

    # Cancel the confirmed slot
    resp = client.delete(f"/events/{event_id}/rsvp", headers=_auth(client, confirmed_user))
    assert resp.status_code == 204

    # Check rsvp list — waiter should now be confirmed
    rsvps = client.get(f"/events/{event_id}/rsvps", headers=_auth(client, test_user)).json()
    waiter_rsvp = next(r for r in rsvps if r["user_id"] == waiter.id)
    assert waiter_rsvp["status"] == "confirmed"
    assert waiter_rsvp["waitlist_position"] is None


def test_cancel_rsvp_no_waitlist_just_removes(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Simple Cancel Club")
    event_id = _make_event(client, test_user, club.id)

    attendee = _make_user(db_session, "leaver@test.com")
    client.post(f"/events/{event_id}/rsvp", headers=_auth(client, attendee))

    resp = client.delete(f"/events/{event_id}/rsvp", headers=_auth(client, attendee))
    assert resp.status_code == 204

    event = client.get(f"/events/{event_id}", headers=_auth(client, test_user)).json()
    assert event["rsvp_count"] == 0


def test_cancel_nonexistent_rsvp_returns_404(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Ghost Club")
    event_id = _make_event(client, test_user, club.id)

    attendee = _make_user(db_session, "ghost@test.com")
    resp = client.delete(f"/events/{event_id}/rsvp", headers=_auth(client, attendee))
    assert resp.status_code == 404


# ── list RSVPs ────────────────────────────────────────────────────────────────

def test_list_rsvps_as_club_admin(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="List Club")
    event_id = _make_event(client, test_user, club.id)

    a1 = _make_user(db_session, "lister1@test.com")
    a2 = _make_user(db_session, "lister2@test.com")
    client.post(f"/events/{event_id}/rsvp", headers=_auth(client, a1))
    client.post(f"/events/{event_id}/rsvp", headers=_auth(client, a2))

    resp = client.get(f"/events/{event_id}/rsvps", headers=_auth(client, test_user))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_rsvps_as_non_admin_forbidden(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Restricted Club")
    event_id = _make_event(client, test_user, club.id)

    outsider = _make_user(db_session, "outsider@test.com")
    resp = client.get(f"/events/{event_id}/rsvps", headers=_auth(client, outsider))
    assert resp.status_code == 403


def test_rsvp_requires_auth(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Auth Club")
    event_id = _make_event(client, test_user, club.id)
    resp = client.post(f"/events/{event_id}/rsvp")
    assert resp.status_code == 401
