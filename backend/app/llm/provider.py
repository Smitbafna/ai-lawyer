from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""

    pass


class LLMProvider(ABC, Generic[T]):
    """Provider-independent interface for LLM interactions."""

    @abstractmethod
    async def generate_structured_output(
        self, prompt: str, schema: type[T], system_prompt: Optional[str] = None
    ) -> T:
        """Generate structured output conforming to the given Pydantic schema."""
        ...

    @abstractmethod
    async def generate_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate a plain-text response."""
        ...


# Re-export Optional for type hints used above
from typing import Optional  # noqa: E402