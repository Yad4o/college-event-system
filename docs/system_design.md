# College Event & Club System — System Design

## Overview

A campus-wide platform that lets students discover and join clubs, attend events, earn certificates, and stay updated via announcements. Club admins manage events, recruitment drives, budgets, and sponsors. A college admin oversees everything.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 React 18 (TypeScript)                │
│         Tailwind CSS  ·  PWA Service Worker         │
│         WebSocket client (real-time notifications)  │
└─────────────────────────┬───────────────────────────┘
                          │ HTTPS / WebSocket
┌─────────────────────────▼───────────────────────────┐
│               FastAPI (Python 3.11)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │  Auth    │ │  REST    │ │  WS hub  │            │
│  │  JWT     │ │  Routers │ │  (notif) │            │
│  └──────────┘ └──────────┘ └──────────┘            │
│  ┌─────────────────────────────────────┐            │
│  │         SQLAlchemy 2.0 ORM          │            │
│  └───────────────────┬─────────────────┘            │
└──────────────────────┼──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   PostgreSQL       Redis          Cloudinary
   (Neon)       (Celery broker   (file/image
                 + cache)         storage)
```

**Background tasks** (Celery workers):
- Send email notifications (RSVP confirm, certificate ready)
- Generate PDF certificates
- Send event reminders 24h before start

---

## Modules

| Module | Phase | Key endpoints |
|--------|-------|---------------|
| Auth | 1 | POST /auth/register, /auth/login, /auth/refresh |
| Users | 1 | GET/PATCH /users/me, GET /users/{id} |
| Clubs | 2 | CRUD /clubs, /clubs/{id}/members |
| Events | 3 | CRUD /events, /events/{id}/rsvp |
| Attendance | 4 | POST /attendance/scan, GET /events/{id}/attendance |
| Certificates | 5 | POST /certificates/issue, GET /certificates/{code}/verify |
| Announcements | 6 | CRUD /clubs/{id}/announcements |
| Recruitment | 7 | CRUD /recruitment-drives, POST /recruitment-drives/{id}/apply |
| Budget | 8 | CRUD /budgets, /budgets/{id}/items |
| Notifications | 9 | GET /notifications, PATCH /notifications/{id}/read |
| Admin | 10 | GET /admin/*, analytics, college-level controls |

---

## Database Schema (entity summary)

```
users
  id, email, full_name, password_hash, role
  branch, year, bio, skills, profile_picture
  is_active, is_email_verified, email_verify_token
  password_reset_token, password_reset_expires

clubs
  id, name, description, domain, logo_url, social_links
  join_type, is_active, is_suspended, faculty_advisor_id

club_memberships
  id, user_id → users, club_id → clubs, role, joined_at

club_applications          ← request to register a new club
  id, applicant_id → users, club_name, status, reviewed_by

events
  id, club_id → clubs, title, description, event_type
  tags, venue, poster_image_url, start_at, end_at
  seat_limit, is_cancelled, is_hidden, qr_token

event_rsvps
  id, event_id → events, user_id → users, status, waitlist_position

event_attendance           ← scanned QR on event day
  id, event_id, user_id, marked_at

event_photos / event_feedback / announcements
  (straightforward, see models/)

certificates
  id, event_id, user_id, certificate_type, pdf_url, unique_code

badges / user_badges
  badge definitions + many-to-many with users

notifications
  id, user_id, type, title, message, is_read, link_url

recruitment_drives
  id, club_id, title, open_roles (JSON), form_questions (JSON)
  opens_at, closes_at, is_active

recruitment_applications
  id, drive_id, applicant_id, answers (JSON), status

budgets / budget_items / sponsors
  budget per event or club; line-item expenses; sponsor records
```

---

## Auth Flow

1. `POST /auth/register` — hash password (bcrypt), send verify email (Celery)
2. `GET /auth/verify-email?token=...` — mark `is_email_verified = True`
3. `POST /auth/login` — verify password → return `access_token` (30 min JWT) + `refresh_token` (7 day JWT, stored in HttpOnly cookie)
4. `POST /auth/refresh` — validate refresh token → issue new access token
5. `POST /auth/logout` — client drops tokens; refresh token blocklisted in Redis

All protected routes use `Depends(get_current_user)` which decodes the JWT from the `Authorization: Bearer <token>` header.

---

## Role Permissions Summary

| Action | student | club_admin | faculty_advisor | college_admin |
|--------|---------|------------|-----------------|---------------|
| Browse clubs / events | ✓ | ✓ | ✓ | ✓ |
| RSVP to open event | ✓ | ✓ | ✓ | ✓ |
| Create / edit own club's event | — | ✓ | — | ✓ |
| Mark attendance (QR) | — | ✓ | — | ✓ |
| Issue certificates | — | ✓ | — | ✓ |
| Approve club application | — | — | — | ✓ |
| View budget | — | ✓ (own club) | ✓ (advised club) | ✓ |
| Suspend club | — | — | — | ✓ |

---

## QR Attendance Flow

1. When an event is created, a `qr_token` (signed JWT with `event_id`, short expiry) is generated and stored on the Event row.
2. Club admin displays the QR on a projector — the QR encodes `/attendance/scan?token=<qr_token>`.
3. Student scans → `POST /attendance/scan` validates the token and creates an `EventAttendance` row.
4. After attendance window closes, certificate generation can be triggered for all confirmed attendees.

---

## Background Task Queue (Celery)

Workers are started separately from the FastAPI process:

```bash
celery -A app.worker worker --loglevel=info
```

Task modules (to be created in Phase 3–5):
- `app/tasks/email.py` — transactional emails via SMTP
- `app/tasks/certificate.py` — PDF generation with WeasyPrint
- `app/tasks/reminders.py` — periodic Celery Beat job for event reminders

---

## File Storage (Cloudinary)

All user-uploaded files (event posters, club logos, certificate PDFs, budget receipts) are uploaded to Cloudinary via the `cloudinary` Python SDK. The returned secure URL is stored in the DB column. No files are stored on the server disk.

---

## Testing Strategy

- **Unit tests** — pure functions, schema validators, utility helpers
- **Integration tests** — API routes hit a real SQLite in-memory DB (see `tests/conftest.py`)
- **Coverage target** — 80 % line coverage per phase

Run all tests:

```bash
pytest --cov=app --cov-report=term-missing
```
