import type { ApplicationSource, ApplicationStatus } from "./common";

export interface AnalyticsSummary {
  total: number;
  wishlist: number;
  sent: number;
  active_pipeline: number;
  interviews_in_progress: number;
  offers: number;
  rejected: number;
  responded: number;
  response_rate: number; // 0..1
  interview_rate: number; // 0..1
  by_status: Record<ApplicationStatus, number>;
}

export interface WeeklyCount {
  week_start: string; // YYYY-MM-DD (Monday)
  count: number;
}

export interface FunnelStage {
  stage: string;
  count: number;
}

export interface SourceBreakdown {
  source: ApplicationSource;
  applications: number;
  interviews: number;
  offers: number;
  interview_rate: number;
}

export interface VariantBreakdown {
  resume_variant_id: string | null;
  name: string;
  applications: number;
  interviews: number;
  offers: number;
  interview_rate: number;
}

export interface TimeToFirstInterview {
  average_days: number | null;
  median_days: number | null;
  sample_size: number;
}
