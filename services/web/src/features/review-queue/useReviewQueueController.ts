import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { useToast } from "@/components/toast/useToast";
import { matchesApi } from "@/lib/api/matches";
import { applicationDependentKeys, queryKeys } from "@/lib/api/queryKeys";
import type { Match, MatchQuery } from "@/types/match";

import { DEFAULT_THRESHOLD, THRESHOLDS, kitText } from "./reviewQueueModel";

export function useReviewQueueController() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [threshold, setThreshold] = useState(DEFAULT_THRESHOLD);
  const [openKits, setOpenKits] = useState<Set<string>>(new Set());
  const [profileOpen, setProfileOpen] = useState(false);

  const query: MatchQuery = { status: "NEW", min_score: threshold, page_size: 50 };
  const matches = useQuery({
    queryKey: queryKeys.matches.list(query),
    queryFn: () => matchesApi.list(query),
  });
  const profile = useQuery({ queryKey: queryKeys.matches.profile, queryFn: matchesApi.profile });

  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.matches.all });
    applicationDependentKeys.forEach((queryKey) => queryClient.invalidateQueries({ queryKey }));
  };

  const approve = useMutation({
    // `tab` is opened BEFORE the request, while we are still inside the click handler:
    // browsers block window.open() that happens later (after an await) as a popup.
    mutationFn: ({ match }: { match: Match; tab: Window | null }) => matchesApi.approve(match.id),
    onSuccess: (result, { tab }) => {
      if (tab) tab.location.href = result.job_url;
      else window.open(result.job_url, "_blank", "noopener");
      toast.success(`POST /api/v1/matches/{id}/approve · 200 OK · added to Applied`);
      refresh();
    },
    onError: (error, { tab }) => {
      tab?.close();
      toast.fromError(error);
    },
  });

  const skip = useMutation({
    mutationFn: (match: Match) => matchesApi.skip(match.id),
    onSuccess: () => {
      toast.success("POST /api/v1/matches/{id}/skip · 200 OK");
      void queryClient.invalidateQueries({ queryKey: queryKeys.matches.all });
    },
    onError: toast.fromError,
  });

  const onApprove = (match: Match) => {
    const tab = window.open("", "_blank");
    if (tab) tab.opener = null; // the job site must not be able to control this tab
    approve.mutate({ match, tab });
  };

  const onCopyKit = async (match: Match) => {
    try {
      await navigator.clipboard.writeText(kitText(match));
      toast.success("Kit copied to clipboard");
    } catch {
      toast.error("Couldn't copy: your browser blocked clipboard access");
    }
  };

  const toggleKit = (id: string) =>
    setOpenKits((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const busyId = approve.isPending
    ? approve.variables?.match.id
    : skip.isPending
      ? skip.variables?.id
      : undefined;

  return {
    thresholds: THRESHOLDS.map((t) => ({ ...t, active: t.value === threshold })),
    onThreshold: setThreshold,
    items: matches.data?.items ?? [],
    total: matches.data?.total ?? 0,
    isLoading: matches.isLoading,
    error: matches.error,
    isKitOpen: (id: string) => openKits.has(id),
    toggleKit,
    onApprove,
    onSkip: (match: Match) => skip.mutate(match),
    onCopyKit: (match: Match) => void onCopyKit(match),
    busyId,
    profile: profile.data,
    profileOpen,
    openProfile: () => setProfileOpen(true),
    closeProfile: () => setProfileOpen(false),
  };
}
