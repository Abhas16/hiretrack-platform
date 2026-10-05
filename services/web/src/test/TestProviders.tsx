import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router";

import { ThemeProvider } from "@/components/theme/ThemeProvider";
import { ToastContext, type ToastApi } from "@/components/toast/ToastContext";
import { AuthContext, type AuthState } from "@/features/auth/AuthContext";

export interface TestContext {
  toast: { [K in keyof ToastApi]: ReturnType<typeof vi.fn> };
  auth: AuthState;
  queryClient: QueryClient;
}

/** Fresh providers for each test: no retries, spy toasts, a signed-in fake user. */
export function createTestContext(): TestContext {
  return {
    toast: { success: vi.fn(), error: vi.fn(), fromError: vi.fn() },
    auth: {
      isAuthenticated: true,
      user: { id: "u1", email: "abhas@example.com", full_name: "Abhas Mukherjee", created_at: "" },
      signIn: vi.fn(),
      signOut: vi.fn(),
    },
    queryClient: new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    }),
  };
}

export function makeWrapper(ctx: TestContext, initialPath = "/") {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={ctx.queryClient}>
        <ToastContext.Provider value={ctx.toast as unknown as ToastApi}>
          <AuthContext.Provider value={ctx.auth}>
            <ThemeProvider>
              <MemoryRouter initialEntries={[initialPath]}>{children}</MemoryRouter>
            </ThemeProvider>
          </AuthContext.Provider>
        </ToastContext.Provider>
      </QueryClientProvider>
    );
  };
}
