import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import ChartCard from "../common/ChartCard";
import { CHART_COLORS } from "../../utils/chartColors";
import type { StateDistribution } from "../../types";

export default function StateDistChart({ data }: { data: StateDistribution }) {
  const totalOpen = data.byType.reduce((s, d) => s + d.open, 0);
  const totalClosed = data.byType.reduce((s, d) => s + d.closed, 0);
  const pieData = [
    { name: "Closed", value: totalClosed },
    { name: "Open", value: totalOpen },
  ];
  const colors = [CHART_COLORS.closed, CHART_COLORS.open];

  return (
    <ChartCard title="Open vs Closed" subtitle="Current state of all records">
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={pieData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={90}
            label={({ name, value }) =>
              `${name}: ${((value / (totalOpen + totalClosed)) * 100).toFixed(1)}%`
            }
          >
            {pieData.map((_, i) => (
              <Cell key={i} fill={colors[i]} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => [Number(value).toLocaleString()]} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      <div className="grid grid-cols-2 gap-4 mt-4 text-center text-sm">
        {data.byType.map((d) => (
          <div key={d.type} className="bg-slate-50 rounded-lg p-3">
            <p className="font-medium text-slate-700">{d.type}s</p>
            <p className="text-xs text-slate-500">
              {d.open.toLocaleString()} open / {d.closed.toLocaleString()} closed
            </p>
          </div>
        ))}
      </div>
    </ChartCard>
  );
}
