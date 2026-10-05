import { KpiGrid } from "@/components/ui/KpiCard";
import { QueryState } from "@/components/ui/QueryState";

import { FollowUpsCard } from "./components/FollowUpsCard";
import { PipelineCard } from "./components/PipelineCard";
import { UpcomingInterviewsCard } from "./components/UpcomingInterviewsCard";
import { useDashboardController } from "./useDashboardController";

export function DashboardPage() {
  const c = useDashboardController();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="m-0 text-xl font-bold">{c.greeting}</h2>
        <p className="text-muted m-0 text-sm">
          Here&apos;s where your job search stands this week.
        </p>
      </div>

      <QueryState isLoading={c.summary.isLoading} error={c.summary.error}>
        <KpiGrid kpis={c.summary.kpis} />
        <PipelineCard segments={c.summary.pipeline} />
      </QueryState>

      <div className="grid grid-cols-[repeat(auto-fit,minmax(320px,1fr))] gap-4">
        <UpcomingInterviewsCard {...c.upcoming} />
        <FollowUpsCard
          items={c.reminders.items}
          isLoading={c.reminders.isLoading}
          error={c.reminders.error}
          pendingId={c.reminders.pendingId}
          onDone={c.reminders.markDone}
        />
      </div>
    </div>
  );
}
