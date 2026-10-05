import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";

import type { IconName } from "@/components/ui/Icon";
import { useTheme } from "@/components/theme/useTheme";
import type { ThemePreference } from "@/components/theme/themeStorage";
import { useAuth } from "@/features/auth/useAuth";
import { getConfig } from "@/lib/config";
import { initials } from "@/lib/format";

export const THEME_OPTIONS: { value: ThemePreference; label: string; icon: IconName }[] = [
  { value: "light", label: "Light", icon: "sun" },
  { value: "dark", label: "Dark", icon: "moon" },
  { value: "system", label: "System", icon: "monitor" },
];

export function useUserMenuController() {
  const { user, signOut } = useAuth();
  const { preference, setPreference } = useTheme();
  const navigate = useNavigate();
  const [isOpen, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const { apiBaseUrl, environment, version } = getConfig();

  const close = useCallback((returnFocus = false) => {
    setOpen(false);
    if (returnFocus) buttonRef.current?.focus();
  }, []);

  // Close on a click outside the menu, or on Escape (focus goes back to the avatar button).
  useEffect(() => {
    if (!isOpen) return;
    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) close();
    };
    const onKeyDown = (event: KeyboardEvent) => event.key === "Escape" && close(true);
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [isOpen, close]);

  return {
    rootRef,
    buttonRef,
    isOpen,
    toggle: () => setOpen((open) => !open),
    name: user?.full_name ?? "",
    email: user?.email ?? "",
    initials: user ? initials(user.full_name) : "",
    theme: preference,
    setTheme: setPreference,
    goToPractice: () => {
      close();
      navigate("/practice");
    },
    // Swagger UI is disabled in prod, so only offer the link elsewhere.
    apiDocsUrl: environment === "prod" ? null : `${apiBaseUrl}/docs`,
    buildInfo: `web ${version} · ${environment}`,
    signOut: () => {
      close();
      signOut();
    },
  };
}
