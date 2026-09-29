import pytest
import json
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from app.schemas.issue import Issue, IssueCategory, IssueSeverity
from app.schemas.ai import AIAnalysisDetails
from app.services.ai.interface import AINotConfiguredError, AIProviderError, StubLLMProvider
from app.services.ai.openai_provider import OpenAILLMProvider
from app.services.ai.gemini_provider import GeminiLLMProvider
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


SECRET_TEST_KEY = "AIzaSyTEST_SECRET_KEY_NEVER_LOG_12345"


# A. Missing API key -> AINotConfiguredError
@pytest.mark.asyncio
async def test_gemini_missing_api_key(sample_issue):
    provider = GeminiLLMProvider(api_key="")
    with pytest.raises(AINotConfiguredError) as exc_info:
        await provider.analyze_issue(sample_issue)
    assert "Gemini API key is not configured" in str(exc_info.value)
    # L. Ensure API key is not in exception text
    assert SECRET_TEST_KEY not in str(exc_info.value)


# B. Provider factory selects Gemini
def test_factory_selects_gemini():
    with patch("app.services.ai.settings.LLM_PROVIDER", "gemini"):
        provider = get_llm_provider()
        assert isinstance(provider, GeminiLLMProvider)


# C. Provider factory selects OpenAI
def test_factory_selects_openai():
    with patch("app.services.ai.settings.LLM_PROVIDER", "openai"):
        provider = get_llm_provider()
        assert isinstance(provider, OpenAILLMProvider)


# D. Provider factory selects Stub
def test_factory_selects_stub():
    with patch("app.services.ai.settings.LLM_PROVIDER", "stub"):
        provider = get_llm_provider()
        assert isinstance(provider, StubLLMProvider)


# E. Mock successful Gemini response -> valid AIAnalysisDetails
@pytest.mark.asyncio
async def test_gemini_successful_response(sample_issue):
    provider = GeminiLLMProvider(api_key=SECRET_TEST_KEY, model_name="gemini-2.5-flash-lite")

    mock_json_content = {
        "summary": "Horizontal overflow on mobile caused by fixed width element exceeding 390px viewport width.",
        "likely_causes": ["Fixed width container set to 428px."],
        "investigation_hints": ["Inspect element bounds around 390px breakpoint."],
        "expected_result": "Document scrollWidth equals 390px with zero horizontal scroll.",
        "constraints": ["Preserve desktop grid layout at 1440px viewport."],
        "verification_steps": ["Check document.documentElement.scrollWidth == 390 on mobile."],
        "fix_prompt": "Investigate root element exceeding 390px width. Do NOT use overflow-x: hidden."
    }

    mock_gemini_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(mock_json_content)
                        }
                    ]
                }
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_gemini_payload

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await provider.analyze_issue(sample_issue)

        assert isinstance(result, AIAnalysisDetails)
        assert result.summary == mock_json_content["summary"]
        assert result.likely_causes == mock_json_content["likely_causes"]
        assert result.fix_prompt == mock_json_content["fix_prompt"]

        # L. Ensure secret API key is present in call URL but safe
        called_url = mock_post.call_args[0][0]
        assert "key=" in called_url


# F. Invalid Gemini JSON -> AIProviderError
@pytest.mark.asyncio
async def test_gemini_invalid_json_response(sample_issue):
    provider = GeminiLLMProvider(api_key=SECRET_TEST_KEY)

    mock_gemini_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "NOT_VALID_JSON_CONTENT"
                        }
                    ]
                }
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_gemini_payload

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(AIProviderError) as exc_info:
            await provider.analyze_issue(sample_issue)
        assert "invalid JSON structure" in str(exc_info.value)
        # L. Ensure secret key is not in exception text
        assert SECRET_TEST_KEY not in str(exc_info.value)


# G. HTTP 429 -> AIProviderError
@pytest.mark.asyncio
async def test_gemini_http_429_rate_limit(sample_issue):
    provider = GeminiLLMProvider(api_key=SECRET_TEST_KEY)

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Quota exceeded"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(AIProviderError) as exc_info:
            await provider.analyze_issue(sample_issue)
        assert "HTTP 429" in str(exc_info.value)
        # L. Ensure secret key is not in exception text
        assert SECRET_TEST_KEY not in str(exc_info.value)


# H. HTTP 403 -> AIProviderError
@pytest.mark.asyncio
async def test_gemini_http_403_forbidden(sample_issue):
    provider = GeminiLLMProvider(api_key=SECRET_TEST_KEY)

    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(AIProviderError) as exc_info:
            await provider.analyze_issue(sample_issue)
        assert "HTTP 403" in str(exc_info.value)
        # L. Ensure secret key is not in exception text
        assert SECRET_TEST_KEY not in str(exc_info.value)


# I. HTTP 404 -> AIProviderError
@pytest.mark.asyncio
async def test_gemini_http_404_not_found(sample_issue):
    provider = GeminiLLMProvider(api_key=SECRET_TEST_KEY)

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Model not found"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(AIProviderError) as exc_info:
            await provider.analyze_issue(sample_issue)
        assert "HTTP 404" in str(exc_info.value)
        # L. Ensure secret key is not in exception text
        assert SECRET_TEST_KEY not in str(exc_info.value)


# J. HTTP 500/503 -> AIProviderError
@pytest.mark.asyncio
async def test_gemini_http_500_503_server_error(sample_issue):
    provider = GeminiLLMProvider(api_key=SECRET_TEST_KEY)

    for status_code in (500, 503):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(AIProviderError) as exc_info:
                await provider.analyze_issue(sample_issue)
            assert f"HTTP {status_code}" in str(exc_info.value)
            # L. Ensure secret key is not in exception text
            assert SECRET_TEST_KEY not in str(exc_info.value)



# K. Timeout -> AIProviderError
@pytest.mark.asyncio
async def test_gemini_timeout(sample_issue):
    provider = GeminiLLMProvider(api_key=SECRET_TEST_KEY)

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(AIProviderError) as exc_info:
            await provider.analyze_issue(sample_issue)
        assert "network failure or timeout" in str(exc_info.value)
        # L. Ensure secret key is not in exception text
        assert SECRET_TEST_KEY not in str(exc_info.value)
