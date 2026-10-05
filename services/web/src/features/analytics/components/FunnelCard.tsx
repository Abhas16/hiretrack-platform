import { BarRow, type BarRowData } from "@/components/ui/BarRow";
import { Card } from "@/components/ui/Card";
import { EmptyText } from "@/components/ui/QueryState";

export function FunnelCard({ funnel, sources }: { funnel: BarRowData[]; sources: BarRowData[] }) {
  return (
    <Card title="Funnel">
      {funnel.map((row) => (
        <BarRow key={row.label} {...row} />
      ))}
      <h3 className="mt-2 mb-0 text-[15px] font-bold">By source</h3>
      {sources.length === 0 && <EmptyText>No applications yet.</EmptyText>}
      {sources.map((row) => (
        <BarRow key={row.label} {...row} />
      ))}
    </Card>
  );
}
