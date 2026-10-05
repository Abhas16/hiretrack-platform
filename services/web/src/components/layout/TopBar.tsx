import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";

import { UserMenu } from "./UserMenu";

interface TopBarProps {
  title: string;
  query: string;
  onSearch: (value: string) => void;
  onAdd: () => void;
}

export function TopBar({ title, query, onSearch, onAdd }: TopBarProps) {
  return (
    <header className="border-line bg-surface flex flex-wrap items-center gap-4 border-b px-8 py-5">
      <h1 className="m-0 flex-[1_1_200px] text-[22px] font-bold">{title}</h1>

      <label
        htmlFor="global-search"
        className="border-line-strong text-muted bg-input flex min-h-11 max-w-[360px] flex-[1_1_260px] items-center gap-2.5 rounded-[10px] border px-3.5"
      >
        <Icon name="search" size={18} />
        <input
          id="global-search"
          type="search"
          placeholder="Search company or role"
          aria-label="Search applications"
          value={query}
          onChange={(event) => onSearch(event.target.value)}
          className="text-ink min-w-0 flex-1 border-0 bg-transparent text-sm outline-none"
        />
      </label>

      <Button size="lg" onClick={onAdd}>
        <Icon name="plus" size={18} strokeWidth={2} />
        Add application
      </Button>

      <UserMenu />
    </header>
  );
}
