import { Button } from "@/components/ui/Button";
import { CompanyAvatar } from "@/components/ui/CompanyAvatar";
import type { Match } from "@/types/match";

import { jobMeta } from "../reviewQueueModel";

import { KitPanel } from "./KitPanel";
import { ScoreMeter } from "./ScoreMeter";
import { SkillChips } from "./SkillChips";

interface Props {
  match: Match;
  kitOpen: boolean;
  busy: boolean;
  onToggleKit: () => void;
  onApprove: () => void;
  onSkip: () => void;
  onCopyKit: () => void;
}

export function MatchCard({ match, kitOpen, busy, ...actions }: Props) {
  const { job } = match;

  return (
    <article
      aria-label={`${job.title} at ${job.company_name}`}
      className="border-line bg-surface flex flex-col gap-3.5 rounded-[14px] border p-5"
    >
      <div className="flex flex-wrap items-start gap-4">
        <CompanyAvatar name={job.company_name} size={44} />
        <div className="flex min-w-0 flex-[1_1_260px] flex-col gap-1">
          <div className="text-base font-bold">{job.title}</div>
          <div className="text-muted text-[13px]">{jobMeta(job)}</div>
        </div>
        <ScoreMeter score={match.score} />
      </div>

      <SkillChips label="Matched" items={match.matched_skills} tone="match" />
      <SkillChips label="Gaps" items={match.gaps} tone="gap" />

      <div className="text-ink-3 text-[13px]">
        Suggested resume:{" "}
        <strong>{match.suggested_resume_variant?.name ?? "your general resume"}</strong>
      </div>

      {kitOpen && <KitPanel match={match} onCopy={actions.onCopyKit} />}

      <div className="flex flex-wrap gap-2">
        <Button onClick={actions.onApprove} disabled={busy}>
          Approve &amp; open apply page
        </Button>
        <Button variant="secondary" onClick={actions.onToggleKit} aria-expanded={kitOpen}>
          {kitOpen ? "Hide kit" : "View kit"}
        </Button>
        <Button variant="ghost" onClick={actions.onSkip} disabled={busy}>
          Skip
        </Button>
      </div>
    </article>
  );
}
