import logging
from typing import List, Optional
from app.schemas.issue import Issue
from app.schemas.evidence import BrowserEvidence
from app.schemas.audit import DeveloperFixPrompt
from app.schemas.ai import AIAnalysisDetails
from app.services.ai.interface import BaseLLMProvider, AIProviderError

logger = logging.getLogger("uiproof.fallback_provider")


class FallbackLLMProvider(BaseLLMProvider):
    """
    Wrapper LLM Provider that executes a primary provider and falls back to a secondary provider
    if the primary provider fails with a transient AIProviderError.
    """

    def __init__(
        self,
        primary: BaseLLMProvider,
        fallback: BaseLLMProvider,
        primary_name: str = "primary",
        fallback_name: str = "fallback"
    ):
        self.primary = primary
        self.fallback = fallback
        self.primary_name = primary_name
        self.fallback_name = fallback_name

    async def analyze_evidence(self, evidence: BrowserEvidence) -> List[Issue]:
        return await self.primary.analyze_evidence(evidence)

    async def generate_fix_prompt(self, audit_id: str, issues: List[Issue]) -> DeveloperFixPrompt:
        try:
            return await self.primary.generate_fix_prompt(audit_id, issues)
        except AIProviderError as primary_err:
            logger.warning(
                f"Primary LLM provider ({self.primary_name}) failed with transient error: {primary_err}. "
                f"Attempting fallback provider ({self.fallback_name})..."
            )
            return await self.fallback.generate_fix_prompt(audit_id, issues)

    async def analyze_issue(self, issue: Issue, evidence: Optional[BrowserEvidence] = None) -> AIAnalysisDetails:
        try:
            return await self.primary.analyze_issue(issue, evidence)
        except AIProviderError as primary_err:
            logger.warning(
                f"Primary LLM provider ({self.primary_name}) failed with transient error: {primary_err}. "
                f"Attempting fallback provider ({self.fallback_name})..."
            )
            return await self.fallback.analyze_issue(issue, evidence)
