import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import ChartCard from "../common/ChartCard";
import { CATEGORY_PALETTE } from "../../utils/chartColors";
import type { LanguageDistribution } from "../../types";

export default function LanguagePieChart({ data }: { data: LanguageDistribution[] }) {
  const top = data.slice(0, 10);
  const otherRepos = data.slice(10).reduce((sum, d) => sum + d.repos, 0);
  const chartData = otherRepos > 0
    ? [...top, { language: "Other", repos: otherRepos, percentage: 0 }]
    : top;

  return (
    <ChartCard title="Programming Languages" subtitle="Provider repository primary languages">
      <ResponsiveContainer width="100%" height={350}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="repos"
            nameKey="language"
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={110}
            paddingAngle={2}
            label={({ name, percent }) =>
              percent && percent > 0.02 ? `${name} (${(percent * 100).toFixed(1)}%)` : ""
            }
            labelLine={true}
          >
            {chartData.map((_, i) => (
              <Cell key={i} fill={CATEGORY_PALETTE[i % CATEGORY_PALETTE.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => [`${value} repos`]} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
