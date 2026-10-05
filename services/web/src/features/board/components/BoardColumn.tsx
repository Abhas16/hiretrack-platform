import { useDroppable } from "@dnd-kit/core";

import { StatusDot } from "@/components/ui/StatusBadge";
import { STATUS_LABEL } from "@/lib/status";
import type { BoardColumn as BoardColumnData } from "@/types/application";

import { ApplicationCard, type CardActions } from "./ApplicationCard";

export function BoardColumn({ column, ...actions }: { column: BoardColumnData } & CardActions) {
  // The column's droppable id is its status, so a drop tells the controller the target status.
  const { setNodeRef, isOver } = useDroppable({ id: column.status });

  return (
    <section
      ref={setNodeRef}
      aria-label={`${STATUS_LABEL[column.status]} column`}
      className={`flex min-h-[520px] flex-col gap-3 rounded-[14px] p-3.5 transition-colors ${isOver ? "bg-drop" : "bg-column"}`}
    >
      <div className="flex items-center gap-2 px-1 py-0.5">
        <StatusDot status={column.status} />
        <h3 className="m-0 flex-1 text-sm font-bold">{STATUS_LABEL[column.status]}</h3>
        <span className="bg-surface text-ink-3 rounded-md px-2 py-0.5 font-mono text-xs">
          {column.count}
        </span>
      </div>
      {column.items.map((app) => (
        <ApplicationCard key={app.id} app={app} {...actions} />
      ))}
    </section>
  );
}
