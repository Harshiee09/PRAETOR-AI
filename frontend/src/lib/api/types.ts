import type { components } from "./schema";
import type { components as DocumentComponents } from "./documents-schema";

export type AskResponse = components["schemas"]["AskResponse"];
export type Citation = components["schemas"]["Citation"];
export type SourceResponse = components["schemas"]["Source"];
export type HealthResponse = components["schemas"]["Health"];
export type ApiErrorEnvelope = components["schemas"]["Error"];
export type ApiResult<T> = T & { sampleData: boolean; requestId: string };
export type DocumentInfo = DocumentComponents["schemas"]["DocumentInfo"];
export type DocumentDetail = DocumentComponents["schemas"]["DocumentDetail"];
export type DocumentPassage = DocumentComponents["schemas"]["DocumentPassage"];
export type DocumentTask = DocumentComponents["schemas"]["DocumentTask"];
export type DocumentCitation = DocumentComponents["schemas"]["DocumentCitation"];
export type DocumentAnalysis = DocumentComponents["schemas"]["DocumentAnalysis"];
export type DocumentAnalysisRequest = DocumentComponents["schemas"]["DocumentAnalysisRequest"];
