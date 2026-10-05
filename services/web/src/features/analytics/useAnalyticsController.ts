import { useQuery } from "@tanstack/react-query";

import { analyticsApi } from "@/lib/api/analytics";
import { queryKeys } from "@/lib/api/queryKeys";

import {
  buildAnalyticsKpis,
  toFunnelRows,
  toSourceRows,
  toVariantRows,
  toWeekBars,
} from "./analyticsModel";

const WEEKS = 8;

export function useAnalyticsController() {
  const summary = useQuery({
    queryKey: queryKeys.analytics.summary,
    queryFn: analyticsApi.summary,
  });
  const ttfi = useQuery({
    queryKey: queryKeys.analytics.timeToFirstInterview,
    queryFn: analyticsApi.timeToFirstInterview,
  });
  const perWeek = useQuery({
    queryKey: queryKeys.analytics.perWeek(WEEKS),
    queryFn: () => analyticsApi.perWeek(WEEKS),
  });
  const funnel = useQuery({ queryKey: queryKeys.analytics.funnel, queryFn: analyticsApi.funnel });
  const bySource = useQuery({
    queryKey: queryKeys.analytics.bySource,
    queryFn: analyticsApi.bySource,
  });
  const byVariant = useQuery({
    queryKey: queryKeys.analytics.byResumeVariant,
    queryFn: analyticsApi.byResumeVariant,
  });

  const queries = [summary, ttfi, perWeek, funnel, bySource, byVariant];

  return {
    isLoading: queries.some((query) => query.isLoading),
    error: queries.find((query) => query.error)?.error ?? null,
    kpis: summary.data ? buildAnalyticsKpis(summary.data, ttfi.data) : [],
    weeks: toWeekBars(perWeek.data?.weeks ?? []),
    funnel: toFunnelRows(funnel.data?.stages ?? []),
    sources: toSourceRows(bySource.data ?? [], summary.data?.total ?? 0),
    variants: toVariantRows(byVariant.data ?? []),
  };
}
