import { Navigate } from "react-router";

import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/fields";

import { useLoginController } from "./useLoginController";

export function LoginPage() {
  const c = useLoginController();
  if (c.isAuthenticated) return <Navigate to="/" replace />;

  const isRegister = c.mode === "register";

  return (
    <div className="flex min-h-screen flex-wrap">
      <div className="bg-sidebar text-sidebar-ink flex flex-[1_1_420px] flex-col justify-between gap-12 p-16">
        <div className="flex items-center gap-3">
          <div className="bg-primary flex size-10 items-center justify-center rounded-[10px] font-mono text-[15px] text-white">
            HT
          </div>
          <div className="text-xl font-bold">HireTrack</div>
        </div>
        <div className="flex max-w-[440px] flex-col gap-4">
          <h1 className="m-0 text-[40px] leading-[1.15] font-bold">
            Every application, interview and follow-up in one board.
          </h1>
          <p className="text-sidebar-text m-0 text-base leading-relaxed">
            Track your job search from wishlist to offer, get reminders when an application goes
            quiet, and see what&apos;s actually working.
          </p>
        </div>
        <div className="text-sidebar-faint font-mono text-xs">{c.buildInfo}</div>
      </div>

      <div className="flex flex-[1_1_420px] items-center justify-center px-6 py-12">
        <form onSubmit={c.onSubmit} noValidate className="flex w-full max-w-[380px] flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <h2 className="m-0 text-[26px] font-bold">
              {isRegister ? "Create account" : "Sign in"}
            </h2>
            <p className="text-muted m-0 text-sm">
              {isRegister
                ? "Start tracking your job search."
                : "Use your HireTrack account to continue."}
            </p>
          </div>
          {isRegister && (
            <TextField
              id="full-name"
              label="Name"
              autoComplete="name"
              error={c.errors.fullName?.message}
              {...c.register("fullName")}
            />
          )}
          <TextField
            id="login-email"
            label="Email"
            type="email"
            autoComplete="email"
            error={c.errors.email?.message}
            {...c.register("email")}
          />
          <TextField
            id="login-pass"
            label="Password"
            type="password"
            autoComplete={isRegister ? "new-password" : "current-password"}
            error={c.errors.password?.message}
            {...c.register("password")}
          />
          <Button type="submit" size="lg" disabled={c.isSubmitting}>
            {c.isSubmitting ? "Please wait…" : isRegister ? "Create account" : "Sign in"}
          </Button>
          <button
            type="button"
            onClick={c.switchMode}
            className="text-primary cursor-pointer border-0 bg-transparent text-sm font-semibold"
          >
            {isRegister ? "Have an account? Sign in" : "New here? Create an account"}
          </button>
          <p className="text-muted m-0 font-mono text-xs">POST /api/v1/auth/login → JWT</p>
        </form>
      </div>
    </div>
  );
}
