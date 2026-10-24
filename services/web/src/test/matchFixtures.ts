/** Test data builder for review-queue tests (only imported by *.test files). */
import type { Match } from "@/types/match";

export function makeMatch(overrides: Partial<Match> = {}): Match {
  return {
    id: "m1",
    job: {
      id: "j1",
      source: "GREENHOUSE",
      company_name: "Acme Cloud",
      title: "DevOps Engineer",
      location: "Remote, India",
      is_remote: true,
      url: "https://boards.greenhouse.io/acme/jobs/1",
      posted_at: "2026-10-17T08:00:00Z",
    },
    score: 86,
    matched_skills: ["kubernetes", "terraform"],
    gaps: ["go", "5+ years experience (you have 2)"],
    suggested_resume_variant: { id: "v1", name: "DevOps - Kubernetes" },
    cover_note: "Hi Acme Cloud team, ...",
    resume_bullets: ["Ran Kubernetes", "Wrote Terraform"],
    kit_provider: "template",
    status: "NEW",
    decided_at: null,
    application_id: null,
    created_at: "2026-10-20T06:00:00Z",
    ...overrides,
  };
}
