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

**Windows:** Use Python 3.11 (not 3.13 — Allosaurus deps need prebuilt wheels). Set `HF_HUB_DISABLE_SYMLINKS=1` before first run if Developer Mode is off.

```bash
cd pronunciation-coach-backend
py -3.11 -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python migrate.py
# Windows PowerShell:
$env:HF_HUB_DISABLE_SYMLINKS="1"
uvicorn app.main:app --reload --port 7860
# Or: .\start-local.ps1
```

First request loads models (~30–60s cold start). Health check: `GET http://localhost:7860/api/health`

## Docker

```bash
docker build -t pronunciation-coach-backend .
docker run -p 7860:7860 pronunciation-coach-backend
```

## Railway deployment (recommended if HF Docker is unavailable)

1. Push this repo to GitHub (already at `KRRamanathan/pronunciation-coach-backend`).
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → select `pronunciation-coach-backend`.
3. Railway detects `railway.toml` and builds via **Dockerfile** (~10–15 min first build).
4. In **Variables**, add:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your Supabase URI — plain `postgresql://...` is fine |
| `CORS_ORIGINS` | `https://pronunciation-coach-frontend.vercel.app` |
| `GEMINI_API_KEY` | Optional |

5. **Settings → Networking → Generate Domain** — copy the public URL (e.g. `https://pronunciation-coach-backend-production.up.railway.app`).
6. Update Vercel env `NEXT_PUBLIC_API_URL` to that Railway URL and redeploy the frontend.

**Note:** Railway free trial credits apply. Whisper + Allosaurus need ~2–4 GB RAM — if the service crashes on startup, upgrade the service memory in Railway or use Hugging Face Docker (16 GB free tier).

## Hugging Face Spaces deployment

1. Create a new **Docker** Space on [huggingface.co/spaces](https://huggingface.co/spaces).
2. Push this repo (or connect GitHub).
3. Set Space secrets (optional):
   - `DATABASE_URL` — Supabase connection string (`postgresql://...` or `postgresql+asyncpg://...`)
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
