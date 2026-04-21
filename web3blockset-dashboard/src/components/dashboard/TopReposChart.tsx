import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import ChartCard from "../common/ChartCard";
import { CHART_COLORS } from "../../utils/chartColors";
import { formatCompact } from "../../utils/formatNumber";
import type { TopRepository } from "../../types";

export default function TopReposChart({ data }: { data: TopRepository[] }) {
  const top = data.slice(0, 15).map((d) => ({
    ...d,
    label: `${d.owner}/${d.repository}`,
  }));

  return (
    <ChartCard title="Top 15 Repositories" subtitle="By total issues and PRs">
      <ResponsiveContainer width="100%" height={420}>
        <BarChart data={top} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis type="number" tickFormatter={formatCompact} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="label" width={200} tick={{ fontSize: 10 }} />
          <Tooltip formatter={(value, name) => [Number(value).toLocaleString(), name]} />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
          <Bar dataKey="issues" name="Issues" stackId="a" fill={CHART_COLORS.issue} />
          <Bar dataKey="prs" name="PRs" stackId="a" fill={CHART_COLORS.pr} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
