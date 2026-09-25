# Prompt for the frontend builder (GPT-6 Astra)

Paste everything below the line. Attach `docs/api/openapi.json` from this repository (the contract is authoritative
if anything here disagrees), and `docs/api/examples/*.json` once they exist.

---

Build the web frontend for **PRAETOR AI**, an informational legal-research assistant for Indian law. It answers
questions from 12 central Acts and 1,000 Supreme Court judgments, and every answer cites its sources. It is **not a
lawyer and gives no legal advice**; the UI must never suggest otherwise.

## Architecture (fixed)
- The backend is a FastAPI server that runs on the owner's laptop (it needs a GPU and several GB of models, so it
  cannot run on Vercel). For a public deployment it is reachable through a tunnel URL.
- Build a **Next.js (App Router) + TypeScript** app deployed on **Vercel**.
- The browser **never calls the backend directly**. Add server-side route handlers that proxy to it:
  - `POST /api/ask` → `POST {PRAETOR_API_URL}/v1/ask`
  - `GET /api/sources/[chunkId]` → `GET {PRAETOR_API_URL}/v1/sources/{chunk_id}`
  - `GET /api/health` → `GET {PRAETOR_API_URL}/v1/healthz`
- Server-only environment variables: `PRAETOR_API_URL` and `PRAETOR_API_KEY`. The proxy sends `X-API-Key:
  PRAETOR_API_KEY` and forwards or creates `X-Request-ID`. **The key must never reach browser code or any
  `NEXT_PUBLIC_*` variable.**
- Answers take about 10–20 s, and the backend answers one question at a time, so requests may queue. Set the ask
  route's `maxDuration` to 300 s (Vercel Hobby maximum) and the upstream fetch timeout to about 280 s.
- Validate on the server too: `question` is 1–2000 characters, trimmed.

## API contract (from openapi.json)
`POST /v1/ask` request: `{"question": string, "mode": "full", "explain": false, "use_cache": true}` (always send
`mode: "full"` or omit it).

Response `AskResponse`:
- `answer_markdown` (string): the answer in Markdown. Refers to sources with markers like `[S1]`, `[S2]`. A
  high-stakes answer starts with a blockquote safety note. The last paragraph is a "**Jurisdiction and date:**" line.
- `citations[]`: `id` (the `S#` marker), `chunk_id`, `title`, `locator` (e.g. `s. 106`, `paras 12-15`),
  `authority`, `jurisdiction` (`IN` = central law, or a state code like `IN-UP`), `status` (`in_force`, `repealed`,
  `partially_in_force`, `n/a` for judgments), `source_url`, `retrieved_at`, `quote` (verbatim, ≤ 300 characters),
  and optionally `section_heading`, `court`, `decision_date`, `citation`.
- `warnings[]` (strings): notes to show with the answer (repeal and transition notes, state-law coverage, removed
  sentences).
- `confidence`: `high` | `medium` | `low`.
- `abstained` (boolean): true when no answer was generated (evidence too thin, or a refused request).
- `jurisdiction_note`, `disclaimer` (strings); `trace_id` (equals the `X-Request-ID` header).
- `provider`: `ollama` (model answer), `extractive` (no model; verbatim passages only), or `null` (abstained).
- `model`, `classification` (`domain`, `intent`, `high_stakes`), `cached` (boolean), `latency_ms`, `explain` (object
  or null; only when requested).

`GET /v1/sources/{chunk_id}` returns the full stored passage: `text` plus `title`, `locator`, `doc_type`,
`authority`, `jurisdiction`, `status`, `language`, `source_url`, `retrieved_at`, `licence`, `page_start`, `page_end`,
and statute fields (`act_title`, `section`, `section_heading`) or judgment fields (`case_title`, `court`,
`decision_date`, `citation`).

`GET /v1/healthz` returns `{"status": "ok" | "degraded" | "down", "checks": {...}}`; `down` comes with HTTP 503.

Errors are always `{"error": {"code", "message", "request_id"}}`: 401 `unauthorized`, 404 `not_found`,
422 `invalid_request`, 503 `unavailable`, 500 `internal_error`.

## Screens and behaviour
1. **Ask page** (the home page): a question box (multiline, 2000-character counter, Enter to submit, Shift+Enter for
   a new line), example questions to click, and the answer area. Disable submit while a request is running (one
   question at a time) and show an elapsed-time indicator with "Searching and checking sources…". Announce the answer
   with `aria-live`.
2. **Answer view**:
   - Render `answer_markdown` with a Markdown renderer that **does not allow raw HTML** (the text is model-generated).
   - Turn every `[S#]` into a small clickable chip that scrolls to and highlights the matching citation card. If a
     marker has no card, render it as plain text.
   - Keep the blockquote safety note at the top, visually distinct (not alarming red, but clear).
   - Show a confidence badge (`high`/`medium`/`low`) with a tooltip: how strongly the retrieved sources support the
     answer.
   - If `provider` is `extractive`, label the answer "Verbatim source passages (no AI summary)".
   - Show `warnings[]` as a "Notes" list under the answer, and `disclaimer` once, always visible.
   - Show `jurisdiction_note` as small print; show `cached` and `latency_ms` only in a details footer.
3. **Citation cards** (next to the answer on desktop, below on mobile): title, locator, section heading or
   court and date, the verbatim `quote` in quotation marks, a status badge (make **Repealed** prominent), authority and
   jurisdiction, "Retrieved {date}", and a link to `source_url`. "Read full passage" opens a side drawer that loads
   `/api/sources/{chunkId}` and shows the full `text` with its locator and page range.
4. **Abstained answers**: no answer styling. Show `answer_markdown` as the explanation (it says what was searched and
   what source would be needed). If citations are present (high-stakes cases), title them "Closest provisions found
   (not confirmed to answer your question)".
5. **Service status**: call `/api/health` on load and every 60 s. `degraded` shows a banner saying answers are limited
   to verbatim source passages; `down` or unreachable disables the ask box with "The research service is offline".
6. **Errors**: plain-language messages mapped from `error.code` (e.g. 422 → the field message; 503 → "Still starting
   or offline, try again shortly"; timeout → "This took too long; try again"). Always show the `request_id` in small
   text so the owner can find it in the logs.
7. **About page**: what the tool covers (central Acts on India Code and Supreme Court judgments 2016–2025, English
   texts; Hindi questions work but answers are in English; state laws and rules are not covered), that it is
   informational only, and how citations work.

## Language and design
- Questions may be in Hindi or English: load a Devanagari-capable font (e.g. Noto Sans Devanagari) alongside the UI
  font, and don't break Devanagari text.
- Calm, legible, professional design; mobile-first; light and dark themes; WCAG 2.2 AA (contrast, keyboard access,
  focus rings, labels, reduced motion).
- No stock legal imagery (gavels, scales). No wording that suggests advice ("you should", "you will win").

## Privacy
- Do not log question or answer text on the server (no `console.log` of request bodies); log only status, latency and
  `request_id`.
- No analytics or third-party scripts that receive question text. Keep conversation history only in the browser tab
  (memory or `sessionStorage`), with a "Clear" button.

## Development without the backend
Build against the OpenAPI types (generate them with `openapi-typescript` from `openapi.json`). For offline UI work
you may add a development-only mock mode behind an explicit `PRAETOR_MOCK=1` flag that serves the real example
responses in `docs/api/examples/` (or clearly labelled placeholder text if they are not available yet). The mock mode
must be impossible to enable in production and must label its output "Sample data".

## Deliverables
- The Next.js app with the three route handlers, typed API client, the pages and components above.
- Unit tests for: `[S#]` marker parsing and linking, error-code mapping, the proxy (key sent, key never exposed,
  timeouts, 401/422/503 passthrough), and abstained / extractive / repealed rendering.
- A README: local setup (`PRAETOR_API_URL=http://127.0.0.1:8000` against a local backend), the Vercel environment
  variables, and deployment steps.
- Keep the repository lean: no committed build output, large fixtures or binaries.
