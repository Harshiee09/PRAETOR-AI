"""Dense retrieval: embed the query with bge-m3 (normalised) and search the FAISS inner-product index."""

from __future__ import annotations

import time

import numpy as np

from app.config import Settings
from app.embeddings.embedder import Embedder
from app.embeddings.index import load_index


class DenseRetriever:
    def __init__(self, settings: Settings, embedder: Embedder | None = None):
        self.settings = settings
        self.index = load_index(settings.faiss_path)
        if self.index is None:
            raise FileNotFoundError(f"{settings.faiss_path} not found: run `praetor index`")
        self.embedder = embedder or Embedder(settings.embed_model, settings.embed_device, settings.embed_batch_size)

    def search(self, query: str, k: int | None = None) -> tuple[list[tuple[int, float]], dict]:
        k = k or self.settings.top_k_dense
        t0 = time.perf_counter()
        q = self.embedder.encode([query])
        t1 = time.perf_counter()
        scores, ids = self.index.search(np.ascontiguousarray(q, dtype=np.float32), k)
        t2 = time.perf_counter()
        hits = [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i != -1]
        return hits, {"embed_ms": round((t1 - t0) * 1000), "search_ms": round((t2 - t1) * 1000)}
