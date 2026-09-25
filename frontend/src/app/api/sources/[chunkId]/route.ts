import { isSourceResponse } from "@/lib/server/validation";
import {
  errorResponse,
  isDevelopmentMock,
  proxyRequest,
  requestIdFor,
} from "@/lib/server/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(
  request: Request,
  context: { params: Promise<{ chunkId: string }> },
): Promise<Response> {
  const requestId = requestIdFor(request);
  const { chunkId } = await context.params;
  if (
    !chunkId ||
    chunkId === "." ||
    chunkId === ".." ||
    chunkId.length > 512 ||
    /[\u0000-\u001f\u007f]/.test(chunkId)
  )
    return errorResponse(
      "invalid_request",
      "The source identifier is invalid.",
      requestId,
      422,
    );
  if (isDevelopmentMock())
    return errorResponse(
      "not_found",
      "Sample data has no stored legal passages.",
      requestId,
      404,
    );
  return proxyRequest(request, requestId, {
    path: `/v1/sources/${encodeURIComponent(chunkId)}`,
    validate: isSourceResponse,
  });
}
