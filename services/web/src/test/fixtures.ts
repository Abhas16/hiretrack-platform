import type { AnalyticsSummary } from "@/types/analytics";
import type { Application, Board } from "@/types/application";

export function makeApplication(overrides: Partial<Application> = {}): Application {
  return {
    id: "app-1",
    company: { id: "co-1", name: "Atlassian" },
    role: "Associate DevOps Engineer",
    location: "Bengaluru",
    source: "REFERRAL",
    job_url: null,
    status: "APPLIED",
    applied_at: "2026-09-28T10:00:00Z",
    status_changed_at: "2026-09-28T10:00:00Z",
    resume_variant: null,
    created_at: "2026-09-28T10:00:00Z",
    updated_at: "2026-09-28T10:00:00Z",
    allowed_transitions: ["WISHLIST", "INTERVIEW", "REJECTED"],
    ...overrides,
  };
}

export function makeBoard(apps: Application[]): Board {
  const statuses = ["WISHLIST", "APPLIED", "INTERVIEW", "OFFER", "REJECTED"] as const;
  return {
    columns: statuses.map((status) => {
      const items = apps.filter((app) => app.status === status);
      return { status, count: items.length, items };
    }),
  };
}

export function makeSummary(overrides: Partial<AnalyticsSummary> = {}): AnalyticsSummary {
  return {
    total: 12,
    wishlist: 2,
    sent: 10,
    active_pipeline: 9,
    interviews_in_progress: 3,
    offers: 1,
    rejected: 2,
    responded: 6,
    response_rate: 0.6,
    interview_rate: 0.4,
    by_status: { WISHLIST: 2, APPLIED: 4, INTERVIEW: 3, OFFER: 1, REJECTED: 2 },
    ...overrides,
  };
}
