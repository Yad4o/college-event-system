"""
Tests for Phase 29 — Recruitment drives and application pipeline.
"""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


# ── helpers ───────────────────────────────────────────────────────────────────

def _token(client, user, password="password123"):
    resp = client.post("/auth/login", json={"email": user.email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(client, user, password="password123"):
    return {"Authorization": f"Bearer {_token(client, user, password)}"}


def _admin_h(client, admin):
    return _auth(client, admin, "adminpass123")


def _make_club(client, admin, name="Recruit Club"):
    resp = client.post(
        "/clubs",
        json={"name": name, "domain": "technical", "join_type": "open"},
        headers=_admin_h(client, admin),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _future(minutes=30):
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def _past(minutes=30):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


def _open_drive(client, admin, club_id, **kwargs):
    payload = {
        "title": kwargs.get("title", "Open Drive"),
        "open_roles": ["core_member", "volunteer"],
        "form_questions": ["Why do you want to join?", "What skills do you bring?"],
        "opens_at": _past(60),
        "closes_at": _future(60),
    }
    payload.update(kwargs)
    resp = client.post(
        f"/clubs/{club_id}/recruitment/drives",
        json=payload,
        headers=_admin_h(client, admin),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# Drives
# ═══════════════════════════════════════════════════════════════════════════════

class TestDrives:

    def test_create_drive_as_president(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Drive Club")
        drive = _open_drive(client, test_admin, club["id"], title="Sem 1 Drive")
        assert drive["title"] == "Sem 1 Drive"
        assert drive["is_active"] is True
        assert drive["club_id"] == club["id"]

    def test_create_drive_as_student_forbidden(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "No Drive Club")
        resp = client.post(
            f"/clubs/{club['id']}/recruitment/drives",
            json={
                "title": "Sneaky Drive",
                "open_roles": [],
                "form_questions": [],
                "opens_at": _past(10),
                "closes_at": _future(10),
            },
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 403

    def test_list_drives(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "List Drive Club")
        _open_drive(client, test_admin, club["id"], title="Drive A")
        _open_drive(client, test_admin, club["id"], title="Drive B")
        resp = client.get(
            f"/clubs/{club['id']}/recruitment/drives",
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 200
        titles = [d["title"] for d in resp.json()]
        assert "Drive A" in titles and "Drive B" in titles

    def test_update_drive(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Update Drive Club")
        drive = _open_drive(client, test_admin, club["id"])
        resp = client.patch(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}",
            json={"title": "Updated Drive"},
            headers=_admin_h(client, admin=test_admin),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Drive"

    def test_close_drive(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Close Drive Club")
        drive = _open_drive(client, test_admin, club["id"])
        resp = client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/close",
            headers=_admin_h(client, admin=test_admin),
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_closes_at_before_opens_at_rejected(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Invalid Window Club")
        resp = client.post(
            f"/clubs/{club['id']}/recruitment/drives",
            json={
                "title": "Bad Window",
                "open_roles": [],
                "form_questions": [],
                "opens_at": _future(60),
                "closes_at": _future(10),  # closes before opens
            },
            headers=_admin_h(client, admin=test_admin),
        )
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# Applications
# ═══════════════════════════════════════════════════════════════════════════════

class TestApplications:

    def test_apply_in_window(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Apply Club")
        drive = _open_drive(client, test_admin, club["id"])
        resp = client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json={"answers": ["I love tech!", "Python & React"], "desired_role": "core_member"},
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "applied"
        assert body["answers"] == ["I love tech!", "Python & React"]

    def test_apply_outside_window_before_open(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Early Apply Club")
        resp = client.post(
            f"/clubs/{club['id']}/recruitment/drives",
            json={
                "title": "Future Drive",
                "open_roles": [],
                "form_questions": [],
                "opens_at": _future(30),
                "closes_at": _future(60),
            },
            headers=_admin_h(client, admin=test_admin),
        )
        drive = resp.json()
        apply_resp = client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json={"answers": []},
            headers=_auth(client, test_user),
        )
        assert apply_resp.status_code == 400

    def test_apply_outside_window_after_close(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Closed Apply Club")
        # Create a drive that is already past
        resp = client.post(
            f"/clubs/{club['id']}/recruitment/drives",
            json={
                "title": "Past Drive",
                "open_roles": [],
                "form_questions": [],
                "opens_at": _past(60),
                "closes_at": _past(10),
            },
            headers=_admin_h(client, admin=test_admin),
        )
        drive = resp.json()
        apply_resp = client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json={"answers": []},
            headers=_auth(client, test_user),
        )
        assert apply_resp.status_code == 400

    def test_duplicate_application_rejected(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Dup Apply Club")
        drive = _open_drive(client, test_admin, club["id"])
        payload = {"answers": ["Once", "Twice"]}
        client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json=payload, headers=_auth(client, test_user),
        )
        resp = client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json=payload, headers=_auth(client, test_user),
        )
        assert resp.status_code == 409

    def test_answer_count_mismatch_rejected(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Mismatch Club")
        drive = _open_drive(client, test_admin, club["id"])
        # Drive has 2 questions; send only 1 answer
        resp = client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json={"answers": ["Only one answer"]},
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 422

    def test_president_sees_all_applications(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "See All Club")
        drive = _open_drive(client, test_admin, club["id"])
        client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json={"answers": ["ans1", "ans2"]},
            headers=_auth(client, test_user),
        )
        resp = client.get(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/applications",
            headers=_admin_h(client, admin=test_admin),
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_student_sees_only_own_application(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Own View Club")
        drive = _open_drive(client, test_admin, club["id"])
        client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json={"answers": ["my ans", "my ans2"]},
            headers=_auth(client, test_user),
        )
        resp = client.get(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/applications",
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 200
        apps = resp.json()
        assert all(a["applicant_id"] == test_user.id for a in apps)

    def test_status_update_shortlisted(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Status Club")
        drive = _open_drive(client, test_admin, club["id"])
        app = client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json={"answers": ["a1", "a2"]},
            headers=_auth(client, test_user),
        ).json()

        resp = client.patch(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/applications/{app['id']}",
            json={"status": "shortlisted", "reviewer_notes": "Good candidate"},
            headers=_admin_h(client, admin=test_admin),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "shortlisted"

    def test_status_update_selected(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Select Club")
        drive = _open_drive(client, test_admin, club["id"])
        app = client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json={"answers": ["a1", "a2"]},
            headers=_auth(client, test_user),
        ).json()

        resp = client.patch(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/applications/{app['id']}",
            json={"status": "selected"},
            headers=_admin_h(client, admin=test_admin),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "selected"

    def test_status_update_by_student_forbidden(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Guard Status Club")
        drive = _open_drive(client, test_admin, club["id"])
        app = client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json={"answers": ["a1", "a2"]},
            headers=_auth(client, test_user),
        ).json()

        resp = client.patch(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/applications/{app['id']}",
            json={"status": "selected"},
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 403

    def test_apply_to_closed_drive_rejected(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Closed Drive Club")
        drive = _open_drive(client, test_admin, club["id"])
        # Close the drive first
        client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/close",
            headers=_admin_h(client, admin=test_admin),
        )
        resp = client.post(
            f"/clubs/{club['id']}/recruitment/drives/{drive['id']}/apply",
            json={"answers": ["a1", "a2"]},
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 400
