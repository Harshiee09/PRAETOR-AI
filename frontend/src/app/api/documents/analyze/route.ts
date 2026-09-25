import { DOCUMENT_EXPIRED_MESSAGE, validateDocumentAnalysis } from "@/lib/api/documents";
import { sampleDocumentAnalysis } from "@/lib/server/document-samples";
import { isDocumentAnalysis } from "@/lib/server/document-validation";
import { ASK_TIMEOUT_MS, errorResponse, isDevelopmentMock, jsonResponse, proxyRequest, requestIdFor } from "@/lib/server/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

export async function POST(request: Request): Promise<Response> {
  const requestId = requestIdFor(request);
  let body: unknown;
  try { body = await request.json(); } catch { return errorResponse("invalid_request", "Send a document task as valid JSON.", requestId, 422); }
  const validated = validateDocumentAnalysis(body);
  if (validated.error) return errorResponse("invalid_request", validated.error, requestId, 422);
  if (isDevelopmentMock()) {
    const result = sampleDocumentAnalysis(validated.data!, requestId);
    return result ? jsonResponse(result, requestId, 200, true) : errorResponse("not_found", DOCUMENT_EXPIRED_MESSAGE, requestId, 404);
  }
  return proxyRequest(request, requestId, { path: "/v1/documents/analyze", method: "POST", body: validated.data, timeoutMs: ASK_TIMEOUT_MS, validate: isDocumentAnalysis });
}
