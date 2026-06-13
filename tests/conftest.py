"""
Shared pytest fixtures used by all tests.

Flow:
  engine_with_schema  — creates all tables in a test SQLite DB (in-memory)
  db_session          — gives each test a fresh, rolled-back session
  client              — a TestClient wired to the test DB via dependency override
  test_user / test_admin — pre-inserted User rows for common scenarios
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app as fastapi_app   # alias avoids shadowing the `app` package
import app.models  # noqa: F401 — ensure all models are registered with Base.metadata

# ---------------------------------------------------------------------------
# Test database — SQLite in-memory so tests never touch a real Postgres DB
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine_with_schema():
    """Create all tables once per test session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(engine_with_schema):
    """
    Each test gets a fresh session wrapped in a transaction that is rolled
    back at the end — leaves the DB clean for the next test.
    """
    connection = engine_with_schema.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with the DB dependency overridden to use the test session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Convenience user factories
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_user(db_session):
    """A plain student user."""
    from app.models.user import User, UserRole
    from passlib.context import CryptContext

    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        email="student@test.com",
        full_name="Test Student",
        password_hash=pwd_ctx.hash("password123"),
        role=UserRole.student,
        is_email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def test_admin(db_session):
    """A college admin user."""
    from app.models.user import User, UserRole
    from passlib.context import CryptContext

    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    admin = User(
        email="admin@test.com",
        full_name="Test Admin",
        password_hash=pwd_ctx.hash("adminpass123"),
        role=UserRole.college_admin,
        is_email_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin
