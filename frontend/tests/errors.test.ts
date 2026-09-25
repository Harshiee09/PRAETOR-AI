// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClientError, errorMessage } from "@/lib/api/errors";
import {
  ASK_CLIENT_TIMEOUT_MS,
  READ_CLIENT_TIMEOUT_MS,
  askQuestion,
  getHealth,
  getSource,
} from "@/lib/api/client";

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("plain-language error mapping", () => {
  it.each([
    [
      "unauthorized",
      "The research service connection needs attention. Please contact the owner.",
    ],
    ["not_found", "This passage is no longer available. Try another source."],
    ["unavailable", "Still starting or offline, try again shortly."],
    ["timeout", "This took too long; try again."],
    [
      "internal_error",
      "Something went wrong while checking the sources. Please try again.",
    ],
  ])("maps %s without exposing server messages", (code, message) => {
    const error = new ApiClientError(
      code,
      "Internal details",
      "request-1",
      500,
    );
    expect(errorMessage(error)).toBe(message);
    expect(error.requestId).toBe("request-1");
  });
  it("uses the validation field message", () => {
    expect(
      errorMessage(
        new ApiClientError(
          "invalid_request",
          "Keep your question to 2,000 characters or fewer.",
          "id",
          422,
        ),
      ),
    ).toBe("Keep your question to 2,000 characters or fewer.");
  });
  it("keeps unknown exceptions generic", () => {
    expect(errorMessage(new Error("sensitive"))).not.toContain("sensitive");
  });
});

describe("typed browser client metadata", () => {
  it("returns a valid down health payload and sample label despite HTTP 503", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          Response.json(
            { status: "down", checks: { index: "offline" } },
            {
              status: 503,
              headers: { "X-Request-ID": "health-id", "X-Praetor-Sample": "1" },
            },
          ),
        ),
    );
    expect(await getHealth()).toEqual({
      status: "down",
      checks: { index: "offline" },
      requestId: "health-id",
      sampleData: true,
    });
  });
  it("retains error code, status and request ID from the proxy", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          Response.json(
            {
              error: {
                code: "unavailable",
                message: "Offline",
                request_id: "backend-id",
              },
            },
            { status: 503 },
          ),
        ),
    );
    await expect(askQuestion("question")).rejects.toMatchObject({
      code: "unavailable",
      requestId: "backend-id",
      status: 503,
    });
  });
  it("gives network failures a request ID", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );
    await expect(askQuestion("question")).rejects.toMatchObject({
      code: "network_error",
      requestId: expect.any(String),
    });
  });
  it("maps platform HTML timeouts to the timeout message", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response("Gateway timeout", {
            status: 504,
            headers: { "X-Request-ID": "timeout-id" },
          }),
        ),
    );
    await expect(askQuestion("question")).rejects.toMatchObject({
      code: "timeout",
      requestId: "timeout-id",
    });
  });

  it("bounds a stalled browser ask request at 290 seconds", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init: RequestInit) =>
          new Promise((_resolve, reject) => {
            init.signal!.addEventListener(
              "abort",
              () => reject(new DOMException("Aborted", "AbortError")),
              { once: true },
            );
          }),
      ),
    );
    const pending = askQuestion("question").catch((error: unknown) => error);
    await vi.advanceTimersByTimeAsync(ASK_CLIENT_TIMEOUT_MS);
    expect(await pending).toMatchObject({
      code: "timeout",
      requestId: expect.any(String),
    });
    expect(vi.getTimerCount()).toBe(0);
  });

  it.each(["health", "source"])(
    "bounds stalled %s response bodies at 20 seconds and retains the received request ID",
    async (kind) => {
      vi.useFakeTimers();
      vi.stubGlobal(
        "fetch",
        vi.fn(async (_url: string, init: RequestInit) => ({
          ok: true,
          status: 200,
          headers: new Headers({ "X-Request-ID": "body-request-id" }),
          json: () =>
            new Promise((_resolve, reject) => {
              init.signal!.addEventListener(
                "abort",
                () => reject(new DOMException("Aborted", "AbortError")),
                { once: true },
              );
            }),
        })),
      );
      const pending = (
        kind === "health" ? getHealth() : getSource("source-id")
      ).catch((error: unknown) => error);
      await vi.advanceTimersByTimeAsync(READ_CLIENT_TIMEOUT_MS);
      expect(await pending).toMatchObject({
        code: "timeout",
        requestId: "body-request-id",
      });
      expect(vi.getTimerCount()).toBe(0);
    },
  );

  it("propagates caller cancellation and clears the pending browser timeout", async () => {
    vi.useFakeTimers();
    const controller = new AbortController();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init: RequestInit) =>
          new Promise((_resolve, reject) => {
            init.signal!.addEventListener(
              "abort",
              () => reject(new DOMException("Aborted", "AbortError")),
              { once: true },
            );
          }),
      ),
    );
    const pending = askQuestion("question", {
      signal: controller.signal,
    }).catch((error: unknown) => error);
    controller.abort();
    expect(await pending).toMatchObject({
      code: "cancelled",
      requestId: expect.any(String),
    });
    expect(vi.getTimerCount()).toBe(0);
  });
});
