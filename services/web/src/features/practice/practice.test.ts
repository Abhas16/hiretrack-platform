import type { PracticeSession, PracticeTurn } from "@/types/practice";

import {
  currentTurn,
  formatScore,
  progressText,
  providerLabel,
  scoreTone,
  weakestTopics,
} from "./practiceModel";
import { startSchema, toSessionCreate } from "./startSchema";

function turn(position: number, topic: string, score: number | null): PracticeTurn {
  return {
    position,
    topic,
    question: `Q${position}`,
    answer: score === null ? null : "an answer",
    score,
    strengths: [],
    improvements: [],
    feedback: null,
    key_points: [],
    evaluated_by: null,
    answered_at: null,
  };
}

function session(turns: PracticeTurn[], overrides: Partial<PracticeSession> = {}): PracticeSession {
  const answered = turns.filter((t) => t.answer !== null).length;
  return {
    id: "s1",
    role: "DevOps Engineer",
    topics: [],
    provider: "rule_based",
    status: answered === turns.length ? "COMPLETED" : "IN_PROGRESS",
    question_count: turns.length,
    answered_count: answered,
    average_score: null,
    created_at: "",
    completed_at: null,
    application_id: null,
    turns,
    ...overrides,
  };
}

describe("practiceModel", () => {
  it("labels scores", () => {
    expect(scoreTone(9).label).toBe("Strong");
    expect(scoreTone(5).label).toBe("Good");
    expect(scoreTone(2).label).toBe("Needs work");
    expect(formatScore(7)).toBe("7 / 10");
    expect(formatScore(7.25)).toBe("7.3 / 10");
    expect(formatScore(null)).toBe("—");
  });

  it("finds the current question and describes progress", () => {
    const s = session([turn(1, "docker", 6), turn(2, "aws", null), turn(3, "linux", null)]);
    expect(currentTurn(s)?.position).toBe(2);
    expect(progressText(s)).toBe("Question 2 of 3");
  });

  it("suggests the weakest topics below 7 to study next", () => {
    const s = session([turn(1, "docker", 9), turn(2, "aws", 3), turn(3, "linux", 5)]);
    expect(currentTurn(s)).toBeUndefined();
    expect(progressText(s)).toBe("Completed · 3 questions");
    expect(weakestTopics(s)).toEqual(["aws", "linux"]);
  });

  it("names the provider", () => {
    expect(providerLabel("anthropic")).toBe("AI interviewer (Claude)");
    expect(providerLabel("rule_based")).toBe("Built-in question bank");
  });
});

describe("startSchema", () => {
  it("needs a role or an application", () => {
    const result = startSchema.safeParse({
      applicationId: "",
      role: " ",
      topics: [],
      questionCount: 5,
    });
    expect(result.success).toBe(false);
  });

  it("maps the form to the API body, letting the API pick topics when none are chosen", () => {
    const values = startSchema.parse({
      applicationId: "",
      role: "SRE",
      topics: [],
      questionCount: "4",
    });
    expect(toSessionCreate(values)).toEqual({
      role: "SRE",
      application_id: undefined,
      topics: undefined,
      question_count: 4,
    });
  });
});
