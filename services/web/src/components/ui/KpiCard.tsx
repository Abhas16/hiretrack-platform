export interface Kpi {
  label: string;
  value: string;
  hint?: string;
}

export function KpiCard({ label, value, hint }: Kpi) {
  return (
    <div className="border-line bg-surface flex flex-col gap-2 rounded-[14px] border p-5">
      <div className="text-muted text-[13px] font-semibold">{label}</div>
      <div className="font-mono text-[32px] font-bold tracking-tight">{value}</div>
      {hint && <div className="text-muted text-xs">{hint}</div>}
    </div>
  );
}

export function KpiGrid({ kpis }: { kpis: Kpi[] }) {
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(190px,1fr))] gap-4">
      {kpis.map((kpi) => (
        <KpiCard key={kpi.label} {...kpi} />
      ))}
    </div>
  );
}
