/**
 * TanStack Query cache keys in one place. Invalidating a prefix (e.g. ["applications"])
 * refreshes every query under it after a change.
 */
import type { ApplicationQuery } from "@/types/application";

export const queryKeys = {
  me: ["auth", "me"] as const,
  applications: {
    all: ["applications"] as const,
    list: (query: ApplicationQuery) => ["applications", "list", query] as const,
    board: (q: string) => ["applications", "board", q] as const,
  },
  analytics: {
    all: ["analytics"] as const,
    summary: ["analytics", "summary"] as const,
    perWeek: (weeks: number) => ["analytics", "per-week", weeks] as const,
    funnel: ["analytics", "funnel"] as const,
    bySource: ["analytics", "by-source"] as const,
    byResumeVariant: ["analytics", "by-resume-variant"] as const,
    timeToFirstInterview: ["analytics", "time-to-first-interview"] as const,
  },
  interviews: { upcoming: ["interviews", "upcoming"] as const },
  reminders: { open: ["reminders", "open"] as const },
  practice: {
    meta: ["practice", "meta"] as const,
    sessions: ["practice", "sessions"] as const,
    session: (id: string) => ["practice", "session", id] as const,
  },
};

/** Everything that changes when an application is created or moves. */
export const applicationDependentKeys = [queryKeys.applications.all, queryKeys.analytics.all];
