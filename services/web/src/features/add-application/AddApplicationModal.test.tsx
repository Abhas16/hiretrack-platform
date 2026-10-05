import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { applicationsApi } from "@/lib/api/applications";
import { makeApplication } from "@/test/fixtures";
import { createTestContext, makeWrapper } from "@/test/TestProviders";

import { AddApplicationModal } from "./AddApplicationModal";

function renderModal() {
  const ctx = createTestContext();
  const onClose = vi.fn();
  render(<AddApplicationModal onClose={onClose} />, { wrapper: makeWrapper(ctx) });
  return { ctx, onClose, user: userEvent.setup() };
}

describe("AddApplicationModal", () => {
  it("shows validation errors and sends nothing when required fields are empty", async () => {
    const create = vi.spyOn(applicationsApi, "create");
    const { user } = renderModal();

    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Company is required")).toBeInTheDocument();
    expect(screen.getByText("Role is required")).toBeInTheDocument();
    expect(create).not.toHaveBeenCalled();
  });

  it("creates the application, toasts and closes", async () => {
    const create = vi.spyOn(applicationsApi, "create").mockResolvedValue(makeApplication());
    const { ctx, onClose, user } = renderModal();

    await user.type(screen.getByLabelText("Company"), "  Postman ");
    await user.type(screen.getByLabelText("Role"), "DevOps Engineer I");
    await user.selectOptions(screen.getByLabelText("Stage"), "WISHLIST");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(create).toHaveBeenCalledWith({
      company_name: "Postman",
      role: "DevOps Engineer I",
      location: null,
      status: "WISHLIST",
      source: "COMPANY_SITE",
      job_url: null,
    });
    expect(ctx.toast.success).toHaveBeenCalledWith("POST /api/v1/applications · 201 Created");
  });

  it("rejects a non-URL job link", async () => {
    const { user } = renderModal();
    await user.type(screen.getByLabelText("Job URL (optional)"), "careers page");
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText(/Enter a full URL/)).toBeInTheDocument();
  });
});
