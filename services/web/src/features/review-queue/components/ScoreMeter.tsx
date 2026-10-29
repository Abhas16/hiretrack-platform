import { scoreTone } from "../reviewQueueModel";

export function ScoreMeter({ score }: { score: number }) {
  const tone = scoreTone(score);
  return (
    <div className="flex min-w-[120px] flex-col items-end gap-1.5">
      <div className={`font-mono text-[15px] font-bold ${tone.text}`}>{score}% match</div>
      <div
        role="meter"
        aria-label="Match score"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={score}
        className="bg-track h-1.5 w-[120px] overflow-hidden rounded-[3px]"
      >
        <div className={`h-full ${tone.bar}`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}
