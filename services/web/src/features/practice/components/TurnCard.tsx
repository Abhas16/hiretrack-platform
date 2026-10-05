import type { PracticeTurn } from "@/types/practice";

import { ScoreBadge } from "./ScoreBadge";

interface Props {
  turn: PracticeTurn;
  topicName: string;
}

function List({ title, items, tone }: { title: string; items: string[]; tone: string }) {
  if (items.length === 0) return null;
  return (
    <div className="flex flex-col gap-1">
      <div className={`text-xs font-bold tracking-[0.6px] uppercase ${tone}`}>{title}</div>
      <ul className="text-ink-2 m-0 flex flex-col gap-1 pl-5 text-sm leading-relaxed">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

/** One answered question: the question, your answer, and the evaluation. */
export function TurnCard({ turn, topicName }: Props) {
  return (
    <article className="border-line bg-surface flex flex-col gap-3.5 rounded-[14px] border p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 flex-col gap-1">
          <span className="text-muted font-mono text-xs">
            Q{turn.position} · {topicName}
          </span>
          <h3 className="m-0 text-[15px] leading-snug font-bold">{turn.question}</h3>
        </div>
        {turn.score !== null && <ScoreBadge score={turn.score} />}
      </div>

      <div className="bg-soft text-ink-2 rounded-xl p-3.5 text-sm leading-relaxed whitespace-pre-wrap">
        {turn.answer}
      </div>

      {turn.feedback && <p className="text-ink-2 m-0 text-sm leading-relaxed">{turn.feedback}</p>}
      <List title="What went well" items={turn.strengths} tone="text-status-offer-ink" />
      <List title="To improve" items={turn.improvements} tone="text-warm-ink" />
      <List title="A strong answer covers" items={turn.key_points} tone="text-ink-3" />

      {turn.evaluated_by && (
        <span className="text-muted font-mono text-[11px]">
          scored by {turn.evaluated_by === "anthropic" ? "Claude" : "the built-in rubric"}
        </span>
      )}
    </article>
  );
}
