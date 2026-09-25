# Prompt for the frontend builder (GPT-6 Astra)

Paste everything below the line. Attach `docs/api/openapi.json` from this repository (the contract is authoritative
if anything here disagrees) and every file in `docs/api/examples/`: the `document_*.json` files are real responses
from the running backend (upload, passages, and one analysis per task) on an official RERA model agreement.

---

Build the web frontend for **PRAETOR AI**, an informational legal-research assistant for Indian law. It has two
parts, and both must be built:
1. **Ask** — answers questions from 12 central Acts and 1,000 Supreme Court judgments.
2. **Your document** — the user uploads a PDF (an agreement, notice, order or policy) and PRAETOR answers questions
   about it, summarises it, highlights its key clauses, obligations, risks and inconsistencies, turns it into a
   checklist, prepares questions for a lawyer, or compares it with a second document.

Every answer cites its sources. PRAETOR is **not a lawyer and gives no legal advice**; the UI must never suggest
otherwise, and it never says whether a document is valid, fair or enforceable.

## Architecture (fixed)
- The backend is a FastAPI server that runs on the owner's laptop (it needs a GPU and several GB of models, so it
  cannot run on Vercel). For a public deployment it is reachable through a tunnel URL.
- Build a **Next.js (App Router) + TypeScript** app deployed on **Vercel**.
- The browser **never calls the backend directly**. Add server-side route handlers that proxy to it:
  - `POST /api/ask` → `POST {PRAETOR_API_URL}/v1/ask`
  - `GET /api/sources/[chunkId]` → `GET {PRAETOR_API_URL}/v1/sources/{chunk_id}`
  - `GET /api/health` → `GET {PRAETOR_API_URL}/v1/healthz`
  - `POST /api/documents` → `POST {PRAETOR_API_URL}/v1/documents`: read `await request.formData()`, take the `file`
    field, reject anything that is not `application/pdf` or is over 4 MB (return the same error shape, 415 / 413),
    then send a new `FormData` with that one `file` upstream
  - `GET /api/documents/[id]` and `DELETE /api/documents/[id]` → `/v1/documents/{document_id}`
  - `POST /api/documents/analyze` → `POST {PRAETOR_API_URL}/v1/documents/analyze`
- Server-only environment variables: `PRAETOR_API_URL` and `PRAETOR_API_KEY`. The proxy sends `X-API-Key:
  PRAETOR_API_KEY` and forwards or creates `X-Request-ID`. **The key must never reach browser code or any
  `NEXT_PUBLIC_*` variable.**
- Answers and document analyses take about 10–25 s, and the backend does one at a time, so requests may queue. Set
  `maxDuration` to 300 s (Vercel Hobby maximum) with an upstream fetch timeout of about 280 s on the ask and analyze
  routes, and 60 s on the upload route (parsing a 24-page PDF takes a few seconds).
- Validate on the server too: `question` is 1–2000 characters, trimmed.
- Uploads: Vercel Functions accept request bodies up to 4.5 MB, so accept PDFs up to **4 MB** (check in the browser
  and again in the route), `application/pdf` only.

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

**Documents** (the user's own PDF; see `docs/api/examples/document_*.json` for real responses):
- `POST /v1/documents` (multipart field `file`) → 201 `DocumentInfo`: `document_id`, `filename`, `pages`,
  `unreadable_pages[]`, `passage_count`, `words`, `uploaded_at`, `expires_at` (60 minutes; the server keeps the file in
  memory only), `warnings[]`. Errors: 413 `too_large`, 415 `unsupported_media_type`, 422 `unreadable_document`
  (scanned or password-protected: show the message).
- `GET /v1/documents/{document_id}` → the same plus `passages[]` (`n`, `locator`, `page_start`, `page_end`, `text`).
  404 means the document expired: ask the user to upload it again.
- `DELETE /v1/documents/{document_id}` → 204.
- `POST /v1/documents/analyze` with `{"document_ids": [id] | [idA, idB], "task": "ask" | "summary" | "risks" |
  "checklist" | "lawyer_questions" | "compare", "question": string | null}`: `ask` needs `question`; `compare` needs
  exactly two ids (the others take one); `question` is an optional focus for the rest. Returns the `AskResponse`
  fields plus `task`, `documents[]` (`filename`, `pages_read`, `complete`) and `law_checked`. Markers: `[D#]` cites
  the user's document (card `kind: "document"`, `locator` like `clause 7.5 · p. 13`, `page_start`, `document_id`;
  the passage text is `passages[n]` from `GET /v1/documents/{document_id}` where `n` is the number after the colon
  in `chunk_id` — **not** the number in `D#`: in the real examples card `D14` has `chunk_id` `…:25`); `[S#]` cites
  Indian law (card `kind: "law"`, as in `/v1/ask`). Document cards have `authority: "Uploaded by you"`,
  `source_url: ""`, `status` and `jurisdiction` `"n/a"`, and `retrieved_at` = the upload date.

`GET /v1/healthz` returns `{"status": "ok" | "degraded" | "down", "checks": {...}}`; `down` comes with HTTP 503 and refers to library questions only; document features are available when `checks.documents` is `"ok"`.

Errors are always `{"error": {"code", "message", "request_id"}}`: 401 `unauthorized`, 404 `not_found`,
413 `too_large`, 415 `unsupported_media_type`, 422 `invalid_request` or `unreadable_document`, 503 `unavailable`, 500 `internal_error`.

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
5. **Service status**: call `/api/health` on load and every 60 s. On the Ask page, `degraded` shows a banner saying
   answers are limited to verbatim source passages, and `down` or unreachable disables the ask box with "The research
   service is offline". The Your document page ignores `status` and looks only at `checks.documents`: `"ok"` →
   enabled; anything else → a banner "Document analysis is limited to quoting the passages (no AI summary)"; health
   unreachable → disabled. (Right now the backend reports `status: "down"` with `checks.documents: "ok"`: the Ask
   page is offline but the document page must work.)
6. **Errors**: plain-language messages mapped from `error.code` (e.g. 422 → the field message; 503 → "Still starting
   or offline, try again shortly"; timeout → "This took too long; try again"). Always show the `request_id` in small
   text so the owner can find it in the logs.
7. **About page**: what the tool covers (central Acts on India Code and Supreme Court judgments 2016–2025, English
   texts; Hindi questions work but answers are in English; state laws and rules are not covered), that it is
   informational only, and how citations work. For documents: PDFs with selectable text only (scanned PDFs cannot be
   read yet), up to 4 MB; the file is held in the PRAETOR server's memory for 60 minutes and never stored; very long
   documents are read in part (the answer says which pages).

8. **Your document page**: see the next section; it is a full page, not an add-on.

## Your document page (build all of it)
Navigation: a top-level tab bar or header links **Ask** | **Your document** | **About**, on every page. Route
`/document`. Keep uploaded document ids in `sessionStorage` only, so a reload keeps the document until it expires.

**Layout.** Desktop: left column = the document panel and the task buttons; right column = the result, with its
citation cards beside it (below it on mobile). Mobile: one column in the order document → tasks → result → cards.

**1. Document panel (states).**
- *Empty:* a drop zone that is also a real `<input type="file" accept="application/pdf">` behind a labelled button
  (keyboard and screen-reader usable). Text: "Upload a PDF with selectable text (up to 4 MB). It is kept for 60
  minutes and never stored." Reject non-PDFs and files over 4 MB in the browser before uploading.
- *Uploading:* progress indicator with the filename; the task buttons stay disabled.
- *Uploaded:* filename, `pages` pages, `passage_count` passages, a live countdown to `expires_at` ("Expires in 42
  min"), any `warnings[]` (e.g. unreadable scanned pages) and `unreadable_pages`, a **View text** button (opens the
  passage drawer listing every passage with its `locator`) and a **Forget this document** button (DELETE, then back
  to empty; confirm first).
- *Expired or 404 from any call:* "This document has expired (documents are kept for 60 minutes). Upload it again."
  Clear it from `sessionStorage` and return to empty.
- *Upload errors:* 413 → the server's `message` (the file is too large, or has more than 80 pages); 415 → "Only PDF files can be uploaded"; 422
  `unreadable_document` → show the server's `message` (it explains scanned or password-protected files).

**2. Task buttons** (disabled until a document is uploaded, and while any request is running: the backend does one
at a time). Each sends `POST /api/documents/analyze` with the body shown:

| Button | Body |
|---|---|
| **Ask about this document** (opens a question box, 1–2000 characters; example chips: "When must I pay?", "Can I cancel, and what do I lose?", "What happens if possession is delayed?") | `{"document_ids": [id], "task": "ask", "question": q}` |
| **Summarise in plain language** | `{"document_ids": [id], "task": "summary"}` |
| **Key clauses, obligations and risks** | `{"document_ids": [id], "task": "risks"}` |
| **Make a checklist** | `{"document_ids": [id], "task": "checklist"}` |
| **Questions for a lawyer** | `{"document_ids": [id], "task": "lawyer_questions"}` |
| **Compare with another document** (reveals a second upload panel with the same states, labelled "Document B", and an optional "Focus on" field, e.g. "refunds and cancellation") | `{"document_ids": [idA, idB], "task": "compare", "question": focus or null}` |

The first document is always **Document A**. An optional "Anything to focus on?" field may also send `question`
with summary, risks, checklist and lawyer_questions.

**3. Waiting.** Show an elapsed-time counter and "Reading your document and checking every citation…" (typically
10–25 s). Allow cancelling the wait in the UI (abort the fetch); the result is simply discarded.

**4. Result view** (reuse the Ask page's answer components):
- A title from the task ("Plain-language summary", "Key clauses, obligations and risks", "Checklist", "Questions for
  a lawyer", "Comparison: {filename A} vs {filename B}", or the question for `ask`).
- `warnings[]` as a "Notes" box **above** the answer. They include "is longer than one analysis can read … pages …"
  and "Law cross-check skipped …"; show them in plain words, don't hide them.
- A "Pages read" line from `documents[]`: "{filename}: pages {pages_read}" plus "(part of the document)" when
  `complete` is false.
- `answer_markdown` rendered with the same safe Markdown renderer (no raw HTML). Its bold headings come from the task
  (e.g. **Risks:**, **Inconsistencies and gaps:**, **Only in Document A:**); render them as section headings.
- Checklist lines `- [ ] …` render as real checkboxes the user can tick; ticks live only in the tab (not sent
  anywhere). Add **Copy as text** and **Print** (browser print, a print stylesheet that keeps citations and the
  disclaimer) buttons for every result.
- Confidence badge, `provider === "extractive"` label ("The passages themselves (no AI summary)"), `disclaimer`
  always visible, `jurisdiction_note` in small print, `request_id` in the footer — as on the Ask page.
- If `law_checked` is true and law cards are present, add a line "Compared with Indian law where a law passage
  covered the same point".

**5. Citation chips and cards.**
- `[D#]` chips link to **"Your document" cards**: filename, locator (e.g. `clause 7.5 · p. 13`), the verbatim
  `quote`, "Page {page_start}" (or "Pages {page_start}–{page_end}"), and **Show full passage**, which opens the
  passage drawer at that passage (fetch `GET /api/documents/{document_id}` once, cache the passages in memory, find
  the passage whose `n` equals the number after the colon in `chunk_id`, and highlight the quoted text in it, matching while ignoring whitespace: the quote has the passage's line
  breaks collapsed). No
  status badge and no external link on document cards.
- In a comparison, colour-code chips and cards by document (A and B, with a text label as well as colour, for
  accessibility), using the card's `document_id`.
- `[S#]` chips link to law cards exactly as on the Ask page (status badge, "Read full passage" via
  `/api/sources/{chunkId}`, link to `source_url`).
- A marker without a card renders as plain text.

**6. Wording.** Never write "you should sign", "this clause is illegal/void/unfair", "you will win". Use "the
document says", "may be worth checking with a lawyer". Show once on the page: "PRAETOR explains what your document
says. It does not decide whether the document is valid or enforceable, and it is not legal advice. For your
situation, consult an advocate or your District Legal Services Authority (free legal aid)."

## Language and design
- Questions may be in Hindi or English: load a Devanagari-capable font (e.g. Noto Sans Devanagari) alongside the UI
  font, and don't break Devanagari text.
- Calm, legible, professional design; mobile-first; light and dark themes; WCAG 2.2 AA (contrast, keyboard access,
  focus rings, labels, reduced motion).
- No stock legal imagery (gavels, scales). No wording that suggests advice ("you should", "you will win").

## Privacy
- Do not log question or answer text on the server (no `console.log` of request bodies); log only status, latency and
  `request_id`.
- Uploaded PDFs go only to the PRAETOR API through the proxy: never to any other service, never stored by the
  frontend (no Vercel Blob, no logging of file contents or names). Keep only `document_id`, filename and
  `expires_at` in `sessionStorage`; results live in the tab's memory. No PDF previews through third-party viewers.
- No analytics or third-party scripts that receive question text. Keep conversation history only in the browser tab
  (memory or `sessionStorage`), with a "Clear" button.

## Development without the backend
Build against the OpenAPI types (generate them with `openapi-typescript` from `openapi.json`). For offline UI work
you may add a development-only mock mode behind an explicit `PRAETOR_MOCK=1` flag that serves the real example
responses in `docs/api/examples/` (or clearly labelled placeholder text if they are not available yet): for
documents, `document_upload.json` answers the upload, `document_passages.json` the passage list, and
`document_{task}.json` each analysis. The mock mode must be impossible to enable in production and must label its
output "Sample data".

## Deliverables
- The Next.js app with the route handlers, typed API client, the pages and components above.
- Unit tests for: `[S#]` and `[D#]` marker parsing and linking (including a `D#` whose passage `n` differs), the
  4 MB and PDF-only checks in the browser and the upload route, the multipart proxy, error-code mapping (413, 415,
  422 `unreadable_document`, 404 expired), the proxy (key sent, key never exposed, timeouts, 401/422/503
  passthrough), checklist checkbox rendering, A/B colour coding in comparisons, and abstained / extractive / repealed
  rendering. Render tests for each `document_*.json` example.
- Acceptance checks (run against the real backend with `PRAETOR_API_URL=http://127.0.0.1:8000`): upload a text PDF
  → the panel shows pages and expiry; each of the six task buttons returns a result whose every chip opens a card;
  "Show full passage" highlights the quote; "Forget this document" then any task → the expired message; a scanned
  PDF → the server's unreadable message; a 5 MB file → rejected in the browser without a request.
- A README: local setup (`PRAETOR_API_URL=http://127.0.0.1:8000` against a local backend), the Vercel environment
  variables, and deployment steps.
- Keep the repository lean: no committed build output, large fixtures or binaries.
