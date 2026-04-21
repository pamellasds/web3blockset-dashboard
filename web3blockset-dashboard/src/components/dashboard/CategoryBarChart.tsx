import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import ChartCard from "../common/ChartCard";
import { CHART_COLORS } from "../../utils/chartColors";
import { formatCompact } from "../../utils/formatNumber";
import type { CategoryDistribution } from "../../types";

const truncate = (s: string, max = 28) => s.length > max ? s.slice(0, max) + "…" : s;

export default function CategoryBarChart({ data }: { data: CategoryDistribution[] }) {
  const top = data.slice(0, 20);

  return (
    <ChartCard title="Records by Repository Category" subtitle="Top 20 categories by volume" className="col-span-full">
      <ResponsiveContainer width="100%" height={Math.max(400, top.length * 28)}>
        <BarChart data={top} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis type="number" tickFormatter={formatCompact} tick={{ fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="category"
            width={200}
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => truncate(v)}
          />
          <Tooltip
            formatter={(value, name) => [Number(value).toLocaleString(), name]}
          />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
          <Bar dataKey="issues" name="Issues" stackId="a" fill={CHART_COLORS.issue} />
          <Bar dataKey="prs" name="Pull Requests" stackId="a" fill={CHART_COLORS.pr} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
