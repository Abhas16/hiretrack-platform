interface Props {
  skills: string[];
  selected: Record<string, number>;
  onCycle: (name: string) => void;
  error?: string;
}

/** Click a skill to add it (weight 3), click again to raise it up to 5, once more to remove. */
export function SkillWeightPicker({ skills, selected, onCycle, error }: Props) {
  const count = Object.keys(selected).length;

  return (
    <fieldset className="m-0 flex flex-col gap-2 border-0 p-0">
      <legend className="text-ink-3 mb-1.5 text-[13px] font-semibold">
        Your skills{" "}
        <span className="text-muted font-normal">({count} picked · click to weight 1-5)</span>
      </legend>
      <div className="flex max-h-52 flex-wrap gap-2 overflow-y-auto pr-1">
        {skills.map((name) => {
          const weight = selected[name];
          const on = weight !== undefined;
          return (
            <button
              key={name}
              type="button"
              aria-pressed={on}
              aria-label={on ? `${name}, weight ${weight}` : name}
              onClick={() => onCycle(name)}
              className={`min-h-8 cursor-pointer rounded-full px-3 text-[13px] font-semibold ${
                on
                  ? "border-ink bg-ink text-canvas border"
                  : "border-line-strong bg-surface text-ink-3 hover:bg-canvas border"
              }`}
            >
              {name}
              {on && <span className="ml-1.5 font-mono text-xs opacity-80">{weight}</span>}
            </button>
          );
        })}
      </div>
      {error && <span className="text-danger text-xs font-medium">{error}</span>}
    </fieldset>
  );
}
