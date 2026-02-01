import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import ChartCard from "../common/ChartCard";
import { CHART_COLORS } from "../../utils/chartColors";
import type { ResolutionByCategory } from "../../types";

export default function ResolutionChart({ data }: { data: ResolutionByCategory[] }) {
  const top = data.slice(0, 12).map((d) => ({
    category: d.category.length > 25 ? d.category.slice(0, 25) + "..." : d.category,
    "Issue Median (days)": d.issueMedian,
    "PR Median (days)": d.prMedian,
  }));

  return (
    <ChartCard title="Median Resolution Time" subtitle="Days to close, by category (top 12)">
      <ResponsiveContainer width="100%" height={380}>
        <BarChart data={top} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} label={{ value: "Days", position: "insideBottom", offset: -2 }} />
          <YAxis type="category" dataKey="category" width={180} tick={{ fontSize: 10 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="Issue Median (days)" fill={CHART_COLORS.issue} radius={[0, 4, 4, 0]} />
          <Bar dataKey="PR Median (days)" fill={CHART_COLORS.pr} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
