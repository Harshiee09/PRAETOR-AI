---
id: 20260922-minimum-viable-architecture
title: Minimum viable architecture
tags: [architecture]
created: 2026-09-22
updated: 2026-09-25
related: [20260922-chunk-schema, 20260922-retrieval-pipeline, 20260922-llm-layer, 20260925-api, 20260925-deployment, 20260922-report-validation]
summary: Everything runs locally (a Vercel frontend calls the local API), the request flow, the env contract, and what was cut from the AWS blueprint and why.
---

# Minimum viable architecture

> Summary: Everything runs locally (a Vercel frontend calls the local API), the request flow, the env contract, and what was cut from the AWS blueprint and why.

## Context
The AWS blueprint (`docs/sources/research-report-2-aws-blueprint.md`) describes a generic enterprise RAG stack sized for 100K–1M documents, thousands of queries a day and sub-second SLOs, built on always-on managed services. PRAETOR's constraints are the opposite: 3 days, about $50 of credits, one RTX 5070 Laptop GPU with 8 GB of VRAM (DECISIONS D8), and a demo audience. This architecture therefore inverts the blueprint: compute-heavy work runs locally. Since 2026-09-25 AWS is dropped entirely (DECISIONS D47): the backend runs on the laptop, and the separately built frontend is deployed on Vercel and calls the local API through a tunnel. Vercel cannot host the backend itself (models of several GB, no GPU; V43).

## Details

### Where each component runs
| Component | Runs | Implementation | Why |
|---|---|---|---|
| Download and ingestion | local | `app/ingestion/`: httpx for web sources, unsigned boto3 or AWS CLI reads for the open-data bucket | free; the judgments bucket needs no AWS account |
| Parsing | local | pdfplumber / pypdfium2 for PDF, BeautifulSoup or trafilatura for HTML, Pillow for images | permissive licences |
| OCR | local | Tesseract with Indic traineddata, on text-less or garbled pages only | Textract's documented languages exclude Indic scripts |
| Language ID and cleaning | local | `regex` script detection plus statistical LID, NFC normalisation | deterministic and free |
| Chunking and metadata | local | `app/chunking/` legal-aware splitters | legal structure needs custom code anyway |
| Embeddings | local GPU | bge-m3 in fp16 | multilingual, long input |
| Vector index | local | FAISS `IndexIDMap2(IndexFlatIP)`, faiss-cpu | exact search is fast at MVP scale and avoids GPU-FAISS build problems on new GPUs |
| Keyword index and metadata | local | SQLite with FTS5 | one file, SQL filters, BM25 built in |
| Reranking | local GPU | bge-reranker-v2-m3 | the biggest precision gain per hour of work |
| LLM | local | `app/llm/` router: Ollama, extractive | swapped by environment variable; no paid APIs |
| API | local | FastAPI via `praetor serve` ([API note](api.md)) | the models need the GPU |
| Frontend | Vercel | built separately; calls the API from server-side code through a tunnel ([deployment note](../ops/deployment.md)) | static and serverless hosting only |

### Request flow
```text
POST /v1/ask {question, mode?, explain?, use_cache?}
 -> answer cache (non-explain requests)
 -> normalise, detect script and language (logs keep only a query hash)
 -> classify: domain, intent, high-stakes, jurisdiction, event dates      [rules, then local LLM]
 -> rewrite: aliases, English rewrite for keyword search, optional LLM expansion
 -> candidates: exact statute lookup + FAISS dense + FTS5 BM25, with metadata filters
 -> RRF fusion -> rerank top 30 -> evidence gate (abstain if weak)
 -> context builder: [S#] blocks with provenance and status warnings, within a token budget
 -> LLM router: ollama | extractive
 -> citation validator: strip unknown IDs and unverified authorities, add repeal warnings
 -> {answer_markdown, citations[], confidence, warnings, trace_id, ...}   (X-Request-ID = trace_id)
```

### Ingestion flow
```text
source registry -> download (cache by URL and sha256) -> parse -> OCR text-less or garbled pages
 -> script and language -> clean and normalise -> legal-aware chunks -> metadata + statute status
 -> validate (reject missing provenance) -> SQLite + FTS5 -> embed on GPU -> FAISS
 -> index_manifest.json (model, dim, counts, corpus hash) -> corpus profile report
```
Runs are incremental: files whose sha256 is unchanged are skipped, and a changed document replaces its own chunks and vectors through `IndexIDMap2.remove_ids`.

### Deployment modes
- `local` (the only mode): everything on the RTX machine, `LLM_ANSWER=ollama`; `extractive` when Ollama is down.
- Remote demo: the Vercel-hosted frontend calls `praetor serve` through a tunnel with `API_KEY` (deployment note). The laptop must be on.

### VRAM budget (8 GB — the dev machine is an RTX 5070 Laptop GPU, DECISIONS D8)
bge-m3 in fp16 peaks at 1.09 GiB (measured), and bge-reranker-v2-m3 is similar. That leaves about 5 GB for the LLM and its KV cache. Measured resident sizes (`ollama ps`, 8k context): `gemma4:latest` 3.2 GB (the chosen answer model, DECISIONS D32), `qwen3.5:4b` 3.3 GB, `gemma4:e2b-it-qat` 1.8 GB — all 100% on GPU alongside both encoders. Judge fit by `ollama ps`, not download size (D33). Load models lazily, convert encoders to fp16 before moving them to CUDA, expose `EMBED_DEVICE` and `RERANK_DEVICE` for CPU fallback, and run bulk embedding with the LLM unloaded.

### Environment contract (`.env.example`, authoritative)
```dotenv

# --- paths and models
DATA_DIR=./data
EMBED_MODEL=BAAI/bge-m3
# cuda or cpu
EMBED_DEVICE=cuda
EMBED_BATCH_SIZE=16
RERANK_MODEL=BAAI/bge-reranker-v2-m3
RERANK_DEVICE=cuda
# counted with the embedding model's tokenizer
MAX_CHUNK_TOKENS=450

# --- retrieval
TOP_K_DENSE=50
TOP_K_KEYWORD=50
RRF_K=60
RERANK_TOP_N=30
CONTEXT_MAX_CHUNKS=8
CONTEXT_MAX_TOKENS=6000
# reranker-score evidence gate, set from the draft gold set (DECISIONS D27); re-calibrate as the gold set grows
MIN_EVIDENCE_SCORE=0.10
# Phase 1 gate on the top dense cosine until the reranker gate exists (provisional, DECISIONS D11)
MIN_DENSE_SCORE=0.60

# --- LLM routing: rules|ollama, aliases|ollama, ollama|extractive (everything runs locally; DECISIONS D47)
LLM_CLASSIFY=rules
LLM_REWRITE=aliases
LLM_ANSWER=ollama
LLM_FALLBACK=extractive
OLLAMA_BASE_URL=http://localhost:11434
# set after the local-model benchmark (docs/DECISIONS.md)
OLLAMA_MODEL=gemma4:latest
OLLAMA_TIMEOUT_S=180
# answer decoding: greedy with a fixed seed so repeated runs are comparable (DECISIONS D37)
LLM_TEMPERATURE=0
LLM_SEED=42
# answer cache for the API (SQLite `cache` table); the key includes prompt, model, decoding and index versions
CACHE_ENABLED=true
CACHE_TTL_HOURS=72

# --- API (praetor serve; local only)
# required for anything that is not a direct localhost call, including tunnel traffic for the Vercel frontend
API_KEY=
API_HOST=127.0.0.1
API_PORT=8000
# comma-separated browser origins allowed to call the API (add your Vercel URL)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# --- ops
LOG_LEVEL=INFO
# hash or full (full only for local debugging)
LOG_QUERIES=hash
# identify the client to government sites; add a contact address you are happy to share
HTTP_USER_AGENT="PRAETOR-AI-MVP/0.1 (informational legal RAG research prototype)"
# only if a gated Hugging Face model or dataset is used
HF_TOKEN=
```

### Cut from the blueprint, and what replaces it
| Blueprint item | Why it's out of the MVP | Replacement |
|---|---|---|
| OpenSearch (Serverless or managed), Kendra | capacity billed around the clock; a Serverless minimum alone would consume the budget quickly | FAISS plus SQLite FTS5 |
| Aurora with pgvector, DocumentDB, MemoryDB, ElastiCache | always-on instances | SQLite for metadata and cache |
| SageMaker endpoints and JumpStart | always-on GPU instances | local RTX 5070 |
| Step Functions, MWAA | orchestration overhead, and MWAA is expensive | idempotent CLI steps |
| VPC, NAT gateway, interface endpoints | hourly charges, and nothing private to reach | none |
| WAF, Shield Advanced, GuardDuty | unnecessary for a private demo | API key, localhost-only default, one request at a time |
| CodePipeline and CodeBuild, EKS/ECS | unnecessary for 3 days | git and local builds |
| Textract, Comprehend | Textract's languages exclude Indic scripts, and both charge for work that runs free locally | Tesseract, local LID |
| Bedrock Knowledge Bases | needs a managed vector store and hides chunking and provenance control | this pipeline |
| LangChain or LlamaIndex, including "LangChain on Lambda" | abstraction we don't need | plain Python |
| X-Ray | overkill at this size | `trace_id` and structured logs |
| "Local LLM first, cloud when its confidence is low" | self-reported model confidence is unreliable | route by task type and retrieval evidence |

Kept from the blueprint: incremental indexing, hybrid semantic and keyword search, a keyword fallback when dense retrieval is weak, answer caching (SQLite rather than Redis), and a local model for private or offline use. Dropped with AWS (D47): S3 backup, Bedrock, IAM, Budgets, the cost meter and the Lambda cloud-lite stretch.

### Failure behaviour
| Failure | Behaviour |
|---|---|
| GPU out of memory, or no CUDA | embed and rerank on CPU, log a warning, keep serving |
| Ollama unreachable | next provider in `LLM_FALLBACK`; `extractive` always works |
| Index missing, or model and dimension disagree with `index_manifest.json` | `/v1/healthz` reports `down` (503) with the command to run; `/v1/ask` returns 503 |
| The local SQLite build lacks FTS5 | detected at startup; switch to `bm25s` and record it in DECISIONS.md |

## Related
- [Chunk schema and provenance](chunk-schema.md) — detail: what the ingestion flow writes.
- [Retrieval pipeline](retrieval-pipeline.md) — detail: the query side of the request flow.
- [LLM layer](llm-layer.md) — detail: provider routing and the fallback chain.
- [API](api.md) — detail: the HTTP contract for the frontend.
- [Deployment](../ops/deployment.md) — detail: local server, Vercel frontend, tunnel.
- [Validation of the research reports](../data/report-validation.md) — rationale: why blueprint items were cut.
