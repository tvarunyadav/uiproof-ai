from abc import ABC, abstractmethod
from typing import List
from app.schemas.issue import Issue
from app.schemas.evidence import BrowserEvidence
from app.schemas.audit import DeveloperFixPrompt


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


class StubLLMProvider(BaseLLMProvider):
    """
    Milestone 1 AI Provider Stub.
    Maintains typed interface contracts without making external API calls in milestone 1.
    """

    async def analyze_evidence(self, evidence: BrowserEvidence) -> List[Issue]:
        # Milestone 1 returns issues derived purely from evidence schemas
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
