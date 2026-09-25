import type { DocumentCitation, DocumentInfo, DocumentTask } from "@/lib/api/types";

export const DOCUMENT_DISCLAIMER = "PRAETOR explains what your document says. It does not decide whether the document is valid or enforceable, and it is not legal advice. For your situation, consult an advocate or your District Legal Services Authority (free legal aid).";
export const EXPIRED_MESSAGE = "This document has expired (documents are kept for 60 minutes). Upload it again.";
export const DOCUMENT_SESSION_KEY = "praetor-documents";
export type SavedDocument = Pick<DocumentInfo, "document_id" | "filename" | "expires_at">;
export const TASKS: { id: DocumentTask; label: string; title: string; description: string }[] = [
  { id: "ask", label: "Ask about this document", title: "Your document question", description: "Find a specific answer in the text." },
  { id: "summary", label: "Summarise in plain language", title: "Plain-language summary", description: "Understand the document's main points." },
  { id: "risks", label: "Key clauses, obligations and risks", title: "Key clauses, obligations and risks", description: "Review commitments, gaps and points to check." },
  { id: "checklist", label: "Make a checklist", title: "Checklist", description: "Turn the document into a practical reading list." },
  { id: "lawyer_questions", label: "Questions for a lawyer", title: "Questions for a lawyer", description: "Prepare questions grounded in the document." },
  { id: "compare", label: "Compare with another document", title: "Document comparison", description: "Read the differences between two documents." },
];

export function passageNumber(citation: Pick<DocumentCitation, "chunk_id">): number | null {
  const suffix = citation.chunk_id.slice(citation.chunk_id.lastIndexOf(":") + 1);
  return /^\d+$/.test(suffix) ? Number(suffix) : null;
}

export function quoteRange(text: string, quote: string): [number, number] | null {
  const positions: number[] = [];
  let normalized = "";
  for (let index = 0; index < text.length; index++) {
    const char = /\s/.test(text[index]) ? " " : text[index];
    if (char === " " && normalized.endsWith(" ")) continue;
    normalized += char;
    positions.push(index);
  }
  const search = quote.replace(/\s+/g, " ").trim();
  if (!search) return null;
  const offset = normalized.indexOf(search);
  return offset < 0 ? null : [positions[offset], positions[offset + search.length - 1] + 1];
}

export function readSavedDocuments(): (SavedDocument | null)[] {
  try {
    const value: unknown = JSON.parse(sessionStorage.getItem(DOCUMENT_SESSION_KEY) ?? "[]");
    if (!Array.isArray(value)) return [null, null];
    return [0, 1].map((index) => {
      const item = value[index];
      return item && typeof item.document_id === "string" && typeof item.filename === "string" && typeof item.expires_at === "string"
        ? { document_id: item.document_id, filename: item.filename, expires_at: item.expires_at } : null;
    });
  } catch { return [null, null]; }
}

export function persistDocuments(documents: (SavedDocument | null)[]) {
  try {
    const records = documents.map((document) => document ? { document_id: document.document_id, filename: document.filename, expires_at: document.expires_at } : null);
    if (records.some(Boolean)) sessionStorage.setItem(DOCUMENT_SESSION_KEY, JSON.stringify(records));
    else sessionStorage.removeItem(DOCUMENT_SESSION_KEY);
  } catch { /* The document remains usable in memory when tab storage is unavailable. */ }
}

export function pagesLabel(start?: number | null, end?: number | null) {
  if (start == null) return "";
  return end != null && end !== start ? `Pages ${start}–${end}` : `Page ${start}`;
}
