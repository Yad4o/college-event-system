"""
Tests for club membership and join request flows.
"""
import pytest
from fastapi.testclient import TestClient


def _token(client, user):
    r = client.post("/auth/login", json={"email": user.email, "password": "password123"})
    return r.json()["access_token"]

def _auth(client, user):
    return {"Authorization": f"Bearer {_token(client, user)}"}

def _make_club(client, admin, join_type="open", name="Test Club"):
    r = client.post("/clubs", json={"name": name, "domain": "technical", "join_type": join_type}, headers=_auth(client, admin))
    assert r.status_code == 201
    return r.json()["id"]


# ── Open join ─────────────────────────────────────────────────────────────────

def test_join_open_club(client: TestClient, test_admin, test_user):
    club_id = _make_club(client, test_admin, join_type="open", name="Open Club")
    r = client.post(f"/clubs/{club_id}/join", headers=_auth(client, test_user))
    assert r.status_code == 201
    body = r.json()
    assert body["user_id"] == test_user.id
    assert body["role"] == "member"


def test_join_open_club_duplicate(client: TestClient, test_admin, test_user):
    club_id = _make_club(client, test_admin, join_type="open", name="Open Club2")
    client.post(f"/clubs/{club_id}/join", headers=_auth(client, test_user))
    r = client.post(f"/clubs/{club_id}/join", headers=_auth(client, test_user))
    assert r.status_code == 409


# ── Invite-only join request ──────────────────────────────────────────────────

def test_join_invite_only_creates_request(client: TestClient, test_admin, test_user):
    club_id = _make_club(client, test_admin, join_type="invite_only", name="Invite Club")
    r = client.post(f"/clubs/{club_id}/join", headers=_auth(client, test_user))
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending"


def test_join_invite_only_duplicate_request(client: TestClient, test_admin, test_user):
    club_id = _make_club(client, test_admin, join_type="invite_only", name="Invite Club2")
    client.post(f"/clubs/{club_id}/join", headers=_auth(client, test_user))
    r = client.post(f"/clubs/{club_id}/join", headers=_auth(client, test_user))
    assert r.status_code == 409


# ── Approve join request ──────────────────────────────────────────────────────

def test_approve_join_request_creates_membership(client: TestClient, test_admin, test_user):
    club_id = _make_club(client, test_admin, join_type="invite_only", name="Approve Club")
    join_r = client.post(f"/clubs/{club_id}/join", headers=_auth(client, test_user))
    request_id = join_r.json()["id"]

    r = client.patch(
        f"/clubs/{club_id}/join-requests/{request_id}",
        params={"decision": "approved"},
        headers=_auth(client, test_admin),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    # Member count should now include the new member
    club_r = client.get(f"/clubs/{club_id}", headers=_auth(client, test_user))
    assert club_r.json()["member_count"] == 2


def test_reject_join_request_no_membership(client: TestClient, test_admin, test_user):
    club_id = _make_club(client, test_admin, join_type="invite_only", name="Reject Club")
    join_r = client.post(f"/clubs/{club_id}/join", headers=_auth(client, test_user))
    request_id = join_r.json()["id"]

    r = client.patch(
        f"/clubs/{club_id}/join-requests/{request_id}",
        params={"decision": "rejected"},
        headers=_auth(client, test_admin),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"

    # Member count should still be 1 (only admin/president)
    club_r = client.get(f"/clubs/{club_id}", headers=_auth(client, test_user))
    assert club_r.json()["member_count"] == 1


def test_student_cannot_decide_join_request(client: TestClient, test_admin, test_user, db_session):
    from app.models.user import User, UserRole
    from app.utils.security import hash_password
    other = User(email="other2@x.com", full_name="Other", password_hash=hash_password("password123"),
                 role=UserRole.student, is_email_verified=True)
    db_session.add(other)
    db_session.commit()

    club_id = _make_club(client, test_admin, join_type="invite_only", name="Guard Club")
    join_r = client.post(f"/clubs/{club_id}/join", headers=_auth(client, other))
    request_id = join_r.json()["id"]

    r = client.patch(
        f"/clubs/{club_id}/join-requests/{request_id}",
        params={"decision": "approved"},
        headers=_auth(client, test_user),
    )
    assert r.status_code == 403


# ── Remove member ─────────────────────────────────────────────────────────────

def test_remove_member(client: TestClient, test_admin, test_user):
    club_id = _make_club(client, test_admin, join_type="open", name="Remove Club")
    client.post(f"/clubs/{club_id}/join", headers=_auth(client, test_user))

    r = client.delete(f"/clubs/{club_id}/members/{test_user.id}", headers=_auth(client, test_admin))
    assert r.status_code == 204

    club_r = client.get(f"/clubs/{club_id}", headers=_auth(client, test_user))
    assert club_r.json()["member_count"] == 1


def test_student_cannot_remove_member(client: TestClient, test_admin, test_user):
    club_id = _make_club(client, test_admin, join_type="open", name="NoRemove Club")
    r = client.delete(f"/clubs/{club_id}/members/{test_admin.id}", headers=_auth(client, test_user))
    assert r.status_code == 403
