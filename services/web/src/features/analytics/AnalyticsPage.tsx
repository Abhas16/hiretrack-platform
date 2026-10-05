import { KpiGrid } from "@/components/ui/KpiCard";
import { QueryState } from "@/components/ui/QueryState";

import { FunnelCard } from "./components/FunnelCard";
import { VariantsCard } from "./components/VariantsCard";
import { WeeklyChart } from "./components/WeeklyChart";
import { useAnalyticsController } from "./useAnalyticsController";

export function AnalyticsPage() {
  const c = useAnalyticsController();

  return (
    <QueryState isLoading={c.isLoading} error={c.error}>
      <div className="flex flex-col gap-4">
        <KpiGrid kpis={c.kpis} />
        <div className="grid grid-cols-[repeat(auto-fit,minmax(340px,1fr))] gap-4">
          <WeeklyChart weeks={c.weeks} />
          <FunnelCard funnel={c.funnel} sources={c.sources} />
        </div>
        <VariantsCard variants={c.variants} />
      </div>
    </QueryState>
  );
}
