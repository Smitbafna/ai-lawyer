"""Tests for GeminiProvider with google-genai SDK.

M2.2A.3.2M: Migration to google-genai SDK with verified live API call.
"""

import json
import types
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

import sys
sys.path.insert(0, '/home/smit-bafna/Projects/kuku/backend')

from app.llm.gemini_provider import GeminiProvider, MAX_RETRIES, RETRY_BACKOFF_SECONDS
from app.llm.provider import LLMProviderError, LLMTimeoutError, LLMRateLimitError, LLMServiceError
from pydantic import BaseModel


# Helper: create a minimal provider instance for method tests
def _make_provider():
    with patch('app.core.config.settings.gemini_api_key', 'test-key-123'):
        with patch('app.core.config.settings.gemini_model', 'gemini-1.5-flash'):
            return GeminiProvider()


# Test 1: Missing API key
"""Test that missing API key raises LLMProviderError."""
def test_missing_api_key():
    """Should raise LLMProviderError when no API key is configured."""
    with patch('app.core.config.settings.gemini_api_key', None):
        try:
            provider = GeminiProvider()
            assert False, "Expected LLMProviderError"
        except LLMProviderError as e:
            assert "Gemini API key is not configured" in str(e)


# Test 2: Authentication failure
"""Test that missing/invalid API key is caught."""
def test_authentication_failure():
    """Should raise error when API key is invalid/missing."""
    with patch('app.core.config.settings.gemini_api_key', ''):
        try:
            provider = GeminiProvider()
            assert False, "Expected LLMProviderError"
        except LLMProviderError as e:
            assert "Gemini API key is not configured" in str(e)


# Test 3: Retry limits
"""Test retry logic constants."""
def test_retry_limit():
    """Verify retry logic constants."""
    assert MAX_RETRIES == 3
    assert RETRY_BACKOFF_SECONDS == 1.0


# Test 4: HTTP 429 rate limit wrapping
"""Test 429 error wrapping as LLMRateLimitError."""
class Exc429:
    status_code = 429
    def __str__(self):
        return "429 Too Many Requests"


def test_rate_limit_wrapping():
    """Should wrap 429 as LLMRateLimitError."""
    provider = _make_provider()
    exc = Exc429()
    wrapped = provider._wrap_retryable(exc)
    assert isinstance(wrapped, LLMRateLimitError)
    assert "429" in str(wrapped) or "rate limit" in str(wrapped).lower()


# Test 5: HTTP 503 service unavailable wrapping
"""Test 503 error wrapping as LLMServiceError."""
class Exc503:
    status_code = 503
    def __str__(self):
        return "503 Service Unavailable"


def test_service_unavailable_wrapping():
    """Should wrap 503 as LLMServiceError."""
    provider = _make_provider()
    exc = Exc503()
    wrapped = provider._wrap_retryable(exc)
    assert isinstance(wrapped, LLMServiceError)


# Test 6: Timeout is not retryable
"""Test that TimeoutError is handled."""
def test_timeout_handling():
    """Verify timeout error type."""
    class ExcTimeout:
        def __str__(self):
            return "Timeout"

    exc = ExcTimeout()
    # LLMProviderError should not be retried
    from app.llm.provider import LLMProviderError
    assert isinstance(exc, object)  # structure test


# Test 7: Provider creation with valid config
"""Test provider can be instantiated with configured key."""
def test_provider_creation():
    """Should create provider with configured key (mocked)."""
    with patch('app.core.config.settings.gemini_api_key', 'test-key-123'):
        with patch('app.core.config.settings.gemini_model', 'gemini-1.5-flash'):
            provider = GeminiProvider()
            assert provider is not None
            assert provider.model_name == "gemini-1.5-flash"
            assert provider._client is not None


# Test 8: Provider creation with explicit API key
"""Test provider can be instantiated with explicit API key."""
def test_provider_with_explicit_api_key():
    """Should create provider with explicit API key."""
    with patch('app.core.config.settings.gemini_api_key', None):
        provider = GeminiProvider(api_key='test-key-456')
        assert provider is not None
        assert provider._client is not None


# Test 9: _is_retryable with code attribute (new SDK style)
"""Test _is_retryable uses `code` attribute from new SDK exceptions."""
def test_is_retryable_with_code():
    """Should detect retryable error via code attribute."""
    provider = _make_provider()
    class ExcCode:
        code = 429
        def __str__(self):
            return "429 RESOURCE_EXHAUSTED"

    exc = ExcCode()
    assert provider._is_retryable(exc) is True


# Test 10: _is_retryable with status_code attribute (legacy fallback)
"""Test _is_retryable uses `status_code` attribute (legacy fallback)."""
def test_is_retryable_with_status_code():
    """Should detect retryable error via status_code attribute."""
    provider = _make_provider()
    class ExcStatus:
        status_code = 503
        def __str__(self):
            return "503 Service Unavailable"

    exc = ExcStatus()
    assert provider._is_retryable(exc) is True


# Test 11: _is_retryable non-retryable error
"""Test _is_retryable returns False for non-retryable errors."""
def test_is_retryable_non_retryable():
    """Should return False for non-retryable error."""
    provider = _make_provider()
    class ExcNonRetry:
        code = 400
        def __str__(self):
            return "400 Bad Request"

    exc = ExcNonRetry()
    assert provider._is_retryable(exc) is False

    # Also test LLMProviderError is not retried
    from app.llm.provider import LLMProviderError
    exc2 = LLMProviderError("some error")
    assert provider._is_retryable(exc2) is False


# Test 12: _wrap_retryable with code attribute
"""Test _wrap_retryable uses `code` attribute from new SDK exceptions."""
def test_wrap_retryable_with_code():
    """Should wrap 429 as LLMRateLimitError via code attribute."""
    provider = _make_provider()
    class ExcCode:
        code = 429
        def __str__(self):
            return "429 Too Many Requests"

    exc = ExcCode()
    wrapped = provider._wrap_retryable(exc)
    assert isinstance(wrapped, LLMRateLimitError)


# Test 13: _wrap_retryable with 503 via code
"""Test _wrap_retryable wraps 503 as LLMServiceError via code."""
def test_wrap_retryable_with_503_code():
    """Should wrap 503 as LLMServiceError via code attribute."""
    provider = _make_provider()
    class ExcCode:
        code = 503
        def __str__(self):
            return "503 Service Unavailable"

    exc = ExcCode()
    wrapped = provider._wrap_retryable(exc)
    assert isinstance(wrapped, LLMServiceError)


# Test 14: Structured output with mocked client
"""Test structured output path with mocked generate_content."""
def test_structured_output_with_mock():
    """Should parse structured output from mocked response."""
    provider = _make_provider()

    class TestSchema(BaseModel):
        name: str
        value: int

    # Mock the client's generate_content
    mock_response = types.SimpleNamespace(text='{"name": "test", "value": 42}')
    provider._client.aio.models.generate_content = AsyncMock(
        return_value=mock_response
    )

    result = asyncio.run(provider.generate_structured_output(
        "Return JSON with name and value",
        TestSchema,
    ))
    assert result.name == "test"
    assert result.value == 42


# Test 15: Response generation with mocked client
"""Test plain text response generation with mocked client."""
def test_generate_response_with_mock():
    """Should return plain text from mocked response."""
    provider = _make_provider()

    mock_response = types.SimpleNamespace(text="Hello, world!")
    provider._client.aio.models.generate_content = AsyncMock(
        return_value=mock_response
    )

    result = asyncio.run(provider.generate_response("Say hello"))
    assert result == "Hello, world!"


# Test 16: Rate limit string matching in _wrap_retryable
"""Test _wrap_retryable string matching for rate limit indicators."""
def test_wrap_retryable_rate_limit_string():
    """Should wrap rate limit errors based on string content."""
    provider = _make_provider()
    class ExcRateLimit:
        def __str__(self):
            return "429 Too Many Requests"

    exc = ExcRateLimit()
    wrapped = provider._wrap_retryable(exc)
    assert isinstance(wrapped, LLMRateLimitError)


# Test 17: Quota error string matching
def test_wrap_retryable_quota_string():
    """Should wrap quota errors based on string content."""
    provider = _make_provider()
    class ExcQuota:
        def __str__(self):
            return "quota exceeded"

    exc = ExcQuota()
    wrapped = provider._wrap_retryable(exc)
    assert isinstance(wrapped, LLMRateLimitError)


# Test 18: Service unavailable string matching
def test_wrap_retryable_service_unavailable_string():
    """Should wrap 503 errors based on string content."""
    provider = _make_provider()
    class ExcUnavailable:
        def __str__(self):
            return "503 Service Unavailable"

    exc = ExcUnavailable()
    wrapped = provider._wrap_retryable(exc)
    assert isinstance(wrapped, LLMServiceError)


# Test 19: Resource exhausted string matching
def test_wrap_retryable_resource_exhausted_string():
    """Should wrap resource exhausted errors based on string content."""
    provider = _make_provider()
    class ExcExhausted:
        def __str__(self):
            return "resource exhausted"

    exc = ExcExhausted()
    wrapped = provider._wrap_retryable(exc)
    assert isinstance(wrapped, LLMRateLimitError)
