"""Amazon Bedrock through the Converse API, for the cloud deployment (DECISIONS D58).

Credentials never live in code or `.env`: on the server they come from the EC2 instance role, on a laptop from the
AWS CLI profile. Amazon Nova is first-party on Bedrock, so no Marketplace subscription is involved; in ap-south-1 it
is reached through the APAC cross-region inference profile (`apac.amazon.nova-pro-v1:0`, verified 2026-09-26).
"""

from __future__ import annotations

import time
from functools import lru_cache

from app.llm.base import LLMError, LLMResult, Message


@lru_cache(maxsize=4)
def _client(region: str, timeout_s: float):
    import boto3
    from botocore.config import Config

    return boto3.client("bedrock-runtime", region_name=region,
                        config=Config(read_timeout=timeout_s, connect_timeout=10, retries={"max_attempts": 2}))


def bedrock_credentials_ok() -> bool:
    """True when boto3 can find credentials (instance role or CLI profile); no network call."""
    try:
        import boto3

        return boto3.Session().get_credentials() is not None
    except Exception:  # noqa: BLE001 — a missing or broken AWS config just means "not available"
        return False


class BedrockClient:
    name = "bedrock"

    def __init__(self, model_id: str, region: str, timeout_s: float = 180.0):
        if not model_id:
            raise LLMError("BEDROCK_MODEL_ID is not set")
        self.model = model_id
        self.region = region
        self.timeout_s = timeout_s

    def generate(self, messages: list[Message], *, system: str, max_tokens: int, temperature: float = 0.1,
                 json_schema: dict | None = None, seed: int | None = None) -> LLMResult:
        from botocore.exceptions import BotoCoreError, ClientError

        t0 = time.perf_counter()
        try:
            response = _client(self.region, self.timeout_s).converse(
                modelId=self.model,
                system=[{"text": system}],
                messages=[{"role": m.role, "content": [{"text": m.content}]} for m in messages],
                inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
            )
        except (BotoCoreError, ClientError) as exc:
            raise LLMError(f"Bedrock {self.model} failed: {exc}") from exc
        content = (response.get("output") or {}).get("message", {}).get("content", [])
        text = "".join(part.get("text", "") for part in content).strip()
        if not text:
            raise LLMError("Bedrock returned an empty answer")
        usage = response.get("usage") or {}
        return LLMResult(text=text, model=self.model, input_tokens=int(usage.get("inputTokens") or 0),
                         output_tokens=int(usage.get("outputTokens") or 0),
                         latency_ms=int((time.perf_counter() - t0) * 1000))
