import {
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useToast } from "@/components/toast/useToast";
import { applicationsApi } from "@/lib/api/applications";
import { applicationDependentKeys, queryKeys } from "@/lib/api/queryKeys";
import { useSearchQuery } from "@/lib/hooks/useSearchQuery";
import { isApplicationStatus, nextStatus, previousStatus } from "@/lib/status";
import type { Application, Board } from "@/types/application";
import type { ApplicationStatus } from "@/types/common";

import { describeMoveError, moveCard, noStageMessage } from "./boardModel";

interface MoveRequest {
  app: Application;
  target: ApplicationStatus;
}

export function useBoardController() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { debouncedQuery } = useSearchQuery();
  const boardKey = queryKeys.applications.board(debouncedQuery);

  const board = useQuery({
    queryKey: boardKey,
    queryFn: () => applicationsApi.board(debouncedQuery || undefined),
  });

  const move = useMutation({
    mutationFn: ({ app, target }: MoveRequest) => applicationsApi.changeStatus(app.id, target),
    onMutate: async ({ app, target }) => {
      await queryClient.cancelQueries({ queryKey: boardKey });
      const previous = queryClient.getQueryData<Board>(boardKey);
      queryClient.setQueryData<Board>(boardKey, (current) => moveCard(current, app.id, target));
      return { previous };
    },
    onError: (error, { app, target }, context) => {
      queryClient.setQueryData(boardKey, context?.previous); // undo the optimistic move
      toast.error(describeMoveError(error, app.status, target));
    },
    onSuccess: (_updated, { app }) => {
      toast.success(`PATCH /api/v1/applications/${app.id}/status · 200 OK`);
    },
    onSettled: () => {
      applicationDependentKeys.forEach((queryKey) => queryClient.invalidateQueries({ queryKey }));
    },
  });

  // distance: 8 -> a click on a card's buttons isn't mistaken for the start of a drag.
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor),
  );

  const requestMove = (
    app: Application,
    target: ApplicationStatus | null,
    end: "before" | "after",
  ) => {
    if (target === null) {
      toast.error(noStageMessage(app.status, end));
      return;
    }
    if (target !== app.status) move.mutate({ app, target });
  };

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    const app = active.data.current?.app as Application | undefined;
    const target = over?.id;
    if (app && isApplicationStatus(target)) requestMove(app, target, "after");
  };

  return {
    isLoading: board.isLoading,
    error: board.error,
    columns: board.data?.columns ?? [],
    sensors,
    onDragEnd,
    moveNext: (app: Application) => requestMove(app, nextStatus(app.status), "after"),
    movePrevious: (app: Application) => requestMove(app, previousStatus(app.status), "before"),
    reject: (app: Application) => requestMove(app, "REJECTED", "after"),
  };
}
