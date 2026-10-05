import { act, renderHook, waitFor } from "@testing-library/react";

import { ApiError } from "@/lib/api/ApiError";
import { applicationsApi } from "@/lib/api/applications";
import { makeApplication, makeBoard } from "@/test/fixtures";
import { createTestContext, makeWrapper } from "@/test/TestProviders";

import { useBoardController } from "./useBoardController";

const interviewing = makeApplication({ id: "a1", status: "INTERVIEW" });

async function renderBoard() {
  const ctx = createTestContext();
  vi.spyOn(applicationsApi, "board").mockResolvedValue(makeBoard([interviewing]));
  const { result } = renderHook(() => useBoardController(), {
    wrapper: makeWrapper(ctx, "/board"),
  });
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  return { ctx, result };
}

const columnOf = (columns: { status: string; items: { id: string }[] }[], id: string) =>
  columns.find((column) => column.items.some((item) => item.id === id))?.status;

describe("useBoardController", () => {
  it("moves a card and shows the success toast", async () => {
    const changeStatus = vi
      .spyOn(applicationsApi, "changeStatus")
      .mockResolvedValue(makeApplication({ id: "a1", status: "OFFER" }));
    const { ctx, result } = await renderBoard();

    act(() => result.current.moveNext(interviewing));

    await waitFor(() => expect(ctx.toast.success).toHaveBeenCalled());
    expect(changeStatus).toHaveBeenCalledWith("a1", "OFFER");
    expect(ctx.toast.success).toHaveBeenCalledWith("PATCH /api/v1/applications/a1/status · 200 OK");
  });

  it("rolls the card back and shows a 409 toast when the API refuses", async () => {
    vi.spyOn(applicationsApi, "changeStatus").mockRejectedValue(
      new ApiError(409, "invalid_status_transition", "Cannot move"),
    );
    const { ctx, result } = await renderBoard();

    act(() => result.current.movePrevious(interviewing)); // INTERVIEW -> APPLIED is not allowed

    await waitFor(() =>
      expect(ctx.toast.error).toHaveBeenCalledWith(
        "409 Conflict · Interview → Applied is not allowed",
      ),
    );
    expect(columnOf(result.current.columns, "a1")).toBe("INTERVIEW");
  });

  it("does not call the API at the end of the board", async () => {
    const changeStatus = vi.spyOn(applicationsApi, "changeStatus");
    const { ctx, result } = await renderBoard();

    act(() => result.current.moveNext(makeApplication({ id: "a9", status: "OFFER" })));

    expect(changeStatus).not.toHaveBeenCalled();
    expect(ctx.toast.error).toHaveBeenCalledWith("No stage after Offer");
  });
});
