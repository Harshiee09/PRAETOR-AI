"""FastAPI app: POST /v1/ask, GET /v1/sources/{chunk_id}, GET /v1/healthz, GET /v1/stats, and uploaded documents:
POST /v1/documents, GET|DELETE /v1/documents/{document_id}, POST /v1/documents/analyze (docs/topics/architecture/api.md).

Local only (DECISIONS D47): the models need the GPU and several GB of weights, so this runs on the laptop; a frontend
on Vercel reaches it through a tunnel, from server-side code that holds the API key.

- Auth: when API_KEY is set, every endpoint except /v1/healthz needs `X-API-Key`. Without API_KEY, only direct
  localhost calls are served; tunnel traffic arrives as localhost but carries forwarding headers, so it is refused.
- One question at a time: the encoders and the local LLM share one 8 GB GPU (DECISIONS D34), so /v1/ask is serialised.
- Request ids: `X-Request-ID` is echoed (or generated) and equals the answer's trace_id.
- Errors: {"error": {"code", "message", "request_id"}}; logs never contain the question (query hashes only).
"""

from __future__ import annotations

import hashlib
import logging
import re
import statistics
import threading
import time
import uuid
from collections import Counter, deque
from collections.abc import Callable
from contextlib import asynccontextmanager
from hmac import compare_digest

import httpx
from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.schemas import (AnalyzeRequest, AnalyzeResponse, AskRequest, AskResponse, DocumentDetail, DocumentInfo,
                             Error, Health, Source, Stats)
from app.config import Settings
from app.documents.parse import UploadError, parse_upload
from app.documents.store import DocumentStore
from app.store import cache
from app.store.db import chunk_by_id, connect

log = logging.getLogger(__name__)
LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}
FORWARDING_HEADERS = ("x-forwarded-for", "forwarded", "x-real-ip", "cf-connecting-ip", "true-client-ip")
REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
SOURCE_FIELDS = list(Source.model_fields)
ERROR_RESPONSES = {401: {"model": Error}, 404: {"model": Error}, 422: {"model": Error}, 503: {"model": Error}}
UPLOAD_RESPONSES = {**ERROR_RESPONSES, 413: {"model": Error}, 415: {"model": Error}}
ERROR_CODES = {401: "unauthorized", 404: "not_found", 413: "too_large", 415: "unsupported_media_type",
               422: "unreadable_document", 503: "unavailable"}


def _is_direct_local(request: Request) -> bool:
    host = request.client.host if request.client else ""
    return host in LOCAL_HOSTS and not any(h in request.headers for h in FORWARDING_HEADERS)


def _registry_hash(settings: Settings) -> str:
    h = hashlib.sha256()
    for p in sorted(settings.registry_dir.glob("*.yaml")):
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


class State:
    """Everything the endpoints share; the engine is loaded once, at startup."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = None
        self.load_error: str | None = None
        self.version: dict = {}
        self.gpu = threading.Lock()
        self.started = time.time()
        self.requests: Counter = Counter()
        self.latencies: deque = deque(maxlen=500)
        self.documents = DocumentStore(settings.doc_ttl_minutes, settings.doc_max_open)


def create_app(settings: Settings, *, engine=None, answer_fn: Callable | None = None, load_engine: bool = True,
               warm_up: bool = True, analyze_fn: Callable | None = None) -> FastAPI:
    """`engine`/`answer_fn`/`analyze_fn` are injected by unit tests; `load_engine=False` builds the app only (OpenAPI
    export)."""
    from app.rag.pipeline import answer as pipeline_answer

    state = State(settings)
    answer = answer_fn or pipeline_answer

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if engine is not None:
            state.engine = engine
        elif load_engine:
            try:
                from app.rag.pipeline import Engine

                loaded = Engine.load(settings)
                if warm_up:  # load both encoders now, so the first question is not slower than the rest
                    loaded.retriever.dense.embedder.encode(["warm up"])
                    if loaded.retriever.reranker is not None:
                        loaded.retriever.reranker.score("warm up", ["warm up"])
                state.engine = loaded  # only once the models really load (a failed warm-up used to leave it set)
            except Exception as exc:  # noqa: BLE001 — reported by /v1/healthz instead of crashing the server
                state.load_error = f"{type(exc).__name__}: {exc}"
                log.error("engine failed to load", extra={"error": state.load_error})
        if state.engine is not None:
            state.version = _version(settings, state.engine)
        yield

    app = FastAPI(title="PRAETOR AI", version="0.3.0", lifespan=lifespan,
                  description="Informational Indian-law answers grounded in cited sources. Not legal advice.")
    app.state.praetor = state
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
                       allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"], expose_headers=["X-Request-ID"])

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        rid = incoming if REQUEST_ID.match(incoming) else uuid.uuid4().hex[:16]
        request.state.request_id = rid
        t0 = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        path = request.url.path
        if path.startswith("/v1/sources/"):
            path = "/v1/sources"
        elif path.startswith("/v1/documents/") and path != "/v1/documents/analyze":
            path = "/v1/documents/{id}"
        state.requests[path] += 1
        log.info("request", extra={"request_id": rid, "method": request.method, "path": path,
                                   "status": response.status_code, "latency_ms": round((time.perf_counter() - t0) * 1000)})
        return response

    def _error(request: Request, status: int, code: str, message: str) -> JSONResponse:
        rid = getattr(request.state, "request_id", "-")
        return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "request_id": rid}},
                            headers={"X-Request-ID": rid})

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        code = ERROR_CODES.get(exc.status_code, "error")
        return _error(request, exc.status_code, code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        msg = "; ".join(f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in exc.errors())
        return _error(request, 422, "invalid_request", msg)

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception):
        log.exception("unhandled error", extra={"request_id": getattr(request.state, "request_id", "-")})
        return _error(request, 500, "internal_error", "Something went wrong; quote the request id when reporting it.")

    def require_key(request: Request) -> None:
        if settings.api_key:
            if not compare_digest(request.headers.get("x-api-key", ""), settings.api_key):
                raise HTTPException(401, "missing or wrong X-API-Key")
        elif not _is_direct_local(request):
            raise HTTPException(401, "this server has no API_KEY, so it only answers direct localhost calls; "
                                     "set API_KEY and send it as X-API-Key")

    def require_engine():
        if state.engine is None:
            raise HTTPException(503, f"the answer engine is not loaded: {state.load_error or 'still starting'}")
        return state.engine

    @app.post("/v1/ask", response_model=AskResponse, responses=ERROR_RESPONSES, dependencies=[Depends(require_key)],
              summary="Answer a question from the indexed sources, with citations")
    def ask(body: AskRequest, request: Request, eng=Depends(require_engine)) -> dict:
        rid = request.state.request_id
        t0 = time.perf_counter()
        use_cache = settings.cache_enabled and body.use_cache and not body.explain and body.mode == "full"
        key = cache.cache_key(body.question, {**state.version, "mode": body.mode}) if use_cache else None
        if key:
            conn = connect(settings.sqlite_path)
            try:
                hit = cache.get(conn, key)
            finally:
                conn.close()
            if hit is not None:
                return {**hit, "trace_id": rid, "cached": True, "latency_ms": round((time.perf_counter() - t0) * 1000)}
        with state.gpu:
            out = answer(eng, body.question, explain=body.explain, mode=body.mode, trace_id=rid)
        ms = round((time.perf_counter() - t0) * 1000)
        state.latencies.append(ms)
        resp = {**out, "cached": False, "latency_ms": ms}
        if key and cache.cacheable(out):
            conn = connect(settings.sqlite_path)
            try:
                cache.put(conn, key, {k: v for k, v in resp.items() if k not in ("explain", "trace_id", "latency_ms")},
                          settings.cache_ttl_hours)
            finally:
                conn.close()
        return resp

    @app.get("/v1/sources/{chunk_id}", response_model=Source, responses=ERROR_RESPONSES,
             dependencies=[Depends(require_key)], summary="The full stored passage behind a citation card")
    def source(chunk_id: str) -> dict:
        conn = connect(settings.sqlite_path)
        try:
            c = chunk_by_id(conn, chunk_id)
        finally:
            conn.close()
        if c is None:
            raise HTTPException(404, f"no source with chunk_id {chunk_id!r}")
        return {k: c.get(k) for k in SOURCE_FIELDS}

    def get_document(document_id: str):
        doc = state.documents.get(document_id)
        if doc is None:
            raise HTTPException(404, f"no uploaded document {document_id!r} (documents expire after "
                                     f"{settings.doc_ttl_minutes} minutes and are lost when the server restarts)")
        return doc

    @app.post("/v1/documents", status_code=201, response_model=DocumentInfo, responses=UPLOAD_RESPONSES,
              dependencies=[Depends(require_key)], summary="Upload a PDF to ask about, summarise, review or compare")
    def upload(file: UploadFile = File(description="A PDF with a text layer (scanned PDFs need OCR, not installed).")) -> dict:
        limit = int(settings.doc_max_mb * 1024 * 1024)
        data = file.file.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"the file is larger than {settings.doc_max_mb:g} MB (DOC_MAX_MB)")
        try:
            parsed = parse_upload(data, settings.doc_max_pages, settings.doc_ocr_max_pages)
        except UploadError as exc:
            raise HTTPException(exc.status, exc.message) from None
        base = re.split(r"[\\/]", file.filename or "document.pdf")[-1]
        return state.documents.put(re.sub(r"[^\w .()-]", "_", base)[:120] or "document.pdf", parsed).info()

    @app.get("/v1/documents/{document_id}", response_model=DocumentDetail, responses=ERROR_RESPONSES,
             dependencies=[Depends(require_key)], summary="An uploaded document's passages (the text behind [D#] cards)")
    def document(document_id: str) -> dict:
        doc = get_document(document_id)
        return {**doc.info(), "passages": [{k: p[k] for k in ("n", "locator", "page_start", "page_end", "text")}
                                           for p in doc.parsed.passages]}

    @app.delete("/v1/documents/{document_id}", status_code=204, responses=ERROR_RESPONSES,
                dependencies=[Depends(require_key)], summary="Forget an uploaded document now")
    def delete_document(document_id: str) -> Response:
        if not state.documents.delete(document_id):
            raise HTTPException(404, f"no uploaded document {document_id!r}")
        return Response(status_code=204)

    @app.post("/v1/documents/analyze", response_model=AnalyzeResponse, responses=ERROR_RESPONSES,
              dependencies=[Depends(require_key)],
              summary="Ask about, summarise, review, make a checklist or lawyer questions from, or compare documents")
    def analyze_documents(body: AnalyzeRequest, request: Request) -> dict:
        from app.documents.analyze import analyze, law_lookup

        docs = [get_document(d) for d in body.document_ids]
        law_fn = law_lookup(state.engine, settings) if hasattr(state.engine, "retriever") else None
        t0 = time.perf_counter()
        with state.gpu:
            out = (analyze_fn or analyze)(settings, docs, body.task, body.question, law_fn=law_fn,
                                          explain=body.explain, trace_id=request.state.request_id)
        return {**out, "cached": False, "latency_ms": round((time.perf_counter() - t0) * 1000)}

    @app.get("/v1/healthz", response_model=Health, responses={503: {"model": Health}},
             summary="Liveness and readiness (no key needed)")
    def healthz() -> JSONResponse:
        from app.embeddings.index import check_index

        checks: dict[str, str] = {}
        conn = connect(settings.sqlite_path)
        try:
            problems = check_index(settings, conn)
        finally:
            conn.close()
        checks["index"] = "ok" if not problems else "; ".join(problems)
        checks["engine"] = "ok" if state.engine is not None else f"not loaded: {state.load_error or 'starting'}"
        checks["answer_model"] = _ollama_check(settings)
        # uploaded documents need neither the index nor the engine (D50); without a model they get verbatim passages
        checks["documents"] = "ok" if checks["answer_model"] == "ok" else "verbatim passages only (no answer model)"
        down = checks["index"] != "ok" or checks["engine"] != "ok"
        status = "down" if down else ("ok" if checks["answer_model"] == "ok" else "degraded")
        return JSONResponse(status_code=503 if down else 200, content={"status": status, "checks": checks})

    @app.get("/v1/stats", response_model=Stats, responses=ERROR_RESPONSES, dependencies=[Depends(require_key)],
             summary="Corpus, index, model and server counters")
    def stats() -> dict:
        from app.embeddings.index import read_manifest

        conn = connect(settings.sqlite_path)
        try:
            docs = dict(conn.execute("SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type").fetchall())
            chunks = dict(conn.execute("SELECT doc_type, COUNT(*) FROM chunks GROUP BY doc_type").fetchall())
            cached = cache.count(conn)
        finally:
            conn.close()
        m = read_manifest(settings) or {}
        lat = sorted(state.latencies)
        return {"documents": docs, "chunks": chunks,
                "index": {k: m.get(k) for k in ("chunk_count", "faiss_ntotal", "corpus_hash", "embed_model", "created_at")},
                "model": {"answer": settings.ollama_model, "digest": state.version.get("model_digest"),
                          "temperature": settings.llm_temperature, "seed": settings.llm_seed,
                          "embed": settings.embed_model, "rerank": settings.rerank_model},
                "prompt_version": state.version.get("prompt_version", "?"), "cache_entries": cached,
                "uptime_s": round(time.time() - state.started), "requests": dict(state.requests),
                "answer_latency_ms": {"p50": round(statistics.median(lat)) if lat else None,
                                      "p95": lat[max(0, int(0.95 * len(lat)) - 1)] if lat else None}}

    return app


def _ollama_check(settings: Settings) -> str:
    if settings.llm_answer != "ollama":
        return f"not used (LLM_ANSWER={settings.llm_answer})"
    try:
        tags = httpx.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=3).json()
    except (httpx.HTTPError, ValueError) as exc:
        return f"Ollama unreachable at {settings.ollama_base_url} ({type(exc).__name__}); answers fall back to verbatim passages"
    names = {m.get("name") for m in tags.get("models", [])} | {m.get("model") for m in tags.get("models", [])}
    return "ok" if settings.ollama_model in names else f"model {settings.ollama_model!r} is not pulled in Ollama"


def _version(settings: Settings, engine) -> dict:
    """Everything that changes an answer; part of the cache key."""
    from app.embeddings.index import read_manifest
    from app.llm.ollama import OllamaClient

    m = read_manifest(settings) or {}
    digest = OllamaClient(settings.ollama_base_url, settings.ollama_model).digest() if settings.ollama_model else None
    return {"prompt_version": engine.prompt_version, "model": settings.ollama_model, "model_digest": digest,
            "temperature": settings.llm_temperature, "seed": settings.llm_seed, "corpus_hash": m.get("corpus_hash"),
            "registry": _registry_hash(settings), "min_evidence_score": settings.min_evidence_score,
            "context_max_chunks": settings.context_max_chunks}
