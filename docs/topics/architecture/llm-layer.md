---
id: 20260922-llm-layer
title: LLM layer
tags: [llm, architecture, cost]
created: 2026-09-22
updated: 2026-09-22
related: [20260922-minimum-viable-architecture, 20260922-retrieval-pipeline, 20260922-grounding-and-citations, 20260922-aws-cost-plan, 20260922-evaluation]
summary: Provider interface, task routing, local model selection, Bedrock usage, caching and the cost meter.
---

# LLM layer

> Summary: Provider interface, task routing, local model selection, Bedrock usage, caching and the cost meter.

## Context
Models will be swapped repeatedly during the build — local candidates, Bedrock models, and no model at all — so nothing outside `app/llm/` may import a provider SDK. There is no training or fine-tuning in this MVP.

## Details

### Interface (`app/llm/base.py`)
```python
class LLMClient(Protocol):
    name: str
    def generate(self, messages: list[Message], *, system: str, max_tokens: int,
                 temperature: float = 0.1, json_schema: dict | None = None) -> LLMResult: ...

@dataclass
class LLMResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_usd: float | None   # None for local providers
```

### Providers
- `OllamaClient` — HTTP to `OLLAMA_BASE_URL` (`/api/chat`), using its structured-output mode for classification and rewriting.
- `BedrockClient` — boto3 `bedrock-runtime` `converse()` with `BEDROCK_MODEL_ID` in `AWS_REGION`; read token counts from the response usage block; retry throttling once with backoff; every call passes the cost meter first.
- `ExtractiveClient` — no model at all: returns the top passages verbatim under "Relevant provisions", with their citations and a note that no generative model was used. It is an honest mode rather than a mock, and it keeps the demo alive when everything else fails.

### Routing (`app/llm/router.py`)
Per task, from the environment: `LLM_CLASSIFY` (rules or ollama), `LLM_REWRITE` (aliases or ollama), `LLM_ANSWER` (ollama, bedrock or extractive), then the `LLM_FALLBACK` chain on errors, timeouts or budget exhaustion. `PRIVACY_MODE=strict` removes every cloud provider from every chain. Routing never depends on a model's self-reported confidence.

### Optional local tasks
Summarising a long judgment chunk into a short case note for the context, cached and labelled as a summary — the citation still points at the underlying chunk, never at the summary. Also all privacy-sensitive preprocessing, which must happen before anything leaves the machine.

### Choosing the local model
Check what the Ollama library offers at build time. Shortlist two or three current instruct models in the 7–14B range that fit in about 8 GB at 4-bit alongside the embedder and reranker, favouring good Hindi and Indic coverage. Run the eval subset on each — answer quality, `[S#]` marker compliance, latency, VRAM — and record the pick in DECISIONS.md. Use temperature 0 to 0.2 for answers.

### Bedrock usage
- Discover rather than hard-code: `aws bedrock list-foundation-models --region $AWS_REGION` and `aws bedrock list-inference-profiles --region $AWS_REGION`. Some models are callable only through an inference-profile ID.
- Start with the cheapest model that passes the eval, and move up only when the numbers show a real gain.
- Check credits before depending on it: make one tiny call, then confirm on the next day's bill that the charge sits under Amazon Bedrock and is offset by credits. Some third-party model usage is billed through AWS Marketplace, which promotional credits may not cover. A new account may also need a one-time use-case form before Anthropic models can be invoked.
- IAM: `bedrock:InvokeModel`, plus `bedrock:InvokeModelWithResponseStream` if streaming, scoped to the chosen model or inference-profile ARNs. Inference profiles may need permissions on both the profile and the underlying model ARNs; confirm in the Bedrock IAM docs.

### Prompts
Versioned files under `app/rag/prompts/`: `answer_system.md`, `classify.md`, `rewrite.md`. The version string is part of the cache key and of every log record. Answers use inline `[S#]` markers rather than JSON, which is more robust with small local models; the validator does the strict checking afterwards.

### Cache (`cache` table in praetor.sqlite)
Key: sha256 over task, provider, model, prompt version, normalised input, context chunk IDs and the index corpus hash. Entries expire after `CACHE_TTL_HOURS`. Cache hits are logged, and eval runs can bypass the cache with `--no-cache`.

### Cost meter (`app/llm/cost.py`)
Cost equals input tokens times the input price plus output tokens times the output price, with prices read from `app/config/prices.yaml`, filled in by hand from the Bedrock pricing page and carrying a `verified_on` date. Daily spend is stored in the `spend` table, and a call that would exceed `BEDROCK_DAILY_BUDGET_USD` is skipped so the router falls back. AWS billing data lags, so this meter — not AWS Budgets — is the real-time guard.

## Related
- [Minimum viable architecture](minimum-viable-architecture.md) — context: fallback behaviour and the env contract.
- [Retrieval pipeline](retrieval-pipeline.md) — prerequisite: produces the context an answer is built from.
- [Grounding and citations](../legal/grounding-and-citations.md) — the contract the answer prompt must meet.
- [AWS plan and cost controls](../ops/aws-cost-plan.md) — Bedrock guardrails and pre-flight checks.
- [Evaluation](../ops/evaluation.md) — how model choices get decided.
