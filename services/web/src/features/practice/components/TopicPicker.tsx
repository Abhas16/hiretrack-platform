import type { PracticeTopic } from "@/types/practice";

interface Props {
  topics: PracticeTopic[];
  selected: string[];
  onToggle: (id: string) => void;
}

export function TopicPicker({ topics, selected, onToggle }: Props) {
  return (
    <fieldset className="m-0 flex flex-col gap-2 border-0 p-0">
      <legend className="text-ink-3 mb-1.5 text-[13px] font-semibold">
        Topics <span className="text-muted font-normal">(leave empty to pick from the role)</span>
      </legend>
      <div className="flex flex-wrap gap-2">
        {topics.map((topic) => {
          const on = selected.includes(topic.id);
          return (
            <button
              key={topic.id}
              type="button"
              aria-pressed={on}
              onClick={() => onToggle(topic.id)}
              className={`min-h-9 cursor-pointer rounded-full px-3.5 text-[13px] font-semibold ${
                on
                  ? "border-ink bg-ink text-canvas border"
                  : "border-line-strong bg-surface text-ink-3 hover:bg-canvas border"
              }`}
            >
              {topic.label}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
