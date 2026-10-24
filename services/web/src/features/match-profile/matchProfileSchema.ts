import { z } from "zod";

import type { MatchProfile, MatchProfileUpdate } from "@/types/match";

/** Mirrors the API's MatchProfileUpdate rules. Lists are typed as comma-separated text. */
export const matchProfileSchema = z.object({
  isActive: z.boolean(),
  skills: z
    .record(z.string(), z.number().int().min(1).max(5))
    .refine((skills) => Object.keys(skills).length > 0, "Pick at least one skill"),
  targetRoles: z.string().max(1000),
  locations: z.string().max(1000),
  remoteOk: z.boolean(),
  yearsExperience: z.coerce.number().int().min(0).max(50),
});

export type MatchProfileValues = z.input<typeof matchProfileSchema>;
export type MatchProfileOutput = z.output<typeof matchProfileSchema>;

export const PROFILE_DEFAULTS: MatchProfileValues = {
  isActive: true,
  skills: {},
  targetRoles: "DevOps Engineer, Platform Engineer, SRE",
  locations: "",
  remoteOk: true,
  yearsExperience: 0,
};

/** "a, b ,, c" -> ["a", "b", "c"] (max 10, like the API) */
export function splitList(text: string): string[] {
  return text
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 10);
}

export function toFormValues(profile: MatchProfile): MatchProfileValues {
  if (!profile.exists) return PROFILE_DEFAULTS;
  return {
    isActive: profile.is_active,
    skills: profile.skills,
    targetRoles: profile.target_roles.join(", "),
    locations: profile.locations.join(", "),
    remoteOk: profile.remote_ok,
    yearsExperience: profile.years_experience,
  };
}

export function toProfileUpdate(values: MatchProfileOutput): MatchProfileUpdate {
  return {
    is_active: values.isActive,
    skills: values.skills,
    target_roles: splitList(values.targetRoles),
    locations: splitList(values.locations),
    remote_ok: values.remoteOk,
    years_experience: values.yearsExperience,
  };
}
