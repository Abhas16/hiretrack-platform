/** Shown when /config.json is missing or invalid — usually a deployment problem, not a user one. */
export function ConfigErrorScreen({ message }: { message: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div role="alert" className="border-line bg-surface max-w-lg rounded-[14px] border p-6">
        <h1 className="mt-0 text-lg font-bold">HireTrack can&apos;t start</h1>
        <p className="text-danger font-mono text-[13px]">{message}</p>
        <p className="text-muted mb-0 text-sm">
          The container should write <code>/config.json</code> with an <code>apiBaseUrl</code> at
          start-up.
        </p>
      </div>
    </div>
  );
}
