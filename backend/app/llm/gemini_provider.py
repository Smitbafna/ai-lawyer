import json
import logging
from typing import Optional, TypeVar

import google.generativeai as genai
from pydantic import BaseModel

from app.core.config import settings
from app.llm.provider import LLMProvider, LLMProviderError

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider[T]):
    """Gemini API implementation of the LLM provider interface."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        if not api_key and not settings.gemini_api_key:
            raise LLMProviderError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in environment."
            )
        genai.configure(api_key=api_key or settings.gemini_api_key)
        self.model_name = model or settings.gemini_model
        self._model = genai.GenerativeModel(self.model_name)

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

        try:
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
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON from Gemini: %s", raw_text[:500] if raw_text else "<empty>")
            raise LLMProviderError(f"Invalid JSON response from LLM: {exc}") from exc
        except Exception as exc:
            logger.error("Gemini provider error: %s", exc)
            raise LLMProviderError(str(exc)) from exc

    async def generate_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        try:
            result = await self._model.generate_content_async(full_prompt)
            return result.text or ""
        except Exception as exc:
            logger.error("Gemini provider error: %s", exc)
            raise LLMProviderError(str(exc)) from exc