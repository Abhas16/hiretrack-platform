const DAY_MS = 86_400_000;

/** Whole calendar days between an ISO timestamp and `now` (never negative). */
export function daysSince(iso: string, now: Date = new Date()): number {
  return Math.max(0, Math.floor((now.getTime() - new Date(iso).getTime()) / DAY_MS));
}

/** "Updated today" / "Updated yesterday" / "Updated 9 days ago". */
export function updatedText(iso: string, now: Date = new Date()): string {
  const days = daysSince(iso, now);
  if (days === 0) return "Updated today";
  if (days === 1) return "Updated yesterday";
  return `Updated ${days} days ago`;
}

/** "Thu, 8 Oct · 11:00" in the browser's time zone. */
export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  const day = date.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
  const time = date.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  return `${day} · ${time}`;
}

/** "Aug 24" for a YYYY-MM-DD week start (parsed as a local date, not UTC midnight). */
export function formatWeekLabel(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(year ?? 1970, (month ?? 1) - 1, day ?? 1);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/** 0.6 -> "60%" */
export function percent(ratio: number): string {
  return `${Math.round(ratio * 100)}%`;
}

/** "Abhas Mukherjee" -> "AM", "abhas" -> "A" */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const letters = parts.length > 1 ? [parts[0], parts[parts.length - 1]] : parts;
  return letters.map((part) => part?.charAt(0).toUpperCase() ?? "").join("");
}

export function firstName(fullName: string): string {
  return fullName.trim().split(/\s+/)[0] ?? "";
}
