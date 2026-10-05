import type {
  PracticeMeta,
  PracticeSession,
  PracticeSessionCreate,
  PracticeSessionSummary,
} from "@/types/practice";

import { apiRequest } from "./client";

export const practiceApi = {
  meta: () => apiRequest<PracticeMeta>("/practice/meta"),

  sessions: () => apiRequest<PracticeSessionSummary[]>("/practice/sessions"),

  session: (id: string) => apiRequest<PracticeSession>(`/practice/sessions/${id}`),

  start: (body: PracticeSessionCreate) =>
    apiRequest<PracticeSession>("/practice/sessions", { method: "POST", body }),

  answer: (id: string, answer: string) =>
    apiRequest<PracticeSession>(`/practice/sessions/${id}/answers`, {
      method: "POST",
      body: { answer },
    }),
};
