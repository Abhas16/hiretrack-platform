import type { IconName } from "@/components/ui/Icon";

export interface NavItem {
  path: string;
  label: string;
  icon: IconName;
}

export const NAV_ITEMS: NavItem[] = [
  { path: "/", label: "Dashboard", icon: "dashboard" },
  { path: "/board", label: "Board", icon: "board" },
  { path: "/review-queue", label: "Review queue", icon: "queue" },
  { path: "/applications", label: "Applications", icon: "applications" },
  { path: "/analytics", label: "Analytics", icon: "analytics" },
  { path: "/practice", label: "Practice interview", icon: "practice" },
];

/** Screens where typing in the top-bar search makes sense; others jump to /applications. */
export const SEARCHABLE_PATHS = new Set(["/board", "/applications"]);

/** Exact match, or the parent section for nested pages (/practice/123 -> "Practice interview"). */
export function pageTitle(pathname: string): string {
  const item =
    NAV_ITEMS.find((nav) => nav.path === pathname) ??
    NAV_ITEMS.find((nav) => nav.path !== "/" && pathname.startsWith(`${nav.path}/`));
  return item?.label ?? "";
}
