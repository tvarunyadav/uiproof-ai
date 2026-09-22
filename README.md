# UIProof AI

**UIProof AI** is an AI-powered web application quality assurance and fix verification platform.

It automatically audits web applications across viewports using Playwright browser automation, captures deterministic evidence (screenshots, layout issues, network errors, console exceptions, accessibility flags), converts findings into developer-ready fix prompts, and performs automated before/after verification audits after fixes are applied.

---

## Technical Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts
- **Backend**: Python 3.10+, FastAPI, Pydantic v2, Uvicorn
- **Browser Automation**: Playwright (isolated service layer)
- **AI Layer**: LLM API Abstraction (Provider independent)
- **Database**: PostgreSQL (stubs/models prepared)

---

## Repository Structure

```
uiproof-ai/
├── docs/                   # Architecture documentation & specifications
├── frontend/               # React + TypeScript + Vite + Tailwind frontend application
│   ├── src/
│   │   ├── components/     # UI primitives & layouts (Linear/Vercel visual style)
│   │   ├── services/       # API client for FastAPI
│   │   └── types/          # TypeScript domain interfaces
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── api/            # Versioned API routes (v1)
│   │   ├── schemas/        # Pydantic data schemas (Evidence, Issues, Audits)
│   │   ├── services/       # Isolated service modules (browser, ai, audit)
│   │   └── config.py       # App settings & env configuration
│   └── tests/              # Pytest backend test suite
```

---

## Getting Started

### Prerequisites

- Node.js >= 18.x
- Python >= 3.10
- npm / pip

### Backend Setup

1. Navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment example:
   ```bash
   cp .env.example .env
   ```
5. Run backend development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   FastAPI interactive API documentation (Swagger) is accessible at [http://localhost:8000/docs](http://localhost:8000/docs).

6. Run backend test suite:
   ```bash
   pytest
   ```

### Frontend Setup

1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Copy environment example:
   ```bash
   cp .env.example .env
   ```
4. Run frontend development server:
   ```bash
   npm run dev
   ```
   Access the frontend interface at [http://localhost:5173](http://localhost:5173).

---

## Design System

The frontend implements a dark-first developer tool UI inspired by Linear and Vercel:
- **Primary Background**: `#09090B`
- **Surface Backgrounds**: `#111113`, `#18181B`
- **Borders**: `#27272A`
- **Accents**: `#6366F1` (Primary Indigo), `#818CF8` (Hover Indigo)
- **Status Colors**: `#22C55E` (Success), `#F59E0B` (Warning), `#EF4444` (Error)
- **Typography**: `Inter` for interface elements, `JetBrains Mono` for code, URLs, and evidence logs.

---

## Milestone 1 Status

- ✅ Repository foundation established for Frontend and Backend.
- ✅ Typed request/response schemas created (Pydantic & TypeScript).
- ✅ Service layer isolation enforced (`browser/`, `ai/`, `audit.py`).
- ✅ Stable Issue ID generation logic defined.
- ✅ Runnable dark-first developer dashboard frontend.
- ✅ Runnable FastAPI backend with health endpoints & OpenAPI docs.
- ⏳ Real Playwright audit runner, Postgres database integration, and live LLM calls will be integrated in subsequent milestones.
