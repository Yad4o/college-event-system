"""
Tests for Phase 15 — Club CRUD endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def _token(client, user):
    resp = client.post("/auth/login", json={"email": user.email, "password": "password123"})
    return resp.json()["access_token"]


def _auth(client, user):
    return {"Authorization": f"Bearer {_token(client, user)}"}


# ── List clubs ────────────────────────────────────────────────────────────────

def test_list_clubs_empty(client: TestClient, test_user):
    resp = client.get("/clubs", headers=_auth(client, test_user))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_clubs_requires_auth(client: TestClient):
    resp = client.get("/clubs")
    assert resp.status_code == 401


# ── Create club ───────────────────────────────────────────────────────────────

def test_create_club_as_admin(client: TestClient, test_admin):
    resp = client.post(
        "/clubs",
        json={"name": "Robotics Club", "domain": "technical", "join_type": "open"},
        headers=_auth(client, test_admin),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Robotics Club"
    assert body["member_count"] == 1   # creator added as president


def test_create_club_as_student_forbidden(client: TestClient, test_user):
    resp = client.post(
        "/clubs",
        json={"name": "Student Club", "domain": "cultural"},
        headers=_auth(client, test_user),
    )
    assert resp.status_code == 403


def test_create_club_duplicate_name(client: TestClient, test_admin):
    payload = {"name": "UniqueClub", "domain": "sports"}
    client.post("/clubs", json=payload, headers=_auth(client, test_admin))
    resp = client.post("/clubs", json=payload, headers=_auth(client, test_admin))
    assert resp.status_code in (400, 409, 500)   # DB unique constraint


# ── Get club ──────────────────────────────────────────────────────────────────

def test_get_club(client: TestClient, test_admin, test_user):
    create_resp = client.post(
        "/clubs",
        json={"name": "Get Me Club", "domain": "cultural"},
        headers=_auth(client, test_admin),
    )
    club_id = create_resp.json()["id"]
    resp = client.get(f"/clubs/{club_id}", headers=_auth(client, test_user))
    assert resp.status_code == 200
    assert resp.json()["id"] == club_id


def test_get_nonexistent_club(client: TestClient, test_user):
    resp = client.get("/clubs/99999", headers=_auth(client, test_user))
    assert resp.status_code == 404


# ── Update club ───────────────────────────────────────────────────────────────

def test_update_club_as_admin(client: TestClient, test_admin):
    club_id = client.post(
        "/clubs",
        json={"name": "Updateable Club", "domain": "sports"},
        headers=_auth(client, test_admin),
    ).json()["id"]

    resp = client.patch(
        f"/clubs/{club_id}",
        json={"description": "Updated description"},
        headers=_auth(client, test_admin),
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated description"


def test_update_club_as_student_forbidden(client: TestClient, test_admin, test_user):
    club_id = client.post(
        "/clubs",
        json={"name": "No Touch Club", "domain": "sports"},
        headers=_auth(client, test_admin),
    ).json()["id"]

    resp = client.patch(
        f"/clubs/{club_id}",
        json={"description": "Sneaky edit"},
        headers=_auth(client, test_user),
    )
    assert resp.status_code == 403


# ── Suspend club ──────────────────────────────────────────────────────────────

def test_suspend_club(client: TestClient, test_admin, test_user):
    club_id = client.post(
        "/clubs",
        json={"name": "Suspend Me Club", "domain": "cultural"},
        headers=_auth(client, test_admin),
    ).json()["id"]

    # Suspend
    resp = client.patch(f"/clubs/{club_id}/suspend", headers=_auth(client, test_admin))
    assert resp.status_code == 200
    assert resp.json()["is_suspended"] is True

    # Suspended club should not appear in public list
    clubs = client.get("/clubs", headers=_auth(client, test_user)).json()
    ids = [c["id"] for c in clubs]
    assert club_id not in ids


def test_suspend_club_as_student_forbidden(client: TestClient, test_admin, test_user):
    club_id = client.post(
        "/clubs",
        json={"name": "Protected Club", "domain": "technical"},
        headers=_auth(client, test_admin),
    ).json()["id"]

    resp = client.patch(f"/clubs/{club_id}/suspend", headers=_auth(client, test_user))
    assert resp.status_code == 403
