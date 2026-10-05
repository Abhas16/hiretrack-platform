import type { KeyboardEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import type { PracticeTurn } from "@/types/practice";

interface Props {
  turn: PracticeTurn;
  topicName: string;
  draft: string;
  setDraft: (value: string) => void;
  maxLength: number;
  canSubmit: boolean;
  isEvaluating: boolean;
  send: () => void;
  onKeyDown: (event: KeyboardEvent<HTMLTextAreaElement>) => void;
}

/** The current question and a box to answer it. */
export function AnswerComposer(p: Props) {
  return (
    <section className="border-primary bg-surface flex flex-col gap-3.5 rounded-[14px] border-2 p-5">
      <div className="flex flex-col gap-1">
        <span className="text-muted font-mono text-xs">
          Q{p.turn.position} · {p.topicName}
        </span>
        <h3 className="m-0 text-lg leading-snug font-bold">{p.turn.question}</h3>
      </div>
      <label htmlFor="practice-answer" className="sr-only">
        Your answer
      </label>
      <textarea
        id="practice-answer"
        rows={7}
        value={p.draft}
        maxLength={p.maxLength}
        disabled={p.isEvaluating}
        onChange={(event) => p.setDraft(event.target.value)}
        onKeyDown={p.onKeyDown}
        placeholder="Answer as you would in the interview: explain the concept, then give an example from your own work."
        className="border-line-strong bg-input text-ink focus:border-primary resize-y rounded-[10px] border p-3.5 text-sm leading-relaxed outline-none disabled:opacity-70"
      />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="text-muted text-xs">
          {p.draft.length}/{p.maxLength} · Ctrl+Enter to submit
        </span>
        <Button onClick={p.send} disabled={!p.canSubmit}>
          <Icon name="send" size={16} />
          {p.isEvaluating ? "Evaluating your answer…" : "Submit answer"}
        </Button>
      </div>
    </section>
  );
}
