import { Link } from "react-router";

import { Icon } from "@/components/ui/Icon";

import type { NavItem } from "./navItems";

interface SidebarProps {
  items: (NavItem & { active: boolean })[];
  buildInfo: string[];
  onSignOut: () => void;
}

const ITEM = "flex min-h-11 items-center gap-3 rounded-[10px] px-3.5 text-sm no-underline";

export function Sidebar({ items, buildInfo, onSignOut }: SidebarProps) {
  return (
    <aside className="bg-sidebar text-sidebar-ink flex flex-[1_1_232px] flex-col gap-7 px-4 py-6 lg:max-w-[260px]">
      <div className="flex items-center gap-3 px-2">
        <div className="bg-primary flex size-9 items-center justify-center rounded-[9px] font-mono text-sm text-white">
          HT
        </div>
        <div className="text-lg font-bold">HireTrack</div>
      </div>

      <nav aria-label="Main" className="flex flex-col gap-1">
        {items.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            aria-current={item.active ? "page" : undefined}
            className={`${ITEM} ${item.active ? "bg-sidebar-active font-semibold text-white" : "text-sidebar-text font-medium hover:text-white"}`}
          >
            <Icon name={item.icon} />
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className="mt-auto flex flex-col gap-3">
        <button
          type="button"
          onClick={onSignOut}
          className={`${ITEM} text-sidebar-text cursor-pointer border-0 bg-transparent text-left font-medium hover:text-white`}
        >
          <Icon name="signOut" />
          <span>Sign out</span>
        </button>
        <div className="bg-sidebar-panel text-sidebar-faint rounded-[10px] px-3.5 py-3 font-mono text-[11px] leading-[1.7]">
          {buildInfo.map((line) => (
            <div key={line}>{line}</div>
          ))}
        </div>
      </div>
    </aside>
  );
}
