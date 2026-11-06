"""Mock LLM provider for deterministic testing."""

from typing import Optional, TypeVar

from pydantic import BaseModel

from app.llm.provider import LLMProvider, LLMProviderError

T = TypeVar("T", bound=BaseModel)


class MockProvider(LLMProvider[T]):
    """
    Mock provider that returns canned responses.
    Tests can set responses via `set_response()` or `set_structured_response()`.
    """

    def __init__(self):
        self._text_response: Optional[str] = None
        self._structured_response: Optional[BaseModel] = None
        self._should_fail: bool = False
        self._fail_error: str = "Provider failure"
        self.call_count: int = 0
        self.last_prompt: Optional[str] = None
        self.last_system_prompt: Optional[str] = None

    def set_text_response(self, text: str) -> None:
        self._text_response = text

    def set_structured_response(self, response: BaseModel) -> None:
        self._structured_response = response

    def set_failure(self, should_fail: bool = True, error: str = "Provider failure") -> None:
        self._should_fail = should_fail
        self._fail_error = error

    def reset(self) -> None:
        self._text_response = None
        self._structured_response = None
        self._should_fail = False
        self.call_count = 0
        self.last_prompt = None
        self.last_system_prompt = None

    async def generate_structured_output(
        self, prompt: str, schema: type[T], system_prompt: Optional[str] = None
    ) -> T:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt

        if self._should_fail:
            raise LLMProviderError(self._fail_error)

        if self._structured_response is not None:
            return self._structured_response  # type: ignore[return-value]

        # Fallback: construct an empty instance of the schema
        return schema()  # type: ignore[call-arg]

    async def generate_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt

        if self._should_fail:
            raise LLMProviderError(self._fail_error)

        if self._text_response is not None:
            return self._text_response

        return "Mock response"