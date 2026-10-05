import { Card } from "@/components/ui/Card";
import { StatusDot } from "@/components/ui/StatusBadge";
import { STATUS_STYLE } from "@/lib/status";

import type { PipelineSegment } from "../dashboardModel";

export function PipelineCard({ segments }: { segments: PipelineSegment[] }) {
  return (
    <Card title="Pipeline">
      <div className="bg-track flex h-3.5 overflow-hidden rounded-[7px]">
        {segments.map((segment) => (
          <div
            key={segment.status}
            className={STATUS_STYLE[segment.status].dot}
            style={{ width: `${segment.widthPercent}%` }}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-[18px]">
        {segments.map((segment) => (
          <div key={segment.status} className="text-ink-3 flex items-center gap-2 text-[13px]">
            <StatusDot status={segment.status} />
            {segment.label} <strong className="font-mono">{segment.count}</strong>
          </div>
        ))}
      </div>
    </Card>
  );
}
