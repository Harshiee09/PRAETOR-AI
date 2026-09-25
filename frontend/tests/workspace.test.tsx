import {
  act,
  createEvent,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ResearchProvider, useResearch } from "@/components/research-provider";
import { ResearchWorkspace } from "@/components/research-workspace";
import { askQuestion, getHealth } from "@/lib/api/client";
import { ApiClientError } from "@/lib/api/errors";
import type { ApiResult, AskResponse, HealthResponse } from "@/lib/api/types";

vi.mock("@/lib/api/client", () => ({
  askQuestion: vi.fn(),
  getHealth: vi.fn(),
}));
vi.mock("@/components/answer-view", () => ({
  AnswerView: ({
    answer,
    sampleData,
  }: {
    answer: AskResponse;
    sampleData: boolean;
  }) => (
    <div data-testid="answer-view" data-sample={String(sampleData)}>
      {answer.answer_markdown}
    </div>
  ),
}));

const response: ApiResult<AskResponse> = {
  answer_markdown: "Test-only research response.",
  language: "en",
  citations: [],
  warnings: [],
  confidence: "low",
  abstained: false,
  jurisdiction_note: "Test coverage note.",
  disclaimer: "Test-only disclaimer.",
  trace_id: "test-ask-request",
  provider: "extractive",
  model: null,
  classification: { domain: "general", intent: "research", high_stakes: false },
  cached: false,
  latency_ms: 1000,
  explain: null,
  sampleData: false,
  requestId: "test-ask-request",
};
const healthy: ApiResult<HealthResponse> = {
  status: "ok",
  checks: {},
  sampleData: false,
  requestId: "test-health-request",
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((complete) => {
    resolve = complete;
  });
  return { promise, resolve };
}

function HistoryControls() {
  const research = useResearch();
  return (
    <>
      <button onClick={research.newResearch}>New research test control</button>
      <ol aria-label="Session history">
        {research.entries.map((entry) => (
          <li key={entry.id}>
            <button onClick={() => research.select(entry.id)}>
              {entry.question}
            </button>
          </li>
        ))}
      </ol>
    </>
  );
}

function renderWorkspace() {
  return render(
    <ResearchProvider>
      <ResearchWorkspace />
      <HistoryControls />
    </ResearchProvider>,
  );
}

async function readyWorkspace() {
  const view = renderWorkspace();
  await waitFor(() => expect(screen.getByRole("textbox")).toBeEnabled());
  return view;
}

function enterQuestion(question: string) {
  fireEvent.change(screen.getByRole("textbox"), {
    target: { value: question },
  });
}

beforeEach(() => {
  vi.mocked(getHealth).mockReset().mockResolvedValue(healthy);
  vi.mocked(askQuestion).mockReset().mockResolvedValue(response);
});
afterEach(() => {
  vi.useRealTimers();
});

describe("research submission", () => {
  it("preserves Shift+Enter and IME composition, then permits exactly one in-flight Enter submission", async () => {
    const pending = deferred<ApiResult<AskResponse>>();
    vi.mocked(askQuestion).mockReturnValue(pending.promise);
    await readyWorkspace();
    enterQuestion("  अनुबंध क्या है?  ");
    const textarea = screen.getByRole("textbox");
    for (const options of [
      { shiftKey: true },
      { isComposing: true },
      { keyCode: 229 },
    ]) {
      const event = createEvent.keyDown(textarea, {
        key: "Enter",
        code: "Enter",
        ...options,
      });
      fireEvent(textarea, event);
      expect(event.defaultPrevented).toBe(false);
    }
    expect(askQuestion).not.toHaveBeenCalled();

    fireEvent.keyDown(textarea, { key: "Enter", code: "Enter" });
    // A second submission can also originate from a form event before React settles.
    fireEvent.submit(textarea.closest("form")!);
    expect(askQuestion).toHaveBeenCalledTimes(1);
    expect(askQuestion).toHaveBeenCalledWith("अनुबंध क्या है?", {
      signal: expect.any(AbortSignal),
    });
    expect(textarea).toBeDisabled();
    expect(screen.getByRole("button", { name: "Researching" })).toBeDisabled();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Searching and checking sources…",
    );

    await act(async () => {
      pending.resolve(response);
    });
    expect(screen.getByRole("textbox")).toHaveValue("");
    expect(
      screen.getByText(
        "Research complete. Your answer and citations are available below.",
      ),
    ).toHaveAttribute("aria-live", "polite");
    expect(
      screen.getByTestId("answer-view").closest(".research-result"),
    ).toHaveFocus();
  });

  it("counts Unicode code points and blocks oversized or blank requests, including direct form submissions", async () => {
    await readyWorkspace();
    const textarea = screen.getByRole("textbox");
    const exactLimit = "क".repeat(1999) + "😀";
    enterQuestion(exactLimit);
    expect(screen.getByText("2,000 / 2,000")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Research question" }),
    ).toBeEnabled();
    expect(textarea).toHaveAttribute("aria-invalid", "false");

    enterQuestion(exactLimit + "अ");
    expect(screen.getByText("2,001 / 2,000")).toBeInTheDocument();
    expect(textarea).toHaveAttribute("aria-invalid", "true");
    expect(
      screen.getByText(
        "Please keep your question to 2,000 characters or fewer.",
      ),
    ).toHaveAttribute("aria-live", "polite");
    expect(
      screen.getByRole("button", { name: "Research question" }),
    ).toBeDisabled();
    fireEvent.submit(textarea.closest("form")!);
    enterQuestion(" \n\t ");
    fireEvent.submit(textarea.closest("form")!);
    expect(askQuestion).not.toHaveBeenCalled();

    enterQuestion(exactLimit);
    fireEvent.click(screen.getByRole("button", { name: "Research question" }));
    await screen.findByTestId("answer-view");
    expect(askQuestion).toHaveBeenCalledWith(exactLimit, {
      signal: expect.any(AbortSignal),
    });
  });

  it("retains in-tab history and Clear aborts requests without allowing late responses to restore erased research", async () => {
    await readyWorkspace();
    enterQuestion("First test question");
    fireEvent.click(screen.getByRole("button", { name: "Research question" }));
    await screen.findByTestId("answer-view");
    expect(
      within(screen.getByRole("list", { name: "Session history" })).getByRole(
        "button",
        { name: "First test question" },
      ),
    ).toBeInTheDocument();

    const oldRequest = deferred<ApiResult<AskResponse>>();
    const newRequest = deferred<ApiResult<AskResponse>>();
    vi.mocked(askQuestion)
      .mockReturnValueOnce(oldRequest.promise)
      .mockReturnValueOnce(newRequest.promise);
    fireEvent.click(
      screen.getByRole("button", { name: "New research test control" }),
    );
    expect(screen.queryByTestId("answer-view")).not.toBeInTheDocument();
    // Selecting history restores the saved answer without another network request.
    fireEvent.click(
      within(screen.getByRole("list", { name: "Session history" })).getByRole(
        "button",
        { name: "First test question" },
      ),
    );
    expect(screen.getByTestId("answer-view")).toBeInTheDocument();
    expect(askQuestion).toHaveBeenCalledTimes(1);
    fireEvent.click(
      screen.getByRole("button", { name: "New research test control" }),
    );
    enterQuestion("Erased pending test question");
    fireEvent.click(screen.getByRole("button", { name: "Research question" }));
    const oldSignal = vi.mocked(askQuestion).mock.calls[1][1]?.signal;
    fireEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(oldSignal?.aborted).toBe(true);
    expect(
      screen.getByRole("list", { name: "Session history" }),
    ).toBeEmptyDOMElement();
    expect(screen.getByRole("textbox")).toHaveValue("");
    expect(screen.queryByTestId("answer-view")).not.toBeInTheDocument();

    enterQuestion("New test question");
    fireEvent.click(screen.getByRole("button", { name: "Research question" }));
    await act(async () => {
      oldRequest.resolve({
        ...response,
        answer_markdown: "Erased late answer",
      });
    });
    expect(screen.getByRole("button", { name: "Researching" })).toBeDisabled();
    expect(screen.queryByText("Erased late answer")).not.toBeInTheDocument();
    await act(async () => {
      newRequest.resolve({ ...response, answer_markdown: "New answer" });
    });
    expect(screen.getByTestId("answer-view")).toHaveTextContent("New answer");
    expect(
      within(
        screen.getByRole("list", { name: "Session history" }),
      ).getAllByRole("button"),
    ).toHaveLength(1);
  });

  it("exposes a plain-language request failure with its log correlation ID", async () => {
    vi.mocked(askQuestion).mockRejectedValueOnce(
      new ApiClientError(
        "timeout",
        "Private upstream detail",
        "test-timeout-request",
      ),
    );
    await readyWorkspace();
    enterQuestion("Test timeout question");
    fireEvent.click(screen.getByRole("button", { name: "Research question" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "This took too long; try again.",
    );
    expect(screen.getByRole("alert")).toHaveTextContent("test-timeout-request");
    expect(
      screen.queryByText("Private upstream detail"),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveValue("Test timeout question");
    expect(
      screen.getByRole("button", { name: "Research question" }),
    ).toBeEnabled();
  });
});

describe("service state and announcements", () => {
  it("polls every 60 seconds, permits degraded research, disables offline research and stops polling on unmount", async () => {
    vi.useFakeTimers();
    const view = renderWorkspace();
    expect(screen.getByRole("textbox")).toBeDisabled();
    await act(async () => {});
    expect(getHealth).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("textbox")).toBeEnabled();

    vi.mocked(getHealth).mockResolvedValueOnce({
      ...healthy,
      status: "degraded",
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(59_999);
    });
    expect(getHealth).toHaveBeenCalledTimes(1);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(getHealth).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Answers are limited to verbatim source passages.",
    );
    expect(screen.getByRole("textbox")).toBeEnabled();

    vi.mocked(getHealth).mockResolvedValueOnce({
      ...healthy,
      status: "down",
      requestId: "offline-health-id",
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60_000);
    });
    expect(screen.getByRole("status")).toHaveTextContent(
      "The research service is offline",
    );
    expect(screen.getByRole("status")).toHaveTextContent("offline-health-id");
    expect(screen.getByRole("textbox")).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Research question" }),
    ).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await act(async () => {});
    expect(screen.getByRole("textbox")).toBeEnabled();
    expect(getHealth).toHaveBeenCalledTimes(4);
    const signal = vi.mocked(getHealth).mock.calls.at(-1)?.[0]?.signal;
    view.unmount();
    expect(signal?.aborted).toBe(true);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60_000);
    });
    expect(getHealth).toHaveBeenCalledTimes(4);
  });

  it("treats an unreachable service as offline and exposes the failed health request ID", async () => {
    vi.mocked(getHealth).mockRejectedValueOnce(
      new ApiClientError("network_error", "Network failed", "unreachable-id"),
    );
    renderWorkspace();
    expect(await screen.findByRole("status")).toHaveTextContent(
      "The research service is offline",
    );
    expect(screen.getByRole("status")).toHaveTextContent("unreachable-id");
    expect(screen.getByRole("textbox")).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Research question" }),
    ).toBeDisabled();
  });

  it("labels sample output and announces an abstention without claiming an answer was generated", async () => {
    vi.mocked(getHealth).mockResolvedValueOnce({
      ...healthy,
      sampleData: true,
    });
    vi.mocked(askQuestion).mockResolvedValueOnce({
      ...response,
      sampleData: true,
      abstained: true,
      provider: null,
    });
    await readyWorkspace();
    expect(screen.getByRole("status")).toHaveTextContent("Sample data");
    expect(screen.getByRole("status")).toHaveTextContent(
      "No live legal research is being performed.",
    );
    enterQuestion("Sample test question");
    fireEvent.click(screen.getByRole("button", { name: "Research question" }));
    expect(await screen.findByTestId("answer-view")).toHaveAttribute(
      "data-sample",
      "true",
    );
    const announcement = screen.getByText(
      "Research complete. The sources were insufficient to answer this question.",
    );
    expect(announcement).toHaveAttribute("aria-live", "polite");
    expect(announcement).toHaveAttribute("aria-atomic", "true");
    expect(
      screen.queryByText(
        "Research complete. Your answer and citations are available below.",
      ),
    ).not.toBeInTheDocument();
  });
});
