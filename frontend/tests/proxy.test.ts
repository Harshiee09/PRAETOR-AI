// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { POST, maxDuration } from "@/app/api/ask/route";
import { GET as health } from "@/app/api/health/route";
import { GET as source } from "@/app/api/sources/[chunkId]/route";
import { sampleAnswer } from "@/lib/server/samples";
import { ASK_TIMEOUT_MS } from "@/lib/server/proxy";
import type { SourceResponse } from "@/lib/api/types";

const SECRET = "private-test-api-key-never-public";
const REQUEST_ID = "test-request-123";
const fetchMock = vi.fn<typeof fetch>();

function ask(
  question: unknown = "What sources cover this question?",
  extras: Record<string, unknown> = {},
): Request {
  return new Request("http://localhost/api/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": REQUEST_ID,
      "X-API-Key": "browser-must-not-override",
      Authorization: "browser-token",
      Cookie: "session=private",
    },
    body: JSON.stringify({ question, ...extras }),
  });
}

beforeEach(() => {
  vi.stubEnv("NODE_ENV", "test");
  vi.stubEnv("PRAETOR_MOCK", "0");
  vi.stubEnv("PRAETOR_API_URL", "https://backend.example");
  vi.stubEnv("PRAETOR_API_KEY", SECRET);
  vi.stubGlobal("fetch", fetchMock);
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("ask proxy security and validation", () => {
  it("sends only server credentials and forced parameters; exposes no upstream secrets or headers", async () => {
    fetchMock.mockResolvedValueOnce(
      Response.json(
        {
          ...sampleAnswer(REQUEST_ID),
          api_key: SECRET,
          metadata: { nested: SECRET },
        },
        {
          headers: {
            "X-API-Key": SECRET,
            "Set-Cookie": `secret=${SECRET}`,
            "X-Request-ID": "untrusted-upstream-id",
          },
        },
      ),
    );
    const response = await POST(
      ask("  हिंदी प्रश्न  ", {
        mode: "dense",
        explain: true,
        use_cache: false,
      }),
    );
    expect(maxDuration).toBe(300);
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("https://backend.example/v1/ask");
    expect(init).toMatchObject({
      redirect: "error",
      cache: "no-store",
      method: "POST",
    });
    expect(JSON.parse(init!.body as string)).toEqual({
      question: "हिंदी प्रश्न",
      mode: "full",
      explain: false,
      use_cache: true,
    });
    const headers = new Headers(init!.headers);
    expect(headers.get("X-API-Key")).toBe(SECRET);
    expect(headers.get("X-Request-ID")).toBe(REQUEST_ID);
    expect(headers.has("Authorization")).toBe(false);
    expect(headers.has("Cookie")).toBe(false);
    expect(response.headers.get("Cache-Control")).toContain("no-store");
    expect(response.headers.get("X-Request-ID")).toBe(REQUEST_ID);
    expect(response.headers.has("X-API-Key")).toBe(false);
    expect(response.headers.has("Set-Cookie")).toBe(false);
    expect(await response.text()).not.toContain(SECRET);
  });

  it.each([undefined, null, 123, "", " \n\t ", "x".repeat(2001)])(
    "rejects an invalid question before fetching (%s)",
    async (question) => {
      const response = await POST(
        ask(question === undefined ? null : question),
      );
      expect(response.status).toBe(422);
      expect(await response.json()).toMatchObject({
        error: { code: "invalid_request", request_id: REQUEST_ID },
      });
      expect(fetchMock).not.toHaveBeenCalled();
    },
  );

  it("counts Unicode code points and trims before validating the limit", async () => {
    fetchMock.mockResolvedValueOnce(Response.json(sampleAnswer(REQUEST_ID)));
    expect((await POST(ask(`  ${"𑀓".repeat(2000)}  `))).status).toBe(200);
  });

  it("returns a generated request ID for malformed JSON without revealing internals", async () => {
    const request = new Request("http://localhost/api/ask", {
      method: "POST",
      body: "not JSON",
    });
    const response = await POST(request);
    const body = await response.json();
    expect(response.status).toBe(422);
    expect(body.error.request_id).toBeTruthy();
    expect(response.headers.get("X-Request-ID")).toBe(body.error.request_id);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("replaces an untrusted or secret-bearing request ID", async () => {
    const request = ask();
    request.headers.set("X-Request-ID", `prefix-${SECRET}`);
    fetchMock.mockResolvedValueOnce(Response.json(sampleAnswer("upstream")));
    const response = await POST(request);
    expect(response.headers.get("X-Request-ID")).not.toContain(SECRET);
    expect(await response.text()).not.toContain(SECRET);
  });

  it.each([
    [401, "unauthorized"],
    [422, "invalid_request"],
    [503, "unavailable"],
  ])(
    "passes through HTTP %i with an error envelope and request ID",
    async (status, code) => {
      fetchMock.mockResolvedValueOnce(
        Response.json(
          {
            error: { code, message: "A field message", request_id: REQUEST_ID },
          },
          { status: Number(status) },
        ),
      );
      const response = await POST(ask());
      expect(response.status).toBe(status);
      expect(await response.json()).toMatchObject({
        error: {
          code,
          request_id: REQUEST_ID,
          ...(status === 422 ? { message: "A field message" } : {}),
        },
      });
    },
  );

  it("redacts reflected credentials in a validation message", async () => {
    fetchMock.mockResolvedValueOnce(
      Response.json(
        {
          error: {
            code: "invalid_request",
            message: `Bad field ${SECRET}`,
            request_id: REQUEST_ID,
          },
        },
        { status: 422 },
      ),
    );
    expect(await (await POST(ask())).text()).not.toContain(SECRET);
  });

  it("does not forward arbitrary HTML errors or internal error text", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(`<html>${SECRET}</html>`, { status: 500 }),
    );
    const response = await POST(ask());
    expect(response.status).toBe(500);
    expect(await response.text()).not.toContain(SECRET);
  });

  it("rejects malformed successful payloads instead of returning data that can crash the UI", async () => {
    fetchMock.mockResolvedValueOnce(
      Response.json({ answer_markdown: "Incomplete", citations: [null] }),
    );
    const response = await POST(ask());
    expect(response.status).toBe(502);
    expect(await response.json()).toMatchObject({
      error: { code: "internal_error" },
    });
  });

  it("does not expose redirect/network exception text", async () => {
    fetchMock.mockRejectedValueOnce(
      new Error(`Redirect rejected for ${SECRET}`),
    );
    const response = await POST(ask());
    expect(response.status).toBe(503);
    expect(await response.text()).not.toContain(SECRET);
  });

  it("aborts the upstream after 280 seconds and returns a timeout request ID", async () => {
    vi.useFakeTimers();
    fetchMock.mockImplementationOnce(
      (_url, init) =>
        new Promise((_resolve, reject) => {
          init!.signal!.addEventListener(
            "abort",
            () => reject(new DOMException("Aborted", "AbortError")),
            { once: true },
          );
        }),
    );
    const pending = POST(ask());
    await vi.advanceTimersByTimeAsync(ASK_TIMEOUT_MS);
    const response = await pending;
    expect(response.status).toBe(504);
    expect(await response.json()).toEqual({
      error: {
        code: "timeout",
        message: "This took too long; try again.",
        request_id: REQUEST_ID,
      },
    });
  });

  it("keeps the timeout active while consuming the upstream body", async () => {
    vi.useFakeTimers();
    fetchMock.mockImplementationOnce(
      async (_url, init) =>
        ({
          ok: true,
          status: 200,
          json: () =>
            new Promise((_resolve, reject) => {
              init!.signal!.addEventListener(
                "abort",
                () => reject(new DOMException("Aborted", "AbortError")),
                { once: true },
              );
            }),
        }) as Response,
    );
    const pending = POST(ask());
    await vi.advanceTimersByTimeAsync(ASK_TIMEOUT_MS);
    expect((await pending).status).toBe(504);
  });

  it("cancels upstream work when the caller disconnects and cleans up the timeout", async () => {
    vi.useFakeTimers();
    const caller = new AbortController();
    let upstreamSignal: AbortSignal | null | undefined;
    fetchMock.mockImplementationOnce(
      (_url, init) =>
        new Promise((_resolve, reject) => {
          upstreamSignal = init!.signal;
          init!.signal!.addEventListener(
            "abort",
            () => reject(new DOMException("Aborted", "AbortError")),
            { once: true },
          );
        }),
    );
    const request = new Request(ask(), { signal: caller.signal });
    const pending = POST(request);
    await vi.advanceTimersByTimeAsync(1);
    caller.abort();
    const response = await pending;
    expect(upstreamSignal?.aborted).toBe(true);
    expect(response.status).toBe(499);
    expect(vi.getTimerCount()).toBe(0);
  });
});

describe("development sample boundary", () => {
  it("labels a citation-free sample abstention only with the explicit development flag", async () => {
    vi.stubEnv("NODE_ENV", "development");
    vi.stubEnv("PRAETOR_MOCK", "1");
    const response = await POST(ask());
    expect(response.headers.get("X-Praetor-Sample")).toBe("1");
    expect(await response.json()).toMatchObject({
      abstained: true,
      citations: [],
      provider: null,
    });
    expect(fetchMock).not.toHaveBeenCalled();
    expect(
      (await health(new Request("http://localhost/api/health"))).headers.get(
        "X-Praetor-Sample",
      ),
    ).toBe("1");
  });

  it("cannot enable sample data in production, even when PRAETOR_MOCK=1", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("PRAETOR_MOCK", "1");
    fetchMock.mockResolvedValueOnce(Response.json(sampleAnswer(REQUEST_ID)));
    const response = await POST(ask());
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(response.headers.has("X-Praetor-Sample")).toBe(false);
  });

  it("fails closed when production credentials are absent despite the mock flag", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("PRAETOR_MOCK", "1");
    vi.stubEnv("PRAETOR_API_KEY", "");
    const response = await POST(ask());
    expect(response.status).toBe(503);
    expect(response.headers.has("X-Praetor-Sample")).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("read proxies", () => {
  it.each([".", "..", "", "bad\u0000id"])(
    "rejects source identifiers that change path semantics (%s)",
    async (chunkId) => {
      const response = await source(
        new Request("http://localhost/api/sources/test"),
        { params: Promise.resolve({ chunkId }) },
      );
      expect(response.status).toBe(422);
      expect(fetchMock).not.toHaveBeenCalled();
    },
  );
  it("preserves the health down payload with HTTP 503", async () => {
    const payload = { status: "down", checks: { index: "unavailable" } };
    fetchMock.mockResolvedValueOnce(Response.json(payload, { status: 503 }));
    const response = await health(new Request("http://localhost/api/health"));
    expect(response.status).toBe(503);
    expect(await response.json()).toEqual(payload);
  });

  it("supports the contract's health endpoint without an API key", async () => {
    vi.stubEnv("PRAETOR_API_KEY", "");
    fetchMock.mockResolvedValueOnce(
      Response.json({ status: "ok", checks: {} }),
    );
    expect(
      (await health(new Request("http://localhost/api/health"))).status,
    ).toBe(200);
    expect(
      new Headers(fetchMock.mock.calls[0][1]?.headers).has("X-API-Key"),
    ).toBe(false);
  });

  it("encodes a source identifier into a single upstream path segment", async () => {
    const payload: SourceResponse = {
      chunk_id: "a/b?c",
      doc_type: "test",
      title: "Test fixture; not a legal authority",
      locator: "Test location",
      text: "Test placeholder with no legal content.",
      authority: "test",
      jurisdiction: "test",
      status: "n/a",
      language: "en",
      source_url: "https://example.com/test",
      retrieved_at: "2026-09-25",
      licence: "test",
    };
    fetchMock.mockResolvedValueOnce(Response.json(payload));
    const response = await source(
      new Request("http://localhost/api/sources/a"),
      { params: Promise.resolve({ chunkId: "a/b?c" }) },
    );
    expect(fetchMock.mock.calls[0][0]).toBe(
      "https://backend.example/v1/sources/a%2Fb%3Fc",
    );
    expect(await response.json()).toEqual(payload);
  });
});
