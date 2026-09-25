import { isHealthResponse } from "@/lib/server/validation";
import {
  isDevelopmentMock,
  jsonResponse,
  proxyRequest,
  requestIdFor,
} from "@/lib/server/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  const requestId = requestIdFor(request);
  if (isDevelopmentMock())
    return jsonResponse(
      {
        status: "ok",
        checks: { documents: "ok", sample_data: "Sample data — no backend connected" },
      },
      requestId,
      200,
      true,
    );
  return proxyRequest(request, requestId, {
    path: "/v1/healthz",
    timeoutMs: 15_000,
    validate: isHealthResponse,
    health: true,
  });
}
