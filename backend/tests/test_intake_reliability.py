"""
M1.2 reliability and data-integrity tests.

Covers correctable facts, fact provenance, atomic persistence, concurrency,
LLM provider reliability, and full multi-turn integration via HTTP API.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.intake import IntakeAgent, IntakeLLMOutput
from app.api.deps import get_intake_workflow
from app.database.connection import Base, get_db
from app.database.models import Case, Conversation, Message
from app.main import app
from app.orchestrator.workflow import IntakeWorkflow
from app.llm.gemini_provider import GeminiProvider
from tests.mock_provider import MockProvider

import uuid

SQLALCHEMY_DATABASE_URL = f"sqlite:///{__import__('tempfile').gettempdir()}/test_reliability_{uuid.uuid4().hex}.db"


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


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def intake_agent(mock_provider):
    return IntakeAgent(mock_provider)


# ============================================================================
# M1.2A — Correctable facts
# ============================================================================

@pytest.mark.asyncio
async def test_explicit_correction_overwrites_existing(intake_agent, mock_provider):
    existing_case = Case(
        id="case-correct", case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={"security_deposit_amount": 25000},
        missing_information=[],
    )
    mock_provider.set_structured_response(
        IntakeLLMOutput(
            extracted_updates={}, corrections={"security_deposit_amount": 30000},
            missing_information=[], follow_up_question=None,
            intake_status="intake_in_progress", assistant_message="Corrected to 30000.",
        )
    )
    merged, conflicts = IntakeAgent.merge_updates(
        existing_case.structured_facts, {},
        mock_provider._structured_response.corrections,
    )
    assert merged["security_deposit_amount"] == 30000
    assert conflicts == []


@pytest.mark.asyncio
async def test_ambiguous_contradiction_preserves_existing(intake_agent, mock_provider):
    existing_case = Case(
        id="case-ambiguous", case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={"security_deposit_amount": 25000},
        missing_information=[],
    )
    mock_provider.set_structured_response(
        IntakeLLMOutput(
            extracted_updates={"security_deposit_amount": 30000}, corrections={},
            missing_information=[], confirmation_needed=["security_deposit_amount"],
            follow_up_question="Did you mean 30000 instead of 25000?",
            intake_status="intake_in_progress", assistant_message="Which is correct?",
        )
    )
    merged, conflicts = IntakeAgent.merge_updates(
        existing_case.structured_facts,
        mock_provider._structured_response.extracted_updates,
        mock_provider._structured_response.corrections,
    )
    assert merged["security_deposit_amount"] == 25000
    assert "security_deposit_amount" in conflicts


@pytest.mark.asyncio
async def test_confirmed_correction_updates_fact(intake_agent, mock_provider):
    existing_case = Case(
        id="case-confirm", case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={"security_deposit_amount": 25000},
        missing_information=["security_deposit_amount"],
    )
    mock_provider.set_structured_response(
        IntakeLLMOutput(
            extracted_updates={}, corrections={"security_deposit_amount": 30000},
            missing_information=[], confirmation_needed=[], follow_up_question=None,
            intake_status="intake_in_progress", assistant_message="Thank you, updated to 30000.",
        )
    )
    merged, conflicts = IntakeAgent.merge_updates(
        existing_case.structured_facts, {},
        mock_provider._structured_response.corrections,
    )
    assert merged["security_deposit_amount"] == 30000
    assert conflicts == []


@pytest.mark.asyncio
async def test_null_updates_do_not_overwrite(intake_agent, mock_provider):
    existing_case = Case(
        id="case-null", case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={"security_deposit_amount": 25000, "property_address": "123 Main St"},
        missing_information=[],
    )
    merged, _ = IntakeAgent.merge_updates(
        existing_case.structured_facts,
        {"security_deposit_amount": None, "property_address": None},
    )
    assert merged["security_deposit_amount"] == 25000
    assert merged["property_address"] == "123 Main St"


@pytest.mark.asyncio
async def test_empty_string_updates_do_not_overwrite(intake_agent, mock_provider):
    existing_case = Case(
        id="case-empty", case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={"property_address": "123 Main St"}, missing_information=[],
    )
    merged, _ = IntakeAgent.merge_updates(
        existing_case.structured_facts, {"property_address": ""},
    )
    assert merged["property_address"] == "123 Main St"


@pytest.mark.asyncio
async def test_nested_dict_merge(intake_agent, mock_provider):
    existing_case = Case(
        id="case-nested", case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={"jurisdiction": {"state": "Maharashtra"}},
        missing_information=[],
    )
    merged, _ = IntakeAgent.merge_updates(
        existing_case.structured_facts, {"jurisdiction": {"city": "Pune"}},
    )
    assert merged["jurisdiction"]["state"] == "Maharashtra"
    assert merged["jurisdiction"]["city"] == "Pune"


@pytest.mark.asyncio
async def test_duplicate_list_entries_deduplicated(intake_agent, mock_provider):
    existing_case = Case(
        id="case-list", case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={"facts": ["tenant paid rent on time"]},
        missing_information=[],
    )
    merged, _ = IntakeAgent.merge_updates(
        existing_case.structured_facts,
        {"facts": ["tenant paid rent on time", "landlord received deposit"]},
    )
    assert merged["facts"] == ["tenant paid rent on time", "landlord received deposit"]
    assert len(merged["facts"]) == 2


@pytest.mark.asyncio
async def test_system_fields_stripped_from_updates(intake_agent, mock_provider):
    existing_case = Case(
        id="case-system", case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={}, missing_information=[],
    )
    merged, _ = IntakeAgent.merge_updates(
        existing_case.structured_facts,
        {"id": "hacked-id", "status": "intake_complete", "security_deposit_amount": 25000},
    )
    assert "id" not in merged
    assert "status" not in merged
    assert merged["security_deposit_amount"] == 25000


# ============================================================================
# M1.2B — Fact provenance
# ============================================================================

@pytest.mark.asyncio
async def test_provenance_tracks_model_extracted_facts(intake_agent, mock_provider):
    workflow = IntakeWorkflow(intake_agent)
    llm_output = IntakeLLMOutput(
        extracted_updates={"security_deposit_amount": 25000}, corrections={},
        missing_information=[], confirmation_needed=[], follow_up_question=None,
        intake_status="intake_in_progress", assistant_message="Noted.",
    )
    prov = workflow._build_provenance({}, llm_output, turn_index=1)
    assert prov["security_deposit_amount"]["source"] == "model"
    assert prov["security_deposit_amount"]["confirmed"] is False
    assert prov["security_deposit_amount"]["turn"] == 1


@pytest.mark.asyncio
async def test_provenance_tracks_user_corrections(intake_agent, mock_provider):
    workflow = IntakeWorkflow(intake_agent)
    llm_output = IntakeLLMOutput(
        extracted_updates={}, corrections={"security_deposit_amount": 30000},
        missing_information=[], confirmation_needed=[], follow_up_question=None,
        intake_status="intake_in_progress", assistant_message="Corrected.",
    )
    prov = workflow._build_provenance({}, llm_output, turn_index=2)
    assert prov["security_deposit_amount"]["source"] == "user"
    assert prov["security_deposit_amount"]["confirmed"] is True
    assert prov["security_deposit_amount"]["turn"] == 2


@pytest.mark.asyncio
async def test_provenance_preserves_previous_entries(intake_agent, mock_provider):
    workflow = IntakeWorkflow(intake_agent)
    existing_prov = {
        "security_deposit_amount": {"source": "model", "confirmed": False, "turn": 1}
    }
    llm_output = IntakeLLMOutput(
        extracted_updates={"vacating_date": "2024-01-15"}, corrections={},
        missing_information=[], confirmation_needed=[], follow_up_question=None,
        intake_status="intake_in_progress", assistant_message="Noted.",
    )
    prov = workflow._build_provenance(existing_prov, llm_output, turn_index=2)
    assert prov["security_deposit_amount"]["turn"] == 1
    assert prov["vacating_date"]["source"] == "model"
    assert prov["vacating_date"]["turn"] == 2


# ============================================================================
# M1.2C — Atomic persistence
# ============================================================================

@pytest.mark.asyncio
async def test_llm_failure_no_orphaned_user_message(mock_provider, db_session):
    """LLM failure must not persist an orphaned user message."""
    from app.services.case_service import create_case

    mock_provider.set_failure(True, "API rate limit exceeded")
    workflow = IntakeWorkflow(IntakeAgent(mock_provider))

    case = create_case(db_session, case_type="security_deposit_dispute")
    case_id = case.id

    conv = db_session.query(Conversation).filter(Conversation.case_id == case_id).first()
    msg_count_before = len(db_session.query(Message).filter(Message.conversation_id == conv.id).all()) if conv else 0

    with pytest.raises(Exception):
        asyncio.run(workflow.process_message(case_id, "My landlord won't pay"))

    conv = db_session.query(Conversation).filter(Conversation.case_id == case_id).first()
    msg_count_after = len(db_session.query(Message).filter(Message.conversation_id == conv.id).all()) if conv else 0
    assert msg_count_after == msg_count_before

    db_session.expire_all()
    unchanged = db_session.query(Case).filter(Case.id == case_id).first()
    assert unchanged.structured_facts == {}


def test_concurrent_version_mismatch_rejected(db_session, mock_provider):
    """Concurrent updates with stale version are rejected."""
    from app.services.case_service import create_case, update_case_facts

    case = create_case(db_session, case_type="security_deposit_dispute")
    case_id = case.id
    original_version = case.version

    update_case_facts(db_session, case_id, {"security_deposit_amount": 99999}, [], expected_version=original_version)
    db_session.commit()

    with pytest.raises(ValueError, match="version mismatch"):
        update_case_facts(
            db_session, case_id, {"vacating_date": "2024-01-15"}, [],
            expected_version=original_version,
        )


def test_successful_turn_increments_version(db_session, mock_provider):
    """Each successful update increments the case version."""
    from app.services.case_service import create_case, update_case_facts

    case = create_case(db_session, case_type="security_deposit_dispute")
    case_id = case.id
    v1 = case.version

    update_case_facts(db_session, case_id, {"security_deposit_amount": 25000}, [], expected_version=v1)
    db_session.commit()

    db_session.expire_all()
    updated = db_session.query(Case).filter(Case.id == case_id).first()
    assert updated.version == v1 + 1


# ============================================================================
# M1.2D — LLM provider reliability
# ============================================================================

@pytest.mark.asyncio
async def test_mock_provider_simulates_timeout(mock_provider):
    mock_provider.set_failure(True, "TimeoutError: deadline exceeded")

    case = Case(
        id="case-timeout", case_type="security_deposit_dispute",
        status="intake_in_progress", structured_facts={}, missing_information=[],
    )
    agent = IntakeAgent(mock_provider)
    with pytest.raises(Exception):
        await agent.run("test message", case, [])


def test_gemini_provider_timeout_configuration():
    import inspect
    sig = inspect.signature(GeminiProvider.__init__)
    assert "timeout" in sig.parameters


# ============================================================================
# M1.2E — Full multi-turn integration via HTTP API
# ============================================================================

def test_multi_turn_conversation_with_correction(mock_provider):
    """Full integration test: create case, complain, provide missing info, correct a fact."""
    from fastapi.testclient import TestClient
    from app.database.connection import Base, get_db, engine
    from sqlalchemy.orm import sessionmaker

    # Use a dedicated engine/session for this test to avoid fixture cross-talk
    test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    test_db = TestSessionLocal()

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    def override_workflow():
        agent = IntakeAgent(mock_provider)
        return IntakeWorkflow(agent)

    app.dependency_overrides[get_intake_workflow] = override_workflow

    try:
        client = TestClient(app)
        create_resp = client.post("/cases")
        assert create_resp.status_code == 201
        case_id = create_resp.json()["id"]

        mock_provider.set_structured_response(
            IntakeLLMOutput(
                extracted_updates={"security_deposit_amount": 25000}, corrections={},
                missing_information=["vacating_date", "rental_agreement_exists"],
                confirmation_needed=[], follow_up_question="When did you vacate?",
                intake_status="intake_in_progress",
                assistant_message="Recorded deposit of ₹25,000. When did you vacate?",
            )
        )
        chat_resp = client.post(
            f"/cases/{case_id}/chat",
            json={"message": "My landlord refuses to return my 25000 rupee deposit. I vacated two weeks ago."},
        )
        assert chat_resp.status_code == 200
        data = chat_resp.json()
        assert data["updated_case"]["structured_facts"]["security_deposit_amount"] == 25000
        assert "confirmation_needed" in data

        mock_provider.set_structured_response(
            IntakeLLMOutput(
                extracted_updates={"vacating_date": "2024-10-20"}, corrections={},
                missing_information=["rental_agreement_exists"], confirmation_needed=[],
                follow_up_question="Written rental agreement?",
                intake_status="intake_in_progress",
                assistant_message="Thank you. Written rental agreement?",
            )
        )
        chat_resp2 = client.post(
            f"/cases/{case_id}/chat",
            json={"message": "I vacated on October 20, 2024."},
        )
        assert chat_resp2.status_code == 200
        data2 = chat_resp2.json()
        assert data2["updated_case"]["structured_facts"]["vacating_date"] == "2024-10-20"
        assert data2["updated_case"]["structured_facts"]["security_deposit_amount"] == 25000

        mock_provider.set_structured_response(
            IntakeLLMOutput(
                extracted_updates={}, corrections={"security_deposit_amount": 30000},
                missing_information=["rental_agreement_exists"], confirmation_needed=[],
                follow_up_question=None, intake_status="intake_in_progress",
                assistant_message="Corrected deposit to ₹30,000.",
            )
        )
        chat_resp3 = client.post(
            f"/cases/{case_id}/chat",
            json={"message": "Actually, the deposit was 30000, not 25000."},
        )
        assert chat_resp3.status_code == 200
        data3 = chat_resp3.json()
        assert data3["updated_case"]["structured_facts"]["security_deposit_amount"] == 30000
        assert data3["updated_case"]["structured_facts"]["vacating_date"] == "2024-10-20"

        msgs_resp = client.get(f"/cases/{case_id}/messages")
        assert msgs_resp.status_code == 200
        messages = msgs_resp.json()
        assert len(messages) == 6
        user_msgs = [m for m in messages if m["role"] == "user"]
        asst_msgs = [m for m in messages if m["role"] == "assistant"]
        assert len(user_msgs) == 3
        assert len(asst_msgs) == 3

        case_resp = client.get(f"/cases/{case_id}")
        assert case_resp.status_code == 200
        final_case = case_resp.json()
        assert final_case["structured_facts"]["security_deposit_amount"] == 30000
        assert final_case["structured_facts"]["vacating_date"] == "2024-10-20"
        assert final_case["version"] >= 1

        test_db.close()
    finally:
        app.dependency_overrides.pop(get_intake_workflow, None)
        app.dependency_overrides.pop(get_db, None)


def test_llm_failure_no_orphaned_message_http(client, mock_provider):
    def override_workflow():
        agent = IntakeAgent(mock_provider)
        return IntakeWorkflow(agent)

    app.dependency_overrides[get_intake_workflow] = override_workflow
    try:
        create_resp = client.post("/cases")
        case_id = create_resp.json()["id"]

        mock_provider.set_failure(True, "API failure")
        chat_resp = client.post(
            f"/cases/{case_id}/chat",
            json={"message": "This should fail"},
        )
        assert chat_resp.status_code in (400, 500)

        msgs_resp = client.get(f"/cases/{case_id}/messages")
        assert msgs_resp.status_code == 200
        messages = msgs_resp.json()
        assert len(messages) == 0
    finally:
        app.dependency_overrides.pop(get_intake_workflow, None)