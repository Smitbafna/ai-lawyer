from app.agents.intake import IntakeAgent
from app.core.config import settings
from app.llm.gemini_provider import GeminiProvider
from app.llm.provider import LLMProvider
from app.orchestrator.workflow import IntakeWorkflow


def get_llm_provider() -> LLMProvider:
    if settings.gemini_api_key:
        return GeminiProvider()
    # Fallback: return a provider that will raise if used without a key
    return GeminiProvider(api_key=None)


def get_intake_workflow() -> IntakeWorkflow:
    provider = get_llm_provider()
    agent = IntakeAgent(provider)
    return IntakeWorkflow(agent)