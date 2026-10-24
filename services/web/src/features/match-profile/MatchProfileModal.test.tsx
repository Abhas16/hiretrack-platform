import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { matchesApi } from "@/lib/api/matches";
import { createTestContext, makeWrapper } from "@/test/TestProviders";
import type { MatchProfile } from "@/types/match";

import { MatchProfileModal } from "./MatchProfileModal";

const EMPTY: MatchProfile = {
  exists: false,
  is_active: false,
  skills: {},
  target_roles: [],
  locations: [],
  remote_ok: true,
  years_experience: 0,
  updated_at: null,
};

function renderModal() {
  const ctx = createTestContext();
  const onClose = vi.fn();
  vi.spyOn(matchesApi, "profile").mockResolvedValue(EMPTY);
  vi.spyOn(matchesApi, "skills").mockResolvedValue({ skills: ["kubernetes", "terraform"] });
  const save = vi.spyOn(matchesApi, "saveProfile").mockImplementation(async (body) => ({
    ...body,
    exists: true,
    updated_at: "2026-10-20T00:00:00Z",
  }));
  render(<MatchProfileModal onClose={onClose} />, { wrapper: makeWrapper(ctx) });
  return { ctx, onClose, save };
}

afterEach(() => vi.restoreAllMocks());

describe("MatchProfileModal", () => {
  it("needs at least one skill", async () => {
    const { save } = renderModal();
    await userEvent.click(await screen.findByRole("button", { name: "Save profile" }));
    expect(await screen.findByText("Pick at least one skill")).toBeInTheDocument();
    expect(save).not.toHaveBeenCalled();
  });

  it("saves weighted skills and comma lists", async () => {
    const { save, onClose, ctx } = renderModal();
    await userEvent.click(await screen.findByRole("button", { name: "kubernetes" }));
    await userEvent.click(screen.getByRole("button", { name: "kubernetes, weight 3" })); // -> 4
    await userEvent.type(screen.getByLabelText(/Locations/), "Pune, Bengaluru");
    await userEvent.clear(screen.getByLabelText("Years of experience"));
    await userEvent.type(screen.getByLabelText("Years of experience"), "2");

    await userEvent.click(screen.getByRole("button", { name: "Save profile" }));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(save).toHaveBeenCalledWith({
      is_active: true,
      skills: { kubernetes: 4 },
      target_roles: ["DevOps Engineer", "Platform Engineer", "SRE"],
      locations: ["Pune", "Bengaluru"],
      remote_ok: true,
      years_experience: 2,
    });
    expect(ctx.toast.success).toHaveBeenCalled();
  });
});
