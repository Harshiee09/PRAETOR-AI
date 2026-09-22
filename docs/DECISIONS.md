# Decisions and verifications

Append-only, newest last. Each entry: what was decided or verified, and the evidence. Add a row whenever you settle a price, a model ID, a licence, an endpoint or a design choice.

## 2026-09-22 — kit setup, before any code

### Decisions
| # | Decision | Reason |
|---|---|---|
| D1 | Local-first architecture; AWS limited to S3, Bedrock, IAM and Budgets, with Lambda as an optional stretch | 3 days and about $50; the blueprint's managed services bill for idle capacity |
| D2 | FAISS (faiss-cpu) plus SQLite FTS5, no managed vector database | exact search is fast at MVP scale and costs nothing |
| D3 | `BAAI/bge-m3` embeddings and `BAAI/bge-reranker-v2-m3` reranking | multilingual and long-context; replaces `all-MiniLM-L6-v2`, which is English-only and truncates at 256 word pieces |
| D4 | No LangChain or LlamaIndex | the reports' splitter sample doesn't run as written, and plain Python is simpler to test |
| D5 | Judgments come from the AWS Open Data bucket rather than scraping or a paid API | free, licensed, already structured |

### Verifications
| # | Fact | Evidence |
|---|---|---|
| V1 | Indian Supreme Court judgments: `s3://indian-supreme-court-judgments`, region ap-south-1, CC-BY-4.0, readable with `--no-sign-request`, 1950–2025, per-year metadata parquet, English and regional PDFs | https://registry.opendata.aws/indian-supreme-court-judgments/ · https://github.com/vanga/indian-supreme-court-judgments |
| V2 | Indian High Court judgments: `s3://indian-high-court-judgments`, 25 High Courts, roughly 17.8M judgments and 1.25 TiB of tar archives | https://registry.opendata.aws/indian-high-court-judgments/ · https://github.com/vanga/indian-high-court-judgments |
| V3 | Indore Development Authority v. Manoharlal is a Constitution Bench decision of 6 March 2020, (2020) 8 SCC 129 — not 2023 | https://api.sci.gov.in/supremecourt/2022/7205/7205_2022_4_1505_42249_Judgement_24-Feb-2023.pdf · https://lawlex.org/?p=25138 |
| V4 | The Aalap instruction dataset is gated, English-only, partly generated with GPT-4 and gpt-3.5-turbo, and licensed per source subset | https://huggingface.co/datasets/opennyaiorg/aalap_instruction_dataset |
| V5 | Indian Kanoon API is prepaid: about ₹0.50 per search, ₹0.20 per document, ₹500 free on signup, ₹10,000 per month for verified non-commercial use | https://indiankanoon.org/members/pricing |
| V6 | Amazon Textract's documented languages are English, Spanish, Italian, Portuguese, French and German — no Indic scripts. Re-check the quotas page, the answer is dated | https://repost.aws/questions/QUVeFLYhy8RFWKRH0H94fXVA |
| V7 | Whether credits cover Bedrock third-party models depends on the credit programme, and some usage is billed through AWS Marketplace | https://repost.aws/questions/QULMmXNMRwRvGSYm6OGt6e3Q/aws-credits-for-bedrock · https://aws.amazon.com/aws-startups/learn/aws-activate-credits-now-accepted-for-third-party-models-on-amazon-bedrock/ |
| V8 | Copyright Act 1957 s. 52(1)(q): (ii) an Act may be reproduced when published with commentary or other original matter; (iv) judgments and orders may be reproduced unless the court prohibits it | https://future.indiankanoon.org/doc/648494 |
| V9 | Claude Code loads the project `CLAUDE.md` at the start of every session, recommends under about 200 lines, and expands `@path` imports at launch | https://code.claude.com/docs/en/memory |
| V10 | `opennyaiorg/InJudgements_dataset` exists (about 12k rows); its licence was not confirmed from the card | https://huggingface.co/opennyaiorg |

### Still to verify during the build
- Current India Code URLs and download behaviour for each seed Act.
- Licences on the InJudgements, InRhetoricalRoles and InLegalNER dataset cards.
- Bedrock models and inference profiles available in ap-south-1, and current token prices.
- AWS Budgets pricing, and API Gateway timeouts if API Gateway is ever considered.
- Tesseract traineddata available on this machine for the demo languages.
- Commencement notifications for the BNS, BNSS, BSA and the Consumer Protection Act 2019, including excluded provisions.

## 2026-09-23 — Phase 0 setup

### Decisions
| # | Decision | Reason |
|---|---|---|
| D6 | Project lives at `C:\dev\praetor-ai` in its own git repo (`main`), not in `OneDrive\Desktop` | OneDrive would sync the venv, corpora, SQLite and FAISS files (locking risk for SQLite), and the old folder sat inside an accidental git repo rooted at the home directory |
| D7 | Python 3.12 (uv-managed, user-level, no admin) with `uv.lock`; torch from the PyTorch `cu130` index via `[tool.uv.sources]` — resolved to `torch 2.14.0+cu130` | only Python 3.14 was installed system-wide; 3.12 has the broadest wheel coverage. cu130 includes `sm_120` and was already proven on this GPU (global `torch 2.13.0+cu130`) |
| D8 | **The GPU has 8 GB, not 12 GB** (RTX 5070 *Laptop*, 7.93 GiB usable). bge-m3 in fp16 peaks at 1.09 GiB when converted to fp16 on the CPU before moving to CUDA (2.62 GiB if moved in fp32 first). Local LLM candidates must fit in ~5 GB: `qwen3.5:4b` (3.4 GB) and `gemma4:e2b-it-qat` (4.3 GB) were pulled. `gemma4:latest` (9.6 GB, already on the machine) can only run partly offloaded to CPU. Phase 1 uses `qwen3.5:4b` provisionally; the pick is made by the Phase 2 benchmark | measured with `praetor gpu-check` and `nvidia-smi` |
| D9 | Tesseract deferred: not installed, and the installer needs admin. Pages that need OCR are rejected with a logged reason, never indexed as garbage | the Phase 1 corpus is English PDFs with text layers |
| D10 | CLI built on stdlib `argparse` | no new dependency needed |

### Verifications
| # | Fact | Evidence |
|---|---|---|
| V11 | India Code moved from `www.indiacode.nic.in` to `https://indiacode.gov.in`; the old domain now serves only a migration notice. The new site runs DSpace 9.1, with a public REST API at `/server/api` (search: `/discover/search/objects`, items: `/core/items/{uuid}`, files: `/core/bitstreams/{uuid}/content`) | GET https://www.indiacode.nic.in/ and https://indiacode.gov.in/server/api, 2026-09-23 |
| V12 | Central Act items (`dc.identifier.state_name = CENTRAL`): Registration Act 1908 handle `123456789/496068`; Transfer of Property Act 1882 `123456789/496421`; Consumer Protection Act 2019 `123456789/496115`. The ORIGINAL bundle holds the English `a<year>-<no>.pdf` and Hindi `H<year>-<no>.pdf` with MD5 checksums. State copies are separate items whose `dc.identifier.refact` points to the central `act_id`. Per-section items (collection `SECTION`) carry `section_number` and the section text | API responses, 2026-09-23; IDs recorded in `data/registry/sources.yaml` |
| V13 | SC judgments bucket layout: `metadata/parquet/year=YYYY/metadata.parquet` (~1 MB for 2023); `data/pdf/year=YYYY/english/<name>_EN.pdf` (854 files for 2023) and `regional/<name>_<LANG>.pdf` (e.g. `HIN`, `PUN`); `data/tar/year=YYYY/{english,regional}/*.tar` with `*.index.json` | `aws s3 ls --no-sign-request --region ap-south-1`, 2026-09-23 |
| V14 | Ollama library sizes: `qwen3.5:4b` 3.4 GB, `qwen3.5:9b` 6.6 GB, `gemma4:e2b-it-qat` 4.3 GB, `gemma4:e4b-it-qat` 6.1 GB, `gemma4:12b-it-qat` 7.2 GB | https://ollama.com/library/qwen3.5/tags · https://ollama.com/library/gemma4/tags, 2026-09-23 |
| V15 | The migrated India Code site's terms of use could not be located (`/info/end-user-agreement` carries none). Licence field says so; still CHECK | https://indiacode.gov.in/info/end-user-agreement, 2026-09-23 |
