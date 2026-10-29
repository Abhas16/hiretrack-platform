const TONES = {
  match: "bg-success-soft text-success",
  gap: "bg-warm-soft text-warm-ink",
};

interface Props {
  label: string;
  items: string[];
  tone: keyof typeof TONES;
}

export function SkillChips({ label, items, tone }: Props) {
  if (items.length === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-ink-3 mr-1 text-xs font-semibold">{label}</span>
      {items.map((item) => (
        <span
          key={item}
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${TONES[tone]}`}
        >
          {item}
        </span>
      ))}
    </div>
  );
}
