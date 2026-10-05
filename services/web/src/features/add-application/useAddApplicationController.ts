import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";

import { useToast } from "@/components/toast/useToast";
import { applicationsApi } from "@/lib/api/applications";
import { applicationDependentKeys } from "@/lib/api/queryKeys";
import { SOURCE_LABEL } from "@/lib/status";
import type { ApplicationSource } from "@/types/common";

import {
  EMPTY_APPLICATION,
  addApplicationSchema,
  toApplicationCreate,
  type AddApplicationValues,
} from "./addApplicationSchema";

export const STAGE_OPTIONS = [
  { value: "APPLIED", label: "Applied" },
  { value: "WISHLIST", label: "Wishlist" },
];

export const SOURCE_OPTIONS = (Object.keys(SOURCE_LABEL) as ApplicationSource[]).map((value) => ({
  value,
  label: SOURCE_LABEL[value],
}));

export function useAddApplicationController(onClose: () => void) {
  const toast = useToast();
  const queryClient = useQueryClient();

  const form = useForm<AddApplicationValues>({
    resolver: zodResolver(addApplicationSchema),
    defaultValues: EMPTY_APPLICATION,
  });

  const create = useMutation({
    mutationFn: (values: AddApplicationValues) =>
      applicationsApi.create(toApplicationCreate(values)),
    onSuccess: () => {
      toast.success("POST /api/v1/applications · 201 Created");
      applicationDependentKeys.forEach((queryKey) => queryClient.invalidateQueries({ queryKey }));
      onClose();
    },
    onError: toast.fromError,
  });

  return {
    register: form.register,
    errors: form.formState.errors,
    onSubmit: form.handleSubmit((values) => create.mutate(values)),
    isSaving: create.isPending,
    onCancel: onClose,
  };
}
