import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { ThemeContext, type ThemeState } from "./ThemeContext";
import {
  applyTheme,
  readPreference,
  resolveTheme,
  writePreference,
  type ResolvedTheme,
  type ThemePreference,
} from "./themeStorage";

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>(readPreference);
  const [resolved, setResolved] = useState<ResolvedTheme>(() => resolveTheme(preference));

  const setPreference = useCallback((next: ThemePreference) => {
    writePreference(next);
    setPreferenceState(next);
    setResolved(resolveTheme(next));
  }, []);

  // Put the theme on <html data-theme="..."> whenever it changes.
  useEffect(() => applyTheme(resolved), [resolved]);

  // In "system" mode, follow the operating system when it switches (e.g. Windows night mode).
  useEffect(() => {
    if (preference !== "system" || !window.matchMedia) return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setResolved(media.matches ? "dark" : "light");
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [preference]);

  const value = useMemo<ThemeState>(
    () => ({ preference, resolved, setPreference }),
    [preference, resolved, setPreference],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
