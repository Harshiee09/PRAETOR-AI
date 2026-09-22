# PRAETOR AI — status

_Last updated: 2026-09-23 · Phase 0 done · Phase 1 in progress_

## What works (with the command that proves it)
| Capability | Command | Result |
|---|---|---|
| Unit tests | `uv run pytest -m "not integration"` | green |
| GPU + embeddings | `uv run praetor gpu-check` | CUDA on RTX 5070 Laptop (sm_120), fp16 matmul ~27 TFLOPS, bge-m3 on CUDA, dim 1024, L2-normalised, peak VRAM 1.09 GiB, en/hi/ta cross-lingual sanity check passes |
| Local LLM candidates | `ollama list` | `qwen3.5:4b` (3.4 GB), `gemma4:e2b-it-qat` (4.3 GB), plus the pre-existing `gemma4:latest` (9.6 GB, too big for full GPU) |

## Environment
- Project: `C:\dev\praetor-ai` (moved out of OneDrive, own git repo on `main`; DECISIONS D6). The original copy at `C:\Users\DELL\OneDrive\Desktop\Praetor AI` is still there and can be deleted.
- Windows 11, native. Python 3.12.13 (uv-managed) in `.venv`, created by `uv sync`. torch 2.14.0+cu130, sentence-transformers 6.1, transformers 5.17, faiss-cpu 1.15.1, SQLite 3.50.4 with FTS5.
- GPU: RTX 5070 Laptop, **8 GB** (DECISIONS D8), driver 616.92, CUDA 13.4 UMD.
- Ollama 0.34.2. AWS CLI 2.34.4, only a `default` profile (a `praetor` profile is needed on Day 3).
- Hugging Face cache: `C:\Users\DELL\.cache\huggingface` (no symlinks on Windows without Developer Mode, so files are copied; harmless).

## Gaps against the minimum viable architecture
Phase 1 (building now): ingestion, parsing, chunking, validation, SQLite + FTS5 store, FAISS index, `praetor ask` with the first citation validator, `praetor profile`, first gold questions.
Later phases: classifier, keyword search, fusion, reranker, evidence gate, full validator, statute registry beyond the Phase 1 Acts, eval harness, Bedrock + cost meter, API, AWS infra.

## Risks
- 8 GB VRAM limits local answer models to the 2–4B class (quality risk for Hindi answers; Bedrock comparison on Day 3 matters more).
- India Code moved domains during 2026 (DECISIONS V11). Its site terms aren't located yet (V15).
- Home-directory git repo at `C:\Users\DELL` (origin `Harshiee09/GenentAi`) still exists with private files untracked inside it; a stray `git add .` + push there would publish credentials. Not touched.
- Laptop GPU: keep it on AC power for bulk embedding.

## Deferred
- **Tesseract OCR** (DECISIONS D9): needs an admin install. Until then, pages that need OCR are rejected and logged. Install the UB Mannheim build plus `eng`, `hin` (and the third demo language), then fill `tesseract` in `app/multilingual/languages.yaml` from `tesseract --list-langs`.
- **Download contact address:** `HTTP_USER_AGENT` identifies the project but carries no contact; set one in `.env` if you want government sites to be able to reach you.
- **India Code terms of use** (V15): locate on the migrated site and update `sources.yaml`.

## Next step
Phase 1: ingest the three Acts and ~50 SC judgments, then parse, chunk, validate, index and ask.
