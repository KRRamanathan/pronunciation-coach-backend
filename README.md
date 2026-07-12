---
title: Pronunciation Coach
emoji: 🎯
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Pronunciation Coach — Backend

Open-source FastAPI backend for English pronunciation scoring. Runs entirely self-hosted with **zero required API keys**.

## Runs with zero configured secrets

The app starts and fully functions with an empty `.env`. All environment variables are optional. SQLite is used by default for local development; point `DATABASE_URL` at Supabase Postgres for production.

## Stack

- **FastAPI** — async API server
- **faster-whisper** (`small.en`, int8) — speech-to-text with word timestamps
- **Allosaurus** — universal phone recognizer
- **g2p_en** — CMU dictionary expected phonemes
- **Postgres / Supabase** — structured results only (no audio)
- **Optional Gemini** — cosmetic feedback polish (not required)

## Local development

```bash
cd pronunciation-coach-backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python migrate.py
uvicorn app.main:app --reload --port 7860
```

First request loads models (~30–60s cold start). Health check: `GET http://localhost:7860/api/health`

## Docker

```bash
docker build -t pronunciation-coach-backend .
docker run -p 7860:7860 pronunciation-coach-backend
```

## Hugging Face Spaces deployment

1. Create a new **Docker** Space on [huggingface.co/spaces](https://huggingface.co/spaces).
2. Push this repo (or connect GitHub).
3. Set Space secrets (optional):
   - `DATABASE_URL` — Supabase connection string (`postgresql+asyncpg://...`)
   - `CORS_ORIGINS` — your Vercel frontend URL
   - `GEMINI_API_KEY` — optional polish
4. Space exposes port **7860** automatically.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Uptime + model load status |
| POST | `/api/consent` | Record DPDP consent, get `session_id` |
| POST | `/api/analyze` | Upload audio (multipart: `audio`, `session_id`) |
| GET | `/api/results/{session_id}` | Fetch stored results |
| DELETE | `/api/results/{session_id}` | Right to erasure (204) |

## Environment variables

See `.env.example`. None are required.

## Data & privacy

- Raw audio is written to `/tmp` only and deleted immediately after scoring.
- Only structured scores and transcripts are persisted (30-day retention by default).
- No PII collected — random session UUID only.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full design, DPDP compliance, and trade-offs.
