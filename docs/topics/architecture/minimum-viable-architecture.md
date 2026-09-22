---
id: 20260922-minimum-viable-architecture
title: Minimum viable architecture
tags: [architecture, aws, cost]
created: 2026-09-22
updated: 2026-09-23
related: [20260922-chunk-schema, 20260922-retrieval-pipeline, 20260922-llm-layer, 20260922-aws-cost-plan, 20260922-report-validation]
summary: What runs locally vs on AWS, the request flow, the env contract, and what was cut from the AWS blueprint and why.
---

# Minimum viable architecture

> Summary: What runs locally vs on AWS, the request flow, the env contract, and what was cut from the AWS blueprint and why.

## Context
The AWS blueprint (`docs/sources/research-report-2-aws-blueprint.md`) describes a generic enterprise RAG stack sized for 100K–1M documents, thousands of queries a day and sub-second SLOs, built on always-on managed services. PRAETOR's constraints are the opposite: 3 days, about $50 of credits, one RTX 5070 Laptop GPU with 8 GB of VRAM (DECISIONS D8), and a demo audience. This architecture therefore inverts the blueprint: compute-heavy work runs locally, and AWS supplies durable storage, optional stronger generation, and cost guardrails.

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
| LLM | local or AWS | `app/llm/` router: Ollama, Bedrock, extractive | swapped by environment variable |
| API | local | FastAPI via `praetor serve` | the demo runs where the GPU is |
| Backup and sharing | AWS S3 | `praetor s3-sync` | durable and cheap |
| Stronger generation | AWS Bedrock | Converse API | pay per token, nothing idle |
| Guardrails | AWS Budgets, IAM, app cost meter | one CloudFormation stack | protects the credits |
| Cloud-lite API (stretch) | AWS Lambda with a Function URL | container image | only if the measured cold start is acceptable |

### Request flow
```text
POST /v1/ask {query, lang?, filters?}
 -> normalise, detect script and language, redact personal data (copy used for cloud calls and logs)
 -> classify: domain, intent, high-stakes, jurisdiction, event dates      [rules, then local LLM]
 -> rewrite: aliases, English rewrite for keyword search, optional LLM expansion
 -> candidates: exact statute lookup + FAISS dense + FTS5 BM25, with metadata filters
 -> RRF fusion -> rerank top 30 -> evidence gate (abstain if weak)
 -> context builder: [S#] blocks with provenance and status warnings, within a token budget
 -> LLM router: ollama | bedrock | extractive   (cache, cost meter)
 -> citation validator: strip unknown IDs and unverified authorities, add repeal warnings
 -> {answer, citations[], confidence, warnings, trace_id}
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
- `local` (default demo): everything on the RTX machine, `LLM_ANSWER=ollama`.
- `local+bedrock`: identical, but final answers use `LLM_ANSWER=bedrock`.
- `cloud-lite` (stretch): a Lambda container behind a Function URL that pulls the SQLite database and FAISS index from S3 into `/tmp` at cold start, embeds queries on CPU, skips or shrinks reranking, and generates with Bedrock. Size the ephemeral storage to fit the index. Build it only after measuring cold start and memory; if the cold start is too slow for a live demo, demo `local` instead, through a tunnel with an API key if people need remote access.

### VRAM budget (8 GB — the dev machine is an RTX 5070 Laptop GPU, DECISIONS D8)
bge-m3 in fp16 peaks at 1.09 GiB (measured), and bge-reranker-v2-m3 is similar. That leaves about 5 GB for the LLM and its KV cache, so local answer models are 2–4B-class at 4-bit (`qwen3.5:4b`, `gemma4:e2b-it-qat`), with a modest context. A 7–9B model only fits by unloading the encoders or partly offloading to CPU. Load models lazily, convert encoders to fp16 before moving them to CUDA, expose `EMBED_DEVICE` and `RERANK_DEVICE` for CPU fallback, and run bulk embedding with the LLM unloaded.

### Environment contract (`.env.example`)
```dotenv
# --- paths and models
DATA_DIR=./data
EMBED_MODEL=BAAI/bge-m3
# cuda or cpu
EMBED_DEVICE=cuda
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
# starting value only; calibrate on the eval dev split
MIN_EVIDENCE_SCORE=0.30
# --- LLM routing: rules|ollama, aliases|ollama, ollama|bedrock|extractive
LLM_CLASSIFY=rules
LLM_REWRITE=aliases
LLM_ANSWER=ollama
LLM_FALLBACK=extractive
OLLAMA_BASE_URL=http://localhost:11434
# set after the local-model benchmark
OLLAMA_MODEL=
# strict = never call a cloud service
PRIVACY_MODE=standard
CACHE_ENABLED=true
CACHE_TTL_HOURS=72
# --- AWS
AWS_PROFILE=praetor
AWS_REGION=ap-south-1
S3_BUCKET=
# verified model ID or inference-profile ID
BEDROCK_MODEL_ID=
BEDROCK_DAILY_BUDGET_USD=2.00
PRICES_FILE=app/config/prices.yaml
# --- API and ops
# required whenever the API binds to anything other than localhost
API_KEY=
LOG_LEVEL=INFO
# hash or full (full only for local debugging)
LOG_QUERIES=hash
HTTP_USER_AGENT="PRAETOR-AI-MVP (contact: set-your-email)"
# only if a gated Hugging Face model or dataset is used
HF_TOKEN=
```

### Cut from the blueprint, and what replaces it
| Blueprint item | Why it's out of the MVP | Replacement |
|---|---|---|
| OpenSearch (Serverless or managed), Kendra | capacity billed around the clock; a Serverless minimum alone would consume the budget quickly | FAISS plus SQLite FTS5 |
| Aurora with pgvector, DocumentDB, MemoryDB, ElastiCache | always-on instances | SQLite for metadata and cache |
| SageMaker endpoints and JumpStart | always-on GPU instances | local RTX 5070 plus on-demand Bedrock |
| Step Functions, MWAA | orchestration overhead, and MWAA is expensive | idempotent CLI steps |
| VPC, NAT gateway, interface endpoints | hourly charges, and nothing private to reach | Lambda, if used at all, outside a VPC |
| WAF, Shield Advanced, GuardDuty | unnecessary for a private demo | API key or IAM-auth Function URL, reserved concurrency |
| CodePipeline and CodeBuild, EKS/ECS | unnecessary for 3 days | git and local builds |
| Textract, Comprehend | Textract's languages exclude Indic scripts, and both charge for work that runs free locally | Tesseract, local LID |
| Bedrock Knowledge Bases | needs a managed vector store and hides chunking and provenance control | this pipeline |
| LangChain or LlamaIndex, including "LangChain on Lambda" | abstraction we don't need | plain Python |
| X-Ray | overkill at this size | `trace_id` and structured logs |
| "Local LLM first, cloud when its confidence is low" | self-reported model confidence is unreliable | route by task type and retrieval evidence |

Kept from the blueprint: incremental indexing, hybrid semantic and keyword search, a keyword fallback when dense retrieval is weak, answer caching (SQLite rather than Redis), least-privilege IAM, budgets and alerts, and a local model for private or offline use.

### Failure behaviour
| Failure | Behaviour |
|---|---|
| GPU out of memory, or no CUDA | embed and rerank on CPU, log a warning, keep serving |
| Ollama unreachable | next provider in `LLM_FALLBACK`; `extractive` always works |
| Bedrock throttled, failing, or over the daily budget | one retry with backoff, then fall back; never block the answer |
| Index missing, or model and dimension disagree with `index_manifest.json` | the API refuses to start and names the command to run |
| The local SQLite build lacks FTS5 | detected at startup; switch to `bm25s` and record it in DECISIONS.md |

## Related
- [Chunk schema and provenance](chunk-schema.md) — detail: what the ingestion flow writes.
- [Retrieval pipeline](retrieval-pipeline.md) — detail: the query side of the request flow.
- [LLM layer](llm-layer.md) — detail: provider routing and the fallback chain.
- [AWS plan and cost controls](../ops/aws-cost-plan.md) — detail: the AWS rows of the table above.
- [Validation of the research reports](../data/report-validation.md) — rationale: why blueprint items were cut.
