import { formatScore, scoreTone } from "../practiceModel";

export function ScoreBadge({ score }: { score: number }) {
  const tone = scoreTone(score);
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${tone.className}`}
    >
      <span className="font-mono">{formatScore(score)}</span>
      {tone.label}
    </span>
  );
}
