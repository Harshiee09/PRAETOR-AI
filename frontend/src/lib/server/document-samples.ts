import "server-only";
import { randomUUID } from "node:crypto";
import type { DocumentAnalysis, DocumentAnalysisRequest, DocumentDetail, DocumentInfo } from "@/lib/api/types";
import { sampleAnswer } from "./samples";

// Metadata only: the development placeholder never stores or parses PDF bytes.
const state = globalThis as typeof globalThis & { __praetorDocumentSamples?: Map<string, DocumentInfo> };
function records(): Map<string, DocumentInfo> {
  const documents = state.__praetorDocumentSamples ??= new Map();
  for (const [id, info] of documents) if (Date.parse(info.expires_at) <= Date.now()) documents.delete(id);
  return documents;
}

export function sampleDocumentUpload(filename: string): DocumentInfo {
  const now = Date.now();
  const info: DocumentInfo = { document_id: `sample-${randomUUID()}`, filename, pages: 0, unreadable_pages: [], passage_count: 0, words: 0, uploaded_at: new Date(now).toISOString(), expires_at: new Date(now + 60 * 60 * 1000).toISOString(), warnings: ["Sample data — this PDF has not been parsed or retained. Connect the backend to read its pages."] };
  const documents = records();
  if (documents.size >= 100) documents.delete(documents.keys().next().value!);
  documents.set(info.document_id, info);
  return info;
}

export function sampleDocumentGet(id: string): DocumentDetail | undefined {
  const info = records().get(id);
  return info ? { ...info, passages: [] } : undefined;
}

export function sampleDocumentForget(id: string): boolean {
  return records().delete(id);
}

export function sampleDocumentAnalysis(input: DocumentAnalysisRequest, requestId: string): DocumentAnalysis | undefined {
  const documents = input.document_ids.map(sampleDocumentGet);
  if (documents.some((document) => !document)) return undefined;
  return { ...sampleAnswer(requestId), answer_markdown: "Sample data — no document analysis was performed.\n\nThe PDF was not read in this development preview. Connect the research backend to extract passages, check citations, and run this task.\n\nJurisdiction and date: no law or date was checked in this sample.", warnings: ["Sample data — uploaded files are not parsed in this preview.", "Law cross-check skipped: the backend is not connected."], task: input.task, citations: [], documents: documents.map((document) => ({ filename: document!.filename, pages_read: [], complete: false })), law_checked: false };
}
