import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import ChartCard from "../common/ChartCard";
import { CHART_COLORS } from "../../utils/chartColors";
import { formatCompact } from "../../utils/formatNumber";
import type { YearlyTrend } from "../../types";

export default function ProviderCommunityChart({ data }: { data: YearlyTrend[] }) {
  const chartData = data.map((d) => ({
    year: d.year,
    provider: d.providerIssues + d.providerPRs,
    community: d.communityIssues + d.communityPRs,
  }));

  return (
    <ChartCard title="Provider vs Community" subtitle="Records by data source per year">
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="year" tick={{ fontSize: 12 }} />
          <YAxis tickFormatter={formatCompact} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value, name) => [Number(value).toLocaleString(), name]} />
          <Legend />
          <Bar dataKey="provider" name="Provider" fill={CHART_COLORS.provider} radius={[2, 2, 0, 0]} />
          <Bar dataKey="community" name="Community" fill={CHART_COLORS.community} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
