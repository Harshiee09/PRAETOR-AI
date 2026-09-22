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
