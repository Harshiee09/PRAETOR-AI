import "server-only";

import type {
  AskResponse,
  Citation,
  HealthResponse,
  SourceResponse,
} from "@/lib/api/types";
import { isObject } from "./proxy";

function strings(value: Record<string, unknown>, fields: string[]): boolean {
  return fields.every((field) => typeof value[field] === "string");
}

function optionalStrings(
  value: Record<string, unknown>,
  fields: string[],
): boolean {
  return fields.every(
    (field) =>
      value[field] === undefined ||
      value[field] === null ||
      typeof value[field] === "string",
  );
}

export function isCitation(value: unknown): value is Citation {
  return (
    isObject(value) &&
    strings(value, [
      "id",
      "chunk_id",
      "title",
      "locator",
      "authority",
      "jurisdiction",
      "status",
      "source_url",
      "retrieved_at",
      "quote",
    ]) &&
    optionalStrings(value, [
      "section_heading",
      "court",
      "decision_date",
      "citation",
    ])
  );
}

export function isAskResponse(value: unknown): value is AskResponse {
  if (!isObject(value)) return false;
  return (
    strings(value, [
      "answer_markdown",
      "language",
      "jurisdiction_note",
      "disclaimer",
      "trace_id",
    ]) &&
    ["high", "medium", "low"].includes(value.confidence as string) &&
    typeof value.abstained === "boolean" &&
    Array.isArray(value.citations) &&
    value.citations.every(isCitation) &&
    Array.isArray(value.warnings) &&
    value.warnings.every((warning) => typeof warning === "string") &&
    (value.provider === null || typeof value.provider === "string") &&
    optionalStrings(value, ["model"]) &&
    isObject(value.classification) &&
    strings(value.classification, ["domain", "intent"]) &&
    typeof value.classification.high_stakes === "boolean" &&
    (value.cached === undefined || typeof value.cached === "boolean") &&
    typeof value.latency_ms === "number" &&
    Number.isInteger(value.latency_ms) &&
    (value.explain === undefined ||
      value.explain === null ||
      isObject(value.explain))
  );
}

export function isSourceResponse(value: unknown): value is SourceResponse {
  return (
    isObject(value) &&
    strings(value, [
      "chunk_id",
      "text",
      "title",
      "locator",
      "doc_type",
      "authority",
      "jurisdiction",
      "status",
      "language",
      "source_url",
      "retrieved_at",
      "licence",
    ]) &&
    optionalStrings(value, [
      "act_title",
      "section",
      "section_heading",
      "case_title",
      "court",
      "decision_date",
      "citation",
    ]) &&
    ["page_start", "page_end"].every(
      (field) =>
        value[field] === undefined ||
        value[field] === null ||
        (typeof value[field] === "number" && Number.isInteger(value[field])),
    )
  );
}

export function isHealthResponse(value: unknown): value is HealthResponse {
  return (
    isObject(value) &&
    ["ok", "degraded", "down"].includes(value.status as string) &&
    isObject(value.checks) &&
    Object.values(value.checks).every((check) => typeof check === "string")
  );
}
