import "server-only";

import { randomUUID } from "node:crypto";

export const ASK_TIMEOUT_MS = 280_000;
export const READ_TIMEOUT_MS = 15_000;
export const UPLOAD_TIMEOUT_MS = 60_000;
const REQUEST_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
type JsonObject = Record<string, unknown>;
type ProxyOptions = {
  path: string;
  method?: "GET" | "POST" | "DELETE";
  body?: unknown;
  formData?: FormData;
  allowNoContent?: boolean;
  timeoutMs?: number;
  validate: (value: unknown) => boolean;
  health?: boolean;
};

export function requestIdFor(request: Request): string {
  const supplied = request.headers.get("X-Request-ID");
  const key = process.env.PRAETOR_API_KEY?.trim();
  return supplied &&
    REQUEST_ID.test(supplied) &&
    !(key && supplied.includes(key))
    ? supplied
    : randomUUID();
}

export function jsonResponse(
  body: unknown,
  requestId: string,
  status = 200,
  sample = false,
): Response {
  return Response.json(body, {
    status,
    headers: {
      "Cache-Control": "no-store, max-age=0",
      "X-Request-ID": requestId,
      "X-Content-Type-Options": "nosniff",
      ...(sample ? { "X-Praetor-Sample": "1" } : {}),
    },
  });
}

export function errorResponse(
  code: string,
  message: string,
  requestId: string,
  status: number,
): Response {
  return jsonResponse(
    { error: { code, message, request_id: requestId } },
    requestId,
    status,
  );
}

export function isDevelopmentMock(): boolean {
  return (
    process.env.NODE_ENV === "development" && process.env.PRAETOR_MOCK === "1"
  );
}

function getConfig(health = false): { baseUrl: string; apiKey: string } | null {
  const baseUrl = process.env.PRAETOR_API_URL?.trim();
  const apiKey = process.env.PRAETOR_API_KEY?.trim() || "";
  if (!baseUrl || (!apiKey && !health)) return null;
  try {
    const parsed = new URL(baseUrl);
    if (
      !["http:", "https:"].includes(parsed.protocol) ||
      parsed.username ||
      parsed.password ||
      parsed.search ||
      parsed.hash
    )
      return null;
    return { baseUrl: baseUrl.replace(/\/+$/, ""), apiKey };
  } catch {
    return null;
  }
}

export function isObject(value: unknown): value is JsonObject {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

/** Prevent a misconfigured upstream from reflecting the credential in JSON. */
function redactCredential(value: unknown, secret: string): unknown {
  if (!secret) return value;
  if (typeof value === "string") return value.split(secret).join("[redacted]");
  if (Array.isArray(value))
    return value.map((item) => redactCredential(item, secret));
  if (isObject(value))
    return Object.fromEntries(
      Object.entries(value)
        .filter(
          ([key]) => !/^(x-api-key|api_key|apiKey|authorization)$/i.test(key),
        )
        .map(([key, item]) => [
          key.split(secret).join("[redacted]"),
          redactCredential(item, secret),
        ]),
    );
  return value;
}

function upstreamError(
  status: number,
  body: unknown,
  requestId: string,
  secret: string,
): Response {
  const error = isObject(body) && isObject(body.error) ? body.error : null;
  const defaults: Record<number, { code: string; message: string }> = {
    401: {
      code: "unauthorized",
      message: "The research service connection is not authorized.",
    },
    404: { code: "not_found", message: "The requested source was not found." },
    413: { code: "too_large", message: "Upload a file up to 4 MB." },
    415: { code: "unsupported_media_type", message: "Upload a PDF, a Word document (.docx) or a photo or scan (JPG, PNG, WebP or TIFF)." },
    422: {
      code: "invalid_request",
      message: "Check your question and try again.",
    },
    503: {
      code: "unavailable",
      message: "Still starting or offline, try again shortly.",
    },
    504: { code: "timeout", message: "This took too long; try again." },
  };
  const fallback = defaults[status] ?? {
    code: "internal_error",
    message: "The research service could not complete the request.",
  };
  const code = status === 422 && error?.code === "unreadable_document" ? "unreadable_document" : fallback.code;
  // Document parsing and size errors explain actionable upload constraints.
  const message =
    (status === 422 || status === 413) &&
    typeof error?.message === "string" &&
    error.message.length <= 500
      ? secret
        ? error.message.split(secret).join("[redacted]")
        : error.message
      : fallback.message;
  return errorResponse(
    code,
    message,
    requestId,
    defaults[status] ? status : 500,
  );
}

export async function proxyRequest(
  request: Request,
  requestId: string,
  options: ProxyOptions,
): Promise<Response> {
  const config = getConfig(options.health);
  if (!config)
    return errorResponse(
      "unavailable",
      "This site is not connected to the research service yet: the owner needs to finish the server setup.",
      requestId,
      503,
    );

  const controller = new AbortController();
  let timedOut = false;
  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, options.timeoutMs ?? READ_TIMEOUT_MS);
  const cancel = () => controller.abort();
  request.signal.addEventListener("abort", cancel, { once: true });
  if (request.signal.aborted) cancel();
  try {
    const response = await fetch(`${config.baseUrl}${options.path}`, {
      method: options.method ?? "GET",
      body:
        options.formData ?? (options.body === undefined ? undefined : JSON.stringify(options.body)),
      headers: {
        Accept: "application/json",
        ...(options.formData ? {} : { "Content-Type": "application/json" }),
        ...(config.apiKey ? { "X-API-Key": config.apiKey } : {}),
        "X-Request-ID": requestId,
      },
      signal: controller.signal,
      cache: "no-store",
      redirect: "error",
    });
    if (options.allowNoContent && response.status === 204) return new Response(null, { status: 204, headers: { "Cache-Control": "no-store, max-age=0", "X-Request-ID": requestId, "X-Content-Type-Options": "nosniff" } });
    // The generated request ID is canonical; upstream response headers are never forwarded.
    let body: unknown;
    try {
      body = await response.json();
    } catch (error) {
      if (controller.signal.aborted) throw error;
      return response.ok
        ? errorResponse(
            "internal_error",
            "The research service returned an unreadable response.",
            requestId,
            502,
          )
        : upstreamError(response.status, null, requestId, config.apiKey);
    }
    if (
      options.health &&
      response.status === 503 &&
      options.validate(body) &&
      isObject(body) &&
      body.status === "down"
    ) {
      const safeHealth = redactCredential(body, config.apiKey);
      if (!options.validate(safeHealth))
        return errorResponse(
          "internal_error",
          "The research service returned an unexpected response.",
          requestId,
          502,
        );
      return jsonResponse(safeHealth, requestId, 503);
    }
    if (!response.ok)
      return upstreamError(response.status, body, requestId, config.apiKey);
    if (!options.validate(body))
      return errorResponse(
        "internal_error",
        "The research service returned an unexpected response.",
        requestId,
        502,
      );
    const safeBody = redactCredential(body, config.apiKey);
    if (!options.validate(safeBody))
      return errorResponse(
        "internal_error",
        "The research service returned an unexpected response.",
        requestId,
        502,
      );
    if (isObject(safeBody) && "trace_id" in safeBody)
      safeBody.trace_id = requestId;
    return jsonResponse(safeBody, requestId, response.status);
  } catch {
    if (timedOut)
      return errorResponse(
        "timeout",
        "This took too long; try again.",
        requestId,
        504,
      );
    if (request.signal.aborted)
      return errorResponse(
        "cancelled",
        "The request was cancelled.",
        requestId,
        499,
      );
    return errorResponse(
      "unavailable",
      "Still starting or offline, try again shortly.",
      requestId,
      503,
    );
  } finally {
    clearTimeout(timeout);
    request.signal.removeEventListener("abort", cancel);
  }
}
