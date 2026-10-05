import type { FilterPill, StatusFilter } from "../applicationsModel";

interface Props {
  pills: FilterPill[];
  onSelect: (value: StatusFilter) => void;
}

export function StatusFilterPills({ pills, onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by status">
      {pills.map((pill) => (
        <button
          key={pill.value}
          type="button"
          aria-pressed={pill.active}
          onClick={() => onSelect(pill.value)}
          className={`min-h-10 cursor-pointer rounded-full px-4 text-[13px] font-semibold ${
            pill.active
              ? "border-ink bg-ink border text-white"
              : "border-line-strong bg-surface text-ink-3 hover:bg-canvas border"
          }`}
        >
          {pill.label}
        </button>
      ))}
    </div>
  );
}
