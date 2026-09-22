# UIProof AI Architecture Document

## Overview

UIProof AI is an AI-powered web application quality assurance and fix verification platform.
It uses deterministic browser automation (Playwright) to capture objective application evidence across multiple viewports, converts findings into structured issues, generates context-aware developer fix prompts, and performs before/after verification audits.

## Architecture Principles

1. **Separation of Concerns**: Frontend and Backend are decoupled and communicate via RESTful JSON APIs.
2. **Deterministic Evidence Isolation**: Objective browser evidence (console errors, screenshots, layout issues, network failures, accessibility logs) is explicitly separated from AI analysis. AI output is never treated as raw browser evidence.
3. **Layer Isolation**:
   - `services/browser`: Isolated Playwright driver abstraction.
   - `services/ai`: Isolated LLM API provider interface (supporting provider swaps).
   - `api/`: Request handler and validation layer.
4. **Stable Issue Identification**: Each issue receives a deterministic stable `Issue ID` based on issue type, category, element target selector, and issue signature. This allows precise matching during before/after fix verification.
5. **No Fake Data / Strong Typing**: Domain schemas are defined strictly via Pydantic (Backend) and TypeScript Interfaces (Frontend).

## Core Data Flow

```
[Target Application URL]
        │
        ▼
[FastAPI Audit Endpoint]
        │
        ├──────────────────────────┐
        ▼                          ▼
[Playwright Runner]        [LLM Analyzer Service]
 (Deterministic Evidence)   (Contextual Analysis & Prompting)
        │                          │
        └────────────┬─────────────┘
                     ▼
          [Structured Audit Result]
                     │
          [Before/After Audit Engine]
```

## Audit Verification Logic

When a developer submits a re-test audit following a fix:
1. UIProof AI runs the identical browser audit configuration.
2. Issues from the baseline audit and new audit are correlated using stable `Issue ID`s.
3. Comparative classification categorizes each issue into:
   - **Fixed**: Present in Baseline, absent in New Audit.
   - **Remaining**: Present in both Baseline and New Audit.
   - **New**: Absent in Baseline, detected in New Audit.
   - **Regression**: Previously fixed issue reappearing or severe new layout break.

## Security & Secrets
- No secrets or API keys are exposed to the frontend client.
- LLM API keys and backend settings are loaded via environment variables (`pydantic-settings`).
