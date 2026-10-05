import type { BarRowData } from "@/components/ui/BarRow";
import type { Kpi } from "@/components/ui/KpiCard";
import { formatWeekLabel, percent } from "@/lib/format";
import { SOURCE_LABEL } from "@/lib/status";
import type {
  AnalyticsSummary,
  FunnelStage,
  SourceBreakdown,
  TimeToFirstInterview,
  VariantBreakdown,
  WeeklyCount,
} from "@/types/analytics";

const FUNNEL_COLORS = ["bg-[#8A93A3]", "bg-[#2F5BEA]", "bg-[#E07A1F]", "bg-[#2E9A5E]"];

export interface WeekBar {
  label: string;
  count: number;
}

export interface VariantRow {
  name: string;
  detail: string;
  interviewRate: string;
}

export function buildAnalyticsKpis(
  summary: AnalyticsSummary,
  ttfi: TimeToFirstInterview | undefined,
): Kpi[] {
  const avg = ttfi?.average_days;
  return [
    {
      label: "Avg. days to first interview",
      value: avg === null || avg === undefined ? "—" : `${Math.round(avg)}d`,
      hint: ttfi ? `from ${ttfi.sample_size} application(s)` : undefined,
    },
    {
      label: "Interview rate",
      value: percent(summary.interview_rate),
      hint: "of applications sent",
    },
    { label: "Offers", value: String(summary.offers) },
  ];
}

export function toWeekBars(weeks: WeeklyCount[]): WeekBar[] {
  return weeks.map((week) => ({ label: formatWeekLabel(week.week_start), count: week.count }));
}

/** Bars are relative to the first funnel stage (everything saved = 100%). */
export function toFunnelRows(stages: FunnelStage[]): BarRowData[] {
  const top = stages[0]?.count ?? 0;
  return stages.map((stage, index) => ({
    label: stage.stage,
    count: stage.count,
    widthPercent: top ? (stage.count / top) * 100 : 0,
    colorClass: FUNNEL_COLORS[index] ?? "bg-ink-3",
  }));
}

export function toSourceRows(sources: SourceBreakdown[], total: number): BarRowData[] {
  return sources.map((source) => ({
    label: SOURCE_LABEL[source.source],
    count: source.applications,
    widthPercent: total ? (source.applications / total) * 100 : 0,
    colorClass: "bg-ink-3",
  }));
}

export function toVariantRows(variants: VariantBreakdown[]): VariantRow[] {
  return variants.map((variant) => ({
    name: variant.name,
    detail: `${variant.applications} applications · ${variant.interviews} interviews · ${variant.offers} offers`,
    interviewRate: percent(variant.interview_rate),
  }));
}
