import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import ChartCard from "../common/ChartCard";
import { formatCompact } from "../../utils/formatNumber";
import type { LabelCount } from "../../types";

export default function TopLabelsChart({ data }: { data: LabelCount[] }) {
  const top = data.slice(0, 15);

  return (
    <ChartCard title="Top 15 Labels" subtitle="Most frequently used labels across issues and PRs">
      <ResponsiveContainer width="100%" height={420}>
        <BarChart data={top} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis type="number" tickFormatter={formatCompact} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="label" width={150} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(value) => [Number(value).toLocaleString(), "Count"]} />
          <Bar dataKey="count" name="Count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
