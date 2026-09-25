import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { AnswerView } from "@/components/answer-view";
import { ApiClientError } from "@/lib/api/errors";
import { getSource } from "@/lib/api/client";
import type { AskResponse, Citation, SourceResponse } from "@/lib/api/types";

vi.mock("@/lib/api/client", () => ({ getSource: vi.fn() }));

// Deliberately labelled test placeholders, never presented as legal source material.
const citation: Citation = {
  id: "S1",
  chunk_id: "test-placeholder-chunk",
  title: "Test placeholder source",
  locator: "Test locator",
  authority: "Test authority",
  jurisdiction: "IN",
  status: "in_force",
  source_url: "https://example.com/source",
  retrieved_at: "2026-09-25T00:00:00Z",
  quote: "Test placeholder passage.",
  section_heading: "Test heading",
};
const answer: AskResponse = {
  language: "en",
  answer_markdown: "> A safety note.\n\nTest placeholder explanation. [S1]",
  citations: [citation],
  warnings: ["Test transition note."],
  confidence: "medium",
  abstained: false,
  jurisdiction_note: "India · test coverage note",
  disclaimer: "Informational only. This is not legal advice.",
  trace_id: "test-request-id",
  provider: "ollama",
  model: "test-model",
  classification: { domain: "general", intent: "research", high_stakes: false },
  cached: false,
  latency_ms: 12300,
  explain: null,
};
const source: SourceResponse & { sampleData: boolean; requestId: string } = {
  chunk_id: citation.chunk_id,
  text: "Full test placeholder passage.\nSecond paragraph.",
  title: citation.title,
  locator: citation.locator,
  doc_type: "statute",
  authority: citation.authority,
  jurisdiction: "IN",
  status: "in_force",
  language: "en",
  source_url: citation.source_url,
  retrieved_at: citation.retrieved_at,
  licence: "Test licence",
  page_start: 3,
  page_end: 5,
  sampleData: true,
  requestId: "test-source-request",
};

beforeAll(() => {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    value: function (this: HTMLDialogElement) {
      this.setAttribute("open", "");
    },
  });
  Object.defineProperty(HTMLDialogElement.prototype, "close", {
    configurable: true,
    value: function (this: HTMLDialogElement) {
      this.removeAttribute("open");
    },
  });
});
beforeEach(() => {
  vi.mocked(getSource).mockReset();
});

describe("answer presentation", () => {
  it("renders an abstention as an explanation with the precise alternate sources heading", () => {
    const { container } = render(
      <AnswerView answer={{ ...answer, abstained: true, provider: null }} />,
    );
    expect(
      screen.getByRole("heading", { name: "More evidence is needed" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Closest provisions found (not confirmed to answer your question)",
      }),
    ).toBeInTheDocument();
    expect(container.querySelector(".answer-explanation")).toHaveTextContent(
      "Test placeholder explanation.",
    );
    expect(container.querySelector(".answer-markdown")).not.toBeInTheDocument();
    expect(screen.getAllByText(answer.disclaimer)).toHaveLength(1);
  });

  it("labels extractive and sample answers, shows repeal status prominently, and preserves safety notes", () => {
    const { container } = render(
      <AnswerView
        sampleData
        answer={{
          ...answer,
          provider: "extractive",
          citations: [{ ...citation, status: "repealed" }],
        }}
      />,
    );
    expect(
      screen.getByText("Verbatim source passages (no AI summary)"),
    ).toBeInTheDocument();
    expect(screen.getByText("Sample data")).toBeInTheDocument();
    expect(screen.getByText("Repealed")).toHaveAttribute(
      "data-status",
      "repealed",
    );
    expect(
      container.querySelector(".answer-markdown > blockquote"),
    ).toHaveTextContent("A safety note.");
    expect(screen.getByRole("region", { name: "Notes" })).toHaveTextContent(
      "Test transition note.",
    );
    expect(screen.getByText(answer.jurisdiction_note)).toBeInTheDocument();
  });

  it("moves focus and highlight to the exact source card and provides a keyboard-readable confidence explanation", () => {
    render(<AnswerView answer={answer} />);
    fireEvent.click(screen.getByRole("button", { name: "View source S1" }));
    const card = screen.getByRole("article", { name: /Source S1:/ });
    expect(card).toHaveFocus();
    expect(card).toHaveAttribute("data-highlighted", "true");
    const confidence = screen.getByRole("button", {
      name: "Medium confidence",
    });
    expect(confidence).toHaveAccessibleDescription(
      /How strongly the retrieved sources support this answer/,
    );
  });

  it("does not create a source link for a malformed URL", () => {
    render(
      <AnswerView
        answer={{
          ...answer,
          citations: [{ ...citation, source_url: "javascript:alert(1)" }],
        }}
      />,
    );
    expect(
      screen.queryByRole("link", { name: /Original source/ }),
    ).not.toBeInTheDocument();
  });
});

describe("full passage drawer", () => {
  it("loads full text and page range, traps focus, closes on Escape and restores the opener", async () => {
    vi.mocked(getSource).mockResolvedValue(source);
    render(<AnswerView answer={answer} />);
    const opener = screen.getByRole("button", { name: "Read full passage" });
    opener.focus();
    fireEvent.click(opener);
    expect(
      await screen.findByText(
        "Full test placeholder passage. Second paragraph.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Test locator · Pages 3–5")).toBeInTheDocument();
    const close = screen.getByRole("button", { name: "Close full passage" });
    expect(close).toHaveFocus();
    fireEvent.keyDown(close, { key: "Tab", shiftKey: true });
    expect(
      screen.getByRole("link", { name: /Open original source/ }),
    ).toHaveFocus();
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(opener).toHaveFocus();
  });

  it("shows an error request ID and can retry the source request", async () => {
    vi.mocked(getSource)
      .mockRejectedValueOnce(
        new ApiClientError(
          "unavailable",
          "Upstream message",
          "passage-error-id",
          503,
        ),
      )
      .mockResolvedValueOnce(source);
    render(<AnswerView answer={answer} />);
    fireEvent.click(screen.getByRole("button", { name: "Read full passage" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Still starting or offline, try again shortly.",
    );
    expect(
      screen.getByText("Request ID: passage-error-id"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(
      await screen.findByText(
        "Full test placeholder passage. Second paragraph.",
      ),
    ).toBeInTheDocument();
    expect(getSource).toHaveBeenCalledTimes(2);
  });

  it("cancels a pending source fetch when the drawer is dismissed", async () => {
    vi.mocked(getSource).mockImplementation(() => new Promise(() => {}));
    render(<AnswerView answer={answer} />);
    fireEvent.click(screen.getByRole("button", { name: "Read full passage" }));
    const signal = vi.mocked(getSource).mock.calls[0][1]?.signal;
    expect(signal?.aborted).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Cancel loading" }));
    await waitFor(() => expect(signal?.aborted).toBe(true));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
