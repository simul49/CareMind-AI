# CareMind AI — Smart Care. Safe Living. Peace of Mind.

A private AI-powered digital care ecosystem connecting **Older Adults + Family/Caregiver + Trusted Doctor + AI**.

Built for the 3-day hackathon. Full product spec in [CareMind_AI_PRD_v2.1.md](./CareMind_AI_PRD_v2.1.md).

## Stack

| Layer | Tech |
|---|---|
| Frontend | Vue 3, TypeScript, Vite, Pinia, Tailwind CSS |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, PyJWT |
| Database | MySQL 8 (Docker) |
| AI | OpenAI-compatible API (DeepSeek / Qwen / Hunyuan) with offline mock fallback |

## Quick Start

### 1. Database

```bash
docker compose up -d mysql
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # Windows  (mac/linux: cp)
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

## Demo Accounts (seeded automatically)

| Role | Email | Password |
|---|---|---|
| Elder | rahma@caremind.demo | Password1! |
| Family | nadia@caremind.demo | Password1! |
| Doctor | doctor@caremind.demo | Password1! |

## AI Configuration

Optional. Set in `backend/.env`:

```
AI_API_KEY=your_key
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat
```

Without a key, CareMind runs in **demo mode** with scripted, context-aware replies — perfect for offline judging.

## Project Layout

```
backend/            FastAPI application
frontend/           Vue 3 application
schema.sql          MySQL reference schema (v2.1)
ER_DIAGRAM.md       Entity relationship model
```
