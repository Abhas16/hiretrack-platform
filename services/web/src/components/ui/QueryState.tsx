import type { ReactNode } from "react";

import { describeError } from "@/lib/api/ApiError";

interface QueryStateProps {
  isLoading: boolean;
  error: unknown;
  children: ReactNode;
}

/** Shows a loading line or an error box instead of the content while data isn't ready. */
export function QueryState({ isLoading, error, children }: QueryStateProps) {
  if (isLoading) {
    return <p className="text-muted m-0 text-sm">Loading…</p>;
  }
  if (error) {
    return (
      <div
        role="alert"
        className="text-danger border-danger-line bg-danger-soft rounded-[14px] border p-5 font-mono text-[13px]"
      >
        {describeError(error)}
      </div>
    );
  }
  return <>{children}</>;
}

export function EmptyText({ children }: { children: ReactNode }) {
  return <p className="text-muted m-0 text-sm">{children}</p>;
}
