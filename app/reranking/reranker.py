"""bge-reranker-v2-m3 cross-encoder (retrieval-pipeline note, step 7).

sentence-transformers' CrossEncoder already applies a Sigmoid for this single-label model (checked on
2026-09-23: `activation_fn = Sigmoid()`), so `score()` returns 0..1 and must not be squashed again.
Loaded lazily, fp16 on CUDA (converted on the CPU first so fp32 weights never occupy VRAM), CPU fallback.
"""

from __future__ import annotations

import logging
import time

log = logging.getLogger(__name__)
MAX_LENGTH = 1024  # query + chunk (<= 450 tokens + header) fits comfortably


class Reranker:
    def __init__(self, model_name: str, device: str = "cuda", batch_size: int = 16):
        self.model_name = model_name
        self.requested_device = device
        self.batch_size = batch_size
        self._model = None
        self.device: str | None = None

    def _load(self):
        if self._model is not None:
            return self._model
        import torch
        from sentence_transformers import CrossEncoder

        device = self.requested_device
        if device == "cuda" and not torch.cuda.is_available():
            log.warning("CUDA requested but unavailable; reranking on CPU")
            device = "cpu"
        t0 = time.perf_counter()
        model = CrossEncoder(self.model_name, device="cpu", max_length=MAX_LENGTH)
        if device == "cuda":
            model.model.half()
            model.to("cuda")
        self._model, self.device = model, device
        log.info("reranker loaded", extra={"model": self.model_name, "device": device,
                                           "load_s": round(time.perf_counter() - t0, 2)})
        return model

    def score(self, query: str, texts: list[str]) -> list[float]:
        if not texts:
            return []
        model = self._load()
        scores = model.predict([(query, t) for t in texts], batch_size=self.batch_size, convert_to_numpy=True,
                               show_progress_bar=False)
        return [float(s) for s in scores]
