# PRAETOR AI

Informational answers about Indian law, grounded in cited sources: 12 central Acts from India Code and 1,000 Supreme
Court judgments (2016–2025), searched with hybrid retrieval and answered by a local model. Every citation is rendered
from stored source metadata, unknown or unsupported authorities are removed, and the system abstains when the evidence
is thin. **It is not a lawyer and does not give legal advice.**

Everything runs on one Windows laptop with an NVIDIA GPU; nothing is sent to a cloud service. A frontend (built
separately) can be deployed on Vercel and call this backend through a tunnel.

## What you need
- Windows 11 with an NVIDIA GPU (developed on an RTX 5070 Laptop, 8 GB) and a current driver
- [uv](https://docs.astral.sh/uv/) (manages Python 3.12 and the dependencies) and Git
- [Ollama](https://ollama.com) for the answer model
- Disk: about 17 GB for models (answer model 9.6 GB, embedder 4.3 GB, reranker 2.2 GB) and about 1 GB for data;
  the judgments download needs about 3.3 GB of temporary space

## From zero to a running demo
Run in CMD from the repository folder. `.\praetor` is `praetor.cmd` in the repo root: it calls the project's command
line through uv, and also works when Windows Smart App Control blocks the generated `praetor.exe`
(`uv run praetor ...` does the same when that launcher is allowed).

```bat
uv sync
copy .env.example .env
ollama pull gemma4:latest
.\praetor gpu-check
```
`gpu-check` must report CUDA in use. The first run downloads the embedding and reranking models from Hugging Face.

Build the corpus and index (downloads from India Code and the public Supreme Court judgments dataset; the index step
parses about 1,000 PDFs and takes a while):
```bat
.\praetor ingest --source indiacode --phase 2
.\praetor ingest --source sc-judgments --years 2016-2025 --limit 1000 --via tar
.\praetor index
.\praetor profile
```
`profile` must end with `PASS`.

Ask from the terminal, then run the API and the scripted demo:
```bat
.\praetor ask "What is the time limit for presenting a document for registration?" --explain
.\praetor serve
```
In a second CMD window, with the server running:
```bat
uv run python scripts/demo.py
```
The demo asks seven questions (statute lookup, procedure, case law, the 2024 criminal-code transition, Hindi, an
out-of-corpus question that must be refused, and a high-stakes question) and checks that every `[S#]` in an answer has
a source card. Interactive API docs: http://127.0.0.1:8000/docs.

**Your own documents** (works even when the library search cannot load): upload a PDF (typed or scanned: scanned pages are read with Windows OCR) and ask about
it, summarise it, list its key clauses, obligations, risks and inconsistencies, turn it into a checklist, prepare
questions for a lawyer, or compare two agreements. With the server running:
```bat
uv run python scripts/demo_documents.py AGREEMENT.pdf [OTHER_AGREEMENT.pdf] --question "What if possession is delayed?"
```
Uploads stay in server memory for 60 minutes and are never indexed, cached or written to disk (DECISIONS D50).

## Connecting a frontend
- Contract: [`docs/api/openapi.json`](docs/api/openapi.json) (regenerate with `.\praetor openapi`), field-by-field
  guidance in [`docs/topics/architecture/api.md`](docs/topics/architecture/api.md), real responses in
  `docs/api/examples/` (`uv run python scripts/demo.py --save-examples docs/api/examples`).
- Local development: allow the frontend's origin in `CORS_ORIGINS` (default `http://localhost:3000` and `:5173`).
- Deployed on Vercel: set `API_KEY` in `.env`, run a tunnel to `http://127.0.0.1:8000`, and call the API **from
  server-side code** that sends `X-API-Key` — never from browser code. Details and limits:
  [`docs/topics/ops/deployment.md`](docs/topics/ops/deployment.md).
- Expect about 13 s per answer (one question at a time on the GPU); repeated questions come from the cache.

## Tests and evaluation
```bat
uv run pytest -m "not integration"
uv run pytest -m integration
.\praetor eval --split all
```
Integration tests and `eval` need the GPU, Ollama and the built index. Evaluation numbers come from 59 draft gold
questions that no person has verified yet: treat them as regression checks, not accuracy claims
(`evaluation/verification_sheet.csv` is the review sheet).

## Configuration
All settings come from `.env` (template: `.env.example`): model names and devices, retrieval sizes, the evidence
threshold (`MIN_EVIDENCE_SCORE`), the Ollama model and decoding, the answer cache, and the API (`API_KEY`,
`API_HOST`, `API_PORT`, `CORS_ORIGINS`). Logs record query hashes, not questions.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `An Application Control policy has blocked this file` | Windows Smart App Control is blocking a downloaded binary (the `praetor.exe` launcher, or a DLL of torch or scikit-learn). Use `praetor.cmd` for the launcher; a blocked library needs the Windows setting changed by you — check Microsoft's documentation first |
| `/v1/healthz` says `degraded` | Ollama is not running or the model is not pulled; answers fall back to verbatim passages |
| `/v1/healthz` says `down` | the index is missing or stale: run `.\praetor index` |
| `refusing to listen ... without API_KEY` | set `API_KEY` in `.env` before binding to anything but localhost |
| Out of GPU memory | run one GPU job at a time; stop other Ollama models (`ollama ps`) |

## Sources and licences
- Acts: India Code (Legislative Department), reproduced under Copyright Act 1957 s. 52(1)(q); the migrated site's own
  terms of use could not be located (see `docs/DECISIONS.md`, V15).
- Judgments: the Indian Supreme Court Judgments dataset on AWS Open Data (`s3://indian-supreme-court-judgments`,
  CC-BY-4.0), read anonymously.
- Models: BAAI/bge-m3 and BAAI/bge-reranker-v2-m3 (Hugging Face), `gemma4:latest` through Ollama (Apache-2.0).

## Project documentation
Start with [`CLAUDE.md`](CLAUDE.md) (rules and commands), [`docs/STATUS.md`](docs/STATUS.md) (what works now) and
[`docs/INDEX.md`](docs/INDEX.md) (the design notes); decisions and verifications with dates are in
[`docs/DECISIONS.md`](docs/DECISIONS.md).
