/**
 * Runtime config, loaded from /config.json before the app renders.
 *
 * The same built image runs in every environment: the container writes /config.json at
 * start-up from env vars, so the API URL is never baked into the JavaScript bundle.
 */
import { z } from "zod";

const RuntimeConfigSchema = z.object({
  apiBaseUrl: z.url(),
  environment: z.string().default("unknown"),
  version: z.string().default("unknown"),
});

export type RuntimeConfig = z.infer<typeof RuntimeConfigSchema>;

let current: RuntimeConfig | null = null;

export async function loadConfig(fetchFn: typeof fetch = fetch): Promise<RuntimeConfig> {
  const response = await fetchFn("/config.json", { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Could not load /config.json (HTTP ${response.status})`);
  }
  const parsed = RuntimeConfigSchema.safeParse(await response.json());
  if (!parsed.success) {
    throw new Error(`Invalid /config.json: ${parsed.error.issues[0]?.message ?? "unknown"}`);
  }
  current = { ...parsed.data, apiBaseUrl: parsed.data.apiBaseUrl.replace(/\/+$/, "") };
  return current;
}

export function getConfig(): RuntimeConfig {
  if (!current) throw new Error("Runtime config not loaded yet");
  return current;
}

export function setConfigForTests(config: RuntimeConfig): void {
  current = config;
}
