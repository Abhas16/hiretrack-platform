import type { Credentials, Registration, TokenResponse, User } from "@/types/auth";

import { apiRequest } from "./client";

export const authApi = {
  login: (credentials: Credentials) =>
    apiRequest<TokenResponse>("/auth/login", { method: "POST", body: credentials }),

  register: (registration: Registration) =>
    apiRequest<User>("/auth/register", { method: "POST", body: registration }),

  me: () => apiRequest<User>("/auth/me"),
};
