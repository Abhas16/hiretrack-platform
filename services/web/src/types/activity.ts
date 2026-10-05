import type { ApplicationBrief } from "./application";

export type InterviewKind =
  "PHONE_SCREEN" | "HR" | "TECHNICAL" | "SYSTEM_DESIGN" | "BEHAVIORAL" | "ONSITE" | "OTHER";

export interface Interview {
  id: string;
  application: ApplicationBrief;
  round_name: string;
  kind: InterviewKind;
  scheduled_at: string | null;
  duration_minutes: number | null;
  interviewer: string | null;
  outcome: "PENDING" | "PASSED" | "FAILED" | "CANCELLED";
  notes: string | null;
}

export type ReminderStatus = "OPEN" | "DONE" | "DISMISSED";

export interface Reminder {
  id: string;
  application: ApplicationBrief | null;
  kind: "FOLLOW_UP" | "CUSTOM";
  status: ReminderStatus;
  created_by: "USER" | "WORKER";
  message: string;
  due_at: string;
  completed_at: string | null;
  created_at: string;
}
