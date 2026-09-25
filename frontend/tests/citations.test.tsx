import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AnswerMarkdown } from "@/components/answer-markdown";
import { parseCitationMarkers, safeExternalUrl } from "@/lib/citations";

describe("citation markers", () => {
  it("links only known complete markers while preserving unknown text and order", () => {
    expect(
      parseCitationMarkers("[S8] One [S1][S2]; [Sx].", new Set(["S1", "S2"])),
    ).toEqual([
      { type: "text", value: "[S8] One " },
      { type: "citation", value: "[S1]", id: "S1" },
      { type: "citation", value: "[S2]", id: "S2" },
      { type: "text", value: "; [Sx]." },
    ]);
  });

  it("handles nested Markdown, leaves code and link labels intact, and invokes the matching ID", () => {
    const onCitationClick = vi.fn();
    const markdown =
      "- A **strong [S1]** statement.\n  - An *emphasized [S2]* source.\n\nUnknown [S99].\n\n`[S1]`\n\n```text\n[S2]\n```\n\n[link [S1]](https://indiacode.nic.in/)";
    const { container } = render(
      <AnswerMarkdown
        markdown={markdown}
        citationIds={new Set(["S1", "S2"])}
        onCitationClick={onCitationClick}
      />,
    );
    expect(screen.getAllByRole("button")).toHaveLength(2);
    fireEvent.click(screen.getByRole("button", { name: "View source S2" }));
    expect(onCitationClick).toHaveBeenCalledWith("S2");
    expect(screen.getByText("Unknown [S99].")).toBeInTheDocument();
    expect(
      container.querySelector("strong .citation-chip"),
    ).toBeInTheDocument();
    expect(
      container.querySelector("li li em .citation-chip"),
    ).toBeInTheDocument();
    expect(container.querySelectorAll("code button")).toHaveLength(0);
    expect(screen.getByRole("link", { name: /link \[S1\]/ })).toHaveAttribute(
      "href",
      "https://indiacode.nic.in/",
    );
  });

  it("discards raw HTML, remote images and unsafe URLs without manufacturing citation buttons", () => {
    const markdown =
      '<script>alert("x")</script>\n\n<img src="https://example.com/pixel" onerror="alert(1)">\n\n![tracking pixel](https://example.com/pixel)\n\n[unsafe](javascript:alert%281%29) and [relative](/path) and [fake source](#citation-S1).';
    const { container } = render(
      <AnswerMarkdown
        markdown={markdown}
        citationIds={new Set(["S1"])}
        onCitationClick={vi.fn()}
      />,
    );
    expect(
      container.querySelector("script, img, iframe"),
    ).not.toBeInTheDocument();
    expect(container.querySelector("a")).not.toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.getByText("unsafe")).toBeInTheDocument();
    expect(screen.getByText("fake source")).toBeInTheDocument();
  });
});

describe("safe source URLs", () => {
  it.each([
    "javascript:alert(1)",
    "data:text/html,hello",
    "//example.com",
    "https://",
    "https://user:secret@example.com",
    "https://example.com\n.evil",
    "file:///etc/passwd",
  ])("rejects %s", (url) => {
    expect(safeExternalUrl(url)).toBeUndefined();
  });

  it("preserves an absolute HTTP(S) source including its locator", () => {
    expect(
      safeExternalUrl("https://indiacode.nic.in/handle/123?x=1#section"),
    ).toBe("https://indiacode.nic.in/handle/123?x=1#section");
    expect(safeExternalUrl("http://example.com")).toBe("http://example.com/");
  });
});
