import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base, get_db
from app.database.models import Case
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cases.db"


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_case(client):
    response = client.post("/cases")
    assert response.status_code == 201
    data = response.json()
    assert data["case_type"] == "security_deposit_dispute"
    assert data["status"] == "intake_in_progress"
    assert "id" in data


def test_get_case(client):
    create_resp = client.post("/cases")
    case_id = create_resp.json()["id"]

    response = client.get(f"/cases/{case_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == case_id
    assert data["case_type"] == "security_deposit_dispute"


def test_get_case_not_found(client):
    response = client.get("/cases/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_patch_case(client):
    create_resp = client.post("/cases")
    case_id = create_resp.json()["id"]

    response = client.patch(
        f"/cases/{case_id}",
        json={"jurisdiction_state": "Maharashtra"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["jurisdiction_state"] == "Maharashtra"


def test_patch_case_not_found(client):
    response = client.patch(
        "/cases/00000000-0000-0000-0000-000000000000",
        json={"jurisdiction_state": "Maharashtra"},
    )
    assert response.status_code == 404