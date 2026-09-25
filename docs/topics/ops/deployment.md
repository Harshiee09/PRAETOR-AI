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

### One link from the laptop (simplest; DECISIONS D53, verified V49)
Double-click `scripts\serve_app_public.cmd`. It starts the API (if not running), builds and serves the website on 127.0.0.1:3100, and opens a Cloudflare quick tunnel to the website. Share the `https://….trycloudflare.com` link it prints (also in `data\scratchpp-tunnel.log`). The API is never exposed; the key stays in `frontend\.env.local`. Keep the three windows open; Ctrl+C or closing one takes the site offline, and a restart gives a new link.

### Connect the Vercel frontend (remote demo; DECISIONS D51, verified V47)
Code: https://github.com/Harshiee09/PRAETOR-AI (public). Put the frontend in `frontend/` of this repository and set the Vercel project's **Root Directory** to `frontend` (or give it its own repository).
1. **Key.** `.env` must hold `API_KEY` (a long random string; generated 2026-09-25). Copy it from `.env` yourself; never paste it into chat, code or a commit.
2. **Tunnel.** Cloudflare quick tunnel, no account: `cloudflared.exe` 2026.9.3 in `C:\dev\tools` (from the cloudflared GitHub releases, SHA-256 checked, V47). Run `scripts\serve_public.cmd`: it starts `praetor serve` in its own window and then the tunnel, which prints a `https://<random>.trycloudflare.com` URL. That URL is public and **changes on every start**.
3. **Vercel.** Import the GitHub repository, set Root Directory `frontend`, and add server-side environment variables `PRAETOR_API_URL` = the tunnel URL and `PRAETOR_API_KEY` = the `API_KEY` (Production and Preview; never `NEXT_PUBLIC_*`). After each tunnel restart, update `PRAETOR_API_URL` and redeploy.
4. Call PRAETOR only from server-side code (a route handler or server action) that adds `X-API-Key`. **Never put the key in browser code**: anything shipped to the browser is public.
5. **Limits.** Vercel Hobby functions stop after 300 s and accept request bodies up to 4.5 MB (V43), so uploads are capped at 4 MB in the frontend. Cloudflare returns 524 if the origin sends no response within 125 s (Proxy Read Timeout; V47): answers take 12–25 s, but the API does one at a time, so several people asking at once can queue past that. Quick tunnels are for testing and development: at most 200 requests in flight, no Server-Sent Events, no uptime guarantee (V47). Keep the demo small.
6. **Offline.** Close the tunnel window (Ctrl+C) and the API window when the demo ends.

For a URL that survives restarts, a named Cloudflare Tunnel (needs a Cloudflare account and a domain) or ngrok's free static domain (needs an ngrok account) would replace step 2; neither is set up.

### Security checklist
- The server listens on 127.0.0.1 by default; `praetor serve` refuses another host without `API_KEY`.
- Tunnel traffic is treated as remote (forwarding headers), so it always needs the key.
- The only write endpoint is the document upload (D50): PDFs up to `DOC_MAX_MB`/`DOC_MAX_PAGES`, held in memory for `DOC_TTL_MINUTES`, at most `DOC_MAX_OPEN` at once (oldest dropped first), never written to disk. The answer cache is internal.
- Stop the tunnel when the demo ends; rotate `API_KEY` if it leaks (edit `.env`, restart `praetor serve`, update Vercel).
- No rate limiting is built: the one-at-a-time GPU lock is the only throttle, and anyone with the key can fill the queue.

### Cost
No cloud spend: models run locally; Vercel Hobby hosting within its limits; Cloudflare quick tunnels are free and need no account; the Supreme Court judgments were read anonymously from a public open-data bucket (no account). The laptop must stay on for a remote demo.

### Repository size
The GitHub repository must stay under 10 MB (D49). Weights, corpora, SQLite and FAISS are gitignored; full eval JSON dumps are no longer committed; `tests/unit/test_repo_size.py` fails above 8 MB of tracked files.

## Related
- [API contract](../architecture/api.md) — endpoints, fields, errors.
- [3-day build plan](build-plan.md) — Phases 3 and 4 as redefined.
- [Minimum viable architecture](../architecture/minimum-viable-architecture.md) — what runs where.
