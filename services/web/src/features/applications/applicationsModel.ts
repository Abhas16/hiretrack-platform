import { STATUS_LABEL, STATUS_ORDER, isApplicationStatus } from "@/lib/status";
import type { AnalyticsSummary } from "@/types/analytics";
import type { ApplicationStatus } from "@/types/common";

export type StatusFilter = ApplicationStatus | "ALL";

export interface FilterPill {
  value: StatusFilter;
  label: string;
  active: boolean;
}

export const PAGE_SIZE = 25;

/** "All · 12", "Applied · 4", ... Counts come from the analytics summary. */
export function buildFilterPills(
  summary: AnalyticsSummary | undefined,
  active: StatusFilter,
): FilterPill[] {
  const count = (value: StatusFilter) =>
    summary ? (value === "ALL" ? summary.total : (summary.by_status[value] ?? 0)) : null;

  return (["ALL", ...STATUS_ORDER] as StatusFilter[]).map((value) => {
    const name = value === "ALL" ? "All" : STATUS_LABEL[value];
    const n = count(value);
    return { value, label: n === null ? name : `${name} · ${n}`, active: value === active };
  });
}

export function parseStatusFilter(raw: string | null): StatusFilter {
  return isApplicationStatus(raw) ? raw : "ALL";
}

export function parsePage(raw: string | null): number {
  const page = Number(raw);
  return Number.isInteger(page) && page > 0 ? page : 1;
}

/** "Showing 26–40 of 40" */
export function rangeText(page: number, pageSize: number, total: number): string {
  if (total === 0) return "No results";
  const first = (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, total);
  return `Showing ${first}–${last} of ${total}`;
}
