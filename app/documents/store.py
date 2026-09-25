"""In-memory holding area for uploaded documents: a time limit, a count limit, explicit delete (DECISIONS D50).

An uploaded document is the user's personal data. It is never indexed into the corpus (it has no verified
provenance), never cached, never logged and never written to disk; a server restart forgets it.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.documents.parse import ParsedUpload


@dataclass
class StoredDocument:
    document_id: str
    filename: str
    parsed: ParsedUpload
    uploaded_at: float
    expires_at: float

    def iso(self, t: float) -> str:
        return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    def info(self) -> dict:
        p = self.parsed
        return {"document_id": self.document_id, "filename": self.filename, "pages": p.pages,
                "unreadable_pages": p.unreadable_pages, "passage_count": len(p.passages), "words": p.words,
                "uploaded_at": self.iso(self.uploaded_at), "expires_at": self.iso(self.expires_at),
                "warnings": p.warnings}

    def chunk(self, passage: dict, role: str) -> dict:
        """A passage shaped like a corpus chunk, so the context builder and validator can treat it the same way."""
        return {"chunk_id": f"{self.document_id}:{passage['n']}", "document_id": self.document_id,
                "doc_type": "user_document", "title": self.filename, "locator": passage["locator"],
                "text": passage["text"], "page_start": passage["page_start"], "page_end": passage["page_end"],
                "status": "n/a", "role": role, "uploaded_at": self.iso(self.uploaded_at)[:10]}


class DocumentStore:
    def __init__(self, ttl_minutes: int, max_open: int):
        self.ttl_s = ttl_minutes * 60
        self.max_open = max_open
        self._docs: dict[str, StoredDocument] = {}
        self._lock = threading.Lock()

    def _expire(self, now: float) -> None:
        for k in [k for k, d in self._docs.items() if d.expires_at <= now]:
            del self._docs[k]

    def put(self, filename: str, parsed: ParsedUpload) -> StoredDocument:
        now = time.time()
        doc = StoredDocument(uuid.uuid4().hex, filename, parsed, now, now + self.ttl_s)
        with self._lock:
            self._expire(now)
            while len(self._docs) >= self.max_open:  # oldest first
                del self._docs[min(self._docs, key=lambda k: self._docs[k].uploaded_at)]
            self._docs[doc.document_id] = doc
        return doc

    def get(self, document_id: str) -> StoredDocument | None:
        with self._lock:
            self._expire(time.time())
            return self._docs.get(document_id)

    def delete(self, document_id: str) -> bool:
        with self._lock:
            return self._docs.pop(document_id, None) is not None

    def __len__(self) -> int:
        with self._lock:
            self._expire(time.time())
            return len(self._docs)
