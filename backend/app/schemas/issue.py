import hashlib
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(str, Enum):
    LAYOUT = "layout"
    CONSOLE_ERROR = "console_error"
    NETWORK_FAILURE = "network_failure"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    INTERACTION = "interaction"


def generate_stable_issue_id(category: str, selector: str, title: str) -> str:
    """
    Generates a deterministic stable Issue ID based on issue category, selector, and title.
    Enables tracking issues across before/after audit runs.
    """
    normalized_str = f"{category.strip().lower()}|{selector.strip().lower()}|{title.strip().lower()}"
    hash_digest = hashlib.sha256(normalized_str.encode("utf-8")).hexdigest()[:12]
    return f"ISSUE-{category.upper()[:3]}-{hash_digest}"


class Issue(BaseModel):
    issue_id: str = Field(..., description="Stable Issue ID formatted as ISSUE-{CAT}-{HASH}")
    category: IssueCategory
    severity: IssueSeverity
    title: str = Field(..., description="Short summary of detected problem")
    description: str = Field(..., description="Detailed breakdown of issue")
    selector: Optional[str] = Field(None, description="CSS selector of element if applicable")
    viewport: Optional[str] = Field(None, description="Viewport name where issue occurred")
    evidence_references: List[str] = Field(default=[], description="Pointers to screenshot paths or raw logs")
    
    # AI Analysis Fields (populated by AI layer, distinct from raw evidence)
    root_cause_analysis: Optional[str] = Field(None, description="AI-generated root cause diagnostic")
    recommended_fix: Optional[str] = Field(None, description="AI-generated developer fix guidance")
