/**
 * Display rules for statuses and sources. The real transition rules live in the API —
 * the UI only knows the board order, and lets the API answer 409 for invalid moves.
 */
import type { ApplicationSource, ApplicationStatus } from "@/types/common";

export const STATUS_ORDER: ApplicationStatus[] = [
  "WISHLIST",
  "APPLIED",
  "INTERVIEW",
  "OFFER",
  "REJECTED",
];

export const STATUS_LABEL: Record<ApplicationStatus, string> = {
  WISHLIST: "Wishlist",
  APPLIED: "Applied",
  INTERVIEW: "Interview",
  OFFER: "Offer",
  REJECTED: "Rejected",
};

/** Full class names (not built from strings) so Tailwind can find them at build time. */
export const STATUS_STYLE: Record<ApplicationStatus, { badge: string; dot: string }> = {
  WISHLIST: { badge: "bg-status-wishlist text-status-wishlist-ink", dot: "bg-[#8A93A3]" },
  APPLIED: { badge: "bg-status-applied text-status-applied-ink", dot: "bg-[#2F5BEA]" },
  INTERVIEW: { badge: "bg-status-interview text-status-interview-ink", dot: "bg-[#E07A1F]" },
  OFFER: { badge: "bg-status-offer text-status-offer-ink", dot: "bg-[#2E9A5E]" },
  REJECTED: { badge: "bg-status-rejected text-status-rejected-ink", dot: "bg-[#B04545]" },
};

export const SOURCE_LABEL: Record<ApplicationSource, string> = {
  REFERRAL: "Referral",
  LINKEDIN: "LinkedIn",
  NAUKRI: "Naukri",
  COMPANY_SITE: "Company site",
  GREENHOUSE: "Greenhouse",
  LEVER: "Lever",
  ASHBY: "Ashby",
  OTHER: "Other",
};

const PIPELINE: ApplicationStatus[] = ["WISHLIST", "APPLIED", "INTERVIEW", "OFFER"];

/** The column to the right on the board (null at the end of the pipeline). */
export function nextStatus(status: ApplicationStatus): ApplicationStatus | null {
  const index = PIPELINE.indexOf(status);
  return index === -1 ? null : (PIPELINE[index + 1] ?? null);
}

/** The column to the left on the board (null at the start of the pipeline). */
export function previousStatus(status: ApplicationStatus): ApplicationStatus | null {
  const index = PIPELINE.indexOf(status);
  return index <= 0 ? null : (PIPELINE[index - 1] ?? null);
}

export function isApplicationStatus(value: unknown): value is ApplicationStatus {
  return typeof value === "string" && (STATUS_ORDER as string[]).includes(value);
}
