"""AI Service Provider Module."""
from typing import Optional
from app.config import settings
from app.services.ai.interface import BaseLLMProvider, StubLLMProvider, AINotConfiguredError, AIProviderError
from app.services.ai.openai_provider import OpenAILLMProvider
from app.services.ai.gemini_provider import GeminiLLMProvider
from app.services.ai.groq_provider import GroqLLMProvider
from app.services.ai.fallback_provider import FallbackLLMProvider


def get_llm_provider(
    provider_name: Optional[str] = None,
    fallback_name: Optional[str] = None
) -> BaseLLMProvider:
    """
    Factory function to instantiate configured LLM provider with optional fallback.
    Supported providers: 'gemini', 'openai', 'groq', 'stub'.
    """
    p_name = (provider_name or settings.LLM_PROVIDER or "openai").lower().strip()
    f_name = (fallback_name or settings.LLM_FALLBACK_PROVIDER or "").lower().strip()

    def _create_single(name: str) -> BaseLLMProvider:
        if name == "gemini":
            return GeminiLLMProvider()
        elif name == "groq":
            return GroqLLMProvider()
        elif name == "stub":
            return StubLLMProvider()
        elif name == "openai":
            return OpenAILLMProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: '{name}'. Supported providers: 'gemini', 'openai', 'groq', 'stub'.")

    primary = _create_single(p_name)
    if f_name and f_name != p_name:
        fallback = _create_single(f_name)
        return FallbackLLMProvider(primary=primary, fallback=fallback, primary_name=p_name, fallback_name=f_name)

    return primary


__all__ = [
    "BaseLLMProvider",
    "StubLLMProvider",
    "OpenAILLMProvider",
    "GeminiLLMProvider",
    "GroqLLMProvider",
    "FallbackLLMProvider",
    "get_llm_provider",
    "AINotConfiguredError",
    "AIProviderError",
]
