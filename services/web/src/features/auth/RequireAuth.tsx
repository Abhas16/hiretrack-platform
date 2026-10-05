import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";

import { useAuth } from "./useAuth";

/** Route guard: no token -> go to /login, then come back to the page you asked for. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }
  return <>{children}</>;
}
