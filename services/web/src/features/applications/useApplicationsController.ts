import { keepPreviousData, useMutation, useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router";

import { useToast } from "@/components/toast/useToast";
import { analyticsApi } from "@/lib/api/analytics";
import { applicationsApi } from "@/lib/api/applications";
import { queryKeys } from "@/lib/api/queryKeys";
import { saveBlob } from "@/lib/download";
import { useSearchQuery } from "@/lib/hooks/useSearchQuery";
import type { ApplicationQuery } from "@/types/application";

import {
  PAGE_SIZE,
  buildFilterPills,
  parsePage,
  parseStatusFilter,
  rangeText,
  type StatusFilter,
} from "./applicationsModel";

export function useApplicationsController() {
  const toast = useToast();
  const [params, setParams] = useSearchParams();
  const { debouncedQuery } = useSearchQuery();
  const filter = parseStatusFilter(params.get("status"));
  const page = parsePage(params.get("page"));

  const query: ApplicationQuery = {
    status: filter === "ALL" ? undefined : [filter],
    q: debouncedQuery || undefined,
    sort: "-updated_at",
    page,
    page_size: PAGE_SIZE,
  };

  const list = useQuery({
    queryKey: queryKeys.applications.list(query),
    queryFn: () => applicationsApi.list(query),
    placeholderData: keepPreviousData, // keep the old page visible while the next one loads
  });
  const summary = useQuery({
    queryKey: queryKeys.analytics.summary,
    queryFn: analyticsApi.summary,
  });

  const exportCsv = useMutation({
    mutationFn: () => applicationsApi.exportCsv({ status: query.status, q: query.q }),
    onSuccess: (blob) => {
      saveBlob(blob, "applications.csv");
      toast.success("GET /api/v1/applications/export.csv · 200 OK");
    },
    onError: toast.fromError,
  });

  // Changing the filter or page is a URL change, so the browser back button works.
  const updateParams = (changes: Record<string, string | null>) =>
    setParams((previous) => {
      const next = new URLSearchParams(previous);
      for (const [key, value] of Object.entries(changes)) {
        if (value === null) next.delete(key);
        else next.set(key, value);
      }
      return next;
    });

  const total = list.data?.total ?? 0;

  return {
    pills: buildFilterPills(summary.data, filter),
    selectFilter: (value: StatusFilter) =>
      updateParams({ status: value === "ALL" ? null : value, page: null }),
    rows: list.data?.items ?? [],
    isLoading: list.isLoading,
    error: list.error,
    emptyText: debouncedQuery ? "No applications match your search." : "No applications yet.",
    pagination: {
      text: rangeText(page, PAGE_SIZE, total),
      hasPrevious: page > 1,
      hasNext: page * PAGE_SIZE < total,
      previous: () => updateParams({ page: String(page - 1) }),
      next: () => updateParams({ page: String(page + 1) }),
    },
    exportCsv: () => exportCsv.mutate(),
    isExporting: exportCsv.isPending,
  };
}
