/** Pure board logic: no React, no HTTP. */
import { ApiError, describeError } from "@/lib/api/ApiError";
import { STATUS_LABEL } from "@/lib/status";
import type { Application, Board } from "@/types/application";
import type { ApplicationStatus } from "@/types/common";

/**
 * Optimistic update: move a card to another column immediately, before the API answers.
 * If the API then says 409, the controller puts the previous board back.
 */
export function moveCard(
  board: Board | undefined,
  applicationId: string,
  target: ApplicationStatus,
  now: Date = new Date(),
): Board | undefined {
  if (!board) return board;

  let moved: Application | undefined;
  const without = board.columns.map((column) => {
    const items = column.items.filter((app) => {
      if (app.id !== applicationId) return true;
      moved = app;
      return false;
    });
    return { ...column, items, count: items.length };
  });
  if (!moved) return board;

  const updated: Application = { ...moved, status: target, updated_at: now.toISOString() };
  return {
    columns: without.map((column) =>
      column.status === target
        ? { ...column, items: [updated, ...column.items], count: column.count + 1 }
        : column,
    ),
  };
}

/** Toast text when the API refuses a move. */
export function describeMoveError(
  error: unknown,
  from: ApplicationStatus,
  to: ApplicationStatus,
): string {
  if (error instanceof ApiError && error.status === 409) {
    return `409 Conflict · ${STATUS_LABEL[from]} → ${STATUS_LABEL[to]} is not allowed`;
  }
  return describeError(error);
}

/** Toast text for prev/next at the ends of the board (no request is sent). */
export function noStageMessage(status: ApplicationStatus, direction: "before" | "after"): string {
  return `No stage ${direction} ${STATUS_LABEL[status]}`;
}
