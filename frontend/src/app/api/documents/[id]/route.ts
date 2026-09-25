import { DOCUMENT_EXPIRED_MESSAGE, isDocumentId } from "@/lib/api/documents";
import { sampleDocumentForget, sampleDocumentGet } from "@/lib/server/document-samples";
import { isDocumentDetail } from "@/lib/server/document-validation";
import { errorResponse, isDevelopmentMock, jsonResponse, proxyRequest, requestIdFor } from "@/lib/server/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
type Context = { params: Promise<{ id: string }> };

export async function GET(request: Request, context: Context): Promise<Response> {
  const requestId = requestIdFor(request);
  const { id } = await context.params;
  if (!isDocumentId(id)) return errorResponse("invalid_request", "The document identifier is invalid.", requestId, 422);
  if (isDevelopmentMock()) {
    const document = sampleDocumentGet(id);
    return document ? jsonResponse(document, requestId, 200, true) : errorResponse("not_found", DOCUMENT_EXPIRED_MESSAGE, requestId, 404);
  }
  return proxyRequest(request, requestId, { path: `/v1/documents/${encodeURIComponent(id)}`, validate: isDocumentDetail });
}

export async function DELETE(request: Request, context: Context): Promise<Response> {
  const requestId = requestIdFor(request);
  const { id } = await context.params;
  if (!isDocumentId(id)) return errorResponse("invalid_request", "The document identifier is invalid.", requestId, 422);
  if (isDevelopmentMock()) {
    if (!sampleDocumentForget(id)) return errorResponse("not_found", DOCUMENT_EXPIRED_MESSAGE, requestId, 404);
    return new Response(null, { status: 204, headers: { "Cache-Control": "no-store", "X-Request-ID": requestId, "X-Praetor-Sample": "1" } });
  }
  return proxyRequest(request, requestId, { path: `/v1/documents/${encodeURIComponent(id)}`, method: "DELETE", allowNoContent: true, validate: () => false });
}
