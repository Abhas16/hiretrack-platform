import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";

import { CompanyAvatar } from "@/components/ui/CompanyAvatar";
import { Icon } from "@/components/ui/Icon";
import { updatedText } from "@/lib/format";
import { SOURCE_LABEL } from "@/lib/status";
import type { Application } from "@/types/application";

export interface CardActions {
  onPrevious: (app: Application) => void;
  onNext: (app: Application) => void;
  onReject: (app: Application) => void;
}

const ARROW =
  "flex size-9 cursor-pointer items-center justify-center rounded-lg border border-line-strong bg-surface text-ink-3 hover:bg-canvas";

export function ApplicationCard({
  app,
  onPrevious,
  onNext,
  onReject,
}: { app: Application } & CardActions) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: app.id,
    data: { app },
  });

  return (
    <article
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      style={{ transform: CSS.Translate.toString(transform) }}
      className={`bg-surface border-line flex cursor-grab flex-col gap-2.5 rounded-xl border p-3.5 ${isDragging ? "relative z-10 opacity-80 shadow-lg" : ""}`}
    >
      <div className="flex items-center gap-2.5">
        <CompanyAvatar name={app.company.name} size={36} />
        <div className="flex min-w-0 flex-col">
          <div className="text-sm font-bold">{app.company.name}</div>
          <div className="text-muted text-xs">
            {app.location ?? "—"} · {SOURCE_LABEL[app.source]}
          </div>
        </div>
      </div>
      <div className="text-ink-2 text-[13px] font-medium">{app.role}</div>
      <div className="text-muted text-xs">{updatedText(app.updated_at)}</div>
      <div className="flex gap-1.5">
        <button
          type="button"
          aria-label="Move to previous stage"
          className={ARROW}
          onClick={() => onPrevious(app)}
        >
          <Icon name="chevronLeft" size={16} strokeWidth={2} />
        </button>
        <button
          type="button"
          aria-label="Move to next stage"
          className={ARROW}
          onClick={() => onNext(app)}
        >
          <Icon name="chevronRight" size={16} strokeWidth={2} />
        </button>
        {app.status !== "REJECTED" && (
          <button
            type="button"
            onClick={() => onReject(app)}
            className="bg-surface text-danger border-danger-line ml-auto min-h-9 cursor-pointer rounded-lg border px-2.5 text-xs font-semibold"
          >
            Reject
          </button>
        )}
      </div>
    </article>
  );
}
