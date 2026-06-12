"""
Tests for Phase 20 — Event CRUD endpoints.
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.models.club import Club, ClubMembership, ClubMemberRole, JoinType


# ── helpers ───────────────────────────────────────────────────────────────────

def _token(client, user, password="password123"):
    resp = client.post("/auth/login", json={"email": user.email, "password": password})
    return resp.json()["access_token"]


def _auth(client, user, password="password123"):
    return {"Authorization": f"Bearer {_token(client, user, password)}"}


def _make_club(db, owner_id, name="Test Club") -> Club:
    club = Club(name=name, domain="technical", join_type=JoinType.open)
    db.add(club)
    db.flush()
    membership = ClubMembership(user_id=owner_id, club_id=club.id, role=ClubMemberRole.president)
    db.add(membership)
    db.commit()
    db.refresh(club)
    return club


def _future(hours: int = 48) -> str:
    dt = datetime.now(timezone.utc) + timedelta(hours=hours)
    return dt.isoformat()


def _event_payload(club_id: int, **overrides) -> dict:
    base = {
        "club_id": club_id,
        "title": "Annual Tech Fest",
        "start_at": _future(48),
        "end_at": _future(52),
        "seat_limit": 100,
    }
    base.update(overrides)
    return base


# ── create ────────────────────────────────────────────────────────────────────

def test_create_event_as_club_president(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id)
    resp = client.post("/events", json=_event_payload(club.id), headers=_auth(client, test_user))
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Annual Tech Fest"
    assert body["qr_token"] is not None   # QR token generated on creation
    assert body["rsvp_count"] == 0
    assert body["is_cancelled"] is False


def test_create_event_as_college_admin(client: TestClient, db_session, test_admin, test_user):
    # college_admin can create events for any club
    club = _make_club(db_session, test_user.id, name="Admin's Club")
    resp = client.post("/events", json=_event_payload(club.id), headers=_auth(client, test_admin, "adminpass123"))
    assert resp.status_code == 201


def test_create_event_as_non_member_forbidden(client: TestClient, db_session, test_user, test_admin):
    # test_user is NOT a president of this club — admin created it separately
    club = _make_club(db_session, test_admin.id, name="Admin Only Club")
    resp = client.post("/events", json=_event_payload(club.id), headers=_auth(client, test_user))
    assert resp.status_code == 403


def test_create_event_end_before_start_rejected(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Time Warp Club")
    payload = _event_payload(club.id, end_at=_future(1), start_at=_future(10))
    resp = client.post("/events", json=payload, headers=_auth(client, test_user))
    assert resp.status_code == 422


def test_create_event_requires_auth(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Open Club")
    resp = client.post("/events", json=_event_payload(club.id))
    assert resp.status_code == 401


# ── list ──────────────────────────────────────────────────────────────────────

def test_list_events_empty(client: TestClient, test_user):
    resp = client.get("/events", headers=_auth(client, test_user))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_events_returns_created(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Listing Club")
    client.post("/events", json=_event_payload(club.id), headers=_auth(client, test_user))
    resp = client.get("/events", headers=_auth(client, test_user))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_list_events_filter_by_club(client: TestClient, db_session, test_user):
    club_a = _make_club(db_session, test_user.id, name="Club A")
    club_b = _make_club(db_session, test_user.id, name="Club B")
    client.post("/events", json=_event_payload(club_a.id, title="Event A"), headers=_auth(client, test_user))
    client.post("/events", json=_event_payload(club_b.id, title="Event B"), headers=_auth(client, test_user))

    resp = client.get(f"/events?club_id={club_a.id}", headers=_auth(client, test_user))
    bodies = resp.json()
    assert all(e["club_id"] == club_a.id for e in bodies)


# ── get single ────────────────────────────────────────────────────────────────

def test_get_event(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Get Club")
    event_id = client.post("/events", json=_event_payload(club.id), headers=_auth(client, test_user)).json()["id"]
    resp = client.get(f"/events/{event_id}", headers=_auth(client, test_user))
    assert resp.status_code == 200
    assert resp.json()["id"] == event_id


def test_get_nonexistent_event(client: TestClient, test_user):
    resp = client.get("/events/99999", headers=_auth(client, test_user))
    assert resp.status_code == 404


# ── update ────────────────────────────────────────────────────────────────────

def test_update_event_title(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Update Club")
    event_id = client.post("/events", json=_event_payload(club.id), headers=_auth(client, test_user)).json()["id"]

    resp = client.patch(
        f"/events/{event_id}",
        json={"title": "Renamed Fest"},
        headers=_auth(client, test_user),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Renamed Fest"


def test_update_event_start_at_regenerates_qr(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="QR Club")
    created = client.post("/events", json=_event_payload(club.id), headers=_auth(client, test_user)).json()
    old_qr = created["qr_token"]

    updated = client.patch(
        f"/events/{created['id']}",
        json={"start_at": _future(72)},
        headers=_auth(client, test_user),
    ).json()
    # QR token must change when start_at changes
    assert updated["qr_token"] != old_qr


def test_update_event_as_non_admin_forbidden(client: TestClient, db_session, test_user, test_admin):
    club = _make_club(db_session, test_admin.id, name="Admin Event Club")
    event_id = client.post(
        "/events", json=_event_payload(club.id), headers=_auth(client, test_admin, "adminpass123")
    ).json()["id"]

    resp = client.patch(f"/events/{event_id}", json={"title": "Hack"}, headers=_auth(client, test_user))
    assert resp.status_code == 403


# ── cancel ────────────────────────────────────────────────────────────────────

def test_cancel_event(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="Cancel Club")
    event_id = client.post("/events", json=_event_payload(club.id), headers=_auth(client, test_user)).json()["id"]

    resp = client.patch(f"/events/{event_id}/cancel", headers=_auth(client, test_user))
    assert resp.status_code == 200
    assert resp.json()["is_cancelled"] is True

    # Cancelled events must not appear in public list
    events = client.get("/events", headers=_auth(client, test_user)).json()
    assert event_id not in [e["id"] for e in events]


def test_cancel_event_non_admin_forbidden(client: TestClient, db_session, test_user, test_admin):
    club = _make_club(db_session, test_admin.id, name="Protected Event Club")
    event_id = client.post(
        "/events", json=_event_payload(club.id), headers=_auth(client, test_admin, "adminpass123")
    ).json()["id"]

    resp = client.patch(f"/events/{event_id}/cancel", headers=_auth(client, test_user))
    assert resp.status_code == 403


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_event_as_college_admin(client: TestClient, db_session, test_user, test_admin):
    club = _make_club(db_session, test_user.id, name="Delete Club")
    event_id = client.post("/events", json=_event_payload(club.id), headers=_auth(client, test_user)).json()["id"]

    resp = client.delete(f"/events/{event_id}", headers=_auth(client, test_admin, "adminpass123"))
    assert resp.status_code == 204

    resp2 = client.get(f"/events/{event_id}", headers=_auth(client, test_user))
    assert resp2.status_code == 404


def test_delete_event_as_student_forbidden(client: TestClient, db_session, test_user):
    club = _make_club(db_session, test_user.id, name="CannotDelete Club")
    event_id = client.post("/events", json=_event_payload(club.id), headers=_auth(client, test_user)).json()["id"]

    resp = client.delete(f"/events/{event_id}", headers=_auth(client, test_user))
    assert resp.status_code == 403
