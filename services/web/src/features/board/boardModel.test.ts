import { ApiError } from "@/lib/api/ApiError";
import { makeApplication, makeBoard } from "@/test/fixtures";

import { describeMoveError, moveCard, noStageMessage } from "./boardModel";

describe("moveCard", () => {
  const app = makeApplication({ id: "a1", status: "APPLIED" });
  const other = makeApplication({ id: "a2", status: "APPLIED" });
  const board = makeBoard([app, other]);
  const now = new Date("2026-10-05T12:00:00Z");

  it("moves the card to the target column and updates counts", () => {
    const moved = moveCard(board, "a1", "INTERVIEW", now)!;
    const column = (status: string) => moved.columns.find((c) => c.status === status)!;

    expect(column("APPLIED").items.map((a) => a.id)).toEqual(["a2"]);
    expect(column("APPLIED").count).toBe(1);
    expect(column("INTERVIEW").items[0]).toMatchObject({ id: "a1", status: "INTERVIEW" });
    expect(column("INTERVIEW").items[0]?.updated_at).toBe(now.toISOString());
  });

  it("does not mutate the original board (so it can be restored on error)", () => {
    moveCard(board, "a1", "OFFER");
    expect(board.columns.find((c) => c.status === "APPLIED")!.count).toBe(2);
  });

  it("returns the board unchanged for an unknown id", () => {
    expect(moveCard(board, "missing", "OFFER")).toBe(board);
    expect(moveCard(undefined, "a1", "OFFER")).toBeUndefined();
  });
});

describe("messages", () => {
  it("explains a 409 in board language", () => {
    const conflict = new ApiError(409, "invalid_status_transition", "Cannot move");
    expect(describeMoveError(conflict, "INTERVIEW", "APPLIED")).toBe(
      "409 Conflict · Interview → Applied is not allowed",
    );
  });

  it("falls back to the generic text for other errors", () => {
    expect(describeMoveError(new ApiError(500, "x", "Boom"), "APPLIED", "OFFER")).toBe(
      "500 Internal Server Error · Boom",
    );
  });

  it("describes the ends of the board", () => {
    expect(noStageMessage("WISHLIST", "before")).toBe("No stage before Wishlist");
  });
});
