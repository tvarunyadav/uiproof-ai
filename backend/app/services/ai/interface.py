from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.issue import Issue
from app.schemas.evidence import BrowserEvidence
from app.schemas.audit import DeveloperFixPrompt
from app.schemas.ai import AIAnalysisDetails


class AINotConfiguredError(Exception):
    """Raised when the AI API Key or provider configuration is missing."""
    pass


class AIProviderError(Exception):
    """Raised when an external LLM API request fails, times out, or returns invalid structure."""
    pass


class BaseLLMProvider(ABC):
    """
    LLM API Abstraction interface.
    Allows changing AI provider (OpenAI, Anthropic, Gemini, local LLMs) without refactoring audit engine.
    """

    @abstractmethod
    async def analyze_evidence(self, evidence: BrowserEvidence) -> List[Issue]:
        """Convert deterministic evidence into contextual developer issues."""
        pass

    @abstractmethod
    async def generate_fix_prompt(self, audit_id: str, issues: List[Issue]) -> DeveloperFixPrompt:
        """Generate context-rich prompt for Antigravity, Cursor, Claude, or VS Code AI."""
        pass

    @abstractmethod
    async def analyze_issue(self, issue: Issue, evidence: Optional[BrowserEvidence] = None) -> AIAnalysisDetails:
        """Analyze an already verified deterministic issue and return structured analysis."""
        pass


class StubLLMProvider(BaseLLMProvider):
    """
    Stub AI Provider.
    Raises AINotConfiguredError if real AI functionality is requested when API key is missing.
    """

    async def analyze_evidence(self, evidence: BrowserEvidence) -> List[Issue]:
        return []

    async def generate_fix_prompt(self, audit_id: str, issues: List[Issue]) -> DeveloperFixPrompt:
        prompt_text = (
            f"UIProof AI Developer Fix Prompt (Audit ID: {audit_id})\n"
            f"Issues Detected: {len(issues)}\n"
            "Please review target element selectors, network errors, and layout bounds to apply fixes."
        )
        return DeveloperFixPrompt(
            audit_id=audit_id,
            target_issues=issues,
            fix_prompt=prompt_text,
            suggested_files=[]
        )

    async def analyze_issue(self, issue: Issue, evidence: Optional[BrowserEvidence] = None) -> AIAnalysisDetails:
        raise AINotConfiguredError("AI API key is not configured. Please set LLM_API_KEY in environment.")
