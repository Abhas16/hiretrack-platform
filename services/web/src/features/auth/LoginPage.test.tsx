import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { authApi } from "@/lib/api/auth";
import { createTestContext, makeWrapper } from "@/test/TestProviders";

import { LoginPage } from "./LoginPage";

function renderLogin() {
  const ctx = createTestContext();
  ctx.auth.isAuthenticated = false;
  render(<LoginPage />, { wrapper: makeWrapper(ctx, "/login") });
  return { ctx, user: userEvent.setup() };
}

const TOKEN = { access_token: "jwt-abc", token_type: "bearer" as const, expires_in: 3600 };

describe("LoginPage", () => {
  it("signs in with the token from the API", async () => {
    const login = vi.spyOn(authApi, "login").mockResolvedValue(TOKEN);
    const { ctx, user } = renderLogin();

    await user.type(screen.getByLabelText("Email"), "abhas@example.com");
    await user.type(screen.getByLabelText("Password"), "correct-horse");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => expect(ctx.auth.signIn).toHaveBeenCalledWith("jwt-abc"));
    expect(login).toHaveBeenCalledWith({ email: "abhas@example.com", password: "correct-horse" });
  });

  it("registers first, then signs in, in create-account mode", async () => {
    const register = vi.spyOn(authApi, "register").mockResolvedValue({
      id: "u1",
      email: "new@example.com",
      full_name: "New User",
      created_at: "",
    });
    vi.spyOn(authApi, "login").mockResolvedValue(TOKEN);
    const { ctx, user } = renderLogin();

    await user.click(screen.getByRole("button", { name: /create an account/i }));
    await user.type(screen.getByLabelText("Name"), "New User");
    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.type(screen.getByLabelText("Password"), "long-enough");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => expect(ctx.auth.signIn).toHaveBeenCalledWith("jwt-abc"));
    expect(register).toHaveBeenCalledWith({
      email: "new@example.com",
      password: "long-enough",
      full_name: "New User",
    });
  });

  it("validates before calling the API", async () => {
    const login = vi.spyOn(authApi, "login");
    const { user } = renderLogin();

    await user.type(screen.getByLabelText("Email"), "not-an-email");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Enter a valid email")).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
  });
});
