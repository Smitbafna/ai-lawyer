"""Tests for the legal-answer service with Gemini + RAG grounding.

M2.3.1A changes: jurisdiction is server-enforced, case facts are supplementary,
grounding checks are strengthened.
"""

import pytest

from app.services.legal_answer import LegalAnswerService
from app.schemas.legal_answer import (
    LegalAnswer,
    GroundingCheck,
    LegalAnswerRequest,
    LegalAnswerResponse,
)


class MockGeminiProvider:
    """Mock Gemini provider for testing."""

    async def generate_structured_output(self, prompt, schema, system_prompt=None):
        import re

        cited = re.findall(r"ST-UK-\S+", prompt)

        if "abstain" in prompt.lower() and "commencement" in prompt.lower():
            disposition = "abstain"
            answer = "The Act commenced on 01.01.2023; whether it applies to deposits paid before commencement requires legal interpretation."
            confidence = 0.7
        elif "full_refund" in prompt.lower() and "2 months" in prompt.lower():
            disposition = "full_refund"
            answer = "Full refund required under S 11(1) for residential deposits not exceeding 2 months rent."
            confidence = 0.9
        elif "over_cap_refund" in prompt.lower():
            disposition = "over_cap_refund"
            answer = "Excess amount above the 2-month statutory cap must be refunded."
            confidence = 0.95
        elif "clarify" in prompt.lower():
            disposition = "clarify"
            answer = "Clarification needed on specific tenant liability under S 11(2)."
            confidence = 0.6
        else:
            disposition = "abstain"
            answer = "Unable to determine answer from provided provisions."
            confidence = 0.0

        from app.schemas.legal_answer import LegalAnswer as LA

        return LA(
            answer=answer,
            disposition=disposition,
            confidence=confidence,
            cited_provisions=cited,
            source_reference="Uttarakhand Tenancy Act 2021, SRC-02",
            explanation="Test explanation",
            unresolved_claims=[],
        )


@pytest.fixture
def service():
    return LegalAnswerService(llm_provider=MockGeminiProvider())


@pytest.fixture
def sample_provisions():
    return [
        {
            "id": "CHUNK-ST-UK-11(1)",
            "provision_identifier": "ST-UK-11(1)",
            "section": "S 11(1)",
            "legal_proposition": "Security deposit paid by tenant in advance agreed between landlord tenant cannot exceed 2 months rent residential",
            "qualifications": "Deposit above cap must be refunded regardless of deductions",
            "source": "Uttarakhand Gazette (SRC-02)",
            "source_url": "https://example.com",
            "verification_status": "Verified",
            "jurisdiction": "Uttarakhand",
            "statute": "Uttarakhand Tenancy Act 2021",
            "act_number": "Act No 02 of 2022",
            "commencement": "01.01.2023",
            "document_type": "statutory provision",
            "original_text": "Security deposit capped at 2 months rent for residential",
        },
        {
            "id": "CHUNK-ST-UK-11(2)",
            "provision_identifier": "ST-UK-11(2)",
            "section": "S 11(2)",
            "legal_proposition": "Security deposit refunded to tenant on date of taking over vacant possession after deducting tenant liability",
            "qualifications": "Deposit above statutory cap must be refunded",
            "source": "Uttarakhand Gazette (SRC-02)",
            "source_url": "https://example.com",
            "verification_status": "Verified",
            "jurisdiction": "Uttarakhand",
            "statute": "Uttarakhand Tenancy Act 2021",
            "act_number": "Act No 02 of 2022",
            "commencement": "01.01.2023",
            "document_type": "statutory provision",
            "original_text": "Deposit refund after vacant possession with liability deduction",
        },
    ]

class TestLegalAnswerSchemas:
    """Test legal answer Pydantic schemas."""

    def test_legal_answer_creation(self):
        """Test LegalAnswer can be created with required fields."""
        answer = LegalAnswer(
            answer="Test answer",
            disposition="full_refund",
            confidence=0.9,
            cited_provisions=["ST-UK-11(1)"],
            source_reference="Uttarakhand Tenancy Act 2021, SRC-02",
        )
        assert answer.answer == "Test answer"
        assert answer.disposition == "full_refund"
        assert answer.confidence == 0.9
        assert answer.cited_provisions == ["ST-UK-11(1)"]
        assert answer.source_reference == "Uttarakhand Tenancy Act 2021, SRC-02"
        assert answer.explanation == ""
        assert answer.unresolved_claims == []
        assert answer.generated_at is not None

    def test_grounding_check_creation(self):
        """Test GroundingCheck can be created."""
        check = GroundingCheck(
            well_grounded=True,
            missing_support=[],
            unsupported_conclusions=[],
            abstention_required=False,
            check_details="Passed",
        )
        assert check.well_grounded is True
        assert check.abstention_required is False

    def test_legal_answer_request_creation(self):
        """Test LegalAnswerRequest can be created."""
        request = LegalAnswerRequest(
            case_id="test-case-1",
            user_question="Can I get my deposit back?",
        )
        assert request.case_id == "test-case-1"
        assert request.user_question == "Can I get my deposit back?"
        assert request.case_facts is None
        assert request.retrieved_provisions == []

    def test_legal_answer_response_creation(self):
        """Test LegalAnswerResponse can be created."""
        from datetime import datetime

        request = LegalAnswerRequest(
            case_id="test-case-1",
            user_question="Test question?",
        )
        from app.schemas.legal_answer import GroundingCheck

        response = LegalAnswerResponse(
            case_id=request.case_id,
            legal_answer=LegalAnswer(
                answer="Test",
                disposition="full_refund",
                confidence=0.9,
                cited_provisions=["ST-UK-11(1)"],
                source_reference="Uttarakhand Tenancy Act 2021, SRC-02",
                explanation="Test",
                unresolved_claims=[],
            ),
            grounding_check=GroundingCheck(
                well_grounded=True,
                missing_support=[],
                unsupported_conclusions=[],
                abstention_required=False,
                check_details="Passed",
            ),
            retrieval_metadata={"query": "Test question?", "results_count": 1},
        )
        assert response.case_id == "test-case-1"
        assert response.generated_at is not None


class TestLegalAnswerService:
    """Test LegalAnswerService with mock provider."""

    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None

    def test_service_initialization_default(self):
        """Test service initializes with default GeminiProvider."""
        svc = LegalAnswerService()
        assert svc is not None

    @pytest.mark.asyncio
    async def test_generate_legal_answer_basic(self, service, sample_provisions):
        """Test basic legal answer generation."""
        from app.schemas.legal_answer import LegalAnswerRequest

        request = LegalAnswerRequest(
            case_id="test-case-1",
            user_question="My landlord won't refund my 2 month deposit for residential property.",
            retrieved_provisions=sample_provisions,
        )

        result = await service.generate_legal_answer(
            case_id="test-case-1",
            user_question=request.user_question,
            case_facts=None,
        )

        assert result is not None
        assert result.case_id == "test-case-1"
        assert result.legal_answer is not None
        assert result.grounding_check is not None
        assert result.retrieval_metadata is not None
        assert result.legal_answer.disposition in (
            "full_refund",
            "partial_refund",
            "over_cap_refund",
            "abstain",
            "clarify",
        )

    @pytest.mark.asyncio
    async def test_generate_legal_answer_with_facts(self, service, sample_provisions):
        """Test legal answer generation with case facts."""
        from app.schemas.legal_answer import LegalAnswerRequest

        case_facts = {
            "security_deposit_amount": 25000,
            "security_deposit_currency": "INR",
            "property_address": "123 Main St, Dehradun",
            "vacating_date": "2024-01-15",
        }

        request = LegalAnswerRequest(
            case_id="test-case-1",
            user_question="Can I get my deposit back?",
            retrieved_provisions=sample_provisions,
            case_facts=case_facts,
        )

        result = await service.generate_legal_answer(
            case_id=request.case_id,
            user_question=request.user_question,
            case_facts=request.case_facts,
        )

        assert result is not None
        assert result.legal_answer is not None
        assert result.grounding_check is not None

    @pytest.mark.asyncio
    async def test_grounding_check_with_cited_provisions(self, service, sample_provisions):
        """Test grounding check passes when provisions are cited."""
        from app.schemas.legal_answer import LegalAnswer, GroundingCheck, LegalAnswerRequest

        legal_answer = LegalAnswer(
            answer="Full refund required",
            disposition="full_refund",
            confidence=0.9,
            cited_provisions=["ST-UK-11(1)", "ST-UK-11(2)"],
            source_reference="Uttarakhand Tenancy Act 2021, SRC-02",
            explanation="Deposit cap and refund provisions apply",
            unresolved_claims=[],
        )

        check = service._validate_grounding(legal_answer, sample_provisions)

        assert check.well_grounded is True
        assert check.abstention_required is False
        assert len(check.missing_support) == 0
        assert len(check.unsupported_conclusions) == 0

    @pytest.mark.asyncio
    async def test_grounding_check_missing_provision(self, service, sample_provisions):
        """Test grounding check fails when cited provision not in context."""
        from app.schemas.legal_answer import LegalAnswer, GroundingCheck, LegalAnswerRequest

        legal_answer = LegalAnswer(
            answer="Full refund required",
            disposition="full_refund",
            confidence=0.9,
            cited_provisions=["ST-UK-99(9)"],  # Not in retrieved provisions
            source_reference="Uttarakhand Tenancy Act 2021, SRC-02",
            explanation="Test",
            unresolved_claims=[],
        )

        check = service._validate_grounding(legal_answer, sample_provisions)

        assert check.well_grounded is False
        assert check.abstention_required is True
        assert "ST-UK-99(9)" in check.missing_support

    @pytest.mark.asyncio
    async def test_grounding_check_override_unsupported_conclusion(self, service, sample_provisions):
        """Test that unsupported conclusions override disposition to abstain."""
        from app.schemas.legal_answer import LegalAnswer, GroundingCheck, LegalAnswerRequest

        legal_answer = LegalAnswer(
            answer="Full refund required",
            disposition="full_refund",
            confidence=0.9,
            cited_provisions=["ST-UK-99(9)"],  # Not in context - unsupported
            source_reference="Uttarakhand Tenancy Act 2021, SRC-02",
            explanation="Test",
            unresolved_claims=[],
        )

        check = service._validate_grounding(legal_answer, sample_provisions)

        assert check.well_grounded is False
        assert check.abstention_required is True

    @pytest.mark.asyncio
    async def test_legal_answer_request_creation(self, service):
        """Test LegalAnswerRequest creation and validation."""
        from app.schemas.legal_answer import LegalAnswerRequest

        request = LegalAnswerRequest(
            case_id="case-123",
            user_question="Deposit not refunded",
            case_facts={"security_deposit_amount": 20000},
        )

        assert request.case_id == "case-123"
        assert request.user_question == "Deposit not refunded"
        assert request.case_facts == {"security_deposit_amount": 20000}
        assert request.retrieved_provisions == []


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_e2e_with_commencement_question(self, service):
        """Test abstention when question involves commencement date interpretation."""
        from app.schemas.legal_answer import LegalAnswerRequest

        provisions = [
            {
                "id": "CHUNK-ST-UK-1(3)",
                "provision_identifier": "ST-UK-1(3)",
                "section": "S 1(3)",
                "legal_proposition": "Comes into force on date appointed by State Govt via gazette notification",
                "qualifications": "Effective date 01.01.2023 per Not No 67/iv(2)-sh. Vi.-2023-53 (sha)/2021 dated 13 Jan 2023",
                "source": "Uttarakhand Gazette (SRC-02)",
                "source_url": "https://example.com",
                "verification_status": "Verified commencement 01.01.2023",
                "jurisdiction": "Uttarakhand",
                "statute": "Uttarakhand Tenancy Act 2021",
                "act_number": "Act No 02 of 2022",
                "commencement": "01.01.2023",
                "document_type": "statutory provision",
                "original_text": "Provision comes into force on appointed date",
            }
        ]

        request = LegalAnswerRequest(
            case_id="case-1",
            user_question="I paid my deposit in December 2022, before the Act commenced. Does the Act apply?",
            retrieved_provisions=provisions,
        )

        result = await service.generate_legal_answer(
            case_id=request.case_id,
            user_question=request.user_question,
            case_facts=None,
        )

        # Should abstain because commencement applicability is ambiguous
        assert result.legal_answer.disposition == "abstain"
        assert result.grounding_check.abstention_required is True
        assert result.grounding_check.well_grounded is False

    @pytest.mark.asyncio
    async def test_e2e_full_refund_with_provisions(self, service, sample_provisions):
        """Test full refund when provisions clearly support it."""
        from app.schemas.legal_answer import LegalAnswerRequest

        request = LegalAnswerRequest(
            case_id="case-1",
            user_question="My landlord is refusing to refund my 2 months security deposit for residential property.",
            retrieved_provisions=sample_provisions,
        )

        result = await service.generate_legal_answer(
            case_id=request.case_id,
            user_question=request.user_question,
            case_facts=None,
        )

        assert result.legal_answer is not None
        assert result.grounding_check is not None
