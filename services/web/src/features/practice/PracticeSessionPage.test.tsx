import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";

import { practiceApi } from "@/lib/api/practice";
import { createTestContext, makeWrapper } from "@/test/TestProviders";
import type { PracticeSession } from "@/types/practice";

import { PracticeSessionPage } from "./PracticeSessionPage";

const base: PracticeSession = {
  id: "s1",
  role: "Junior DevOps Engineer",
  topics: ["kubernetes"],
  provider: "rule_based",
  status: "IN_PROGRESS",
  question_count: 1,
  answered_count: 0,
  average_score: null,
  created_at: "",
  completed_at: null,
  application_id: null,
  turns: [
    {
      position: 1,
      topic: "kubernetes",
      question: "Liveness vs readiness?",
      answer: null,
      score: null,
      strengths: [],
      improvements: [],
      feedback: null,
      key_points: [],
      evaluated_by: null,
      answered_at: null,
    },
  ],
};

const answered: PracticeSession = {
  ...base,
  status: "COMPLETED",
  answered_count: 1,
  average_score: 8,
  turns: [
    {
      ...base.turns[0]!,
      answer: "Liveness restarts, readiness removes from the Service.",
      score: 8,
      feedback: "Strong answer.",
      strengths: ["Covered: Liveness failure restarts the container"],
      key_points: ["Liveness failure restarts the container"],
      evaluated_by: "rule_based",
    },
  ],
};

function renderSession() {
  const ctx = createTestContext();
  vi.spyOn(practiceApi, "meta").mockResolvedValue({
    provider: "rule_based",
    topics: [{ id: "kubernetes", label: "Kubernetes" }],
    min_questions: 3,
    max_questions: 8,
  });
  render(
    <Routes>
      <Route path="/practice/:sessionId" element={<PracticeSessionPage />} />
    </Routes>,
    { wrapper: makeWrapper(ctx, "/practice/s1") },
  );
  return { ctx, user: userEvent.setup() };
}

describe("PracticeSessionPage", () => {
  it("submits an answer and shows the evaluation and summary", async () => {
    vi.spyOn(practiceApi, "session").mockResolvedValue(base);
    const answer = vi.spyOn(practiceApi, "answer").mockResolvedValue(answered);
    const { ctx, user } = renderSession();

    expect(await screen.findByText("Liveness vs readiness?")).toBeInTheDocument();
    const submit = screen.getByRole("button", { name: /submit answer/i });
    expect(submit).toBeDisabled(); // nothing typed yet

    await user.type(screen.getByLabelText("Your answer"), "Liveness restarts, readiness removes.");
    await user.click(submit);

    await waitFor(() =>
      expect(answer).toHaveBeenCalledWith("s1", "Liveness restarts, readiness removes."),
    );
    expect(await screen.findByText("Interview complete")).toBeInTheDocument();
    expect(screen.getByText("Strong answer.")).toBeInTheDocument();
    expect(screen.getByText("A strong answer covers")).toBeInTheDocument();
    expect(ctx.toast.success).toHaveBeenCalledWith("Answer scored 8 / 10");
  });
});
