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
    RESPONSIVE = "responsive"
    CONSOLE_ERROR = "console_error"
    CONSOLE = "console"
    NETWORK_FAILURE = "network_failure"
    BROKEN_RESOURCE = "broken_resource"
    SEO = "seo"
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


def generate_deterministic_issue_id(rule_code: str, viewport: str, target: str = "") -> str:
    """
    Generates a human-readable deterministic Issue ID formatted like:
    UI-OVERFLOW-MOBILE or UI-BROKEN-IMAGE-DESKTOP-3A8B12
    """
    clean_rule = rule_code.strip().upper().replace(" ", "-")
    clean_vp = viewport.strip().upper()
    if target:
        hash_digest = hashlib.sha256(f"{clean_rule}|{clean_vp}|{target.strip().lower()}".encode("utf-8")).hexdigest()[:6].upper()
        return f"UI-{clean_rule}-{clean_vp}-{hash_digest}"
    return f"UI-{clean_rule}-{clean_vp}"



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
