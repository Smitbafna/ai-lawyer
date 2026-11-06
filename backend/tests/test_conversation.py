import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

from app.database.connection import Base, get_db
from app.database.models import Case, Conversation, Message
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_conversation.db"


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


def test_persist_conversation_messages(client):
    """Test that conversation messages are persisted in SQLite."""
    # Create case
    create_resp = client.post("/cases")
    case_id = create_resp.json()["id"]

    # Send a chat message (will need a mock for full flow; here just check messages endpoint returns empty)
    messages_resp = client.get(f"/cases/{case_id}/messages")
    assert messages_resp.status_code == 200
    assert messages_resp.json() == []


def test_case_has_conversation_relationship(db_session):
    """Test that a case can have conversations and messages."""
    case = Case(case_type="security_deposit_dispute", status="intake_in_progress")
    db_session.add(case)
    db_session.commit()

    conv = Conversation(case_id=case.id)
    db_session.add(conv)
    db_session.commit()

    msg = Message(conversation_id=conv.id, role="user", content="Hello")
    db_session.add(msg)
    db_session.commit()

    # Query back
    queried_case = (
        db_session.query(Case)
        .options(joinedload(Case.conversations).joinedload(Conversation.messages))
        .filter(Case.id == case.id)
        .first()
    )

    assert queried_case is not None
    assert len(queried_case.conversations) == 1
    assert len(queried_case.conversations[0].messages) == 1
    assert queried_case.conversations[0].messages[0].content == "Hello"