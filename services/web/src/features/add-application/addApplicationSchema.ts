import { z } from "zod";

import type { ApplicationCreate } from "@/types/application";

/** Mirrors the API's ApplicationCreate rules so most mistakes are caught before a request. */
export const addApplicationSchema = z.object({
  company: z.string().trim().min(1, "Company is required").max(200),
  role: z.string().trim().min(1, "Role is required").max(200),
  location: z.string().trim().max(200),
  status: z.enum(["APPLIED", "WISHLIST"]),
  source: z.enum([
    "REFERRAL",
    "LINKEDIN",
    "NAUKRI",
    "COMPANY_SITE",
    "GREENHOUSE",
    "LEVER",
    "ASHBY",
    "OTHER",
  ]),
  jobUrl: z.union([z.literal(""), z.url("Enter a full URL (https://…)").max(2000)]),
});

export type AddApplicationValues = z.infer<typeof addApplicationSchema>;

export const EMPTY_APPLICATION: AddApplicationValues = {
  company: "",
  role: "",
  location: "",
  status: "APPLIED",
  source: "COMPANY_SITE",
  jobUrl: "",
};

/** Form values (camelCase, empty strings) -> API body (snake_case, nulls). */
export function toApplicationCreate(values: AddApplicationValues): ApplicationCreate {
  return {
    company_name: values.company,
    role: values.role,
    location: values.location || null,
    status: values.status,
    source: values.source,
    job_url: values.jobUrl || null,
  };
}
