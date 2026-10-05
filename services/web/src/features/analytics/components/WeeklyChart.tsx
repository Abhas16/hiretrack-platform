import { Bar, BarChart, LabelList, ResponsiveContainer, Tooltip, XAxis } from "recharts";

import { CHART_COLORS } from "@/components/theme/chartColors";
import { useTheme } from "@/components/theme/useTheme";
import { Card } from "@/components/ui/Card";

import type { WeekBar } from "../analyticsModel";

export function WeeklyChart({ weeks }: { weeks: WeekBar[] }) {
  const colors = CHART_COLORS[useTheme().resolved];

  return (
    <Card title="Applications sent per week">
      <div className="h-[230px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={weeks} margin={{ top: 20, right: 4, bottom: 0, left: 4 }}>
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={{ stroke: colors.axis }}
              tick={{ fontSize: 12, fill: colors.tick }}
            />
            <Tooltip
              cursor={{ fill: colors.cursor }}
              contentStyle={{ background: colors.tooltipBg, borderColor: colors.axis }}
            />
            <Bar
              dataKey="count"
              name="Applications"
              fill={colors.bar}
              radius={[6, 6, 0, 0]}
              maxBarSize={44}
            >
              <LabelList
                dataKey="count"
                position="top"
                style={{ fontSize: 12, fill: colors.label, fontFamily: "JetBrains Mono" }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
