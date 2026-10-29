import type { Page } from "@/types/common";
import type {
  ApproveResponse,
  Match,
  MatchProfile,
  MatchProfileUpdate,
  MatchQuery,
} from "@/types/match";

import { apiRequest } from "./client";

export const matchesApi = {
  list: (query: MatchQuery) => apiRequest<Page<Match>>("/matches", { query: { ...query } }),

  approve: (id: string) =>
    apiRequest<ApproveResponse>(`/matches/${id}/approve`, { method: "POST" }),

  skip: (id: string) => apiRequest<Match>(`/matches/${id}/skip`, { method: "POST" }),

  profile: () => apiRequest<MatchProfile>("/match-profile"),

  saveProfile: (body: MatchProfileUpdate) =>
    apiRequest<MatchProfile>("/match-profile", { method: "PUT", body }),

  skills: () => apiRequest<{ skills: string[] }>("/match-profile/skills"),
};
