# UIProof AI

**AI-Powered Web Application Quality Assurance & Fix Verification Platform**

*Test. Diagnose. Fix. Re-test.*

[![Production Web App](https://img.shields.io/badge/Production%20App-Vercel-000000?style=for-the-badge&logo=vercel)](https://uiproof-ai.vercel.app)
[![Production API](https://img.shields.io/badge/Production%20API-FastAPI%20%7C%20Render-009688?style=for-the-badge&logo=fastapi)](https://uiproof-ai-3.onrender.com)
[![Validation Target](https://img.shields.io/badge/Controlled%20Target-Demo%20Vercel-4F46E5?style=for-the-badge&logo=vercel)](https://uiproof-demo-target.vercel.app)

---

## Overview

**UIProof AI** is an automated quality assurance and verification platform for web applications. It automates multi-viewport browser testing using headless Playwright Chromium, collects empirical browser evidence (full-page screenshot artifacts, DOM measurements, console exceptions, network failures, broken resources, and basic accessibility flags), generates grounded AI-assisted root-cause analyses and developer fix prompts, and performs baseline-versus-retest comparison audits to verify whether reported defects are genuinely resolved.

UIProof AI treats **deterministic browser evidence as the source of truth**. AI models do not detect defects or guess page states; instead, they analyze verified browser traces to help developers understand why issues occur and how to fix them.

---

## Live Demo Links

| Environment / Service | URL / Link | Description |
| :--- | :--- | :--- |
| **Frontend Web Application** | [https://uiproof-ai.vercel.app](https://uiproof-ai.vercel.app) | React + Vite single-page web app deployed on Vercel |
| **Backend REST API** | [https://uiproof-ai-3.onrender.com](https://uiproof-ai-3.onrender.com) | FastAPI backend deployed on Render with Playwright Chromium |
| **Controlled Validation Target** | [https://uiproof-demo-target.vercel.app](https://uiproof-demo-target.vercel.app) | Deployed target application used for end-to-end verification |
| **Target Codebase Repository** | [github.com/tvarunyadav/uiproof-demo-target](https://github.com/tvarunyadav/uiproof-demo-target) | Target repository containing baseline (broken) and fixed commits |

---

## Why UIProof AI?

Modern web application development requires constant testing across desktop and mobile viewports. Traditional automated testing scripts detect errors but require manual investigation to analyze logs, capture visual evidence, draft bug reports, and confirm resolution after code edits.

UIProof AI bridges browser automation and developer workflows by providing:
1. **Multi-Viewport Automation**: Simultaneous auditing across Desktop ($1440 \times 900$) and Mobile ($390 \times 844$) viewports.
2. **Empirical Evidence Collection**: Grounding every reported issue in exact CSS selectors, HTTP response codes, document measurements, and full-page visual screenshots.
3. **Structured AI Root-Cause Analysis**: Converting raw browser diagnostics into step-by-step developer remediation prompts using primary (Google Gemini) and fallback (Groq) LLM providers.
4. **Automated Re-Test Verification**: Retesting updated applications against historical baselines to classify findings into **FIXED**, **REMAINING**, or **NEW** issues.

---

## Core Workflow

```
[ Target URL ]
      │
      ▼
[ Playwright Browser Audit ]  ──► Desktop (1440x900) & Mobile (390x844)
      │
      ▼
[ Deterministic Issue Detection ] ──► Console, Network, Overflow, A11y, Images, Links, Metadata, Page-Load
      │
      ▼
[ Evidence Collection ] ──► Screenshots, Selectors, DOM Scroll Measurements
      │
      ▼
[ Grounded AI Analysis ] ──► Google Gemini (with Groq Fallback)
      │
      ▼
[ Developer Fix Prompt ] ──► Formatted Prompt & Investigation Guidance
      │
      ▼
[ Developer Fixes & Redeploys ]
      │
      ▼
[ UIProof Re-Test ] ──► Automated Baseline Comparison
      │
      ▼
[ Verification Output ] ──► FIXED / REMAINING / NEW Classification
```

---

## Key Features

* **Multi-Viewport Playwright Audits**: Executes isolated headless Chromium instances for Desktop ($1440 \times 900$) and Mobile ($390 \times 844$) viewports.
* **Deterministic Issue Detection**: Implemented deterministic audit checks for console errors, network failures, horizontal overflow, broken images, broken links, missing page metadata, basic accessibility violations, and page-load failures.
* **Stable Deterministic Issue Hash IDs**: Generates predictable, reproducible issue hashes (e.g., `UI-OVERFLOW-MOBILE`, `UI-BROKEN-IMAGE-DESKTOP`) to track issues across re-runs.
* **Protected Screenshot Artifacts**: Authenticated artifact API serving Blob URLs via JWT Bearer authorization and project ownership validation.
* **Fit-to-View Lightbox Viewer**: Interactive screenshot viewer with fit-to-view containment, aspect ratio preservation ($16:10$ desktop, $390:844$ mobile), zoom controls ($50\% \text{ to } 300\%$), and keyboard shortcuts (`+`, `-`, `0`, `Esc`).
* **Resilient Multi-Provider LLM Engine**: Primary AI analysis powered by Google Gemini, with automatic failover to Groq if the primary provider exhausts its handling for retryable/transient provider failures. Models are fully configurable via environment variables.
* **Developer Fix Prompt Generator**: Synthesizes issue context, element selectors, and browser diagnostics into structured investigation hints, expected results, verification steps, and prompts for developer AI coding tools.
* **Before/After Retest Engine**: Differential comparison algorithm mapping re-test findings to baseline audits.
* **Dual Execution Modes**: Support for **Local Audit Mode** (auditing `localhost` / `127.0.0.1` dev servers) and **Remote Audit Mode** (auditing public production URLs).
* **Project & History Management**: Project creation, audit history tracking, and persistent storage backed by PostgreSQL.

---

## Architecture

UIProof AI uses a decoupled client-server architecture with an isolated browser worker execution thread and a resilient multi-provider AI engine.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        React 18 + Vite Frontend                        │
│             (TypeScript, Vanilla/Tailwind CSS, Lucide Icons)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Authenticated REST API (JWT)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend Service                        │
│    ┌──────────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│    │ Playwright Runner    │  │ LLM Engine       │  │ Audit Engine │   │
│    │ (Dedicated Thread)   │  │ (Gemini + Groq)  │  │ & Retest     │   │
│    └──────────┬───────────┘  └────────┬─────────┘  └──────┬───────┘   │
└───────────────┼───────────────────────┼───────────────────┼────────────┘
                │                       │                   │
                ▼                       ▼                   ▼
     ┌────────────────────┐   ┌───────────────────┐   ┌──────────────┐
     │ Headless Chromium  │   │  Gemini / Groq    │   │  PostgreSQL  │
     │ Desktop & Mobile   │   │  API Providers    │   │  Database    │
     └────────────────────┘   └───────────────────┘   └──────────────┘
```

---

## Implemented Deterministic Detections

All defects identified by UIProof AI are derived strictly from empirical browser inspection:

* **Console Errors**: Uncaught JavaScript exceptions and runtime errors trapped during page execution.
* **Network Failures**: Failed HTTP requests, connection timeouts, or 4xx/5xx network responses.
* **Horizontal Overflow**: Measured document `scrollWidth` exceeding viewport `clientWidth` (e.g., $687\text{px} > 390\text{px}$ on mobile).
* **Broken Images**: `<img>` elements with zero natural width or unresolvable image sources.
* **Broken Links**: On-page hyperlinks (`<a href>`) pointing to unreachable or non-2xx HTTP endpoints.
* **Missing Page Metadata**: Lacking or empty `<title>` tags and `<meta name="description">` tags.
* **Basic Accessibility Violations**: Fundamental accessibility flags, such as images missing `alt` attributes or form controls lacking accessible labels.
* **Page-Load Failures**: Target application navigation timeouts, connection refusals, or HTTP 4xx/5xx status codes.

---

## Evidence-Based AI Analysis

UIProof AI enforces a strict boundary between **deterministic defect detection** and **AI analysis**:

> **Ground Truth Principle**: Deterministic browser evidence is the absolute source of truth. Playwright inspects actual DOM dimensions, network traces, and console logs. AI models do NOT perform defect detection or page inspection. AI is utilized solely to analyze verified browser evidence, hypothesize likely causes, and suggest debugging strategies.

When a developer requests AI analysis for an issue, the AI provider receives verified browser evidence and returns a structured payload matching the following schema:

* **`summary`**: High-level summary of the detected issue and initial diagnostic context.
* **`likely_causes`**: Hypothesized root causes grounded in observed browser trace evidence.
* **`investigation_hints`**: Recommended DOM, CSS, or network inspection steps for developers.
* **`expected_result`**: Description of expected correct behavior once resolved.
* **`constraints`**: Technical, responsive, or architectural constraints to preserve during fix implementation.
* **`verification_steps`**: Measurable verification steps for validating the resolution.
* **`fix_prompt`**: Context-rich prompt formatted for developer AI coding tools.

### LLM Provider & Fallback Resilience
* **Primary Provider**: Google Gemini (configured via environment variables).
* **Fallback Provider**: Groq (configured via environment variables).
* **Fallback Mechanism**: Automatic failover to Groq occurs only after the primary provider exhausts its handling for retryable or transient provider failures (such as rate limits or server errors).

---

## Fix Prompt & AI Diagnostic Payload Example

The structured AI analysis payload provides developers with both evidence-grounded hypotheses and a formatted prompt for AI coding assistants:

```json
{
  "summary": "Mobile horizontal overflow detected: document scrollWidth (687px) exceeds viewport clientWidth (390px) by 297px.",
  "likely_causes": [
    "Unconstrained element with fixed pixel width (e.g. width: 480px or min-width: 480px) extending beyond 390px mobile viewport.",
    "Unresponsive header navigation container or media element lacking max-width constraints."
  ],
  "investigation_hints": [
    "Inspect elements with rect.right > 390px in DevTools Console using document.querySelectorAll('*').",
    "Check top-level wrapper containers, navigation headers, and hero media elements for explicit inline or CSS width declarations."
  ],
  "expected_result": "Document scrollWidth should match clientWidth (390px) on mobile viewports with zero horizontal scrolling.",
  "constraints": [
    "Preserve desktop layout styling and breakpoint behavior at 1440px viewport.",
    "Do not hide overflow globally using overflow-x: hidden on body if content is clipped."
  ],
  "verification_steps": [
    "Load page in mobile viewport (390x844).",
    "Evaluate window.innerWidth === document.documentElement.scrollWidth."
  ],
  "fix_prompt": "### UIProof AI Issue Fix Request\n- **Issue ID**: UI-OVERFLOW-MOBILE\n- **Viewport**: Mobile (390x844)\n- **Target Selector**: body\n- **Evidence**: Viewport: 390px, ScrollWidth: 687px, Overflow: 297px\n\nPlease investigate the likely causes above, inspect the element constraints, and update the responsive CSS layout to ensure all content fits within 390px without introducing global overflow hidden masks."
}
```

---

## Re-test & Fix Verification

When code changes are committed and deployed, developers run a **UIProof Re-test** against the baseline audit. UIProof compares the new audit results with the baseline using deterministic issue hashes:

* <span style="color:#22c55e; font-weight:bold;">FIXED</span>: Issue was present in the baseline audit but is no longer detected in the re-test.
* <span style="color:#f59e0b; font-weight:bold;">REMAINING</span>: Issue was present in the baseline audit and persists in the re-test.
* <span style="color:#3b82f6; font-weight:bold;">NEW</span>: Issue was not present in the baseline audit but appeared in the re-test (regression).

---

## Local vs Remote Audit Mode

UIProof AI supports two distinct execution environments for auditing applications:

| Mode | Allowed Target URLs | Environment | Use Case |
| :--- | :--- | :--- | :--- |
| **Local Audit Mode** | `http://localhost:<port>`, `http://127.0.0.1:<port>` | Local Backend (`ENVIRONMENT=development`) | Auditing pre-release code running on a developer's local machine. |
| **Remote Audit Mode** | `https://your-app.com` (Public URLs) | Local or Deployed Backend (`ENVIRONMENT=production`) | Auditing staging or production deployments accessible over the public internet. |

> **Network Isolation Note**: Deployed cloud instances of UIProof AI (such as on Render or Vercel) **cannot** directly access a developer's `localhost` or internal private network. To audit local development servers (`http://localhost:3000`), run the UIProof backend locally. In production mode (`ENVIRONMENT=production`), SSRF protection actively blocks loopback addresses, private IP ranges ($10.x, 192.168.x$), and cloud metadata endpoints (`169.254.169.254`).

---

## Technology Stack

### Frontend
* **Framework**: React 18, TypeScript, Vite
* **Styling**: Vanilla CSS custom design system + Tailwind CSS utilities
* **Icons & Components**: Lucide React, custom accessible components
* **HTTP Client**: Native `fetch` with custom JWT Bearer interceptor

### Backend
* **Framework**: Python 3.10+, FastAPI, Pydantic v2
* **Server**: Uvicorn ASGI server (configured with single-worker concurrency for Chromium stability)
* **Database**: SQLite (Development) / PostgreSQL (Production via SQLAlchemy ORM & Alembic migrations)
* **Authentication**: PyJWT (HS256 algorithm) with bcrypt password hashing

### Browser Automation & AI
* **Browser Engine**: Playwright Chromium (async API executed inside dedicated thread worker)
* **Primary LLM Provider**: Google Gemini (model configurable via `GEMINI_MODEL`)
* **Fallback LLM Provider**: Groq (model configurable via `GROQ_MODEL`)
* **Resilience**: Multi-provider fallback engine with HTTPX request log sanitization

---

## Security Architecture

1. **Authenticated Artifact API**: Audit screenshots are stored in a protected directory. Image endpoints require a valid JWT `Authorization: Bearer <token>` header.
2. **Project Ownership & IDOR Protection**: Users can only query audits, issues, and artifacts belonging to projects owned by their user account. Unauthorized requests return `404 Not Found` to prevent resource enumeration.
3. **Log Sanitization**: Sensitive query parameters (such as `?key=...` for API keys) and Authorization headers are automatically scrubbed from HTTPX request logs and application error traces.
4. **SSRF Guardrails**: Target URL validation rejects non-HTTP(S) protocols and blocks private IP ranges when deployed in production mode.

---

## Controlled End-to-End Validation

To verify UIProof AI's end-to-end audit, AI diagnosis, fix prompt generation, and re-test comparison workflow, a dedicated controlled target application was deployed:

* **Target Repository**: [github.com/tvarunyadav/uiproof-demo-target](https://github.com/tvarunyadav/uiproof-demo-target)
* **Target Deployment**: [uiproof-demo-target.vercel.app](https://uiproof-demo-target.vercel.app)

### Verification Scenario

1. **Baseline Audit (Commit [`f2a4f26`](https://github.com/tvarunyadav/uiproof-demo-target/commit/f2a4f26))**:
   * Target intentionally contained defects including responsive horizontal overflow, a broken image resource (`404`), a missing `<meta name="description">` tag, and an unlabeled form control.
   * Investigation revealed multiple contributors to horizontal overflow, including fixed-width content blocks and responsive header layout elements.
2. **Fix Application (Commit [`82c4a12`](https://github.com/tvarunyadav/uiproof-demo-target/commit/82c4a12))**:
   * Applied responsive content and header layout fixes (`max-width: 100%`, flex wrapping), replaced the broken image resource, added the missing meta description, and added proper form labels.
3. **Re-Test Audit**:
   * UIProof AI executed a re-test audit against the updated target deployment.
   * **Results**: Demonstrated baseline issues classified as <span style="color:#22c55e; font-weight:bold;">FIXED</span> with **0** <span style="color:#f59e0b; font-weight:bold;">REMAINING</span> issues and **0** <span style="color:#3b82f6; font-weight:bold;">NEW</span> issues for that comparison run.

> **Scope Note**: This controlled validation demonstrates that the end-to-end audit, measurement, issue tracking, and comparison pipeline functions as designed on a reproducible test fixture. It is not a generalized claim of universal accuracy across all web applications.

---

## Screenshots

> *Placeholders for UIProof AI platform screenshots. Add captured PNG files into `docs/screenshots/`.*

### 1. Launching a New Multi-Viewport Audit
![New Audit Workspace](docs/screenshots/new-audit.png)
*Configuring target URL, audit mode (Remote/Local), and viewports (Desktop & Mobile).*

### 2. Audit Findings & Summary Dashboard
![Audit Results Workspace](docs/screenshots/audit-results.png)
*Summary metrics, severity distribution, category breakdown, and deterministic issue list.*

### 3. Mobile Horizontal Overflow Evidence
![Mobile Overflow Evidence](docs/screenshots/overflow-evidence.png)
*Empirical DOM scroll measurements (390px viewport vs 687px scrollWidth) and selector location.*

### 4. AI Root Cause Analysis & Fix Prompt
![AI Analysis Panel](docs/screenshots/ai-analysis.png)
*Grounded AI root cause explanation, recommended code fix, and developer copy-prompt.*

### 5. Protected Fit-to-View Lightbox Viewer
![Evidence Lightbox Viewer](docs/screenshots/evidence-lightbox.png)
*Full-page screenshot artifact with contain-style scaling, aspect ratio preservation, and zoom.*

### 6. Retest & Baseline Comparison Workspace
![Retest Comparison Workspace](docs/screenshots/retest-comparison.png)
*Before/After comparative analysis classifying findings into FIXED, REMAINING, and NEW.*

---

## Local Development Setup

### Prerequisites
* **Node.js**: `>= 18.0.0`
* **Python**: `>= 3.10`
* **Chromium Dependencies**: Installed automatically via Playwright CLI

### 1. Clone Repository
```bash
git clone https://github.com/tvarunyadav/uiproof-ai.git
cd uiproof-ai
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright Chromium browser binary
playwright install chromium

# Copy environment variables
cp .env.example .env
```

### 3. Frontend Setup
```bash
cd ../frontend

# Install Node dependencies
npm install

# Copy environment variables
cp .env.example .env
```

---

## Environment Variable Configuration

### Backend (`backend/.env`)
```ini
# Operating Environment
ENVIRONMENT=development
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO

# Database Connection (SQLite for local dev, PostgreSQL for production)
DATABASE_URL=sqlite:///./uiproof.db

# Security & Authentication
JWT_SECRET_KEY=your_development_jwt_secret_key_min_32_characters_long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration (comma-separated origins)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# AI Provider Configuration
LLM_PROVIDER=gemini
LLM_FALLBACK_PROVIDER=groq
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=<configured_gemini_model>
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=<configured_groq_model>

# Artifact Storage Directory
ARTIFACTS_DIR=artifacts
```

### Frontend (`frontend/.env`)
```ini
# FastAPI Backend Base URL
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## Running Development Servers

### Start Backend
```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
* Interactive Swagger API documentation available at: `http://127.0.0.1:8000/docs`
* ReDoc API documentation available at: `http://127.0.0.1:8000/redoc`

### Start Frontend
```bash
cd frontend
npm run dev
```
* Web application available at: `http://localhost:5173`

---

## Testing & Build Instructions

### Run Backend Pytest Suite
```bash
cd backend
python -m pytest -q
```

### Run Frontend Type Check & Production Build
```bash
cd frontend
npm run build
```

---

## Production Deployment Architecture

### Frontend (Vercel)
* Build Command: `npm run build`
* Output Directory: `dist`
* Environment Variables: `VITE_API_BASE_URL=https://uiproof-ai-3.onrender.com`

### Backend (Render Web Service)
* Environment: Python 3.10+
* Build Command: `pip install -r requirements.txt && PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium`
* Environment Variables: `PLAYWRIGHT_BROWSERS_PATH=0`, `DATABASE_URL=postgresql://user:password@host:5432/uiproof_db`
* Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`
* Database: Managed PostgreSQL (Supabase / Render Postgres)
* Migrations: `alembic upgrade head`

---

## Current Limitations

1. **Ephemeral Cloud Storage**: Standard cloud free tiers (e.g. Render without persistent disk mounts) clear local filesystem storage on container restarts. Screenshot artifacts from historical audits may expire unless persistent disk volumes or S3 storage adapters are configured.
2. **Concurrency Constraints**: Running headless Chromium browser contexts consumes significant CPU and RAM. Backend instances run single-worker processes to avoid memory exhaustion during concurrent audits.
3. **Network Accessibility**: Deployed cloud instances cannot audit local developer applications (`http://localhost:3000`). Local audit capability requires running the backend on the developer's machine.

---

## Future Enhancements

* **S3 / Cloud Object Storage Adapter**: Plug-in adapter for AWS S3 / Cloudflare R2 / Supabase Storage for persistent screenshot artifacts.
* **CI/CD Pipeline Integration**: GitHub Action plugin to automatically trigger UIProof audits on Pull Requests.
* **Expanded Accessibility Audit Rules**: Integration with `axe-core` for full WCAG 2.1 AA accessibility compliance testing.
* **Scheduled Synthetic Monitoring**: Periodic background auditing of production endpoints with failure alerting.

---

## Repository Structure

```
uiproof-ai/
├── README.md                   # Project documentation
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/                # API router & endpoints (audits, auth, projects)
│   │   ├── db/                 # Database models, sessions, Alembic migrations
│   │   ├── schemas/            # Pydantic data schemas (audit, evidence, issue, ai)
│   │   ├── services/           # Service layer
│   │   │   ├── ai/             # LLM provider abstraction (Gemini, Groq, OpenAI, Stub)
│   │   │   ├── browser/        # Playwright runner & deterministic detection
│   │   │   └── audit.py        # Audit engine orchestrator & retest comparator
│   │   ├── config.py           # Application settings & environment configuration
│   │   └── main.py             # FastAPI entrypoint & CORS middleware
│   ├── artifacts/              # Local storage for screenshot artifacts
│   ├── requirements.txt        # Python dependencies
│   └── tests/                  # Backend pytest test suite
└── frontend/                   # React 18 + TypeScript + Vite frontend
    ├── src/
    │   ├── components/         # UI components (audit, compare, results, ai, auth)
    │   ├── services/           # API fetch client & JWT state
    │   ├── types/              # TypeScript interface definitions
    │   ├── App.tsx             # Root application component & lightbox
    │   └── main.tsx            # React DOM entrypoint
    ├── package.json            # Node dependencies & scripts
    └── vite.config.ts          # Vite build configuration
```

---

## Author & Project Context

Developed as an advanced AI-powered web quality assurance platform demonstration.

* **Author**: Varun Yadav ([@tvarunyadav](https://github.com/tvarunyadav))
* **Repository**: [https://github.com/tvarunyadav/uiproof-ai](https://github.com/tvarunyadav/uiproof-ai)

---

## License

UIProof AI is source-available for personal, educational, academic,
research, evaluation, and other non-commercial purposes.

**Commercial use is not permitted without prior written authorization.**

Organizations or individuals interested in using UIProof AI or substantial
portions of its source code commercially must obtain a separate commercial
license from the copyright holder.

See the [LICENSE](LICENSE) file for the complete terms.

Copyright © 2026 Varun Yadav T. All rights reserved.