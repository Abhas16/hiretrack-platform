/** Placeholder until Phase 4 (needs the Smart Apply backend from Phase 3). */
export function ReviewQueuePage() {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <p className="text-ink-3 m-0 text-sm">
          New jobs matched to your profile. Approve to open the apply page with your kit ready; you
          always submit yourself.
        </p>
        <span className="text-muted font-mono text-xs">
          job-scout CronJob · every 6h → match-scorer workers (KEDA)
        </span>
      </div>
      <div className="border-line bg-surface text-muted rounded-[14px] border p-8 text-center text-sm">
        Smart Apply arrives in Phase 4. The next scout run will fill this queue.
      </div>
    </div>
  );
}
