import type { Interview, Reminder, ReminderStatus } from "@/types/activity";

import { apiRequest } from "./client";

export const interviewsApi = {
  upcoming: (limit: number) =>
    apiRequest<Interview[]>("/interviews", { query: { upcoming: true, limit } }),
};

export const remindersApi = {
  open: () => apiRequest<Reminder[]>("/reminders", { query: { status: "OPEN" } }),

  setStatus: (id: string, status: ReminderStatus) =>
    apiRequest<Reminder>(`/reminders/${id}`, { method: "PATCH", body: { status } }),
};
