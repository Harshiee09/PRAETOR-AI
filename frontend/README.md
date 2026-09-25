# PRAETOR AI — frontend

Next.js (App Router) + TypeScript + Tailwind 4, deployed on Vercel. The browser never calls the PRAETOR API directly:
server-side route handlers in `src/app/api/*` proxy to it and add the key. Contract: `../docs/api/openapi.json`;
real responses: `../docs/api/examples/`.

Pages: **Ask** (`/`, library questions), **Your document** (`/document`: upload a PDF, then ask, summarise, key
clauses and risks, checklist, questions for a lawyer, or compare two documents) and **About** (`/about`).
Design: monochrome (black gown, white bands), light and dark themes, the Velaris hero, Gateway Flow document hero,
Flow buttons, the Header and Comparison-2 layouts; motion pauses with the header toggle or `prefers-reduced-motion`.

## Local

```bash
npm ci
cp .env.example .env.local   # PRAETOR_API_URL=http://127.0.0.1:8000, PRAETOR_API_KEY = API_KEY from ../.env
npm run dev                  # http://127.0.0.1:3000 (the API must be running: `praetor serve` in the repo root)
npm test                     # 119 unit tests
npm run build
```

## Vercel

Import the GitHub repository, set **Root Directory** to `frontend` (framework: Next.js), and add two server-side
environment variables: `PRAETOR_API_URL` (the tunnel URL printed by `scripts\serve_public.cmd`) and
`PRAETOR_API_KEY` (the backend's `API_KEY`). Never use a `NEXT_PUBLIC_` prefix for either. The quick-tunnel URL
changes on every start: update `PRAETOR_API_URL` and redeploy. Details: `../docs/topics/ops/deployment.md`.
