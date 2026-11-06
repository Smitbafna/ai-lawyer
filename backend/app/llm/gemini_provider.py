import asyncio
import json
import logging
from typing import Any, Optional, TypeVar

import google.generativeai as genai
from pydantic import BaseModel

from app.core.config import settings
from app.llm.provider import LLMProvider, LLMProviderError, LLMTimeoutError, LLMRateLimitError, LLMServiceError

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.0

# Retryable HTTP/gRPC status codes from Gemini API
RETRYABLE_STATUS_CODES = {429, 503}


class GeminiProvider(LLMProvider[T]):
    """Gemini API implementation of the LLM provider interface."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ):
        if not api_key and not settings.gemini_api_key:
            raise LLMProviderError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in environment."
            )
        genai.configure(api_key=api_key or settings.gemini_api_key)
        self.model_name = model or settings.gemini_model
        self._model = genai.GenerativeModel(self.model_name)
        self.timeout = timeout

    def _wrap_retryable(self, exc: Exception) -> LLMProviderError:
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            status_code = getattr(exc, "code", None)
        msg = str(exc).lower()
        if (isinstance(status_code, int) and status_code == 429) or any(
            i in msg for i in ("429", "rate limit", "quota", "too many requests", "resource exhausted")
        ):
            return LLMRateLimitError(str(exc))
        return LLMServiceError(str(exc))


    def _is_retryable(self, exc: Exception) -> bool:
        """Determine if an exception is from a retryable transient failure."""
        # LLMProviderError is treated as a (possibly already-classified) error;
        # only retry when it wraps a retryable condition is not detectable, so
        # do not retry LLMProviderError by default.
        if isinstance(exc, LLMProviderError):
            return False

        # Check HTTP/gRPC status code in exception attributes
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            status_code = getattr(exc, "code", None)
        if isinstance(status_code, int) and status_code in RETRYABLE_STATUS_CODES:
            return True

        # Check message text for common rate-limit / transient indicators
        msg = str(exc).lower()
        for indicator in (
            "429",
            "503",
            "rate limit",
            "quota",
            "unavailable",
            "overloaded",
            "resource exhausted",
            "service unavailable",
            "too many requests",
        ):
            if indicator in msg:
                return True
        return False

    async def _call_with_retry(self, coro_factory) -> Any:
        """Execute an async LLM call with bounded retries for transient failures."""
        last_exc: Optional[Exception] = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                return await asyncio.wait_for(coro_factory(), timeout=self.timeout)
            except asyncio.TimeoutError as exc:
                last_exc = exc
                logger.error(
                    "Gemini API call timed out after %ss (attempt %d/%d)",
                    self.timeout,
                    attempt + 1,
                    MAX_RETRIES + 1,
                )
                # Timeouts are not retried (may indicate a hung call).
                raise LLMTimeoutError(
                    f"LLM request timed out after {self.timeout}s"
                ) from exc
            except LLMProviderError:
                raise
            except Exception as exc:
                last_exc = exc
                if not self._is_retryable(exc):
                    logger.error("Gemini provider non-retryable error: %s", exc)
                    raise LLMProviderError(str(exc)) from exc
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_SECONDS * (2 ** attempt)
                    logger.warning(
                        "Gemini provider retryable error (attempt %d/%d): %s. Retrying in %ss",
                        attempt + 1,
                        MAX_RETRIES + 1,
                        exc,
                        wait,
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error("Gemini provider max retries exceeded: %s", exc)
                    raise self._wrap_retryable(exc) from exc

        # Should not reach here
        raise LLMProviderError(
            str(last_exc) if last_exc else "Unknown LLM error"
        )

    async def generate_structured_output(
        self, prompt: str, schema: type[T], system_prompt: Optional[str] = None
    ) -> T:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        full_prompt += (
            "\n\nIMPORTANT: Return ONLY valid JSON that exactly matches the requested schema. "
            "Do not include markdown code fences, explanations, or any text outside the JSON object."
        )

        raw_text = ""

        async def _call() -> T:
            nonlocal raw_text
            result = await self._model.generate_content_async(full_prompt)
            raw_text = result.text or ""

            # Strip markdown fences if present
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```", 2)
                if len(cleaned) >= 3:
                    cleaned = cleaned[1]
                    # Remove language hint line if present
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()

            data = json.loads(cleaned)
            return schema(**data)

        try:
            return await self._call_with_retry(_call)
        except LLMProviderError:
            raise
        except Exception as exc:
            logger.error("Gemini provider error: %s", exc)
            raise LLMProviderError(str(exc)) from exc

    async def generate_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        async def _call() -> str:
            result = await self._model.generate_content_async(full_prompt)
            return result.text or ""

        try:
            return await self._call_with_retry(_call)
        except LLMProviderError:
            raise
        except Exception as exc:
            logger.error("Gemini provider error: %s", exc)
            raise LLMProviderError(str(exc)) from exc
