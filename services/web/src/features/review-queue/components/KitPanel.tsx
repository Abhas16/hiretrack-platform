import { Button } from "@/components/ui/Button";
import type { Match } from "@/types/match";

const HEADING = "text-ink-3 text-xs font-bold tracking-[0.6px] uppercase";

export function KitPanel({ match, onCopy }: { match: Match; onCopy: () => void }) {
  return (
    <div className="border-line bg-soft flex flex-col gap-3 rounded-xl border p-4">
      <div className="flex flex-col gap-1.5">
        <div className={HEADING}>Cover note</div>
        <p className="text-ink-2 m-0 text-sm leading-relaxed whitespace-pre-line">
          {match.cover_note}
        </p>
      </div>
      <div className="flex flex-col gap-1.5">
        <div className={HEADING}>Tailored bullets</div>
        <ul className="text-ink-2 m-0 flex flex-col gap-1 pl-5 text-sm leading-normal">
          {match.resume_bullets.map((bullet) => (
            <li key={bullet}>{bullet}</li>
          ))}
        </ul>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="secondary" size="sm" onClick={onCopy}>
          Copy kit
        </Button>
        <span className="text-muted font-mono text-xs">
          {match.kit_provider === "anthropic" ? "written by Claude" : "template"} · a draft: edit
          before you send
        </span>
      </div>
    </div>
  );
}
