"""
Tests for Phase 27 (club announcements) and Phase 28 (platform announcements).
"""

from fastapi.testclient import TestClient


# ── helpers ───────────────────────────────────────────────────────────────────

def _token(client, user, password="password123"):
    resp = client.post("/auth/login", json={"email": user.email, "password": password})
    return resp.json()["access_token"]


def _auth(client, user, password="password123"):
    return {"Authorization": f"Bearer {_token(client, user, password)}"}


def _admin_headers(client, admin):
    return _auth(client, admin, "adminpass123")


def _make_club(client, admin, name="Test Club"):
    resp = client.post(
        "/clubs",
        json={"name": name, "domain": "technical", "join_type": "open"},
        headers=_admin_headers(client, admin),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _join_club(client, user, club_id):
    resp = client.post(f"/clubs/{club_id}/join", headers=_auth(client, user))
    assert resp.status_code in (200, 201), resp.text


def _post_ann(client, admin, club_id, title="Hello", pinned=False):
    resp = client.post(
        f"/clubs/{club_id}/announcements",
        json={"title": title, "body": "Body text", "is_pinned": pinned},
        headers=_admin_headers(client, admin),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 27 — Club announcements
# ═══════════════════════════════════════════════════════════════════════════════

class TestClubAnnouncements:

    def test_member_can_read(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Read Club")
        _join_club(client, test_user, club["id"])
        _post_ann(client, test_admin, club["id"], "Welcome!")

        resp = client.get(
            f"/clubs/{club['id']}/announcements",
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 200
        titles = [a["title"] for a in resp.json()]
        assert "Welcome!" in titles

    def test_non_member_blocked(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Private Club")
        _post_ann(client, test_admin, club["id"], "Secret")

        resp = client.get(
            f"/clubs/{club['id']}/announcements",
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 403

    def test_student_cannot_create(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "No Post Club")
        _join_club(client, test_user, club["id"])

        resp = client.post(
            f"/clubs/{club['id']}/announcements",
            json={"title": "Sneaky", "body": "Nope"},
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 403

    def test_pinned_appears_first(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Pin Club")
        _join_club(client, test_user, club["id"])
        _post_ann(client, test_admin, club["id"], "Normal post", pinned=False)
        _post_ann(client, test_admin, club["id"], "Pinned post", pinned=True)

        resp = client.get(
            f"/clubs/{club['id']}/announcements",
            headers=_auth(client, test_user),
        )
        items = resp.json()
        assert items[0]["title"] == "Pinned post"
        assert items[0]["is_pinned"] is True

    def test_update_announcement(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Update Club")
        _join_club(client, test_user, club["id"])
        ann = _post_ann(client, test_admin, club["id"], "Old title")

        resp = client.patch(
            f"/clubs/{club['id']}/announcements/{ann['id']}",
            json={"title": "New title"},
            headers=_admin_headers(client, test_admin),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New title"

    def test_delete_announcement(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Delete Club")
        _join_club(client, test_user, club["id"])
        ann = _post_ann(client, test_admin, club["id"], "Delete me")

        resp = client.delete(
            f"/clubs/{club['id']}/announcements/{ann['id']}",
            headers=_admin_headers(client, test_admin),
        )
        assert resp.status_code == 204

        # Gone from list
        items = client.get(
            f"/clubs/{club['id']}/announcements",
            headers=_auth(client, test_user),
        ).json()
        ids = [a["id"] for a in items]
        assert ann["id"] not in ids

    def test_update_by_non_president_forbidden(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Guard Club")
        _join_club(client, test_user, club["id"])
        ann = _post_ann(client, test_admin, club["id"], "Protected")

        resp = client.patch(
            f"/clubs/{club['id']}/announcements/{ann['id']}",
            json={"title": "Hacked"},
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 403

    def test_author_name_returned(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Author Club")
        _join_club(client, test_user, club["id"])
        _post_ann(client, test_admin, club["id"], "Named post")

        items = client.get(
            f"/clubs/{club['id']}/announcements",
            headers=_auth(client, test_user),
        ).json()
        assert items[0]["author_name"] == test_admin.full_name


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 28 — Platform-wide announcements
# ═══════════════════════════════════════════════════════════════════════════════

class TestPlatformAnnouncements:

    def test_any_user_can_read(self, client: TestClient, test_admin, test_user):
        client.post(
            "/announcements/platform",
            json={"title": "Platform Notice", "body": "For everyone"},
            headers=_admin_headers(client, test_admin),
        )
        resp = client.get(
            "/announcements/platform",
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 200
        titles = [a["title"] for a in resp.json()]
        assert "Platform Notice" in titles

    def test_requires_auth(self, client: TestClient):
        resp = client.get("/announcements/platform")
        assert resp.status_code == 401

    def test_college_admin_can_create(self, client: TestClient, test_admin):
        resp = client.post(
            "/announcements/platform",
            json={"title": "Admin Notice", "body": "Important update"},
            headers=_admin_headers(client, test_admin),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["club_id"] is None
        assert body["title"] == "Admin Notice"

    def test_student_cannot_create(self, client: TestClient, test_user):
        resp = client.post(
            "/announcements/platform",
            json={"title": "Sneaky Platform Post", "body": "Nope"},
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 403

    def test_platform_and_club_announcements_are_separate(
        self, client: TestClient, test_admin, test_user
    ):
        club = _make_club(client, test_admin, "Separate Club")
        _join_club(client, test_user, club["id"])

        _post_ann(client, test_admin, club["id"], "Club-only post")
        client.post(
            "/announcements/platform",
            json={"title": "Platform-only post", "body": "..."},
            headers=_admin_headers(client, test_admin),
        )

        platform = client.get(
            "/announcements/platform", headers=_auth(client, test_user)
        ).json()
        club_anns = client.get(
            f"/clubs/{club['id']}/announcements", headers=_auth(client, test_user)
        ).json()

        platform_titles = [a["title"] for a in platform]
        club_titles = [a["title"] for a in club_anns]

        assert "Platform-only post" in platform_titles
        assert "Club-only post" not in platform_titles
        assert "Club-only post" in club_titles
        assert "Platform-only post" not in club_titles
