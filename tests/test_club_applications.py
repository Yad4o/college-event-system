"""
Tests for new-club application flow.
"""
import pytest
from fastapi.testclient import TestClient


def _token(client, user):
    r = client.post("/auth/login", json={"email": user.email, "password": "password123"})
    return r.json()["access_token"]

def _auth(client, user):
    return {"Authorization": f"Bearer {_token(client, user)}"}


def test_student_can_apply(client: TestClient, test_user):
    r = client.post(
        "/club-applications",
        json={"club_name": "AI Society", "domain": "technical"},
        headers=_auth(client, test_user),
    )
    assert r.status_code == 201
    body = r.json()
    assert body["club_name"] == "AI Society"
    assert body["status"] == "pending"
    assert body["applicant_id"] == test_user.id


def test_student_cannot_list_applications(client: TestClient, test_user):
    r = client.get("/club-applications", headers=_auth(client, test_user))
    assert r.status_code == 403


def test_admin_can_list_applications(client: TestClient, test_admin, test_user):
    client.post(
        "/club-applications",
        json={"club_name": "Drama Club", "domain": "cultural"},
        headers=_auth(client, test_user),
    )
    r = client.get("/club-applications", headers=_auth(client, test_admin))
    assert r.status_code == 200
    assert any(a["club_name"] == "Drama Club" for a in r.json())


def test_admin_can_filter_by_status(client: TestClient, test_admin, test_user):
    client.post(
        "/club-applications",
        json={"club_name": "Filter Club"},
        headers=_auth(client, test_user),
    )
    r = client.get("/club-applications?status=pending", headers=_auth(client, test_admin))
    assert r.status_code == 200
    for a in r.json():
        assert a["status"] == "pending"


def test_approve_creates_club(client: TestClient, test_admin, test_user):
    apply_r = client.post(
        "/club-applications",
        json={"club_name": "Robotics Society", "domain": "technical"},
        headers=_auth(client, test_user),
    )
    app_id = apply_r.json()["id"]

    r = client.patch(
        f"/club-applications/{app_id}",
        json={"decision": "approved"},
        headers=_auth(client, test_admin),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    # Club should now exist
    clubs_r = client.get("/clubs", headers=_auth(client, test_user))
    names = [c["name"] for c in clubs_r.json()]
    assert "Robotics Society" in names


def test_approve_applicant_is_president(client: TestClient, test_admin, test_user):
    apply_r = client.post(
        "/club-applications",
        json={"club_name": "Chess Club", "domain": "sports"},
        headers=_auth(client, test_user),
    )
    app_id = apply_r.json()["id"]
    client.patch(
        f"/club-applications/{app_id}",
        json={"decision": "approved"},
        headers=_auth(client, test_admin),
    )

    clubs_r = client.get("/clubs", headers=_auth(client, test_user))
    club = next(c for c in clubs_r.json() if c["name"] == "Chess Club")
    assert club["member_count"] == 1   # applicant added as president


def test_reject_does_not_create_club(client: TestClient, test_admin, test_user):
    apply_r = client.post(
        "/club-applications",
        json={"club_name": "Ghost Club", "domain": "cultural"},
        headers=_auth(client, test_user),
    )
    app_id = apply_r.json()["id"]

    r = client.patch(
        f"/club-applications/{app_id}",
        json={"decision": "rejected", "admin_remarks": "Not enough detail"},
        headers=_auth(client, test_admin),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    assert r.json()["admin_remarks"] == "Not enough detail"

    clubs_r = client.get("/clubs", headers=_auth(client, test_user))
    names = [c["name"] for c in clubs_r.json()]
    assert "Ghost Club" not in names


def test_double_review_blocked(client: TestClient, test_admin, test_user):
    apply_r = client.post(
        "/club-applications",
        json={"club_name": "Double Club"},
        headers=_auth(client, test_user),
    )
    app_id = apply_r.json()["id"]
    client.patch(f"/club-applications/{app_id}", json={"decision": "rejected"}, headers=_auth(client, test_admin))
    r = client.patch(f"/club-applications/{app_id}", json={"decision": "approved"}, headers=_auth(client, test_admin))
    assert r.status_code == 400


def test_student_cannot_review(client: TestClient, test_admin, test_user):
    apply_r = client.post(
        "/club-applications",
        json={"club_name": "Sneaky Club"},
        headers=_auth(client, test_user),
    )
    app_id = apply_r.json()["id"]
    r = client.patch(
        f"/club-applications/{app_id}",
        json={"decision": "approved"},
        headers=_auth(client, test_user),
    )
    assert r.status_code == 403
