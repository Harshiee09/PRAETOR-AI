import { MAX_PDF_BYTES, validatePdfFile } from "@/lib/api/documents";
import { sampleDocumentUpload } from "@/lib/server/document-samples";
import { isDocumentInfo } from "@/lib/server/document-validation";
import { errorResponse, isDevelopmentMock, jsonResponse, proxyRequest, requestIdFor, UPLOAD_TIMEOUT_MS } from "@/lib/server/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
// Leave time for multipart parsing around the 60-second upstream deadline.
export const maxDuration = 90;
const MAX_MULTIPART_BYTES = 4_500_000;

export async function POST(request: Request): Promise<Response> {
  const requestId = requestIdFor(request);
  const lengthHeader = request.headers.get("Content-Length");
  if (lengthHeader && (!/^\d+$/.test(lengthHeader) || Number(lengthHeader) > MAX_MULTIPART_BYTES)) return errorResponse("too_large", "Upload a PDF up to 4 MB.", requestId, 413);
  if (!request.body || !request.headers.get("Content-Type")?.toLowerCase().startsWith("multipart/form-data")) return errorResponse("invalid_request", "Choose a PDF file to upload.", requestId, 422);
  let bytes = 0;
  let form: FormData;
  const reader = request.body.getReader();
  try {
    const chunks: ArrayBuffer[] = [];
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > MAX_MULTIPART_BYTES) return errorResponse("too_large", "Upload a PDF up to 4 MB.", requestId, 413);
      chunks.push(new Uint8Array(value).buffer);
    }
    const boundedRequest = new Request(request.url, { method: "POST", headers: request.headers, body: new Blob(chunks), signal: request.signal });
    form = await boundedRequest.formData();
  } catch {
    if (bytes > MAX_MULTIPART_BYTES) return errorResponse("too_large", "Upload a PDF up to 4 MB.", requestId, 413);
    if (request.signal.aborted) return errorResponse("cancelled", "The request was cancelled.", requestId, 499);
    return errorResponse("invalid_request", "The file upload could not be read. Choose the PDF again.", requestId, 422);
  } finally {
    reader.releaseLock();
  }
  const file = form.get("file");
  if (!file || typeof file === "string" || form.getAll("file").length !== 1) return errorResponse("invalid_request", "Choose one PDF file to upload.", requestId, 422);
  const invalid = validatePdfFile(file);
  if (invalid) {
    const status = file.type !== "application/pdf" ? 415 : file.size > MAX_PDF_BYTES ? 413 : 422;
    return errorResponse(status === 415 ? "unsupported_media_type" : status === 413 ? "too_large" : "unreadable_document", invalid, requestId, status);
  }
  if (isDevelopmentMock()) return jsonResponse(sampleDocumentUpload(file.name), requestId, 201, true);
  const upstream = new FormData();
  upstream.set("file", file);
  return proxyRequest(request, requestId, { path: "/v1/documents", method: "POST", formData: upstream, timeoutMs: UPLOAD_TIMEOUT_MS, validate: isDocumentInfo });
}
