import { CompanyAvatar } from "@/components/ui/CompanyAvatar";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { updatedText } from "@/lib/format";
import { SOURCE_LABEL } from "@/lib/status";
import { safeHttpUrl } from "@/lib/url";
import type { Application } from "@/types/application";

export const CELL = "px-5 py-3.5";

export function ApplicationRow({ app }: { app: Application }) {
  const jobUrl = safeHttpUrl(app.job_url);

  return (
    <tr className="border-track border-t">
      <td className={CELL}>
        <div className="flex items-center gap-2.5">
          <CompanyAvatar name={app.company.name} size={32} />
          <strong className="font-semibold">{app.company.name}</strong>
        </div>
      </td>
      <td className={`${CELL} text-ink-2`}>
        {jobUrl ? (
          <a href={jobUrl} target="_blank" rel="noreferrer noopener">
            {app.role}
          </a>
        ) : (
          app.role
        )}
      </td>
      <td className={`${CELL} text-ink-3`}>{app.location ?? "—"}</td>
      <td className={`${CELL} text-ink-3`}>{SOURCE_LABEL[app.source]}</td>
      <td className={CELL}>
        <StatusBadge status={app.status} />
      </td>
      <td className={`${CELL} text-muted`}>{updatedText(app.updated_at)}</td>
    </tr>
  );
}
