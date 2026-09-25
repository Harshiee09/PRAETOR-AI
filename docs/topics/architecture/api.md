---
id: 20260925-api
title: API contract
tags: [architecture, safety]
created: 2026-09-25
updated: 2026-09-25
related: [20260922-minimum-viable-architecture, 20260922-grounding-and-citations, 20260925-deployment, 20260922-llm-layer]
summary: The local HTTP API the frontend builds against — endpoints, fields, auth, errors, cache, latency and how to render answers.
---

# API contract

> Summary: The local HTTP API the frontend builds against — endpoints, fields, auth, errors, cache, latency and how to render answers.

## Context
The frontend is built separately (DECISIONS D47). It talks to PRAETOR only through this API, which runs on the laptop with the GPU (`praetor serve`). The machine-readable contract is `docs/api/openapi.json` (regenerate with `praetor openapi`); real responses are in `docs/api/examples/`. Interactive docs are served at `http://127.0.0.1:8000/docs` while the server runs.

## Details

### Endpoints
| Method and path | Auth | Purpose |
|---|---|---|
| `POST /v1/ask` | key* | answer a question with citations |
| `GET /v1/sources/{chunk_id}` | key* | the full stored passage behind a citation card |
| `GET /v1/healthz` | none | `ok` / `degraded` (no answer model: verbatim passages only) / `down` (HTTP 503: index or engine unusable) |
| `POST /v1/documents` | key* | upload a PDF (multipart field `file`) → `document_id`, pages, passages, expiry |
| `GET /v1/documents/{document_id}` | key* | the uploaded document's passages (`n`, `locator`, pages, `text`): the text behind `[D#]` cards |
| `DELETE /v1/documents/{document_id}` | key* | forget the document now (204) |
| `POST /v1/documents/analyze` | key* | `task`: `ask` (needs `question`), `summary`, `risks`, `checklist`, `lawyer_questions`, or `compare` (two `document_ids`) |
| `GET /v1/stats` | key* | corpus and index counts, model and digest, prompt version, cache size, uptime, request counts, answer latency p50/p95 |

\* With `API_KEY` set, send it as `X-API-Key` on every call except `/v1/healthz`. Without `API_KEY`, the server answers only direct localhost calls; tunnel traffic (forwarding headers) and other hosts get 401. `praetor serve` refuses to listen on anything but localhost without a key.

### `POST /v1/ask`
Request: `{"question": "...", "mode": "full", "explain": false, "use_cache": true}` — `question` 1–2000 characters, any language (Hindi works; answers are in English). Keep `mode` at `full`.

Response fields and how to render them:
| Field | Render as |
|---|---|
| `answer_markdown` | the answer, as Markdown. `[S1]`, `[S2]` … refer to `citations[].id`; make them links to the cards. High-stakes answers begin with a safety block (a `>` quote) — keep it at the top. The last line is the system's "Jurisdiction and date" line |
| `citations[]` | source cards: `title`, `locator`, `status` (show "repealed" prominently), `authority`, `jurisdiction`, `retrieved_at`, `quote` (verbatim, ≤ 300 characters), `source_url`; judgments add `court`, `decision_date`, `citation`. A card's `chunk_id` opens the full passage via `/v1/sources/{chunk_id}`. Cards come from stored metadata, never from model text |
| `warnings[]` | notes under the answer: repeal and transition notes, state-law coverage, removed sentences |
| `confidence` | `high` / `medium` / `low` badge |
| `abstained` | `true`: no answer was generated (thin evidence, or a refused request). Show `answer_markdown` as the explanation; high-stakes abstentions may still carry unconfirmed source cards |
| `disclaimer` | once per answer |
| `jurisdiction_note` | small print |
| `provider` | `ollama` (model answer), `extractive` (no model: verbatim passages), or `null` (abstained / refused) |
| `classification` | `domain`, `intent`, `high_stakes` — optional UI hints |
| `trace_id` | equals the `X-Request-ID` response header; show it in error reports |
| `cached`, `latency_ms` | diagnostics |
| `explain` | only with `explain: true`: per-stage ranks and validator details (for a debug panel) |

Latency: about 13 s median and 20 s p95 on the dev laptop (eval `20260924T174231Z`); questions are answered **one at a time**, so concurrent requests queue. Show progress, and set client timeouts to at least 120 s. A cache hit returns in milliseconds.

### Uploaded documents (DECISIONS D50)
- **Upload:** a PDF with a text layer, at most `DOC_MAX_MB` (10) and `DOC_MAX_PAGES` (80). Errors: 413 `too_large`, 415 `unsupported_media_type` (not a PDF), 422 `unreadable_document` (scanned without OCR, encrypted, damaged). Pages without text are listed in `unreadable_pages` and left out. Passages follow the document's own numbering (`clause 7 · p. 2`, `section 18 · p. 11`, `paras 12-14 · pp. 3-4`) or its pages.
- **Held in memory only:** never indexed into the corpus, cached, logged or written to disk; expires after `DOC_TTL_MINUTES` (60), at most `DOC_MAX_OPEN` (20) at a time (oldest dropped first), lost on restart. An expired id gives 404.
- **Analyze** returns the `/v1/ask` answer shape plus `task`, `documents[]` (`pages_read`, `complete`) and `law_checked`. Markers: `[D#]` = a passage of the user's document (card `kind: "document"`, `document_id`, `page_start`/`page_end`; full text via `GET /v1/documents/{document_id}`, passage `n` = the number after the colon in `chunk_id`); `[S#]` = Indian law (card `kind: "law"`, as in `/v1/ask`). Same validator as `/v1/ask`: unknown ids stripped, sentences with authorities or quotations the cited passages lack removed, ungrounded output retried once then replaced by the passages verbatim.
- **Law cross-check:** when the retrieval engine is loaded, up to `DOC_LAW_PASSAGES` (3) corpus passages for the document's topic (or the question) are added if they pass the evidence gate, so a clause can be compared with the Act. Without the engine the analysis uses the document alone and says so in `warnings`. Not used for `compare`.
- **Long documents:** one analysis reads up to `DOC_CONTEXT_TOKENS` (≈ 14k estimated, ~10k real) in a 16k window (`DOC_NUM_CTX`): the whole document if it fits, otherwise the opening passage plus the passages that best match the question or task (BM25), in document order. `documents[].complete` is false and a warning names the pages read.
- Answers take 12–21 s on the RTX 5070 (V46). `/v1/healthz` `checks.documents` is `ok` when the answer model is available, whatever the library status.

### Errors
Every error is `{"error": {"code", "message", "request_id"}}` with the HTTP status: 401 `unauthorized`, 404 `not_found`, 413 `too_large`, 415 `unsupported_media_type`, 422 `invalid_request` (the message names the field) or `unreadable_document`, 503 `unavailable` (engine still loading or failed), 500 `internal_error`. `X-Request-ID` is echoed on every response; send your own (letters, digits, `-`, `_`, ≤ 64) to correlate logs.

### Cache
Non-`explain` answers are cached in SQLite for `CACHE_TTL_HOURS` (72). The key covers the normalised question and every version that can change an answer (prompt, model digest, decoding, index, registries, gate), so updates miss automatically. Send `"use_cache": false` to force a fresh answer. The question text itself is never stored.

### CORS
`CORS_ORIGINS` lists browser origins allowed to call the API directly (default: `http://localhost:3000`, `http://localhost:5173`). A deployed frontend should call the API from server-side code instead (see the deployment note), which needs no CORS.

### Privacy and logs
Logs record method, path, status, latency and request id; the question is logged only as a hash (`LOG_QUERIES=hash`). Nothing is sent to any cloud service.

## Related
- [Grounding and citations](../legal/grounding-and-citations.md) — what the answer and cards guarantee.
- [Deployment](../ops/deployment.md) — running the server and connecting a Vercel frontend.
- [Minimum viable architecture](minimum-viable-architecture.md) — where the API sits in the request flow.
