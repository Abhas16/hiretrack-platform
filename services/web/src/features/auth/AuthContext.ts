import { createContext } from "react";

import type { User } from "@/types/auth";

export interface AuthState {
  isAuthenticated: boolean;
  /** Loaded from GET /auth/me after login; null while loading. */
  user: User | null;
  signIn: (accessToken: string) => void;
  signOut: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);
