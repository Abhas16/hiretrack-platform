import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyText, QueryState } from "@/components/ui/QueryState";
import type { Reminder } from "@/types/activity";

interface Props {
  items: Reminder[];
  isLoading: boolean;
  error: unknown;
  pendingId?: string;
  onDone: (id: string) => void;
}

export function FollowUpsCard({ items, isLoading, error, pendingId, onDone }: Props) {
  return (
    <Card title="Follow-up reminders" subtitle="reminder-worker CronJob · daily 09:00">
      <QueryState isLoading={isLoading} error={error}>
        {items.length === 0 && <EmptyText>All caught up.</EmptyText>}
        {items.map((reminder) => (
          <div key={reminder.id} className="bg-soft flex items-center gap-3.5 rounded-[10px] p-3">
            <div className="flex min-w-0 flex-1 flex-col gap-0.5">
              {reminder.application && (
                <div className="text-sm font-semibold">
                  {reminder.application.company_name} · {reminder.application.role}
                </div>
              )}
              <div className="text-muted text-[13px]">{reminder.message}</div>
            </div>
            <Button
              variant="secondary"
              size="sm"
              disabled={pendingId === reminder.id}
              onClick={() => onDone(reminder.id)}
            >
              Mark done
            </Button>
          </div>
        ))}
      </QueryState>
    </Card>
  );
}
