/** Smart Apply shapes. They mirror services/api/.../schemas/match.py. */
import type { Application } from "./application";

export type JobSource = "GREENHOUSE" | "LEVER" | "ASHBY";
export type MatchStatus = "NEW" | "APPROVED" | "SKIPPED";

export interface Job {
  id: string;
  source: JobSource;
  company_name: string;
  title: string;
  location: string | null;
  is_remote: boolean;
  url: string;
  posted_at: string | null;
}

export interface Match {
  id: string;
  job: Job;
  score: number; // 0..100
  matched_skills: string[];
  gaps: string[];
  suggested_resume_variant: { id: string; name: string } | null;
  cover_note: string;
  resume_bullets: string[];
  /** "template" (built in) or "anthropic" (Claude). */
  kit_provider: string;
  status: MatchStatus;
  decided_at: string | null;
  application_id: string | null;
  created_at: string;
}

export interface ApproveResponse {
  match: Match;
  application: Application;
  job_url: string;
}

export interface MatchQuery {
  status?: MatchStatus;
  min_score?: number;
  page?: number;
  page_size?: number;
}

export interface MatchProfile {
  exists: boolean;
  is_active: boolean;
  skills: Record<string, number>; // skill -> weight 1..5
  target_roles: string[];
  locations: string[];
  remote_ok: boolean;
  years_experience: number;
  updated_at: string | null;
}

export type MatchProfileUpdate = Omit<MatchProfile, "exists" | "updated_at">;
