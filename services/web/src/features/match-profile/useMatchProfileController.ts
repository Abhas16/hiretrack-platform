import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";

import { useToast } from "@/components/toast/useToast";
import { matchesApi } from "@/lib/api/matches";
import { queryKeys } from "@/lib/api/queryKeys";

import {
  PROFILE_DEFAULTS,
  matchProfileSchema,
  toFormValues,
  toProfileUpdate,
  type MatchProfileOutput,
  type MatchProfileValues,
} from "./matchProfileSchema";

/** A skill's weight cycles 1 -> 2 -> ... -> 5 -> removed when you click its chip. */
export function nextWeight(current: number | undefined): number | undefined {
  if (current === undefined) return 3; // first click: a solid "I use this" default
  return current >= 5 ? undefined : current + 1;
}

export function useMatchProfileController(onClose: () => void) {
  const toast = useToast();
  const queryClient = useQueryClient();

  const profile = useQuery({ queryKey: queryKeys.matches.profile, queryFn: matchesApi.profile });
  const skills = useQuery({ queryKey: queryKeys.matches.skills, queryFn: matchesApi.skills });

  const form = useForm<MatchProfileValues, unknown, MatchProfileOutput>({
    resolver: zodResolver(matchProfileSchema),
    defaultValues: PROFILE_DEFAULTS,
  });
  const selected = useWatch({ control: form.control, name: "skills" });

  // Fill the form once the saved profile has loaded.
  useEffect(() => {
    if (profile.data) form.reset(toFormValues(profile.data));
  }, [profile.data, form]);

  const save = useMutation({
    mutationFn: (values: MatchProfileOutput) => matchesApi.saveProfile(toProfileUpdate(values)),
    onSuccess: (saved) => {
      toast.success("PUT /api/v1/match-profile · 200 OK · new jobs are scored with it");
      queryClient.setQueryData(queryKeys.matches.profile, saved);
      onClose();
    },
    onError: toast.fromError,
  });

  const cycleSkill = (name: string) => {
    const next = { ...form.getValues("skills") };
    const weight = nextWeight(next[name]);
    if (weight === undefined) delete next[name];
    else next[name] = weight;
    form.setValue("skills", next, { shouldValidate: form.formState.isSubmitted });
  };

  // Skills already in the profile but no longer in the taxonomy still show, so they can be removed.
  const allSkills = [
    ...new Set([...(skills.data?.skills ?? []), ...Object.keys(selected ?? {})]),
  ].sort();

  return {
    isLoading: profile.isLoading || skills.isLoading,
    error: profile.error ?? skills.error,
    allSkills,
    selected: selected ?? {},
    cycleSkill,
    register: form.register,
    errors: form.formState.errors,
    // A record field's errors type is a map per key; the "pick at least one" message is its own.
    skillsError: (form.formState.errors.skills as { message?: string } | undefined)?.message,
    onSubmit: form.handleSubmit((values) => save.mutate(values)),
    isSaving: save.isPending,
    onCancel: onClose,
  };
}
