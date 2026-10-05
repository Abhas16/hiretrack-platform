import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type KeyboardEvent } from "react";
import { useParams } from "react-router";

import { useToast } from "@/components/toast/useToast";
import { practiceApi } from "@/lib/api/practice";
import { queryKeys } from "@/lib/api/queryKeys";
import type { PracticeSession } from "@/types/practice";

import {
  answeredTurns,
  currentTurn,
  formatScore,
  progressText,
  providerLabel,
  topicLabel,
  weakestTopics,
} from "./practiceModel";

const MAX_ANSWER = 5000;

export function usePracticeSessionController() {
  const { sessionId = "" } = useParams();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState("");

  const session = useQuery({
    queryKey: queryKeys.practice.session(sessionId),
    queryFn: () => practiceApi.session(sessionId),
  });
  const meta = useQuery({ queryKey: queryKeys.practice.meta, queryFn: practiceApi.meta });
  const topics = meta.data?.topics ?? [];

  const submit = useMutation({
    mutationFn: (answer: string) => practiceApi.answer(sessionId, answer),
    onSuccess: (updated: PracticeSession) => {
      queryClient.setQueryData(queryKeys.practice.session(sessionId), updated);
      void queryClient.invalidateQueries({ queryKey: queryKeys.practice.sessions });
      setDraft("");
      const scored = answeredTurns(updated).at(-1);
      toast.success(`Answer scored ${formatScore(scored?.score ?? null)}`);
    },
    onError: toast.fromError,
  });

  const trimmed = draft.trim();
  const canSubmit = trimmed.length > 0 && trimmed.length <= MAX_ANSWER && !submit.isPending;
  const send = () => canSubmit && submit.mutate(trimmed);

  const data = session.data;
  return {
    isLoading: session.isLoading,
    error: session.error,
    role: data?.role ?? "",
    providerText: data ? providerLabel(data.provider) : "",
    progress: data ? progressText(data) : "",
    isCompleted: data?.status === "COMPLETED",
    averageScore: formatScore(data?.average_score ?? null),
    studyNext: data ? weakestTopics(data).map((id) => topicLabel(topics, id)) : [],
    answered: data ? answeredTurns(data) : [],
    current: data ? currentTurn(data) : undefined,
    topicName: (id: string) => topicLabel(topics, id),
    composer: {
      draft,
      setDraft,
      maxLength: MAX_ANSWER,
      canSubmit,
      isEvaluating: submit.isPending,
      send,
      // Ctrl+Enter (Cmd+Enter on Mac) sends, like most chat apps.
      onKeyDown: (event: KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
          event.preventDefault();
          send();
        }
      },
    },
  };
}
