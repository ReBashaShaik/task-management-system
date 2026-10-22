"""Give each API test a clean temporary SQLite database."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from dependencies import get_db
from main import app

test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
@event.listens_for(test_engine, "connect")
def enable_test_foreign_keys(connection, _record):
    """Make cascade-delete tests behave like the MySQL database."""
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture
def client():
    Base.metadata.create_all(test_engine)

    def test_database():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = test_database
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(test_engine)


def register(client, name, email, role="member"):
    response = client.post("/auth/register", json={"name": name, "email": email,
        "password": "StrongPass123!", "role": role})
    assert response.status_code == 201
    return response.json()


def login(client, email):
    response = client.post("/auth/login", data={"email": email, "password": "StrongPass123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
