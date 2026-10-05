import type { ResolvedTheme } from "./themeStorage";

/** Recharts draws SVG with explicit colours, so charts need a palette per theme. */
export const CHART_COLORS: Record<
  ResolvedTheme,
  { bar: string; axis: string; tick: string; label: string; cursor: string; tooltipBg: string }
> = {
  light: {
    bar: "#2F5BEA",
    axis: "#E3E6EC",
    tick: "#5A6172",
    label: "#3A4150",
    cursor: "#F4F5F8",
    tooltipBg: "#FFFFFF",
  },
  dark: {
    bar: "#4D74F0",
    axis: "#343A48",
    tick: "#8E95A4",
    label: "#B6BCC8",
    cursor: "#1D212B",
    tooltipBg: "#171A22",
  },
};
