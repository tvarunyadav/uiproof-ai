# UIProof AI

**UIProof AI** is an AI-powered web application quality assurance and fix verification platform.

It automatically audits web applications across viewports using Playwright browser automation, captures deterministic evidence (screenshots, layout issues, network errors, console exceptions, accessibility flags), converts findings into developer-ready fix prompts, and performs automated before/after verification audits after fixes are applied.

---

## Production Deployment & Environment Configuration

### Overview
UIProof AI supports two primary operating environments: `development` and `production`. Environment configurations are managed via environment variables passed directly or loaded from `.env` files.

---

### Local Development Setup

#### Backend Configuration (`backend/.env`)
```ini
ENVIRONMENT=development
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=sqlite:///./uiproof.db
JWT_SECRET_KEY=change-this-development-secret-key-32chars
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key-here
ARTIFACTS_DIR=artifacts
```

#### Frontend Configuration (`frontend/.env`)
```ini
VITE_API_BASE_URL=http://127.0.0.1:8000
```

#### Running Development Servers
1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   playwright install chromium
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

### Production Deployment Setup

> **Note**: While production configuration hooks and environment hardening are implemented, deploying to a cloud platform requires provisioning managed database services (PostgreSQL) and setting runtime environment variables.

#### Production Backend Configuration (`ENVIRONMENT=production`)
In production mode (`ENVIRONMENT=production`), the application enforces strict security validation at startup:

```ini
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-app-domain.vercel.app,https://qa.yourdomain.com
DATABASE_URL=postgresql://user:password@pg-host:5432/uiproof_db
JWT_SECRET_KEY=a-very-long-random-cryptographically-secure-secret-key-32chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
LLM_PROVIDER=openai
LLM_API_KEY=sk-proj-prod-key-here
ARTIFACTS_DIR=backend/artifacts
```

#### Production Backend Hardening Rules
- **Host**: Defaults to `0.0.0.0` when `ENVIRONMENT=production` to bind to platform container networks.
- **Port**: Respects platform-provided `PORT` environment variables.
- **JWT Secret**: The app will fail to start if `JWT_SECRET_KEY` is missing or uses the development default placeholder.
- **CORS Hardening**: Wildcards (`*`) and `localhost` origins are disallowed in production. Explicit production domains must be specified in `CORS_ORIGINS`.
- **Database Migration**: Do not rely on `Base.metadata.create_all()`. Apply schema changes using Alembic:
  ```bash
  cd backend
  alembic upgrade head
  ```
- **Playwright Installation**: Install Playwright Chromium with system dependencies during the build/container build step (NOT at app startup):
  ```bash
  playwright install chromium --with-deps
  ```
- **Single Worker Recommendation**: Run Uvicorn with a single worker (`--workers 1`) initially. Each headless Chromium audit instance requires significant CPU/memory resources:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
  ```
- **Ephemeral Storage Notice**: Screenshots and artifacts are stored on the local disk at `ARTIFACTS_DIR`. On ephemeral container platforms (Render, Heroku, Railway without persistent volumes), artifacts are reset upon container restart/redeploy.

#### Production Frontend Configuration
When building the production static bundle, configure `VITE_API_BASE_URL` to point to the deployed backend URL:

```ini
VITE_API_BASE_URL=https://api.yourdomain.com
```

Build command:
```bash
cd frontend
npm run build
```
The output in `frontend/dist/` can be served via Vercel, Netlify, Cloudflare Pages, or Nginx.

---

## Technical Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts
- **Backend**: Python 3.10+, FastAPI, Pydantic v2, Uvicorn
- **Browser Automation**: Playwright Chromium (isolated service layer)
- **AI Layer**: OpenAI Provider Abstraction
- **Database**: SQLite (Development) / PostgreSQL (Production via SQLAlchemy & Alembic)

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
