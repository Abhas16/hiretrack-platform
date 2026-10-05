import { Card } from "@/components/ui/Card";
import { CompanyAvatar } from "@/components/ui/CompanyAvatar";
import { EmptyText, QueryState } from "@/components/ui/QueryState";
import { formatDateTime } from "@/lib/format";
import type { Interview } from "@/types/activity";

interface Props {
  items: Interview[];
  isLoading: boolean;
  error: unknown;
}

export function UpcomingInterviewsCard({ items, isLoading, error }: Props) {
  return (
    <Card title="Upcoming interviews">
      <QueryState isLoading={isLoading} error={error}>
        {items.length === 0 && <EmptyText>No interviews scheduled.</EmptyText>}
        {items.map((interview) => (
          <div
            key={interview.id}
            className="bg-warm-soft flex items-center gap-3.5 rounded-[10px] p-3"
          >
            <CompanyAvatar name={interview.application.company_name} size={40} />
            <div className="flex min-w-0 flex-col gap-0.5">
              <div className="text-sm font-semibold">
                {interview.application.company_name} · {interview.application.role}
              </div>
              <div className="text-warm-ink text-[13px]">
                {interview.round_name}
                {interview.scheduled_at && ` · ${formatDateTime(interview.scheduled_at)}`}
              </div>
            </div>
          </div>
        ))}
      </QueryState>
    </Card>
  );
}
