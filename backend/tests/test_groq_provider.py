import pytest
import json
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from app.schemas.issue import Issue, IssueCategory, IssueSeverity
from app.schemas.ai import AIAnalysisDetails
from app.services.ai.interface import AINotConfiguredError, AIProviderError, StubLLMProvider
from app.services.ai.groq_provider import GroqLLMProvider
from app.services.ai.gemini_provider import GeminiLLMProvider
from app.services.ai.fallback_provider import FallbackLLMProvider
from app.services.ai import get_llm_provider


@pytest.fixture
def sample_issue():
    return Issue(
        issue_id="UI-OVERFLOW-MOBILE",
        category=IssueCategory.RESPONSIVE,
        severity=IssueSeverity.HIGH,
        title="Mobile Layout Overflow",
        description="Document scroll width (428px) exceeds client width (390px) by 38px on Mobile.",
        selector="body",
        viewport="Mobile",
        evidence_references=["Viewport: 390px, ScrollWidth: 428px, Overflow: 38px"]
    )


SECRET_GROQ_KEY = "gsk_TEST_GROQ_SECRET_12345"


# 1. Missing API key -> AINotConfiguredError
@pytest.mark.asyncio
async def test_groq_missing_api_key(sample_issue):
    provider = GroqLLMProvider(api_key="")
    with pytest.raises(AINotConfiguredError) as exc_info:
        await provider.analyze_issue(sample_issue)
    assert "Groq API key is not configured" in str(exc_info.value)
    assert SECRET_GROQ_KEY not in str(exc_info.value)


# 2. Provider factory selection variations
def test_factory_selects_groq():
    with patch("app.services.ai.settings.LLM_PROVIDER", "groq"), patch("app.services.ai.settings.LLM_FALLBACK_PROVIDER", None):
        provider = get_llm_provider()
        assert isinstance(provider, GroqLLMProvider)


def test_factory_selects_groq_primary_gemini_fallback():
    with patch("app.services.ai.settings.LLM_PROVIDER", "groq"), patch("app.services.ai.settings.LLM_FALLBACK_PROVIDER", "gemini"):
        provider = get_llm_provider()
        assert isinstance(provider, FallbackLLMProvider)
        assert isinstance(provider.primary, GroqLLMProvider)
        assert isinstance(provider.fallback, GeminiLLMProvider)


def test_factory_prevents_primary_equals_fallback():
    with patch("app.services.ai.settings.LLM_PROVIDER", "groq"), patch("app.services.ai.settings.LLM_FALLBACK_PROVIDER", "groq"):
        provider = get_llm_provider()
        # Should return GroqLLMProvider directly without wrapping in FallbackLLMProvider
        assert isinstance(provider, GroqLLMProvider)


def test_factory_rejects_unsupported_provider():
    with patch("app.services.ai.settings.LLM_PROVIDER", "invalid_provider"), patch("app.services.ai.settings.LLM_FALLBACK_PROVIDER", None):
        with pytest.raises(ValueError) as exc_info:
            get_llm_provider()
        assert "Unsupported LLM provider" in str(exc_info.value)


# 3. Successful Groq response -> valid AIAnalysisDetails, correct model, Authorization header, key not in URL
@pytest.mark.asyncio
async def test_groq_successful_response(sample_issue):
    provider = GroqLLMProvider(api_key=SECRET_GROQ_KEY, model_name="openai/gpt-oss-120b")

    mock_json_content = {
        "summary": "Horizontal overflow on mobile caused by fixed width element exceeding 390px viewport width.",
        "likely_causes": ["Fixed width container set to 428px."],
        "investigation_hints": ["Inspect element bounds around 390px breakpoint."],
        "expected_result": "Document scrollWidth equals 390px with zero horizontal scroll.",
        "constraints": ["Preserve desktop grid layout at 1440px viewport."],
        "verification_steps": ["Check document.documentElement.scrollWidth == 390 on mobile."],
        "fix_prompt": "Investigate root element exceeding 390px width. Do NOT use overflow-x: hidden."
    }

    mock_groq_payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(mock_json_content)
                }
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_groq_payload

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await provider.analyze_issue(sample_issue)

        assert isinstance(result, AIAnalysisDetails)
        assert result.summary == mock_json_content["summary"]
        assert result.likely_causes == mock_json_content["likely_causes"]
        assert result.fix_prompt == mock_json_content["fix_prompt"]

        # Verify call arguments
        called_url = mock_post.call_args[0][0]
        assert "api.groq.com" in called_url
        assert "key=" not in called_url
        assert SECRET_GROQ_KEY not in called_url

        headers_sent = mock_post.call_args[1].get("headers", {})
        assert headers_sent.get("Authorization") == f"Bearer {SECRET_GROQ_KEY}"

        payload_sent = mock_post.call_args[1].get("json", {})
        assert payload_sent.get("model") == "openai/gpt-oss-120b"


# 4. Invalid Groq JSON / Malformed structure -> AIProviderError
@pytest.mark.asyncio
async def test_groq_invalid_json_response(sample_issue):
    provider = GroqLLMProvider(api_key=SECRET_GROQ_KEY)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "NOT_VALID_JSON"}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(AIProviderError) as exc_info:
            await provider.analyze_issue(sample_issue)
        assert "invalid JSON structure" in str(exc_info.value)
        assert SECRET_GROQ_KEY not in str(exc_info.value)


# 5. Missing required fields in AI response -> AIProviderError
@pytest.mark.asyncio
async def test_groq_malformed_schema_missing_fields(sample_issue):
    provider = GroqLLMProvider(api_key=SECRET_GROQ_KEY)

    # Missing expected_result and fix_prompt
    incomplete_json = {
        "summary": "Incomplete analysis"
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(incomplete_json)}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(AIProviderError) as exc_info:
            await provider.analyze_issue(sample_issue)
        assert "invalid JSON structure" in str(exc_info.value)


# 6. HTTP 503 & 429 Retry behavior (retries 3 attempts)
@pytest.mark.asyncio
async def test_groq_transient_retries_exhausted(sample_issue, caplog):
    provider = GroqLLMProvider(api_key=SECRET_GROQ_KEY, model_name="openai/gpt-oss-120b")

    for status_code in (503, 429):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.headers = {"Retry-After": "1"}
        mock_response.text = f"Error {status_code}: Service Busy"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, patch("asyncio.sleep", new_callable=AsyncMock):
            mock_post.return_value = mock_response
            with pytest.raises(AIProviderError) as exc_info:
                await provider.analyze_issue(sample_issue)

            assert f"HTTP {status_code}" in str(exc_info.value)
            assert mock_post.call_count == 3
            assert SECRET_GROQ_KEY not in str(exc_info.value)


# 7. Non-transient errors (400, 401, 403, 404) fail immediately without retry
@pytest.mark.asyncio
async def test_groq_non_transient_failure_no_retry(sample_issue):
    provider = GroqLLMProvider(api_key=SECRET_GROQ_KEY)

    for status_code in (400, 401, 403, 404):
        fail_resp = MagicMock()
        fail_resp.status_code = status_code
        fail_resp.headers = {}
        fail_resp.text = f"Client Error {status_code}"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_post.return_value = fail_resp
            with pytest.raises(AIProviderError):
                await provider.analyze_issue(sample_issue)

            assert mock_post.call_count == 1
            assert mock_sleep.call_count == 0


# 8. Timeout -> AIProviderError after 3 retries
@pytest.mark.asyncio
async def test_groq_timeout(sample_issue):
    provider = GroqLLMProvider(api_key=SECRET_GROQ_KEY)

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Groq connection timeout")) as mock_post, patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(AIProviderError) as exc_info:
            await provider.analyze_issue(sample_issue)
        assert "network failure or timeout" in str(exc_info.value)
        assert mock_post.call_count == 3
        assert SECRET_GROQ_KEY not in str(exc_info.value)


# 9. Regression Test: Fake Groq API Key TEST_GROQ_SECRET_12345 never appears in logs, URLs, or exceptions
@pytest.mark.asyncio
async def test_groq_api_key_never_appears_in_logs(sample_issue, caplog):
    fake_secret = "TEST_GROQ_SECRET_12345"
    provider = GroqLLMProvider(api_key=fake_secret, model_name="openai/gpt-oss-120b")

    mock_503_body = f'{{"error": {{"code": 503, "message": "Echoing secret {fake_secret}", "status": "UNAVAILABLE"}}}}'
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.headers = {}
    mock_response.text = mock_503_body

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, patch("asyncio.sleep", new_callable=AsyncMock):
        mock_post.return_value = mock_response

        with caplog.at_level("DEBUG"):
            with pytest.raises(AIProviderError) as exc_info:
                await provider.analyze_issue(sample_issue)

        log_text = caplog.text

        # 1. Fake secret MUST NOT appear in log text
        assert fake_secret not in log_text
        assert "[REDACTED]" in log_text

        # 2. Fake secret MUST NOT appear in exception text
        assert fake_secret not in str(exc_info.value)

        # 3. URL MUST NOT contain key= or fake secret
        called_url = mock_post.call_args[0][0]
        assert "key=" not in called_url
        assert fake_secret not in called_url


# ==================================================
# FALLBACK TESTS
# ==================================================

# 10. Gemini succeeds -> Groq not called
@pytest.mark.asyncio
async def test_fallback_gemini_succeeds_groq_not_called(sample_issue):
    mock_gemini = AsyncMock(spec=GeminiLLMProvider)
    mock_groq = AsyncMock(spec=GroqLLMProvider)

    expected_analysis = AIAnalysisDetails(
        summary="Gemini summary",
        likely_causes=["Cause 1"],
        investigation_hints=["Hint 1"],
        expected_result="Result",
        constraints=["Constraint 1"],
        verification_steps=["Step 1"],
        fix_prompt="Fix prompt"
    )
    mock_gemini.analyze_issue.return_value = expected_analysis

    fallback_provider = FallbackLLMProvider(primary=mock_gemini, fallback=mock_groq, primary_name="gemini", fallback_name="groq")
    result = await fallback_provider.analyze_issue(sample_issue)

    assert result == expected_analysis
    assert mock_gemini.analyze_issue.call_count == 1
    assert mock_groq.analyze_issue.call_count == 0


# 11. Gemini fails transiently -> Groq called once and succeeds
@pytest.mark.asyncio
async def test_fallback_gemini_fails_transiently_groq_succeeds(sample_issue, caplog):
    mock_gemini = AsyncMock(spec=GeminiLLMProvider)
    mock_groq = AsyncMock(spec=GroqLLMProvider)

    mock_gemini.analyze_issue.side_effect = AIProviderError("LLM Provider returned HTTP 503")

    expected_analysis = AIAnalysisDetails(
        summary="Groq summary",
        likely_causes=["Cause 1"],
        investigation_hints=["Hint 1"],
        expected_result="Result",
        constraints=["Constraint 1"],
        verification_steps=["Step 1"],
        fix_prompt="Fix prompt"
    )
    mock_groq.analyze_issue.return_value = expected_analysis

    fallback_provider = FallbackLLMProvider(primary=mock_gemini, fallback=mock_groq, primary_name="gemini", fallback_name="groq")

    with caplog.at_level("WARNING"):
        result = await fallback_provider.analyze_issue(sample_issue)

    assert result == expected_analysis
    assert mock_gemini.analyze_issue.call_count == 1
    assert mock_groq.analyze_issue.call_count == 1

    assert "Primary LLM provider (gemini) failed with transient error" in caplog.text
    assert "Attempting fallback provider (groq)" in caplog.text


# 12. Gemini fails non-transiently (AINotConfiguredError) -> Groq NOT called
@pytest.mark.asyncio
async def test_fallback_gemini_not_configured_groq_not_called(sample_issue):
    mock_gemini = AsyncMock(spec=GeminiLLMProvider)
    mock_groq = AsyncMock(spec=GroqLLMProvider)

    mock_gemini.analyze_issue.side_effect = AINotConfiguredError("Gemini API key is not configured.")

    fallback_provider = FallbackLLMProvider(primary=mock_gemini, fallback=mock_groq, primary_name="gemini", fallback_name="groq")

    with pytest.raises(AINotConfiguredError):
        await fallback_provider.analyze_issue(sample_issue)

    assert mock_gemini.analyze_issue.call_count == 1
    assert mock_groq.analyze_issue.call_count == 0


# 13. Gemini fails & Groq fails -> provider error returned
@pytest.mark.asyncio
async def test_fallback_both_fail_raises_provider_error(sample_issue):
    mock_gemini = AsyncMock(spec=GeminiLLMProvider)
    mock_groq = AsyncMock(spec=GroqLLMProvider)

    mock_gemini.analyze_issue.side_effect = AIProviderError("Gemini HTTP 503")
    mock_groq.analyze_issue.side_effect = AIProviderError("Groq HTTP 503")

    fallback_provider = FallbackLLMProvider(primary=mock_gemini, fallback=mock_groq, primary_name="gemini", fallback_name="groq")

    with pytest.raises(AIProviderError) as exc_info:
        await fallback_provider.analyze_issue(sample_issue)

    assert "Groq HTTP 503" in str(exc_info.value)
    assert mock_gemini.analyze_issue.call_count == 1
    assert mock_groq.analyze_issue.call_count == 1


# 14. Fallback happens only once (no repeated loops)
@pytest.mark.asyncio
async def test_fallback_happens_only_once(sample_issue):
    mock_gemini = AsyncMock(spec=GeminiLLMProvider)
    mock_groq = AsyncMock(spec=GroqLLMProvider)

    mock_gemini.analyze_issue.side_effect = AIProviderError("Gemini error")
    mock_groq.analyze_issue.side_effect = AIProviderError("Groq error")

    fallback_provider = FallbackLLMProvider(primary=mock_gemini, fallback=mock_groq, primary_name="gemini", fallback_name="groq")

    with pytest.raises(AIProviderError):
        await fallback_provider.analyze_issue(sample_issue)

    assert mock_gemini.analyze_issue.call_count == 1
    assert mock_groq.analyze_issue.call_count == 1
