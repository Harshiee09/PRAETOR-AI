---
id: 20260922-aws-cost-plan
title: AWS plan and cost controls
tags: [aws, cost]
created: 2026-09-22
updated: 2026-09-22
related: [20260922-minimum-viable-architecture, 20260922-llm-layer, 20260922-build-plan, 20260922-report-validation]
summary: Which AWS services are used and why, their cost drivers, guardrails, pre-flight checks and deployment steps.
---

# AWS plan and cost controls

> Summary: Which AWS services are used and why, their cost drivers, guardrails, pre-flight checks and deployment steps.

## Context
Before adding any AWS service, ask whether it can run locally for free without hurting the demo. If it can, run it locally. Prices are deliberately not quoted in this note: verify them on the official pricing pages on the day you deploy, and record them with the date in `app/config/prices.yaml` and DECISIONS.md.

## Details

### Services used
| Service | Why it's needed | Cost driver | Cheaper alternative | Phase |
|---|---|---|---|---|
| S3, ap-south-1 | durable copy of the processed database, FAISS index, manifests and eval reports, and the source for cloud-lite | GB-month stored plus requests, tiny at this scale; also noncurrent versions if versioning is on | local disk only | 3 |
| Bedrock, Converse API | stronger answers and Indic generation, when the eval shows a real gain | input and output tokens per call, the dominant cost | Ollama locally, or `extractive` | 3 |
| IAM | least-privilege identity for the app | free | — | 3 |
| AWS Budgets | email alerts, and optionally an action, as spend approaches the cap | check the pricing page; a small number of budgets has historically been free | checking the Billing console by hand | 3, first thing |
| CloudWatch Logs | only if Lambda runs | GB ingested and stored; set 7-day retention | local JSON logs | 3, stretch |
| SSM Parameter Store, standard tier | third-party tokens, such as Indian Kanoon, if ever needed | standard parameters are free, whereas Secrets Manager charges per secret | `.env` locally | as needed |
| Lambda, Function URL, ECR (stretch) | the cloud-lite query API | GB-seconds and requests, plus ECR storage for a multi-GB image | the local API, exposed through a tunnel with an API key | 3, stretch |

### Explicitly not used
OpenSearch in either form, Kendra, RDS or Aurora, DocumentDB, MemoryDB and ElastiCache, SageMaker endpoints, always-on EC2, EKS or ECS, NAT gateways, interface VPC endpoints, MWAA, WAF, Textract, and Bedrock Knowledge Bases. Each either bills for idle capacity or duplicates something that runs locally for free. Revisit one only with a measured need and a cost estimate recorded in DECISIONS.md.

### Guardrails
1. **App meter** (`app/llm/cost.py`): a hard daily cap through `BEDROCK_DAILY_BUDGET_USD`, enforced in real time because billing data lags.
2. **AWS Budgets**: a monthly budget well under the credit balance, with alerts at 50%, 80% and 100% of actual spend and at 100% of forecast. Optionally a budget action that attaches a deny-Bedrock policy to the app identity near the cap.
3. **Limits in code**: `max_tokens` on every call, a context budget, caching on, and eval runs using the local model unless a comparison is the point.
4. **Lambda, if used**: reserved concurrency of at most 2, a timeout of at most 60 seconds, a Function URL with IAM auth or an API-key check, and 7-day log retention.
5. **No long-lived root keys.** A named profile, `praetor`, ideally through SSO. Nothing lands in the repo.

### Pre-flight (`praetor aws-check`, before any spend, and after asking me)
1. Credits: balance, expiry and eligible services, read from the Billing console. Don't call the Cost Explorer API, which charges per request.
2. Identity: `aws sts get-caller-identity --profile praetor`, and confirm the region is ap-south-1.
3. A budget exists, with alert subscribers.
4. Bedrock: list foundation models and inference profiles in the region, choose one, make one tiny test call, and the next day confirm the line item sits under Amazon Bedrock and is offset by credits rather than appearing as an AWS Marketplace charge.
5. Prices recorded in `app/config/prices.yaml` with `verified_on`.

### Infrastructure as code, deliberately small
`infra/cloudformation.yaml` holds the S3 bucket (public access blocked, default encryption, a lifecycle rule expiring noncurrent versions after 7 days), the IAM policy (`s3:GetObject`, `s3:PutObject` and `s3:ListBucket` on that bucket, and `bedrock:InvokeModel` on the chosen model or profile ARNs), and the budget with its alert subscribers. `infra/deploy.sh` and `infra/teardown.sh` wrap it, and teardown asks before emptying the bucket. No CDK bootstrap, and no VPC.

### Deployment steps (Phase 3)
1. Ask me, then run pre-flight.
2. `infra/deploy.sh`, and copy the outputs — bucket name, role ARN — into `.env`.
3. `praetor s3-sync push` for the processed database, index, manifests and eval reports.
4. Set `LLM_ANSWER=bedrock` and `BEDROCK_MODEL_ID`, then run `praetor eval --subset 15 --compare ollama,bedrock`. Keep Bedrock only if it wins.
5. Stretch: build the Lambda image with CPU torch, bge-m3 for query embedding, and the index and database pulled from S3 into `/tmp`; push to ECR; create the function and Function URL; measure cold start and p95 latency; then decide. Prefer a Function URL to API Gateway for long generations, since API Gateway integrations time out at roughly 30 seconds — verify the current limit if you go that way.
6. After the demo, stop anything with a running cost, and run `infra/teardown.sh` when the work is done.

### Cost estimate method
Per answer: prompt and context tokens times the input price, plus answer tokens times the output price. Log real token counts on every call, and have `praetor eval` report tokens and dollars per query, per 100 queries, and for the whole run. The final report carries measured numbers, not guesses.

## Related
- [Minimum viable architecture](../architecture/minimum-viable-architecture.md) — context: the deployment modes.
- [LLM layer](../architecture/llm-layer.md) — the cost meter and the Bedrock client.
- [3-day build plan](build-plan.md) — when Phase 3 happens and what it must prove.
- [Validation of the research reports](../data/report-validation.md) — why the blueprint's services were cut.
