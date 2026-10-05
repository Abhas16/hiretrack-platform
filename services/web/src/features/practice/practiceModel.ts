/** Pure helpers for the practice screens (no React, easy to test). */
import type { PracticeSession, PracticeTopic, PracticeTurn } from "@/types/practice";

export interface ScoreTone {
  label: string;
  className: string; // full Tailwind classes so they survive the build
}

export function scoreTone(score: number): ScoreTone {
  if (score >= 8) return { label: "Strong", className: "bg-status-offer text-status-offer-ink" };
  if (score >= 5) return { label: "Good", className: "bg-status-applied text-status-applied-ink" };
  return { label: "Needs work", className: "bg-status-interview text-status-interview-ink" };
}

export function providerLabel(provider: string): string {
  return provider === "anthropic" ? "AI interviewer (Claude)" : "Built-in question bank";
}

export function topicLabel(topics: PracticeTopic[], id: string): string {
  return topics.find((topic) => topic.id === id)?.label ?? id;
}

/** The question waiting for an answer, or undefined when the session is finished. */
export function currentTurn(session: PracticeSession): PracticeTurn | undefined {
  return session.turns.find((turn) => turn.answer === null);
}

export function answeredTurns(session: PracticeSession): PracticeTurn[] {
  return session.turns.filter((turn) => turn.answer !== null);
}

export function progressText(session: PracticeSession): string {
  if (session.status === "COMPLETED") return `Completed · ${session.question_count} questions`;
  return `Question ${session.answered_count + 1} of ${session.question_count}`;
}

/** "7.5 / 10" or "—" */
export function formatScore(score: number | null): string {
  return score === null ? "—" : `${Number.isInteger(score) ? score : score.toFixed(1)} / 10`;
}

/** Topics where the user scored lowest: what to study next. */
export function weakestTopics(session: PracticeSession, limit = 2): string[] {
  const scored = session.turns.filter((turn) => turn.score !== null);
  return [...scored]
    .sort((a, b) => (a.score ?? 0) - (b.score ?? 0))
    .filter((turn) => (turn.score ?? 0) < 7)
    .slice(0, limit)
    .map((turn) => turn.topic);
}
