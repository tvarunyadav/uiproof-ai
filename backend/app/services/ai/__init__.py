"""AI Service Provider Module."""
from typing import Optional
from app.config import settings
from app.services.ai.interface import BaseLLMProvider, StubLLMProvider, AINotConfiguredError, AIProviderError
from app.services.ai.openai_provider import OpenAILLMProvider
from app.services.ai.gemini_provider import GeminiLLMProvider


def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory function to instantiate configured LLM provider.
    Supports: 'gemini', 'openai', 'stub'.
    """
    name = (provider_name or settings.LLM_PROVIDER or "openai").lower().strip()
    if name == "gemini":
        return GeminiLLMProvider()
    elif name == "stub":
        return StubLLMProvider()
    else:
        return OpenAILLMProvider()


__all__ = [
    "BaseLLMProvider",
    "StubLLMProvider",
    "OpenAILLMProvider",
    "GeminiLLMProvider",
    "get_llm_provider",
    "AINotConfiguredError",
    "AIProviderError",
]
