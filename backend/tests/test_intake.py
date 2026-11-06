import pytest

from app.agents.intake import IntakeAgent, IntakeLLMOutput
from app.database.models import Case
from tests.mock_provider import MockProvider


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def intake_agent(mock_provider):
    return IntakeAgent(mock_provider)


@pytest.fixture
def existing_case():
    return Case(
        id="test-case-id",
        case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={"security_deposit_amount": 25000, "jurisdiction": {"state": "Maharashtra"}},
        missing_information=["vacating_date", "rental_agreement_exists"],
    )


@pytest.mark.asyncio
async def test_extract_facts_from_initial_complaint(intake_agent, mock_provider):
    """Test that the agent extracts new facts from a user message."""
    mock_provider.set_structured_response(
        IntakeLLMOutput(
            extracted_updates={
                "security_deposit_amount": 25000,
                "facts": ["Landlord refuses to return deposit"],
            },
            missing_information=["vacating_date"],
            follow_up_question="When did you vacate the property?",
            intake_status="intake_in_progress",
            assistant_message="Thank you. When did you vacate?",
        )
    )

    case = Case(
        id="case-1",
        case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={},
        missing_information=[],
    )

    result = await intake_agent.run("My landlord won't return my 25000 deposit", case, [])

    assert result.extracted_updates["security_deposit_amount"] == 25000
    assert "vacating_date" in result.missing_information
    assert result.follow_up_question is not None


@pytest.mark.asyncio
async def test_merge_does_not_overwrite_known_facts(intake_agent, mock_provider, existing_case):
    """Test that known facts are not overwritten with null/empty values."""
    merged, _ = IntakeAgent.merge_updates(
        existing_case.structured_facts,
        {"security_deposit_amount": None, "jurisdiction": {"city": None}},
    )
    assert merged["security_deposit_amount"] == 25000
    assert merged["jurisdiction"]["state"] == "Maharashtra"


@pytest.mark.asyncio
async def test_merge_adds_new_facts(intake_agent, mock_provider, existing_case):
    """Test that new facts are added to existing facts."""
    merged, _ = IntakeAgent.merge_updates(
        existing_case.structured_facts,
        {"vacating_date": "2024-01-15", "property_address": "123 Main St"},
    )
    assert merged["vacating_date"] == "2024-01-15"
    assert merged["property_address"] == "123 Main St"
    assert merged["security_deposit_amount"] == 25000  # preserved


@pytest.mark.asyncio
async def test_avoid_repeated_questions(intake_agent, mock_provider, existing_case):
    """Test that the agent doesn't ask for information already provided."""
    mock_provider.set_structured_response(
        IntakeLLMOutput(
            extracted_updates={},
            missing_information=["landlord_response"],
            follow_up_question=None,
            intake_status="intake_in_progress",
            assistant_message="I have all the information I need.",
        )
    )

    result = await intake_agent.run("I already told you everything", existing_case, [])
    assert result.follow_up_question is None
    assert "security_deposit_amount" not in result.missing_information
    assert "jurisdiction" not in str(result.missing_information)


@pytest.mark.asyncio
async def test_handle_contradictory_information(intake_agent, mock_provider):
    """Test handling of contradictory information - new info overrides null but not existing."""
    case = Case(
        id="case-contradict",
        case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={"security_deposit_amount": 25000},
        missing_information=[],
    )

    # New turn provides contradictory value
    mock_provider.set_structured_response(
        IntakeLLMOutput(
            extracted_updates={"security_deposit_amount": 30000},
            missing_information=[],
            follow_up_question=None,
            intake_status="intake_in_progress",
            assistant_message="Updated.",
        )
    )

    merged, conflicts = IntakeAgent.merge_updates(
        case.structured_facts,
        mock_provider._structured_response.extracted_updates,
    )
    # First non-null value wins (existing value kept)
    assert merged["security_deposit_amount"] == 25000
    # Conflict detected because new value differs from existing
    assert "security_deposit_amount" in conflicts


@pytest.mark.asyncio
async def test_handle_invalid_llm_json(intake_agent, mock_provider):
    """Test that invalid JSON from LLM raises an error."""
    mock_provider.set_failure(True, "Invalid JSON response from LLM: ...")

    case = Case(
        id="case-invalid",
        case_type="security_deposit_dispute",
        status="intake_in_progress",
        structured_facts={},
        missing_information=[],
    )

    with pytest.raises(Exception):
        await intake_agent.run("some message", case, [])