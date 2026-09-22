# PRAETOR AI — status

_Last updated: 2026-09-23 · Phase: 0 not started. Inspection done; waiting for plan approval._

## What exists
- The knowledge-base kit only: `CLAUDE.md`, `KICKOFF_PROMPT.md`, `docs/` (INDEX, DECISIONS, 12 topic notes, 2 source reports), extracted from `praetor-ai-kit.zip` (the zip is still in the folder).
- No application code, no `pyproject.toml`, no tests, no `data/`, no `evaluation/`, no `infra/`.
- **Git:** the project folder isn't its own repository. It sits inside a repo rooted at the **home directory `C:\Users\DELL`** (branch `master`, 0 commits, `origin` = `github.com/Harshiee09/GenentAi.git`). Committing from here would commit into that home repo. A decision is needed (see Risks).

## Environment (checked 2026-09-23, read-only)
| Item | Found | Notes |
|---|---|---|
| OS | Windows 11 Home 10.0.26200, native (no usable WSL distro; only Docker Desktop's, stopped) | commands will be PowerShell |
| Project path | `C:\Users\DELL\OneDrive\Desktop\Praetor AI` | **OneDrive-synced**, path has a space |
| Python | 3.14.0 only (python.org install), `uv` 0.11.6 available | no 3.11/3.12 installed |
| Global torch | `2.13.0+cu130`, arch list includes `sm_120` | installed in the global 3.14 site-packages, not a project env |
| GPU | **RTX 5070 Laptop GPU, 8 GB** (7.93 GiB usable), compute capability 12.0 (Blackwell) | KB assumes 12 GB. See Discrepancies |
| Driver | 616.92, CUDA UMD 13.4 | supports cu128 / cu130 wheels |
| GPU proof | `torch.cuda.is_available()` = True; fp16 4096² matmul **26.7 TFLOPS** after warm-up | first cold call took 14 s (one-time init) |
| Disk | C: 288.5 GB free | enough |
| SQLite | 3.50.4 with FTS5 (in Python 3.14) | re-check inside the project venv |
| Ollama | 0.34.2, server running; one model: `gemma4:latest` (9.6 GB) | that model is larger than VRAM and would partially offload to CPU |
| Tesseract | **not installed** | needed for OCR pages; the installer needs admin |
| AWS CLI | 2.34.4; profiles: `default` only, **no `praetor` profile** | needed on Day 3 only |
| Network | `s3://indian-supreme-court-judgments` lists unsigned (`data/{pdf,tar}/`, `metadata/{json,parquet,tar}/`, parquet at `metadata/parquet/year=YYYY/metadata.parquet`, ~1 MB/year); `https://www.indiacode.nic.in/` → HTTP 200 | India Code per-Act download behaviour still unverified |
| gh CLI | not installed | not needed |

## What works when run
Nothing of PRAETOR exists yet. Verified pieces of the environment:
- GPU compute: `python -c "import torch; print(torch.cuda.is_available())"` → `True` (global interpreter).
- Judgments bucket: `aws s3 ls --no-sign-request --region ap-south-1 s3://indian-supreme-court-judgments/metadata/parquet/`.

## Gaps against the minimum viable architecture
Everything is still to build: config/env contract, CLI, ingestion and manifest, parsing and OCR, language ID, legal-aware chunking, schema validation, SQLite + FTS5, embeddings, FAISS, retrieval, reranking, evidence gate, context builder, LLM router (ollama / bedrock / extractive), cost meter, citation validator, registries (`statutes.yaml`, `aliases.yaml`, `sources.yaml`, `languages.yaml`), gold set and eval, API, AWS infra.

## Discrepancies with the KB
1. **VRAM is 8 GB, not 12 GB.** `CLAUDE.md` and the architecture note's VRAM budget assume 12 GB. With bge-m3 (~1.1 GB) and the reranker (~1.1 GB) resident, about 5 GB remains for the LLM plus KV cache. That points to ~4B-class models fully on GPU, or 7–8B at Q4 with a short context, or unloading the encoders during generation. Proposed fix: a DECISIONS entry, and correcting both notes.
2. The existing Ollama model (`gemma4:latest`, 9.6 GB) can't run fully on this GPU.

## Risks
- **OneDrive sync.** `.venv` (several GB), `data/raw`, the SQLite database and the FAISS index would all sync. OneDrive locking a live SQLite file risks corruption and failed writes. Recommendation: move the project outside OneDrive.
- **Home-directory git repo.** `C:\Users\DELL` is a git repo with a GitHub remote, and `.aws/`, `.claude.json` and other private files sit untracked inside it. A stray `git add .` + push from home would publish credentials. Not touched; flagged for the user.
- **Tesseract missing**, and its Windows installer needs admin. The Phase 1 corpus (English India Code PDFs, SC judgments) should mostly have text layers, so this isn't blocking day one. Hindi/Indic OCR needs it later.
- **India Code** may serve PDFs through handle pages or with bot protection. If a download is blocked, stop and ask (per the kickoff rules).
- **Laptop GPU** (40 W cap, battery 9% on AC at inspection time): long embedding runs should stay on AC power.
- Python 3.14 is recent; some wheels (faiss-cpu, pypdfium2, regex) may lag. A uv-managed 3.12 venv avoids that without admin rights.

## Side effects of the inspection
- Extracted `praetor-ai-kit.zip` into the project folder (required to install the kit).
- `ollama list` started the Ollama app while its server wasn't running; the app then applied a queued self-update, **0.34.1 → 0.34.2**. Nothing else was changed.

## Deferred
_(none yet)_

## Next step
Waiting for approval of the Phase 0/1 plan and decisions on project location, git, downloads and Tesseract.
