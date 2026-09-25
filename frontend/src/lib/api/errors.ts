import { DOCUMENT_EXPIRED_MESSAGE } from "./documents";

export class ApiClientError extends Error {
  readonly code: string;
  readonly requestId: string;
  readonly status: number;

  constructor(code: string, message: string, requestId: string, status = 0) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.requestId = requestId;
    this.status = status;
  }
}

/** Server errors are mapped here so internals never become product copy. */
export function errorMessage(error: unknown): string {
  if (!(error instanceof ApiClientError))
    return "We couldn’t reach the research service. Try again shortly.";
  switch (error.code) {
    case "invalid_request":
      return error.message || "Check your question and try again.";
    case "too_large":
      return error.message || "Upload a PDF up to 4 MB.";
    case "unsupported_media_type":
      return "Only PDF files can be uploaded";
    case "unreadable_document":
      return error.message || "Upload a PDF with selectable text. Scanned or password-protected PDFs cannot be read.";
    case "unauthorized":
      return "The research service connection needs attention. Please contact the owner.";
    case "not_found":
      return "This passage is no longer available. Try another source.";
    case "unavailable":
      return "Still starting or offline, try again shortly.";
    case "timeout":
      return "This took too long; try again.";
    case "cancelled":
      return "The request was cancelled.";
    case "network_error":
      return "We couldn’t reach the research service. Try again shortly.";
    default:
      return "Something went wrong while checking the sources. Please try again.";
  }
}

export function documentErrorMessage(error: unknown): string {
  return error instanceof ApiClientError && (error.status === 404 || error.code === "not_found" || error.code === "expired") ? DOCUMENT_EXPIRED_MESSAGE : errorMessage(error);
}
