import asyncio

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base, get_db
from app.database.models import Case
from app.main import app
from app.orchestrator.workflow import IntakeWorkflow
from tests.mock_provider import MockProvider

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_workflow.db"


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def intake_workflow(mock_provider):
    from app.agents.intake import IntakeAgent

    agent = IntakeAgent(mock_provider)
    return IntakeWorkflow(agent)


def test_create_and_retrieve_case(db_session):
    from app.services.case_service import create_case, get_case

    case = create_case(db_session)
    assert case.id is not None
    assert case.case_type == "security_deposit_dispute"
    assert case.status == "intake_in_progress"

    retrieved = get_case(db_session, case.id)
    assert retrieved is not None
    assert retrieved.id == case.id


def test_handle_llm_provider_failure(intake_workflow, mock_provider, db_session):
    """Test that LLM provider failure is not silently swallowed."""
    mock_provider.set_failure(True, "API rate limit exceeded")

    from app.services.case_service import create_case

    case = create_case(db_session, case_type="security_deposit_dispute")

    with pytest.raises(Exception):
        asyncio.run(intake_workflow.process_message(case.id, "My landlord won't pay"))


def test_handle_invalid_llm_json(intake_workflow, mock_provider, db_session):
    """Test handling invalid LLM JSON."""
    mock_provider.set_failure(True, "Invalid JSON response from LLM: Expecting value")

    from app.services.case_service import create_case

    case = create_case(db_session)

    with pytest.raises(Exception):
        asyncio.run(intake_workflow.process_message(case.id, "some message"))


def test_untrusted_input_cannot_modify_system(db_session):
    """Test that untrusted user input cannot directly modify database records."""
    from app.services.case_service import create_case, update_case_facts

    case = create_case(db_session)
    case_id = case.id

    # Simulate untrusted input trying to inject fields
    malicious_facts = {"__class__": "Case", "status": "intake_complete", "id": "hacked"}
    update_case_facts(db_session, case_id, malicious_facts, [])

    updated = db_session.query(Case).filter(Case.id == case_id).first()
    # The structured facts should only contain what was passed, not modify system fields directly
    assert updated.structured_facts == malicious_facts
    # Status should NOT be changed by the facts update
    assert updated.status == "intake_in_progress"