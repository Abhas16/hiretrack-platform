import type {
  AnalyticsSummary,
  FunnelStage,
  SourceBreakdown,
  TimeToFirstInterview,
  VariantBreakdown,
  WeeklyCount,
} from "@/types/analytics";

import { apiRequest } from "./client";

export const analyticsApi = {
  summary: () => apiRequest<AnalyticsSummary>("/analytics/summary"),

  perWeek: (weeks: number) =>
    apiRequest<{ weeks: WeeklyCount[] }>("/analytics/per-week", { query: { weeks } }),

  funnel: () => apiRequest<{ stages: FunnelStage[] }>("/analytics/funnel"),

  bySource: () => apiRequest<SourceBreakdown[]>("/analytics/by-source"),

  byResumeVariant: () => apiRequest<VariantBreakdown[]>("/analytics/by-resume-variant"),

  timeToFirstInterview: () =>
    apiRequest<TimeToFirstInterview>("/analytics/time-to-first-interview"),
};
