"""A polite HTTP client for government sites: identifying User-Agent, ~1 request/second per host, retries
with backoff on transient errors, and no attempt to get around blocks (docs/topics/data/data-sources.md)."""

from __future__ import annotations

import logging
import threading
import time
from urllib.parse import urlparse

import httpx

log = logging.getLogger(__name__)


class BlockedError(RuntimeError):
    """The server refused automated access (401/403/429 or a captcha page). Stop and ask the user for the file."""


class PoliteClient:
    def __init__(self, user_agent: str, min_interval_s: float = 1.0, timeout_s: float = 90.0, retries: int = 3):
        self._client = httpx.Client(
            headers={"User-Agent": user_agent}, timeout=timeout_s, follow_redirects=True
        )
        self._min_interval = min_interval_s
        self._retries = retries
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def _wait_turn(self, url: str) -> None:
        host = urlparse(url).netloc
        with self._lock:
            wait = self._last.get(host, 0.0) + self._min_interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last[host] = time.monotonic()

    def get(self, url: str, **kwargs) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(1, self._retries + 1):
            self._wait_turn(url)
            try:
                resp = self._client.get(url, **kwargs)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                log.warning("http transport error", extra={"url": url, "attempt": attempt, "error": str(exc)})
                time.sleep(2**attempt)
                continue
            if resp.status_code in (401, 403, 429):
                raise BlockedError(f"{resp.status_code} from {url}: automated access refused; fetch it manually")
            if resp.status_code >= 500:
                last_exc = httpx.HTTPStatusError(f"{resp.status_code}", request=resp.request, response=resp)
                log.warning("http server error", extra={"url": url, "attempt": attempt, "status": resp.status_code})
                time.sleep(2**attempt)
                continue
            resp.raise_for_status()
            if "captcha" in resp.headers.get("content-type", "") or (
                resp.headers.get("content-type", "").startswith("text/html") and b"captcha" in resp.content[:5000].lower()
            ):
                raise BlockedError(f"captcha page served for {url}; fetch it manually")
            return resp
        raise RuntimeError(f"GET {url} failed after {self._retries} attempts: {last_exc}")

    def get_json(self, url: str) -> dict:
        return self.get(url, headers={"Accept": "application/json"}).json()

    def close(self) -> None:
        self._client.close()
