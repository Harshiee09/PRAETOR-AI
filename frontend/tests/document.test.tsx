import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { ResearchProvider } from "@/components/research-provider";
import { DocumentWorkspace } from "@/components/document/document-workspace";
import { DocumentResult } from "@/components/document/document-result";
import { PassageDrawer } from "@/components/document/passage-drawer";
import { DOCUMENT_DISCLAIMER, DOCUMENT_SESSION_KEY, EXPIRED_MESSAGE, passageNumber, quoteRange } from "@/components/document/utils";
import { analyzeDocuments, getDocument, getHealth, uploadDocument, forgetDocument } from "@/lib/api/client";
import { ApiClientError } from "@/lib/api/errors";
import { MAX_PDF_BYTES, validatePdfFile } from "@/lib/api/documents";
import type { ApiResult, DocumentAnalysis, DocumentCitation, DocumentDetail, DocumentInfo, DocumentTask } from "@/lib/api/types";

vi.mock("@/lib/api/client", () => ({ askQuestion: vi.fn(), getHealth: vi.fn(), uploadDocument: vi.fn(), getDocument: vi.fn(), forgetDocument: vi.fn(), analyzeDocuments: vi.fn(), getSource: vi.fn() }));

// These are UI-test placeholders, not purported legal excerpts or backend examples.
const info = (id = "test-a", filename = "Test document A.pdf"): ApiResult<DocumentInfo> => ({ document_id: id, filename, pages: 3, unreadable_pages: [2], passage_count: 2, words: 120, uploaded_at: new Date().toISOString(), expires_at: new Date(Date.now() + 60 * 60_000).toISOString(), warnings: ["Test note about an unreadable page."], requestId: "test-upload-request", sampleData: true });
const documentCitation: DocumentCitation = { id: "D14", chunk_id: "test-a:25", title: "Test document A.pdf", locator: "Test clause · p. 3", authority: "Uploaded by you", jurisdiction: "n/a", status: "n/a", source_url: "", retrieved_at: "2026-09-25T00:00:00Z", quote: "A test passage with collapsed whitespace.", kind: "document", document_id: "test-a", page_start: 3, page_end: 3 };
const detail = (): ApiResult<DocumentDetail> => ({ ...info(), passages: [{ n: 14, locator: "Wrong passage for D14", page_start: 1, page_end: 1, text: "Another test passage." }, { n: 25, locator: "Correct passage for D14", page_start: 3, page_end: 3, text: "Before. A test\n passage with\t collapsed whitespace. After." }] });
const analysis = (task: DocumentTask = "summary"): ApiResult<DocumentAnalysis> => ({ answer_markdown: "**Test heading:**\n\nA test explanation. [D14]", language: "en", citations: [documentCitation], warnings: ["Test document is longer than one analysis can read; only pages 1 and 3 were read."], confidence: "low", abstained: false, jurisdiction_note: "Test document coverage.", disclaimer: DOCUMENT_DISCLAIMER, trace_id: "test-analysis-id", provider: "extractive", model: null, classification: { domain: "general", intent: "research", high_stakes: false }, cached: false, latency_ms: 1000, task, documents: [{ filename: "Test document A.pdf", pages_read: [1, 3], complete: false }], law_checked: false, sampleData: true, requestId: "test-analysis-id" });

beforeAll(() => {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } });
  Object.defineProperty(HTMLDialogElement.prototype, "close", { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } });
});
beforeEach(() => {
  sessionStorage.clear();
  vi.mocked(getHealth).mockReset().mockResolvedValue({ status: "down", checks: { documents: "ok" }, sampleData: false, requestId: "test-health-id" });
  vi.mocked(uploadDocument).mockReset().mockResolvedValue(info());
  vi.mocked(getDocument).mockReset().mockResolvedValue(detail());
  vi.mocked(forgetDocument).mockReset().mockResolvedValue(undefined);
  vi.mocked(analyzeDocuments).mockReset().mockImplementation(async (request) => analysis(request.task));
});
afterEach(() => { vi.useRealTimers(); });

async function workspace() {
  const view = render(<ResearchProvider><DocumentWorkspace /></ResearchProvider>);
  await waitFor(() => expect(screen.getByLabelText("Upload Document A")).toBeEnabled());
  return view;
}
async function uploadA() {
  fireEvent.change(screen.getByLabelText("Upload Document A"), { target: { files: [new File(["%PDF-test"], "Test document A.pdf", { type: "application/pdf" })] } });
  await screen.findByRole("button", { name: "View text of Document A" });
}

describe("document upload guards", () => {
  it("accepts PDF at 4 MB but rejects non-PDF and larger files", () => {
    expect(validatePdfFile({ type: "application/pdf", size: MAX_PDF_BYTES })).toBeNull();
    expect(validatePdfFile({ type: "application/pdf", size: MAX_PDF_BYTES + 1 })).toMatch(/4 MB/);
    expect(validatePdfFile({ type: "text/plain", size: 100 })).toBe("Only PDF files can be uploaded");
  });
  it("rejects a 5 MB selection and non-PDF drop before a network call", async () => {
    const { container } = await workspace();
    const large = new File([new Uint8Array(5 * 1024 * 1024)], "large.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText("Upload Document A"), { target: { files: [large] } });
    expect(screen.getByRole("alert")).toHaveTextContent("4 MB");
    fireEvent.drop(container.querySelector(".document-dropzone")!, { dataTransfer: { files: [new File(["text"], "fake.pdf", { type: "text/plain" })] } });
    expect(screen.getByRole("alert")).toHaveTextContent("Only PDF files can be uploaded");
    expect(uploadDocument).not.toHaveBeenCalled();
  });
});

describe("document evidence rendering", () => {
  it("resolves D14 to passage n=25 and highlights collapsed-whitespace quotes", () => {
    expect(passageNumber(documentCitation)).toBe(25);
    const text = detail().passages[1].text;
    const range = quoteRange(text, documentCitation.quote)!;
    expect(text.slice(...range)).toBe("A test\n passage with\t collapsed whitespace.");
    const { container } = render(<PassageDrawer detail={detail()} citation={documentCitation} onClose={vi.fn()}/>);
    expect(container.querySelector("[data-selected='true']")).toHaveTextContent("Correct passage for D14");
    expect(container.querySelector("mark")).toHaveTextContent(documentCitation.quote);
  });
  it("renders real checklist checkboxes, task headings, pages read, and copy/print controls", () => {
    const answer = { ...analysis("checklist"), answer_markdown: "**Checklist:**\n\n- [ ] Read the test clause. [D14]\n- [ ] Prepare a question." };
    render(<DocumentResult result={{ answer, question: "", sampleData: true, documents: [info()] }} onPassage={vi.fn()}/>);
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes).toHaveLength(2);
    expect(checkboxes[0]).toBeEnabled();
    expect(checkboxes[0]).toHaveAccessibleName(/Read the test clause/);
    fireEvent.click(checkboxes[0]);
    expect(checkboxes[0]).toBeChecked();
    expect(checkboxes[1]).not.toBeChecked();
    expect(screen.getByRole("heading", { name: "Checklist:", level: 3 })).toBeInTheDocument();
    expect(screen.getByText("Test document A.pdf: pages 1, 3 (part of the document)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy as text" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Print" })).toBeInTheDocument();
    expect(screen.getByText("The passages themselves (no AI summary)")).toBeInTheDocument();
    expect(screen.queryByText("Judgment")).not.toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
  it("labels comparison chips and cards with A/B independently of their numeric marker", () => {
    const b = { ...documentCitation, id: "D2", chunk_id: "test-b:7", document_id: "test-b", title: "Test document B.pdf" };
    const answer = { ...analysis("compare"), answer_markdown: "Document A [D14] and Document B [D2]. Unknown [D99].", citations: [documentCitation, b] };
    render(<DocumentResult result={{ answer, question: "", sampleData: false, documents: [info(), info("test-b", "Test document B.pdf")] }} onPassage={vi.fn()}/>);
    expect(screen.getByRole("button", { name: "View source D14, Document A" })).toHaveAttribute("data-document", "A");
    expect(screen.getByRole("button", { name: "View source D2, Document B" })).toHaveAttribute("data-document", "B");
    const card = screen.getByRole("article", { name: "Source D2: Document B" });
    expect(card).toHaveAttribute("data-document", "B");
    fireEvent.click(screen.getByRole("button", { name: "View source D2, Document B" }));
    expect(card).toHaveFocus();
    expect(card).toHaveAttribute("data-highlighted", "true");
    expect(screen.getByText(/Unknown \[D99\]/)).toBeInTheDocument();
  });
  it.each(["ask", "summary", "risks", "checklist", "lawyer_questions", "compare"] as DocumentTask[])("renders the %s response without changing evidence text", (task) => {
    const answer = analysis(task);
    render(<DocumentResult result={{ answer, question: "A test question", sampleData: true, documents: [info(), info("test-b", "Test document B.pdf")] }} onPassage={vi.fn()}/>);
    expect(screen.getByText("Sample data")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "View source D14, Document A" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Notes" })).toHaveTextContent(answer.warnings[0]);
  });
});

describe("document workflow", () => {
  it("works while library health is down, persists only metadata, caches passages, and confirms forgetting", async () => {
    await workspace();
    await uploadA();
    expect(screen.queryByText("The document research service is offline")).not.toBeInTheDocument();
    expect(screen.getByText(/Expires in 60 min/)).toBeInTheDocument();
    expect(screen.getByText("Unreadable pages: 2")).toBeInTheDocument();
    const stored = JSON.parse(sessionStorage.getItem(DOCUMENT_SESSION_KEY)!);
    expect(Object.keys(stored[0]).sort()).toEqual(["document_id", "expires_at", "filename"]);
    fireEvent.click(screen.getByRole("button", { name: "View text of Document A" }));
    await screen.findByRole("dialog");
    fireEvent.click(screen.getByRole("button", { name: "Close Your document text" }));
    fireEvent.click(screen.getByRole("button", { name: "View text of Document A" }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(getDocument).toHaveBeenCalledTimes(1);
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    fireEvent.click(screen.getByRole("button", { name: "Forget this document A" }));
    expect(forgetDocument).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Keep document" }));
    expect(forgetDocument).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Forget this document A" }));
    fireEvent.click(screen.getByRole("button", { name: "Forget document", exact: true } as never));
    await waitFor(() => expect(screen.getByLabelText("Upload Document A")).toBeInTheDocument());
    expect(forgetDocument).toHaveBeenCalledWith("test-a", { signal: expect.any(AbortSignal) });
    expect(sessionStorage.getItem(DOCUMENT_SESSION_KEY)).toBeNull();
  });
  it("sends each task and optional focus, then cancels an analysis without showing its late result", async () => {
    await workspace(); await uploadA();
    fireEvent.click(screen.getByRole("button", { name: /Summarise in plain language/ }));
    fireEvent.change(screen.getByLabelText("Anything to focus on? (optional)"), { target: { value: " payments " } });
    fireEvent.click(screen.getByRole("button", { name: "Read my document" }));
    await screen.findByRole("heading", { name: "Plain-language summary" });
    expect(analyzeDocuments).toHaveBeenCalledWith({ document_ids: ["test-a"], task: "summary", question: "payments" }, { signal: expect.any(AbortSignal) });
    expect(screen.getAllByText(DOCUMENT_DISCLAIMER)).toHaveLength(1);
    let resolve!: (value: ApiResult<DocumentAnalysis>) => void;
    vi.mocked(analyzeDocuments).mockReturnValueOnce(new Promise((complete) => { resolve = complete; }));
    fireEvent.click(screen.getByRole("button", { name: /Key clauses, obligations and risks/ }));
    fireEvent.click(screen.getByRole("button", { name: "Read my document" }));
    expect(screen.getByText("Reading your document and checking every citation…")).toBeInTheDocument();
    const signal = vi.mocked(analyzeDocuments).mock.calls.at(-1)?.[1]?.signal;
    fireEvent.click(screen.getByRole("button", { name: "Cancel wait" }));
    expect(signal?.aborted).toBe(true);
    await act(async () => { resolve({ ...analysis("risks"), answer_markdown: "This cancelled result must stay hidden." }); });
    expect(screen.queryByText("This cancelled result must stay hidden.")).not.toBeInTheDocument();
  });
  it("restores passages after reload and removes expired metadata on a 404", async () => {
    sessionStorage.setItem(DOCUMENT_SESSION_KEY, JSON.stringify([{ document_id: "test-a", filename: "Test document A.pdf", expires_at: info().expires_at }, null]));
    // a restored document shows its file card, not the upload control, so wait for the card
    render(<ResearchProvider><DocumentWorkspace /></ResearchProvider>);
    await screen.findByRole("button", { name: "View text of Document A" });
    expect(getDocument).toHaveBeenCalledTimes(1);
    vi.mocked(analyzeDocuments).mockRejectedValueOnce(new ApiClientError("not_found", "Not found", "expired-request", 404));
    fireEvent.click(screen.getByRole("button", { name: /Summarise in plain language/ }));
    fireEvent.click(screen.getByRole("button", { name: "Read my document" }));
    await waitFor(() => expect(screen.getByLabelText("Upload Document A")).toBeInTheDocument());
    expect(screen.getAllByText(EXPIRED_MESSAGE).length).toBeGreaterThan(0);
    expect(screen.getByText("Request ID: expired-request")).toBeInTheDocument();
    expect(sessionStorage.getItem(DOCUMENT_SESSION_KEY)).toBeNull();
  });
});
