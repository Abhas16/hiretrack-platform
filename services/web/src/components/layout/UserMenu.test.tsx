import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { THEME_KEY } from "@/components/theme/themeStorage";
import { createTestContext, makeWrapper } from "@/test/TestProviders";

import { UserMenu } from "./UserMenu";

function renderMenu() {
  const ctx = createTestContext();
  render(<UserMenu />, { wrapper: makeWrapper(ctx) });
  return { ctx, user: userEvent.setup() };
}

afterEach(() => {
  localStorage.clear();
  delete document.documentElement.dataset.theme;
});

describe("UserMenu", () => {
  it("opens from the avatar and shows who is signed in", async () => {
    const { user } = renderMenu();
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /account menu/i }));

    expect(screen.getByRole("menu")).toBeInTheDocument();
    expect(screen.getByText("Abhas Mukherjee")).toBeInTheDocument();
    expect(screen.getByText("abhas@example.com")).toBeInTheDocument();
  });

  it("switches to dark mode and remembers the choice", async () => {
    const { user } = renderMenu();
    await user.click(screen.getByRole("button", { name: /account menu/i }));

    await user.click(screen.getByRole("menuitemradio", { name: /dark/i }));

    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem(THEME_KEY)).toBe("dark");
    expect(screen.getByRole("menuitemradio", { name: /dark/i })).toHaveAttribute(
      "aria-checked",
      "true",
    );
  });

  it("signs out and closes on Escape", async () => {
    const { ctx, user } = renderMenu();
    await user.click(screen.getByRole("button", { name: /account menu/i }));
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /account menu/i }));
    await user.click(screen.getByRole("menuitem", { name: /sign out/i }));
    expect(ctx.auth.signOut).toHaveBeenCalledOnce();
  });
});
