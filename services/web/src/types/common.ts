/** Shapes shared by many API responses. They mirror services/api/.../schemas. */

export type ApplicationStatus = "WISHLIST" | "APPLIED" | "INTERVIEW" | "OFFER" | "REJECTED";

export type ApplicationSource =
  "REFERRAL" | "LINKEDIN" | "NAUKRI" | "COMPANY_SITE" | "GREENHOUSE" | "LEVER" | "ASHBY" | "OTHER";

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** Error body returned by the API for domain errors (404, 409, 401, ...). */
export interface ApiErrorBody {
  error: { code: string; message: string; request_id: string | null };
}

/** FastAPI's own validation error body (422). */
export interface ValidationErrorBody {
  detail: { loc: (string | number)[]; msg: string }[];
}
