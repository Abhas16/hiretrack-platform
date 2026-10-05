import { Link } from "react-router";

import { QueryState } from "@/components/ui/QueryState";

import { AnswerComposer } from "./components/AnswerComposer";
import { SessionSummary } from "./components/SessionSummary";
import { TurnCard } from "./components/TurnCard";
import { usePracticeSessionController } from "./usePracticeSessionController";

export function PracticeSessionPage() {
  const c = usePracticeSessionController();

  return (
    <QueryState isLoading={c.isLoading} error={c.error}>
      <div className="flex max-w-3xl flex-col gap-4">
        <Link to="/practice" className="text-sm font-semibold no-underline">
          ← All sessions
        </Link>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div className="flex flex-col gap-1">
            <h2 className="m-0 text-xl font-bold">{c.role}</h2>
            <span className="text-muted font-mono text-xs">{c.providerText}</span>
          </div>
          <span className="text-ink-3 text-sm font-semibold">{c.progress}</span>
        </div>

        {c.isCompleted && <SessionSummary averageScore={c.averageScore} studyNext={c.studyNext} />}

        {c.answered.map((turn) => (
          <TurnCard key={turn.position} turn={turn} topicName={c.topicName(turn.topic)} />
        ))}

        {c.current && (
          <AnswerComposer
            turn={c.current}
            topicName={c.topicName(c.current.topic)}
            {...c.composer}
          />
        )}
      </div>
    </QueryState>
  );
}
