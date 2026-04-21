import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import ChartCard from "../common/ChartCard";
import { CHART_COLORS } from "../../utils/chartColors";
import { formatCompact } from "../../utils/formatNumber";
import type { TopOwner } from "../../types";

const SingleLineTick = ({ x, y, payload, maxChars = 18 }: any) => {
  const label: string = payload.value;
  const text = label.length > maxChars ? label.slice(0, maxChars) + "…" : label;
  return (
    <g transform={`translate(${x},${y})`}>
      <text x={0} y={0} dy={4} textAnchor="end" fill="#475569" fontSize={11}>
        {text}
      </text>
    </g>
  );
};

export default function TopOwnersChart({ data }: { data: TopOwner[] }) {
  const top = data.slice(0, 15);

  return (
    <ChartCard title="Top 15 Organizations" subtitle="By total issues and PRs">
      <ResponsiveContainer width="100%" height={420}>
        <BarChart data={top} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis type="number" tickFormatter={formatCompact} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="owner" width={130} tick={<SingleLineTick maxChars={18} />} />
          <Tooltip formatter={(value, name) => [Number(value).toLocaleString(), name]} />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
          <Bar dataKey="issues" name="Issues" stackId="a" fill={CHART_COLORS.issue} />
          <Bar dataKey="prs" name="PRs" stackId="a" fill={CHART_COLORS.pr} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
