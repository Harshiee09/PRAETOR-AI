import {
  normalizeQuestion,
  questionValidationMessage,
} from "@/lib/api/question";
import { sampleAnswer } from "@/lib/server/samples";
import { isAskResponse } from "@/lib/server/validation";
import {
  ASK_TIMEOUT_MS,
  errorResponse,
  isDevelopmentMock,
  isObject,
  jsonResponse,
  proxyRequest,
  requestIdFor,
} from "@/lib/server/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

export async function POST(request: Request): Promise<Response> {
  const requestId = requestIdFor(request);
  let input: unknown;
  try {
    input = await request.json();
  } catch {
    return errorResponse(
      "invalid_request",
      "Send a question as valid JSON.",
      requestId,
      422,
    );
  }
  const question = isObject(input) ? input.question : undefined;
  const validation = questionValidationMessage(question);
  if (validation)
    return errorResponse("invalid_request", validation, requestId, 422);
  if (isDevelopmentMock())
    return jsonResponse(sampleAnswer(requestId), requestId, 200, true);
  return proxyRequest(request, requestId, {
    path: "/v1/ask",
    method: "POST",
    body: {
      question: normalizeQuestion(question as string),
      mode: "full",
      explain: false,
      use_cache: true,
    },
    timeoutMs: ASK_TIMEOUT_MS,
    validate: isAskResponse,
  });
}
