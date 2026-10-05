import type { Application, ApplicationCreate, ApplicationQuery, Board } from "@/types/application";
import type { ApplicationStatus, Page } from "@/types/common";

import { apiDownload, apiRequest } from "./client";

export const applicationsApi = {
  list: (query: ApplicationQuery) =>
    apiRequest<Page<Application>>("/applications", { query: { ...query } }),

  board: (q?: string) => apiRequest<Board>("/board", { query: { q } }),

  create: (body: ApplicationCreate) =>
    apiRequest<Application>("/applications", { method: "POST", body }),

  changeStatus: (id: string, status: ApplicationStatus) =>
    apiRequest<Application>(`/applications/${id}/status`, { method: "PATCH", body: { status } }),

  exportCsv: (query: Pick<ApplicationQuery, "status" | "q">) =>
    apiDownload("/applications/export.csv", { ...query }),
};
