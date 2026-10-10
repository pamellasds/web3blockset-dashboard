import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import ChartCard from "../common/ChartCard";
import { CHART_COLORS } from "../../utils/chartColors";
import { formatCompact } from "../../utils/formatNumber";
import type { YearlyTrend } from "../../types";

export default function YearlyTrendsChart({ data }: { data: YearlyTrend[] }) {
  return (
    <ChartCard title="Issues and Pull Requests Over Time" subtitle="Yearly creation volume by type">
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="year" tick={{ fontSize: 12 }} />
          <YAxis tickFormatter={formatCompact} tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value, name) => [Number(value).toLocaleString(), name]}
            labelFormatter={(label) => `Year: ${label}`}
          />
          <Legend />
          <Area type="monotone" dataKey="prs" name="Pull Requests" stackId="1" fill={CHART_COLORS.pr} stroke={CHART_COLORS.pr} fillOpacity={0.6} />
          <Area type="monotone" dataKey="issues" name="Issues" stackId="1" fill={CHART_COLORS.issue} stroke={CHART_COLORS.issue} fillOpacity={0.6} />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
