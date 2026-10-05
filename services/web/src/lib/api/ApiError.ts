import type { ApiErrorBody, ValidationErrorBody } from "@/types/common";

const STATUS_TEXT: Record<number, string> = {
  400: "Bad Request",
  401: "Unauthorized",
  403: "Forbidden",
  404: "Not Found",
  409: "Conflict",
  422: "Unprocessable Entity",
  500: "Internal Server Error",
  503: "Service Unavailable",
};

/** Any non-2xx answer from the API, normalised into one shape the UI can show. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly requestId: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }

  /** "409 Conflict · Cannot move ..." — the toast format from the design. */
  get summary(): string {
    const text = STATUS_TEXT[this.status] ?? "Error";
    return `${this.status} ${text} · ${this.message}`;
  }

  static async fromResponse(response: Response): Promise<ApiError> {
    const requestId = response.headers.get("X-Request-ID");
    const body: unknown = await response.json().catch(() => null);

    if (isApiErrorBody(body)) {
      const { code, message, request_id } = body.error;
      return new ApiError(response.status, code, message, request_id ?? requestId);
    }
    if (isValidationBody(body)) {
      const first = body.detail[0];
      const field = first?.loc.filter((part) => part !== "body").join(".");
      const message = first ? `${field ? `${field}: ` : ""}${first.msg}` : "Invalid input";
      return new ApiError(response.status, "validation_error", message, requestId);
    }
    return new ApiError(
      response.status,
      "http_error",
      response.statusText || "Request failed",
      requestId,
    );
  }
}

function isApiErrorBody(body: unknown): body is ApiErrorBody {
  return typeof body === "object" && body !== null && "error" in body;
}

function isValidationBody(body: unknown): body is ValidationErrorBody {
  return (
    typeof body === "object" && body !== null && "detail" in body && Array.isArray(body.detail)
  );
}

/** Text for a toast from any thrown value. */
export function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.summary;
  if (error instanceof TypeError) return "Network error · is the API running?";
  return error instanceof Error ? error.message : "Something went wrong";
}
