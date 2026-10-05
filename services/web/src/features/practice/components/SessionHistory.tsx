import { Link } from "react-router";

import { Card } from "@/components/ui/Card";
import { EmptyText, QueryState } from "@/components/ui/QueryState";
import { updatedText } from "@/lib/format";
import type { PracticeSessionSummary, PracticeTopic } from "@/types/practice";

import { formatScore, topicLabel } from "../practiceModel";

interface Props {
  items: PracticeSessionSummary[];
  topics: PracticeTopic[];
  isLoading: boolean;
  error: unknown;
}

export function SessionHistory({ items, topics, isLoading, error }: Props) {
  return (
    <Card title="Past sessions">
      <QueryState isLoading={isLoading} error={error}>
        {items.length === 0 && (
          <EmptyText>No sessions yet. Your first one takes 5 minutes.</EmptyText>
        )}
        {items.map((s) => (
          <Link
            key={s.id}
            to={`/practice/${s.id}`}
            className="border-line hover:bg-canvas text-ink flex items-center justify-between gap-3 rounded-xl border p-3 no-underline"
          >
            <div className="flex min-w-0 flex-col gap-0.5">
              <span className="truncate text-sm font-semibold">{s.role}</span>
              <span className="text-muted truncate text-xs">
                {s.topics.map((id) => topicLabel(topics, id)).join(" · ")}
              </span>
              <span className="text-muted text-xs">{updatedText(s.created_at)}</span>
            </div>
            <div className="flex flex-none flex-col items-end gap-0.5">
              <strong className="font-mono text-sm">{formatScore(s.average_score)}</strong>
              <span className="text-muted text-xs">
                {s.status === "COMPLETED"
                  ? "Completed"
                  : `${s.answered_count}/${s.question_count} answered`}
              </span>
            </div>
          </Link>
        ))}
      </QueryState>
    </Card>
  );
}
