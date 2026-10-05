import { Card } from "@/components/ui/Card";
import { EmptyText } from "@/components/ui/QueryState";

import type { VariantRow } from "../analyticsModel";

/** Which resume version gets the most interviews — the most actionable insight. */
export function VariantsCard({ variants }: { variants: VariantRow[] }) {
  return (
    <Card title="By resume variant" subtitle="interview rate">
      {variants.length === 0 && <EmptyText>No applications yet.</EmptyText>}
      {variants.map((variant) => (
        <div
          key={variant.name}
          className="border-track flex items-center justify-between gap-3 border-t pt-3 first-of-type:border-0 first-of-type:pt-0"
        >
          <div className="flex min-w-0 flex-col gap-0.5">
            <div className="text-sm font-semibold">{variant.name}</div>
            <div className="text-muted text-xs">{variant.detail}</div>
          </div>
          <strong className="font-mono text-lg">{variant.interviewRate}</strong>
        </div>
      ))}
    </Card>
  );
}
