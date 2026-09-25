"""No model at all: the top passages verbatim, each with its [S#] marker. An honest mode, not a mock — it keeps the
system answering when every generative provider is unavailable, and says so."""

from __future__ import annotations

import re
import time

from app.llm.base import LLMResult, Message

EXCERPT_CHARS = 600


def excerpt(text: str, limit: int = EXCERPT_CHARS) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind("; "), cut.rfind(": "))
    return (cut[: end + 1] if end > limit * 0.5 else cut.rsplit(" ", 1)[0]) + " …"


class ExtractiveClient:
    name = "extractive"
    model = "none"

    def answer_from_blocks(self, blocks: list[dict], max_blocks: int = 4) -> LLMResult:
        t0 = time.perf_counter()
        lines = ["**Relevant provisions** — no generative model was used; these are the closest passages, verbatim.", ""]
        for b in blocks[:max_blocks]:
            lines.append(f"- {b['label']}: “{excerpt(b['text'])}” [{b['sid']}]")
        return LLMResult(text="\n".join(lines), model=self.model, input_tokens=0, output_tokens=0,
                         latency_ms=int((time.perf_counter() - t0) * 1000))

    def generate(self, messages: list[Message], *, system: str, max_tokens: int,
                 temperature: float = 0.1, json_schema: dict | None = None) -> LLMResult:
        raise NotImplementedError("ExtractiveClient answers from context blocks: use answer_from_blocks()")
