# College Event & Club System

A campus-wide platform for managing college clubs, events, attendance, certificates, announcements, recruitment drives, and budgets.

**Stack:** FastAPI · PostgreSQL (Neon) · SQLAlchemy 2 · Alembic · Celery + Redis · React 18 + TypeScript (frontend — Phase 6+)

---

## Quick Start

### Prerequisites

- Python 3.11
- PostgreSQL database (local or [Neon](https://neon.tech) cloud)
- Redis (for Celery background tasks)

### 1. Clone and set up the environment

```bash
git clone https://github.com/Yad4o/college-event-system.git
cd college-event-system

# Option A — automated setup (creates venv, installs deps)
bash setup.sh

# Option B — manual
python3.11 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

After the venv is active, you can use the shortcut script in future terminal sessions:

```bash
source ./activate        # Linux / macOS
activate.bat             # Windows CMD
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://user:pass@host/dbname` |
| `SECRET_KEY` | Random 32-byte hex string — run `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALGORITHM` | `HS256` (default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token lifetime (default `30`) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token lifetime (default `7`) |
| `CORS_ORIGINS` | Comma-separated allowed origins, e.g. `http://localhost:5173` |
| `REDIS_URL` | Redis connection string (default `redis://localhost:6379`) |
| `CLOUDINARY_CLOUD_NAME` | From your Cloudinary dashboard |
| `CLOUDINARY_API_KEY` | From your Cloudinary dashboard |
| `CLOUDINARY_API_SECRET` | From your Cloudinary dashboard |
| `SMTP_HOST` | SMTP server for transactional emails |
| `SMTP_PORT` | Usually `587` |
| `SMTP_USER` | SMTP login |
| `SMTP_PASSWORD` | SMTP password |
| `EMAILS_FROM_EMAIL` | Sender address shown to users |
| `APP_NAME` | Displayed in emails and docs (default `College Event System`) |
| `FRONTEND_URL` | Used in email links, e.g. `http://localhost:5173` |

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Start the API server

```bash
uvicorn app.main:app --reload
```

API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 5. Start the Celery worker (for background tasks)

```bash
celery -A app.worker worker --loglevel=info
```

---

## Running Tests

```bash
pytest --cov=app --cov-report=term-missing
```

Tests use an in-memory SQLite database — no Postgres connection needed to run the suite.

---

## Project Structure

```
college-event-system/
├── app/
│   ├── main.py              # FastAPI app factory, middleware, route registration
│   ├── config.py            # Pydantic settings (reads .env)
│   ├── database.py          # SQLAlchemy engine, session, Base
│   ├── models/              # ORM models (one file per domain)
│   │   ├── user.py
│   │   ├── club.py
│   │   ├── event.py
│   │   ├── announcement.py
│   │   ├── certificate.py
│   │   ├── notification.py
│   │   ├── recruitment.py
│   │   └── budget.py
│   ├── routers/             # Route handlers (added per phase)
│   ├── schemas/             # Pydantic request/response models (added per phase)
│   ├── services/            # Business logic (added per phase)
│   ├── tasks/               # Celery tasks: email, PDF, reminders (added per phase)
│   └── utils/               # Helpers: JWT, file upload, QR generation
├── alembic/                 # Database migration scripts
│   ├── env.py
│   ├── script.py.mako
│   └── versions/            # Auto-generated migration files go here
├── tests/
│   ├── conftest.py          # Shared fixtures: test DB, TestClient, user factories
│   └── ...                  # Test files added alongside each phase
├── docs/
│   └── system_design.md     # Architecture, DB schema, auth flow, role matrix
├── .env.example             # Template — copy to .env and fill in values
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Dev/test dependencies
├── alembic.ini              # Alembic configuration
├── setup.sh                 # One-command environment bootstrap
├── activate                 # Source this to activate the venv (Linux/macOS)
└── activate.bat             # Same for Windows CMD
```

---

## Development Phases

| Phase | Scope |
|-------|-------|
| 0 | Project foundation — models, config, migrations, tests scaffold ✅ |
| 1 | Auth — register, login, JWT, email verification, password reset |
| 2 | Clubs — CRUD, membership, join requests, club applications |
| 3 | Events — CRUD, RSVP, waitlist, QR token generation |
| 4 | Attendance — QR scan endpoint, attendance records |
| 5 | Certificates & Badges — PDF generation, verification URL |
| 6 | Announcements — pinned posts, club-level broadcasts |
| 7 | Recruitment — drives, application form, status tracking |
| 8 | Budget & Sponsors — per-event budgets, expense line items |
| 9 | Notifications — in-app + email, real-time via WebSocket |
| 10 | Admin Panel & Analytics — college-level reports, dashboards |

---

## Contributing

1. Pick an unassigned task from the ClickUp board.
2. Create a branch: `git checkout -b feature/<short-description>`
3. Write the feature + tests (aim for 80 % coverage on new code).
4. Open a pull request against `main` — the project lead reviews all PRs.

Refer to `docs/system_design.md` for architecture decisions and the role permission matrix.
