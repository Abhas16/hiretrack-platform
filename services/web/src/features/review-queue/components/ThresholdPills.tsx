interface Props {
  pills: { value: number; label: string; active: boolean }[];
  onSelect: (value: number) => void;
}

export function ThresholdPills({ pills, onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Minimum match score">
      {pills.map((pill) => (
        <button
          key={pill.value}
          type="button"
          aria-pressed={pill.active}
          onClick={() => onSelect(pill.value)}
          className={`min-h-9 cursor-pointer rounded-full px-3.5 text-[13px] font-semibold ${
            pill.active
              ? "border-ink bg-ink text-canvas border"
              : "border-line-strong bg-surface text-ink-3 hover:bg-canvas border"
          }`}
        >
          {pill.label}
        </button>
      ))}
    </div>
  );
}
