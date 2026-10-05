import type { ApplicationSource, ApplicationStatus } from "./common";

export interface NamedRef {
  id: string;
  name: string;
}

export interface Application {
  id: string;
  company: NamedRef;
  role: string;
  location: string | null;
  source: ApplicationSource;
  job_url: string | null;
  status: ApplicationStatus;
  applied_at: string | null;
  status_changed_at: string;
  resume_variant: NamedRef | null;
  created_at: string;
  updated_at: string;
  /** Moves the API will accept from the current status. */
  allowed_transitions: ApplicationStatus[];
}

export interface ApplicationCreate {
  company_name: string;
  role: string;
  location?: string | null;
  source?: ApplicationSource;
  status?: ApplicationStatus;
  job_url?: string | null;
}

export interface ApplicationQuery {
  status?: ApplicationStatus[];
  q?: string;
  sort?: string;
  page?: number;
  page_size?: number;
}

export interface BoardColumn {
  status: ApplicationStatus;
  count: number;
  items: Application[];
}

export interface Board {
  columns: BoardColumn[];
}

/** "Atlassian · DevOps Engineer" reference used inside interviews and reminders. */
export interface ApplicationBrief {
  id: string;
  role: string;
  company_name: string;
}
