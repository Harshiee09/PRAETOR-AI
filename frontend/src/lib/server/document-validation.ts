import "server-only";
import { DOCUMENT_TASKS } from "@/lib/api/documents";
import type { DocumentAnalysis, DocumentDetail, DocumentInfo } from "@/lib/api/types";
import { isObject } from "./proxy";
import { isAskResponse } from "./validation";

const integer = (value: unknown) => typeof value === "number" && Number.isInteger(value) && value >= 0;
const strings = (value: unknown) => Array.isArray(value) && value.every((item) => typeof item === "string");
const numbers = (value: unknown) => Array.isArray(value) && value.every(integer);
const nullableNumber = (value: unknown) => value === undefined || value === null || integer(value);

export function isDocumentInfo(value: unknown): value is DocumentInfo {
  return isObject(value) && ["document_id", "filename", "uploaded_at", "expires_at"].every((key) => typeof value[key] === "string")
    && Number.isFinite(Date.parse(value.uploaded_at as string)) && Number.isFinite(Date.parse(value.expires_at as string))
    && ["pages", "passage_count", "words"].every((key) => integer(value[key])) && numbers(value.unreadable_pages) && strings(value.warnings);
}

export function isDocumentDetail(value: unknown): value is DocumentDetail {
  if (!isDocumentInfo(value)) return false;
  const record = value as unknown as Record<string, unknown>;
  return Array.isArray(record.passages) && record.passages.every((passage) => isObject(passage)
    && integer(passage.n) && typeof passage.locator === "string" && integer(passage.page_start) && integer(passage.page_end) && typeof passage.text === "string");
}

export function isDocumentAnalysis(value: unknown): value is DocumentAnalysis {
  if (!isAskResponse(value)) return false;
  const record = value as unknown as Record<string, unknown>;
  return DOCUMENT_TASKS.includes(record.task as DocumentAnalysis["task"])
    && typeof record.law_checked === "boolean" && Array.isArray(record.documents)
    && record.documents.every((document) => isObject(document) && typeof document.filename === "string" && typeof document.complete === "boolean" && (typeof document.pages_read === "string" || numbers(document.pages_read)))
    && (record.citations as unknown[]).every((citation) => isObject(citation) && ["document", "law"].includes(citation.kind as string)
      && (citation.kind !== "document" || typeof citation.document_id === "string") && nullableNumber(citation.page_start) && nullableNumber(citation.page_end));
}
