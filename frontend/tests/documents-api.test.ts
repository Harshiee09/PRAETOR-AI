// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { POST as upload, maxDuration as uploadDuration } from "@/app/api/documents/route";
import { GET as getDocumentRoute, DELETE as forgetRoute } from "@/app/api/documents/[id]/route";
import { POST as analyzeRoute, maxDuration as analyzeDuration } from "@/app/api/documents/analyze/route";
import { GET as healthRoute } from "@/app/api/health/route";
import { analyzeDocuments, forgetDocument, uploadDocument } from "@/lib/api/client";
import { DOCUMENT_EXPIRED_MESSAGE, MAX_PDF_BYTES, validateDocumentAnalysis, validatePdfFile } from "@/lib/api/documents";
import { ApiClientError, documentErrorMessage, errorMessage } from "@/lib/api/errors";
import type { DocumentAnalysis, DocumentInfo, DocumentTask } from "@/lib/api/types";
import { sampleAnswer } from "@/lib/server/samples";
import { ASK_TIMEOUT_MS, UPLOAD_TIMEOUT_MS } from "@/lib/server/proxy";

const secret = "private-document-api-key";
const fetchMock = vi.fn<typeof fetch>();
const info: DocumentInfo = { document_id: "fixture-a", filename: "fixture.pdf", pages: 1, unreadable_pages: [], passage_count: 0, words: 0, uploaded_at: "2026-09-25T00:00:00Z", expires_at: "2026-09-25T01:00:00Z", warnings: ["Test metadata; no real document processing."] };
const pdf = (size = 32, type = "application/pdf") => new File([new Uint8Array(size)], "fixture.pdf", { type });
function uploadRequest(file = pdf(), extras = false): Request {
  const form = new FormData();
  form.set("file", file);
  if (extras) { form.set("api_key", "browser-key"); form.set("private_note", "Do not forward"); }
  return new Request("http://localhost/api/documents", { method: "POST", body: form, headers: { "X-Request-ID": "document-test-id", "X-API-Key": "browser-key", Cookie: "private-cookie" } });
}
function analysisRequest(body: unknown): Request {
  return new Request("http://localhost/api/documents/analyze", { method: "POST", body: JSON.stringify(body), headers: { "Content-Type": "application/json", "X-Request-ID": "document-test-id" } });
}
const context = (id = "fixture-a") => ({ params: Promise.resolve({ id }) });
const analysis = (task: DocumentTask = "summary"): DocumentAnalysis => ({ ...sampleAnswer("document-test-id"), citations: [], task, documents: [{ filename: "fixture.pdf", pages_read: [1], complete: true }], law_checked: false });

beforeEach(() => {
  vi.stubEnv("NODE_ENV", "test"); vi.stubEnv("PRAETOR_MOCK", "0");
  vi.stubEnv("PRAETOR_API_URL", "https://backend.example"); vi.stubEnv("PRAETOR_API_KEY", secret);
  vi.stubGlobal("fetch", fetchMock);
});
afterEach(() => { vi.useRealTimers(); vi.unstubAllEnvs(); vi.unstubAllGlobals(); });

describe("PDF validation in browser and upload route", () => {
  it("accepts exactly 4 MiB and rejects the next byte", () => {
    expect(validatePdfFile(pdf(MAX_PDF_BYTES))).toBeNull();
    expect(validatePdfFile(pdf(MAX_PDF_BYTES + 1))).toContain("4 MB");
  });
  it("rejects a non-PDF MIME type despite a .pdf filename", () => {
    expect(validatePdfFile(pdf(32, "text/plain"))).toBe("Only PDF files can be uploaded");
  });
  it("rejects a 5 MB file in the browser without issuing any request", async () => {
    await expect(uploadDocument(pdf(5 * 1024 * 1024))).rejects.toMatchObject({ code: "too_large", status: 413 });
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it("rejects a non-PDF in the browser without a request", async () => {
    await expect(uploadDocument(pdf(20, "text/plain"))).rejects.toMatchObject({ code: "unsupported_media_type", status: 415 });
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it.each([[MAX_PDF_BYTES + 1, "application/pdf", 413], [20, "text/plain", 415], [0, "application/pdf", 422]] as const)("validates file bytes and MIME type on the server (%s,%s)", async (size, type, status) => {
    const response = await upload(uploadRequest(pdf(size, type)));
    expect(response.status).toBe(status);
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it("bounds the entire multipart stream even without a content-length header", async () => {
    const response = await upload(uploadRequest(pdf(5 * 1024 * 1024)));
    expect(response.status).toBe(413);
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it("rejects oversized content-length before parsing the body", async () => {
    const request = uploadRequest();
    request.headers.set("Content-Length", "99999999");
    expect((await upload(request)).status).toBe(413);
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it("rejects duplicate file fields", async () => {
    const form = new FormData(); form.append("file", pdf()); form.append("file", pdf());
    const response = await upload(new Request("http://localhost/api/documents", { method: "POST", body: form }));
    expect(response.status).toBe(422);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("document proxy", () => {
  it("forwards exactly one file and server key with a generated multipart boundary, preserving 201", async () => {
    fetchMock.mockResolvedValueOnce(Response.json(info, { status: 201, headers: { "X-API-Key": secret } }));
    const response = await upload(uploadRequest(pdf(), true));
    expect(response.status).toBe(201);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("https://backend.example/v1/documents");
    expect(init?.body).toBeInstanceOf(FormData);
    expect([...((init!.body as FormData).keys())]).toEqual(["file"]);
    const headers = new Headers(init!.headers);
    expect(headers.get("X-API-Key")).toBe(secret);
    expect(headers.has("Content-Type")).toBe(false);
    expect(headers.has("Cookie")).toBe(false);
    expect(init).toMatchObject({ redirect: "error", cache: "no-store" });
    expect(response.headers.has("X-API-Key")).toBe(false);
    expect(await response.text()).not.toContain(secret);
    expect(uploadDuration).toBeGreaterThanOrEqual(60);
  });
  it.each([[413, "too_large", "The PDF has more than 80 pages."], [415, "unsupported_media_type", "Only PDF files can be uploaded"], [422, "unreadable_document", "This PDF is scanned or password-protected."]])("preserves actionable document upload errors %s", async (status, code, message) => {
    fetchMock.mockResolvedValueOnce(Response.json({ error: { code, message, request_id: "document-test-id" } }, { status: Number(status) }));
    const response = await upload(uploadRequest());
    expect(response.status).toBe(status);
    const body = await response.json();
    expect(body.error).toMatchObject({ code, message });
    expect(errorMessage(new ApiClientError(body.error.code, body.error.message, body.error.request_id, Number(status)))).toBe(message);
  });
  it("forwards DELETE and accepts an empty 204 response", async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));
    const response = await forgetRoute(new Request("http://localhost/api/documents/fixture-a", { method: "DELETE" }), context());
    expect(response.status).toBe(204);
    expect(await response.text()).toBe("");
    expect(fetchMock.mock.calls[0][1]?.method).toBe("DELETE");
  });
  it("handles a browser DELETE 204 without attempting JSON parsing", async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));
    await expect(forgetDocument("fixture-a")).resolves.toBeUndefined();
  });
  it("maps document 404 to expiry while leaving library source errors unchanged", () => {
    const error = new ApiClientError("not_found", "Missing", "id", 404);
    expect(documentErrorMessage(error)).toBe(DOCUMENT_EXPIRED_MESSAGE);
    expect(errorMessage(error)).toContain("passage");
  });
  it("preserves available document health when library status is down", async () => {
    fetchMock.mockResolvedValueOnce(Response.json({ status: "down", checks: { documents: "ok", index: "offline" } }, { status: 503 }));
    const response = await healthRoute(new Request("http://localhost/api/health"));
    expect(response.status).toBe(503);
    expect(await response.json()).toMatchObject({ status: "down", checks: { documents: "ok" } });
  });
  it("times out an upload after 60 seconds", async () => {
    vi.useFakeTimers();
    fetchMock.mockImplementationOnce((_url, init) => new Promise((_resolve, reject) => init!.signal!.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")), { once: true })));
    const pending = upload(uploadRequest());
    // Multipart parsing resolves through microtasks before the upstream timer begins.
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    await vi.advanceTimersByTimeAsync(UPLOAD_TIMEOUT_MS);
    expect((await pending).status).toBe(504);
  });
});

describe("document analysis requests", () => {
  it.each(["ask", "summary", "risks", "checklist", "lawyer_questions", "compare"] as DocumentTask[])("accepts task %s and forwards only its contract fields", async (task) => {
    fetchMock.mockResolvedValueOnce(Response.json(analysis(task)));
    const input = { document_ids: task === "compare" ? ["a", "b"] : ["a"], task, question: "  What does it say?  ", explain: true };
    const response = await analyzeRoute(analysisRequest(input));
    expect(response.status).toBe(200);
    expect(JSON.parse(fetchMock.mock.calls[0][1]!.body as string)).toEqual({ document_ids: input.document_ids, task, question: "What does it say?" });
    expect(analyzeDuration).toBe(300);
  });
  it.each([
    { document_ids: ["a"], task: "ask", question: " " },
    { document_ids: ["a"], task: "summary", question: "x".repeat(2001) },
    { document_ids: ["a"], task: "compare" },
    { document_ids: ["a", "b"], task: "summary" },
    { document_ids: ["a", "a"], task: "compare" },
    { document_ids: ["a"], task: "unknown" },
  ])("rejects invalid task input before any upstream call", async (input) => {
    expect(validateDocumentAnalysis(input).error).toBeTruthy();
    expect((await analyzeRoute(analysisRequest(input))).status).toBe(422);
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it("validates browser analysis requests too", async () => {
    await expect(analyzeDocuments({ document_ids: ["a"], task: "ask", question: "" })).rejects.toMatchObject({ code: "invalid_request" });
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it("times out an analysis after 280 seconds", async () => {
    vi.useFakeTimers();
    fetchMock.mockImplementationOnce((_url, init) => new Promise((_resolve, reject) => init!.signal!.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")), { once: true })));
    const pending = analyzeRoute(analysisRequest({ document_ids: ["a"], task: "summary" }));
    await vi.advanceTimersByTimeAsync(ASK_TIMEOUT_MS);
    expect((await pending).status).toBe(504);
  });
});

describe("document sample boundary", () => {
  it("returns explicitly unprocessed metadata, abstains, forgets, then reports expiry", async () => {
    vi.stubEnv("NODE_ENV", "development"); vi.stubEnv("PRAETOR_MOCK", "1");
    const uploaded = await upload(uploadRequest());
    expect(uploaded.headers.get("X-Praetor-Sample")).toBe("1");
    const document: DocumentInfo = await uploaded.json();
    expect(document).toMatchObject({ pages: 0, words: 0, passage_count: 0 });
    expect(document.warnings.join(" ")).toContain("not been parsed");
    expect(Date.parse(document.expires_at) - Date.parse(document.uploaded_at)).toBe(3_600_000);
    const result = await analyzeRoute(analysisRequest({ document_ids: [document.document_id], task: "summary" }));
    expect(await result.json()).toMatchObject({ abstained: true, citations: [], law_checked: false });
    expect((await forgetRoute(new Request("http://localhost/api/documents/id", { method: "DELETE" }), context(document.document_id))).status).toBe(204);
    expect((await getDocumentRoute(new Request("http://localhost/api/documents/id"), context(document.document_id))).status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it("cannot return document samples in production", async () => {
    vi.stubEnv("NODE_ENV", "production"); vi.stubEnv("PRAETOR_MOCK", "1");
    fetchMock.mockResolvedValueOnce(Response.json(info, { status: 201 }));
    const response = await upload(uploadRequest());
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(response.headers.has("X-Praetor-Sample")).toBe(false);
  });
});
