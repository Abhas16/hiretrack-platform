import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm, useWatch } from "react-hook-form";
import { useNavigate } from "react-router";

import { useToast } from "@/components/toast/useToast";
import { applicationsApi } from "@/lib/api/applications";
import { practiceApi } from "@/lib/api/practice";
import { queryKeys } from "@/lib/api/queryKeys";
import type { ApplicationQuery } from "@/types/application";

import { providerLabel } from "./practiceModel";
import {
  START_DEFAULTS,
  startSchema,
  toSessionCreate,
  type StartOutput,
  type StartValues,
} from "./startSchema";

// Applications worth practising for: ones you've applied to or are interviewing for.
const ACTIVE_APPLICATIONS: ApplicationQuery = {
  status: ["APPLIED", "INTERVIEW", "OFFER"],
  sort: "-updated_at",
  page_size: 100,
};

export function usePracticeController() {
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const meta = useQuery({ queryKey: queryKeys.practice.meta, queryFn: practiceApi.meta });
  const sessions = useQuery({
    queryKey: queryKeys.practice.sessions,
    queryFn: practiceApi.sessions,
  });
  const applications = useQuery({
    queryKey: queryKeys.applications.list(ACTIVE_APPLICATIONS),
    queryFn: () => applicationsApi.list(ACTIVE_APPLICATIONS),
  });

  const form = useForm<StartValues, unknown, StartOutput>({
    resolver: zodResolver(startSchema),
    defaultValues: START_DEFAULTS,
  });
  const selectedTopics = useWatch({ control: form.control, name: "topics" });

  const start = useMutation({
    mutationFn: (values: StartOutput) => practiceApi.start(toSessionCreate(values)),
    onSuccess: (session) => {
      toast.success("POST /api/v1/practice/sessions · 201 Created");
      void queryClient.invalidateQueries({ queryKey: queryKeys.practice.sessions });
      navigate(`/practice/${session.id}`);
    },
    onError: toast.fromError,
  });

  const applicationOptions = [
    { value: "", label: "Not linked — practise for any role" },
    ...(applications.data?.items ?? []).map((app) => ({
      value: app.id,
      label: `${app.company.name} · ${app.role}`,
    })),
  ];

  /** Picking an application fills in its role (if the role box is still empty). */
  const onApplicationChange = (applicationId: string) => {
    form.setValue("applicationId", applicationId);
    const app = applications.data?.items.find((item) => item.id === applicationId);
    if (app && !form.getValues("role")) form.setValue("role", app.role);
  };

  const toggleTopic = (id: string) => {
    const current = form.getValues("topics");
    const next = current.includes(id) ? current.filter((t) => t !== id) : [...current, id];
    form.setValue("topics", next);
  };

  return {
    providerText: meta.data ? providerLabel(meta.data.provider) : "",
    topics: meta.data?.topics ?? [],
    selectedTopics,
    toggleTopic,
    questionCounts: [3, 4, 5, 6, 7, 8].map((n) => ({ value: String(n), label: `${n} questions` })),
    applicationOptions,
    onApplicationChange,
    register: form.register,
    errors: form.formState.errors,
    onSubmit: form.handleSubmit((values) => start.mutate(values)),
    isStarting: start.isPending,
    history: {
      items: sessions.data ?? [],
      isLoading: sessions.isLoading,
      error: sessions.error,
      topics: meta.data?.topics ?? [],
    },
  };
}
