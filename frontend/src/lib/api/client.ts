import { ApiClientError } from "./errors";
import type {
  ApiResult,
  AskResponse,
  HealthResponse,
  SourceResponse,
  DocumentInfo,
  DocumentDetail,
  DocumentAnalysis,
  DocumentAnalysisRequest,
} from "./types";
import { isSupportedFile, validateDocumentAnalysis, validatePdfFile } from "./documents";

export { ApiClientError } from "./errors";
type RequestOptions = { signal?: AbortSignal };
export const ASK_CLIENT_TIMEOUT_MS = 290_000;
export const READ_CLIENT_TIMEOUT_MS = 20_000;
export const UPLOAD_CLIENT_TIMEOUT_MS = 70_000;

function makeRequestId(): string {
  return (
    globalThis.crypto?.randomUUID?.() ??
    `web-${Date.now()}-${Math.random().toString(36).slice(2)}`
  );
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  acceptDown = false,
  timeoutMs = READ_CLIENT_TIMEOUT_MS,
  allowNoContent = false,
): Promise<ApiResult<T>> {
  const requestId = makeRequestId();
  let responseId = requestId;
  const controller = new AbortController();
  let timedOut = false;
  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const cancel = () => controller.abort();
  options.signal?.addEventListener("abort", cancel, { once: true });
  if (options.signal?.aborted) cancel();
  try {
    const response = await fetch(path, {
      ...options,
      signal: controller.signal,
      cache: "no-store",
      credentials: "same-origin",
      headers: {
        ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        "X-Request-ID": requestId,
      },
    });
    responseId = response.headers.get("X-Request-ID") || requestId;
    if (allowNoContent && response.status === 204) return { sampleData: response.headers.get("X-Praetor-Sample") === "1", requestId: responseId } as ApiResult<T>;
    let body: Record<string, unknown>;
    try {
      body = await response.json();
      if (!body || typeof body !== "object" || Array.isArray(body))
        throw new Error("Invalid response");
    } catch (error) {
      if (controller.signal.aborted) throw error;
      const code =
        response.status === 504
          ? "timeout"
          : response.status === 503
            ? "unavailable"
            : "internal_error";
      throw new ApiClientError(
        code,
        "The research service returned an unreadable response.",
        responseId,
        response.status,
      );
    }
    const validDown =
      acceptDown &&
      response.status === 503 &&
      body.status === "down" &&
      body.checks !== null &&
      typeof body.checks === "object" &&
      !Array.isArray(body.checks);
    if (!response.ok && !validDown) {
      const details =
        body.error && typeof body.error === "object"
          ? (body.error as Record<string, unknown>)
          : {};
      throw new ApiClientError(
        typeof details.code === "string"
          ? details.code
          : response.status === 504
            ? "timeout"
            : "internal_error",
        typeof details.message === "string"
          ? details.message
          : "The research service returned an error.",
        typeof details.request_id === "string"
          ? details.request_id
          : responseId,
        response.status,
      );
    }
    return {
      ...body,
      sampleData: response.headers.get("X-Praetor-Sample") === "1",
      requestId: responseId,
    } as ApiResult<T>;
  } catch (error) {
    if (timedOut || (error instanceof Error && error.name === "TimeoutError"))
      throw new ApiClientError(
        "timeout",
        "This took too long; try again.",
        responseId,
      );
    if (options.signal?.aborted)
      throw new ApiClientError(
        "cancelled",
        "The request was cancelled.",
        responseId,
      );
    if (error instanceof ApiClientError) throw error;
    throw new ApiClientError(
      "network_error",
      "The research service could not be reached.",
      responseId,
    );
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener("abort", cancel);
  }
}

export function askQuestion(
  question: string,
  options: RequestOptions = {},
): Promise<ApiResult<AskResponse>> {
  return request<AskResponse>(
    "/api/ask",
    {
      method: "POST",
      body: JSON.stringify({ question }),
      signal: options.signal,
    },
    false,
    ASK_CLIENT_TIMEOUT_MS,
  );
}

export function getSource(
  chunkId: string,
  options: RequestOptions = {},
): Promise<ApiResult<SourceResponse>> {
  return request<SourceResponse>(
    `/api/sources/${encodeURIComponent(chunkId)}`,
    { signal: options.signal },
  );
}

export function getHealth(
  options: RequestOptions = {},
): Promise<ApiResult<HealthResponse>> {
  return request<HealthResponse>(
    "/api/health",
    { signal: options.signal },
    true,
  );
}

export async function uploadDocument(file: File, options: RequestOptions = {}): Promise<ApiResult<DocumentInfo>> {
  const invalid = validatePdfFile(file);
  if (invalid) throw new ApiClientError(!isSupportedFile(file) ? "unsupported_media_type" : file.size === 0 ? "unreadable_document" : "too_large", invalid, makeRequestId(), !isSupportedFile(file) ? 415 : file.size === 0 ? 422 : 413);
  const form = new FormData();
  form.set("file", file);
  return request<DocumentInfo>("/api/documents", { method: "POST", body: form, signal: options.signal }, false, UPLOAD_CLIENT_TIMEOUT_MS);
}

export function getDocument(id: string, options: RequestOptions = {}): Promise<ApiResult<DocumentDetail>> {
  return request<DocumentDetail>(`/api/documents/${encodeURIComponent(id)}`, { signal: options.signal });
}

export async function forgetDocument(id: string, options: RequestOptions = {}): Promise<void> {
  await request<Record<string, never>>(`/api/documents/${encodeURIComponent(id)}`, { method: "DELETE", signal: options.signal }, false, READ_CLIENT_TIMEOUT_MS, true);
}

export function analyzeDocuments(input: DocumentAnalysisRequest, options: RequestOptions = {}): Promise<ApiResult<DocumentAnalysis>> {
  const validated = validateDocumentAnalysis(input);
  if (validated.error) return Promise.reject(new ApiClientError("invalid_request", validated.error, makeRequestId(), 422));
  return request<DocumentAnalysis>("/api/documents/analyze", { method: "POST", body: JSON.stringify(validated.data), signal: options.signal }, false, ASK_CLIENT_TIMEOUT_MS);
}

export const deleteDocument = forgetDocument;
export const analyzeDocument = analyzeDocuments;
