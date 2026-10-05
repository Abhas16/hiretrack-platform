import { useState } from "react";
import { useLocation, useNavigate } from "react-router";

import { useAuth } from "@/features/auth/useAuth";
import { getConfig } from "@/lib/config";
import { useSearchQuery } from "@/lib/hooks/useSearchQuery";

import { NAV_ITEMS, SEARCHABLE_PATHS, pageTitle } from "./navItems";

export function useAppLayoutController() {
  const { signOut } = useAuth();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { query, setQuery } = useSearchQuery();
  const [isAddOpen, setAddOpen] = useState(false);
  const { environment, version } = getConfig();

  const onSearch = (value: string) => {
    if (SEARCHABLE_PATHS.has(pathname)) {
      setQuery(value);
    } else {
      // Typing on the dashboard/analytics jumps to the applications table (as in the design).
      navigate(`/applications?q=${encodeURIComponent(value)}`);
    }
  };

  return {
    navItems: NAV_ITEMS.map((item) => ({ ...item, active: pageTitle(pathname) === item.label })),
    title: pageTitle(pathname),
    query,
    onSearch,
    buildInfo: [`web ${version}`, environment],
    isAddOpen,
    openAdd: () => setAddOpen(true),
    closeAdd: () => setAddOpen(false),
    signOut,
  };
}
