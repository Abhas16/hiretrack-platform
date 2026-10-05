export interface BarRowData {
  label: string;
  count: number;
  /** Bar width, 0..100 */
  widthPercent: number;
  /** Full Tailwind class for the bar colour, e.g. "bg-[#2F5BEA]" */
  colorClass: string;
}

/** A labelled horizontal bar: used by the funnel and "by source" lists. */
export function BarRow({ label, count, widthPercent, colorClass }: BarRowData) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="text-ink-3 flex justify-between text-[13px]">
        <span>{label}</span>
        <strong className="font-mono">{count}</strong>
      </div>
      <div className="bg-track h-3 overflow-hidden rounded-md">
        <div className={`h-full rounded-md ${colorClass}`} style={{ width: `${widthPercent}%` }} />
      </div>
    </div>
  );
}
