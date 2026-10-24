import { EmptyText, QueryState } from "@/components/ui/QueryState";
import { MatchProfileModal } from "@/features/match-profile/MatchProfileModal";

import { MatchCard } from "./components/MatchCard";
import { ProfileBanner } from "./components/ProfileBanner";
import { ThresholdPills } from "./components/ThresholdPills";
import { useReviewQueueController } from "./useReviewQueueController";

export function ReviewQueuePage() {
  const c = useReviewQueueController();

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-1">
          <p className="text-ink-3 m-0 text-sm">
            New jobs matched to your profile. Approve to open the apply page with your kit ready;
            you always submit yourself.
          </p>
          <span className="text-muted font-mono text-xs">
            job-scout CronJob · every 6h → match-scorer workers (KEDA)
          </span>
        </div>
        <ThresholdPills pills={c.thresholds} onSelect={c.onThreshold} />
      </div>

      <ProfileBanner profile={c.profile} onEdit={c.openProfile} />

      <QueryState isLoading={c.isLoading} error={c.error}>
        {c.items.length === 0 ? (
          <div className="border-line bg-surface rounded-[14px] border p-8 text-center">
            <EmptyText>
              Queue is empty at this threshold. The next scout run will add new matches.
            </EmptyText>
          </div>
        ) : (
          c.items.map((match) => (
            <MatchCard
              key={match.id}
              match={match}
              kitOpen={c.isKitOpen(match.id)}
              busy={c.busyId === match.id}
              onToggleKit={() => c.toggleKit(match.id)}
              onApprove={() => c.onApprove(match)}
              onSkip={() => c.onSkip(match)}
              onCopyKit={() => c.onCopyKit(match)}
            />
          ))
        )}
      </QueryState>

      {c.profileOpen && <MatchProfileModal onClose={c.closeProfile} />}
    </div>
  );
}
