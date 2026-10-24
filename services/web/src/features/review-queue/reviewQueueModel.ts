/** Pure display rules for the review queue (unit-tested, no React). */
import { daysSince } from "@/lib/format";
import { SOURCE_LABEL } from "@/lib/status";
import type { Job, Match } from "@/types/match";

export const THRESHOLDS = [
  { value: 80, label: "Score 80+" },
  { value: 70, label: "Score 70+" },
  { value: 0, label: "All" },
];
export const DEFAULT_THRESHOLD = 70;

/** Full class names so Tailwind can find them at build time. */
export function scoreTone(score: number): { text: string; bar: string } {
  if (score >= 80) return { text: "text-success", bar: "bg-success" };
  if (score >= 60) return { text: "text-primary", bar: "bg-primary" };
  return { text: "text-warm-ink", bar: "bg-accent" };
}

export function postedText(iso: string | null, now: Date = new Date()): string | null {
  if (!iso) return null;
  const days = daysSince(iso, now);
  if (days === 0) return "posted today";
  if (days === 1) return "posted yesterday";
  return `posted ${days} days ago`;
}

/** "Acme · Remote, India · via Greenhouse · posted 3 days ago" */
export function jobMeta(job: Job, now: Date = new Date()): string {
  const location = job.location ?? (job.is_remote ? "Remote" : null);
  return [
    job.company_name,
    location,
    `via ${SOURCE_LABEL[job.source]}`,
    postedText(job.posted_at, now),
  ]
    .filter(Boolean)
    .join(" · ");
}

/** What "Copy kit" puts on the clipboard: ready to paste into the application form. */
export function kitText(match: Match): string {
  const bullets = match.resume_bullets.map((bullet) => `- ${bullet}`).join("\n");
  return `${match.cover_note}\n\nResume bullets:\n${bullets}\n`;
}
