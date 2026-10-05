import { DndContext } from "@dnd-kit/core";

import { QueryState } from "@/components/ui/QueryState";

import { BoardColumn } from "./components/BoardColumn";
import { useBoardController } from "./useBoardController";

export function BoardPage() {
  const c = useBoardController();

  return (
    <div className="flex flex-col gap-4">
      <p className="text-muted m-0 text-sm">
        Drag cards between stages or use the arrows. Invalid moves are rejected by the API&apos;s
        service layer.
      </p>
      <QueryState isLoading={c.isLoading} error={c.error}>
        <DndContext sensors={c.sensors} onDragEnd={c.onDragEnd}>
          <div className="overflow-x-auto pb-2">
            <div className="grid min-w-[1200px] grid-cols-[repeat(5,minmax(230px,1fr))] gap-4">
              {c.columns.map((column) => (
                <BoardColumn
                  key={column.status}
                  column={column}
                  onPrevious={c.movePrevious}
                  onNext={c.moveNext}
                  onReject={c.reject}
                />
              ))}
            </div>
          </div>
        </DndContext>
      </QueryState>
    </div>
  );
}
