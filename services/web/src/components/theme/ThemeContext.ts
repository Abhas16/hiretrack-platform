import { createContext } from "react";

import type { ResolvedTheme, ThemePreference } from "./themeStorage";

export interface ThemeState {
  /** What the user chose. */
  preference: ThemePreference;
  /** What is actually shown ("system" resolved to light or dark). */
  resolved: ResolvedTheme;
  setPreference: (preference: ThemePreference) => void;
}

export const ThemeContext = createContext<ThemeState | null>(null);
