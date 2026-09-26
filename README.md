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

#### A. Frontend Deployment (Vercel)
Deploy the `frontend/` directory as a Vercel project:
- **Root Directory**: `frontend`
- **Framework Preset**: Vite
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Required Environment Variable**:
  ```ini
  VITE_API_BASE_URL=https://YOUR-BACKEND-DOMAIN
  ```
  *Note*: `VITE_API_BASE_URL` must point to your deployed FastAPI backend API base URL (e.g. `https://your-backend.onrender.com/api/v1` or `https://your-backend.onrender.com`).

#### B. Backend Deployment (Render / Railway)
Deploy the `backend/` directory as a Web Service on Render or Railway:
- **Environment**: Python 3.10+
- **Build Command**:
  ```bash
  pip install -r requirements.txt && playwright install --with-deps chromium
  ```
- **Start Command**:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
  ```
- **System Requirements**: Python 3.10+, PostgreSQL, Playwright Chromium, and environment variables. Uvicorn is recommended to run with `--workers 1` because each headless Chromium audit instance requires dedicated CPU and RAM resources.

#### C. Database Setup & Alembic Migrations (PostgreSQL)
Provision a managed PostgreSQL database (Supabase, Neon, Render Postgres, Railway Postgres):
- Set `DATABASE_URL` environment variable:
  ```ini
  DATABASE_URL=postgresql://user:password@pg-host:5432/uiproof_db
  ```
  *(URI schemes starting with `postgres://` are automatically normalized to `postgresql://` at runtime).*
- Apply database migrations before launching the application:
  ```bash
  cd backend
  alembic upgrade head
  ```

#### D. Required Backend Environment Variables
Set the following environment variables in your cloud platform settings (never commit real secrets to Git):
```ini
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:password@host:5432/uiproof_db
JWT_SECRET_KEY=a-cryptographically-secure-random-32char-string
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=https://your-app-domain.vercel.app
LLM_PROVIDER=openai
LLM_API_KEY=sk-proj-your-api-key-here
ARTIFACTS_DIR=backend/artifacts
```

#### E. Production CORS Configuration
- **`CORS_ORIGINS`**: Must explicitly contain your deployed Vercel frontend origin (e.g. `https://your-app-domain.vercel.app`).
- Wildcards (`*`) and `localhost`/`127.0.0.1` origins are automatically stripped and rejected at backend startup when `ENVIRONMENT=production`. Do NOT use wildcard CORS in production.

#### F. Playwright Chromium Installation
- Playwright Chromium must be installed with Linux system dependencies during the build/container creation step:
  ```bash
  playwright install --with-deps chromium
  ```

#### G. Local vs Remote Audit Mode Configuration
- **Development (`ENVIRONMENT=development`)**:
  - **Local Audit Mode**: Can audit local targets (`http://localhost:<port>`, `http://127.0.0.1:<port>`).
  - **Remote Audit Mode**: Audits public web applications.
- **Production (`ENVIRONMENT=production`)**:
  - **Local Audit Mode**: Strictly blocked to prevent security risks.
  - **Remote Audit Mode**: Intended exclusively for public target URLs (SSRF protections actively block loopback, private IP ranges, and cloud metadata endpoints `169.254.169.254`).

#### H. Artifact & Screenshot Storage Warning
- **Current Implementation**: Screenshots, DOM metrics, and audit evidence artifacts are saved to the configured local filesystem directory (`ARTIFACTS_DIR`).
- **Cloud Storage Limitations**: Ephemeral cloud hosts (Render, Railway, Heroku without persistent disk mounts) will reset local filesystem storage upon instance restarts or redeployments, causing previously generated screenshots to become unavailable.
- **MVP Deployment**: For initial MVP deployments, persistent disk volume attachments or transient screenshot usage is acceptable depending on platform configuration.
- **Long-Term Production Recommendation**: Upgrade storage adapter to S3-compatible cloud object storage (Cloudflare R2, AWS S3, or Supabase Storage).

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
