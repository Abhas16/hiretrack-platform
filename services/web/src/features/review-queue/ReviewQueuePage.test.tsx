import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { matchesApi } from "@/lib/api/matches";
import { makeMatch } from "@/test/matchFixtures";
import { createTestContext, makeWrapper } from "@/test/TestProviders";
import type { ApproveResponse, MatchProfile } from "@/types/match";

import { ReviewQueuePage } from "./ReviewQueuePage";

const PROFILE: MatchProfile = {
  exists: true,
  is_active: true,
  skills: { kubernetes: 5, terraform: 4 },
  target_roles: ["DevOps Engineer"],
  locations: [],
  remote_ok: true,
  years_experience: 2,
  updated_at: "2026-10-19T00:00:00Z",
};

function renderPage() {
  const ctx = createTestContext();
  const list = vi.spyOn(matchesApi, "list").mockResolvedValue({
    items: [makeMatch()],
    total: 1,
    page: 1,
    page_size: 50,
  });
  vi.spyOn(matchesApi, "profile").mockResolvedValue(PROFILE);
  render(<ReviewQueuePage />, { wrapper: makeWrapper(ctx, "/review-queue") });
  return { ctx, list };
}

afterEach(() => vi.restoreAllMocks());

it("shows the match with its score, chips and suggested resume", async () => {
  renderPage();
  expect(await screen.findByText("DevOps Engineer")).toBeInTheDocument();
  expect(screen.getByText("86% match")).toBeInTheDocument();
  expect(screen.getByText("kubernetes")).toBeInTheDocument();
  expect(screen.getByText("5+ years experience (you have 2)")).toBeInTheDocument();
  expect(screen.getByText("DevOps - Kubernetes")).toBeInTheDocument();
  expect(screen.getByText(/Matching on 2 skills/)).toBeInTheDocument();
});

it("refetches with the chosen threshold", async () => {
  const { list } = renderPage();
  await screen.findByText("DevOps Engineer");
  await userEvent.click(screen.getByRole("button", { name: "Score 80+" }));
  await waitFor(() =>
    expect(list).toHaveBeenLastCalledWith({ status: "NEW", min_score: 80, page_size: 50 }),
  );
});

it("approve opens the job in the tab it opened during the click", async () => {
  const { ctx } = renderPage();
  const tab = { location: { href: "" }, opener: {}, close: vi.fn() };
  vi.spyOn(window, "open").mockReturnValue(tab as unknown as Window);
  const approve = vi
    .spyOn(matchesApi, "approve")
    .mockResolvedValue({ job_url: makeMatch().job.url } as ApproveResponse);

  await userEvent.click(await screen.findByRole("button", { name: /Approve/ }));

  await waitFor(() => expect(tab.location.href).toBe(makeMatch().job.url));
  expect(approve).toHaveBeenCalledWith("m1");
  expect(tab.opener).toBeNull();
  expect(ctx.toast.success).toHaveBeenCalled();
});

it("closes the blank tab if approve fails", async () => {
  const { ctx } = renderPage();
  const tab = { location: { href: "" }, opener: null, close: vi.fn() };
  vi.spyOn(window, "open").mockReturnValue(tab as unknown as Window);
  vi.spyOn(matchesApi, "approve").mockRejectedValue(new Error("409"));

  await userEvent.click(await screen.findByRole("button", { name: /Approve/ }));

  await waitFor(() => expect(tab.close).toHaveBeenCalled());
  expect(ctx.toast.fromError).toHaveBeenCalled();
});

it("shows the kit and skips a match", async () => {
  renderPage();
  const skip = vi.spyOn(matchesApi, "skip").mockResolvedValue(makeMatch({ status: "SKIPPED" }));

  await userEvent.click(await screen.findByRole("button", { name: "View kit" }));
  expect(screen.getByText("Hi Acme Cloud team, ...")).toBeInTheDocument();
  expect(screen.getByText("Ran Kubernetes")).toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: "Skip" }));
  await waitFor(() => expect(skip).toHaveBeenCalledWith("m1"));
});
