import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useToast } from "@/components/toast/useToast";
import { useAuth } from "@/features/auth/useAuth";
import { interviewsApi, remindersApi } from "@/lib/api/activity";
import { analyticsApi } from "@/lib/api/analytics";
import { queryKeys } from "@/lib/api/queryKeys";
import { firstName } from "@/lib/format";

import { buildKpis, buildPipeline } from "./dashboardModel";

const UPCOMING_LIMIT = 5;

export function useDashboardController() {
  const { user } = useAuth();
  const toast = useToast();
  const queryClient = useQueryClient();

  const summary = useQuery({
    queryKey: queryKeys.analytics.summary,
    queryFn: analyticsApi.summary,
  });
  const upcoming = useQuery({
    queryKey: queryKeys.interviews.upcoming,
    queryFn: () => interviewsApi.upcoming(UPCOMING_LIMIT),
  });
  const reminders = useQuery({ queryKey: queryKeys.reminders.open, queryFn: remindersApi.open });

  const markDone = useMutation({
    mutationFn: (id: string) => remindersApi.setStatus(id, "DONE"),
    onSuccess: (_reminder, id) => {
      toast.success(`PATCH /api/v1/reminders/${id} · 200 OK`);
      void queryClient.invalidateQueries({ queryKey: queryKeys.reminders.open });
    },
    onError: toast.fromError,
  });

  return {
    greeting: user ? `Welcome back, ${firstName(user.full_name)}` : "Welcome back",
    summary: {
      isLoading: summary.isLoading,
      error: summary.error,
      kpis: summary.data ? buildKpis(summary.data) : [],
      pipeline: summary.data ? buildPipeline(summary.data) : [],
    },
    upcoming: { isLoading: upcoming.isLoading, error: upcoming.error, items: upcoming.data ?? [] },
    reminders: {
      isLoading: reminders.isLoading,
      error: reminders.error,
      items: reminders.data ?? [],
      markDone: (id: string) => markDone.mutate(id),
      pendingId: markDone.isPending ? markDone.variables : undefined,
    },
  };
}
