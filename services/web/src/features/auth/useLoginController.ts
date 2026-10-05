import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm, useWatch } from "react-hook-form";
import { useLocation, useNavigate } from "react-router";

import { useToast } from "@/components/toast/useToast";
import { authApi } from "@/lib/api/auth";
import { getConfig } from "@/lib/config";

import { authSchema, type AuthFormValues, type AuthMode } from "./authSchema";
import { useAuth } from "./useAuth";

export function useLoginController() {
  const { signIn, isAuthenticated } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const returnTo = (location.state as { from?: string } | null)?.from ?? "/";

  const form = useForm<AuthFormValues>({
    resolver: zodResolver(authSchema),
    defaultValues: { mode: "login", email: "", password: "", fullName: "" },
  });
  const mode = useWatch({ control: form.control, name: "mode" });

  const submit = useMutation({
    mutationFn: async ({ mode, email, password, fullName }: AuthFormValues) => {
      if (mode === "register") {
        await authApi.register({ email, password, full_name: fullName });
        toast.success("POST /api/v1/auth/register · 201 Created");
      }
      return authApi.login({ email, password });
    },
    onSuccess: ({ access_token }) => {
      signIn(access_token);
      toast.success("POST /api/v1/auth/login · 200 OK");
      navigate(returnTo, { replace: true });
    },
    onError: toast.fromError,
  });

  const switchMode = () => {
    const next: AuthMode = mode === "login" ? "register" : "login";
    form.setValue("mode", next);
    form.clearErrors();
  };

  const { environment, version } = getConfig();

  return {
    isAuthenticated,
    mode,
    register: form.register,
    errors: form.formState.errors,
    onSubmit: form.handleSubmit((values) => submit.mutate(values)),
    isSubmitting: submit.isPending,
    switchMode,
    buildInfo: `build ${version} · ${environment}`,
  };
}
