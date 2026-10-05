import { STATUS_LABEL, STATUS_STYLE } from "@/lib/status";
import type { ApplicationStatus } from "@/types/common";

export function StatusBadge({ status }: { status: ApplicationStatus }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLE[status].badge}`}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}

export function StatusDot({ status }: { status: ApplicationStatus }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block size-2.5 flex-none rounded-full ${STATUS_STYLE[status].dot}`}
    />
  );
}
