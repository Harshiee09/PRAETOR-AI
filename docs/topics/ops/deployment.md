---
id: 20260925-deployment
title: Deployment
tags: [plan, safety, cost]
created: 2026-09-25
updated: 2026-09-25
related: [20260925-api, 20260922-minimum-viable-architecture, 20260922-build-plan]
summary: Local-only backend, Vercel-hosted frontend, the tunnel between them, secrets, limits and cost.
---

# Deployment

> Summary: Local-only backend, Vercel-hosted frontend, the tunnel between them, secrets, limits and cost.

## Context
AWS was dropped on 2026-09-25 (DECISIONS D47). The backend needs the GPU, two encoder models (4.3 GB and 2.2 GB on disk), torch and a local LLM through Ollama; Vercel Functions offer at most 2–4 GB of memory, 500 MB Python bundles (5 GB in beta) and no GPU (V43). So the backend runs on the laptop and only the frontend is deployed on Vercel.

## Details

### Topology
```text
browser ──> Vercel (frontend, built separately)
               └─ server-side route (holds PRAETOR_API_KEY) ──https──> tunnel ──> laptop: praetor serve (127.0.0.1:8000)
                                                                                        ├─ SQLite + FAISS (data/)
                                                                                        ├─ bge-m3 + reranker (GPU)
                                                                                        └─ Ollama gemma4:latest (GPU)
```
For local development the frontend can call `http://127.0.0.1:8000` directly (allowed origins in `CORS_ORIGINS`, no key needed from localhost).

### Run the backend
1. Ollama running with the model pulled (`ollama list` shows `gemma4:latest`).
2. `.env`: `API_KEY=<long random string>` for anything beyond localhost; `CORS_ORIGINS` for local frontends.
3. `praetor serve` (or `praetor.cmd serve` if Windows blocks the `praetor.exe` launcher, V45). Check `GET /v1/healthz` → `ok`.

### Connect the Vercel frontend (optional remote demo)
1. Start a tunnel to `http://127.0.0.1:8000` with a tunnel tool you trust (for example Cloudflare Tunnel or ngrok; follow the tool's current docs). The tunnel URL is public.
2. In the Vercel project, set server-side environment variables `PRAETOR_API_URL` (the tunnel URL) and `PRAETOR_API_KEY` (the same `API_KEY`).
3. Call PRAETOR only from server-side code (a route handler or server action) that adds `X-API-Key`. **Never put the key in browser code**: anything shipped to the browser is public.
4. Vercel Hobby functions stop after 300 s (V43); PRAETOR answers in ~13–20 s but queues concurrent questions, so keep the demo's concurrency low and the route's timeout generous.

### Security checklist
- The server listens on 127.0.0.1 by default; `praetor serve` refuses another host without `API_KEY`.
- Tunnel traffic is treated as remote (forwarding headers), so it always needs the key.
- The API has no write endpoints (the answer cache is internal); stop the tunnel when the demo ends; rotate `API_KEY` if it leaks.
- No rate limiting is built: the one-at-a-time GPU lock is the only throttle.

### Cost
No cloud spend: models run locally; Vercel Hobby hosting within its limits; the Supreme Court judgments were read anonymously from a public open-data bucket (no account). The laptop must stay on for a remote demo.

### Repository size
The GitHub repository must stay under 10 MB (D49). Weights, corpora, SQLite and FAISS are gitignored; full eval JSON dumps are no longer committed; `tests/unit/test_repo_size.py` fails above 8 MB of tracked files.

## Related
- [API contract](../architecture/api.md) — endpoints, fields, errors.
- [3-day build plan](build-plan.md) — Phases 3 and 4 as redefined.
- [Minimum viable architecture](../architecture/minimum-viable-architecture.md) — what runs where.
