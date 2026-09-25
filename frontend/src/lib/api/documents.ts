import { countQuestionCharacters, normalizeQuestion, questionValidationMessage } from "./question";
import type { DocumentAnalysisRequest, DocumentTask } from "./types";

export const MAX_PDF_BYTES = 4 * 1024 * 1024;
export const DOCUMENT_TASKS: DocumentTask[] = ["ask", "summary", "risks", "checklist", "lawyer_questions", "compare"];
export const DOCUMENT_EXPIRED_MESSAGE = "This document has expired (documents are kept for 60 minutes). Upload it again.";

export function validatePdfFile(file: Pick<File, "size" | "type">): string | null {
  if (file.type !== "application/pdf") return "Only PDF files can be uploaded";
  if (file.size > MAX_PDF_BYTES) return "Upload a PDF up to 4 MB.";
  if (file.size === 0) return "This PDF is empty. Upload a PDF with text or a clear scan.";
  return null;
}

export function isDocumentId(id: unknown): id is string {
  return typeof id === "string" && id.length > 0 && id.length <= 512 && id !== "." && id !== ".." && !/[\u0000-\u001f\u007f]/.test(id);
}

export function validateDocumentAnalysis(input: unknown): { data: DocumentAnalysisRequest; error?: never } | { data?: never; error: string } {
  if (!input || typeof input !== "object" || Array.isArray(input)) return { error: "Choose a document task." };
  const value = input as Record<string, unknown>;
  if (!DOCUMENT_TASKS.includes(value.task as DocumentTask)) return { error: "Choose a document task." };
  const task = value.task as DocumentTask;
  const ids = value.document_ids;
  if (!Array.isArray(ids) || ids.length !== (task === "compare" ? 2 : 1) || !ids.every(isDocumentId)) return { error: task === "compare" ? "Upload two documents to compare." : "Upload one document for this task." };
  if (task === "compare" && ids[0] === ids[1]) return { error: "Choose two different documents to compare." };
  if (value.question !== undefined && value.question !== null && typeof value.question !== "string") return { error: "Enter a question or focus as text." };
  const question = typeof value.question === "string" ? normalizeQuestion(value.question) : null;
  if (task === "ask") {
    const invalid = questionValidationMessage(question);
    if (invalid) return { error: invalid };
  } else if (question && countQuestionCharacters(question) > 2000) return { error: "Keep your question to 2,000 characters or fewer." };
  return { data: { document_ids: ids, task, question: question || null } };
}
