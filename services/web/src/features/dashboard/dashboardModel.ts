/** Pure functions: API data -> what the dashboard shows. No React, so they're trivial to test. */
import type { Kpi } from "@/components/ui/KpiCard";
import { percent } from "@/lib/format";
import { STATUS_LABEL, STATUS_ORDER } from "@/lib/status";
import type { AnalyticsSummary } from "@/types/analytics";
import type { ApplicationStatus } from "@/types/common";

export interface PipelineSegment {
  status: ApplicationStatus;
  label: string;
  count: number;
  widthPercent: number;
}

export function buildKpis(s: AnalyticsSummary): Kpi[] {
  return [
    {
      label: "Total applications",
      value: String(s.total),
      hint: `${s.sent} sent, ${s.wishlist} on wishlist`,
    },
    {
      label: "Active pipeline",
      value: String(s.active_pipeline),
      hint: "Not yet offered or rejected",
    },
    {
      label: "Interviews",
      value: String(s.interviews_in_progress),
      hint: "Currently in interview stage",
    },
    {
      label: "Response rate",
      value: percent(s.response_rate),
      hint: `${s.responded} of ${s.sent} sent got a reply`,
    },
  ];
}

export function buildPipeline(s: AnalyticsSummary): PipelineSegment[] {
  return STATUS_ORDER.map((status) => {
    const count = s.by_status[status] ?? 0;
    return {
      status,
      label: STATUS_LABEL[status],
      count,
      widthPercent: s.total ? (count / s.total) * 100 : 0,
    };
  });
}
