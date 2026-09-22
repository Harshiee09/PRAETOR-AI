"""bge-m3 dense embeddings via sentence-transformers: fp16 on CUDA, L2-normalised, 1024-d.

The model loads lazily. If CUDA is requested but unusable, we fall back to CPU and log a warning
(failure-behaviour table in the minimum-viable-architecture note).
"""

from __future__ import annotations

import logging
import time
from functools import lru_cache

import numpy as np

log = logging.getLogger(__name__)

EMBED_DIM = 1024
MAX_SEQ_LENGTH = 1024  # chunks are <= MAX_CHUNK_TOKENS plus a metadata header


@lru_cache(maxsize=2)
def get_tokenizer(model_name: str):
    """The embedding model's tokenizer, for token counts (no model weights loaded)."""
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(model_name)


def count_tokens(text: str, model_name: str) -> int:
    return len(get_tokenizer(model_name)(text, add_special_tokens=False)["input_ids"])


class Embedder:
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
        from sentence_transformers import SentenceTransformer

        device = self.requested_device
        if device == "cuda" and not torch.cuda.is_available():
            log.warning("CUDA requested but unavailable; embedding on CPU", extra={"model": self.model_name})
            device = "cpu"
        t0 = time.perf_counter()
        # Convert to fp16 on the CPU before moving to the GPU, so fp32 weights never occupy VRAM.
        model = SentenceTransformer(self.model_name, device="cpu")
        if device == "cuda":
            model.half()
            model.to("cuda")
        model.max_seq_length = MAX_SEQ_LENGTH
        self._model, self.device = model, device
        log.info(
            "embedding model loaded",
            extra={"model": self.model_name, "device": device, "load_s": round(time.perf_counter() - t0, 2)},
        )
        return model

    @property
    def dim(self) -> int:
        return self._load().get_sentence_embedding_dimension()

    def encode(self, texts: list[str], show_progress: bool = False) -> np.ndarray:
        model = self._load()
        vecs = model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=show_progress,
        )
        # fp16 normalisation leaves norms around 1 +/- 5e-4; renormalise in fp32 so inner product == cosine.
        vecs = vecs.astype(np.float32)
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True).clip(min=1e-12)
        return np.ascontiguousarray(vecs)

    def unload(self) -> None:
        if self._model is None:
            return
        import gc

        import torch

        self._model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
