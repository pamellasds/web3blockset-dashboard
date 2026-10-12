import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line,
} from "recharts";
import { Activity } from "lucide-react";
import type { ProductivityData, ProductivityGroupMetric } from "../types";
import { formatCompact } from "../utils/formatNumber";
import SectionTitle from "../components/common/SectionTitle";
import ChartCard from "../components/common/ChartCard";
import LoadingSpinner from "../components/common/LoadingSpinner";

const SingleLineTick = ({ x, y, payload, maxChars = 20 }: any) => {
  const label: string = payload.value;
  const text = label.length > maxChars ? label.slice(0, maxChars) + "…" : label;
  return (
    <g transform={`translate(${x},${y})`}>
      <text x={0} y={0} dy={4} textAnchor="end" fill="#475569" fontSize={10}>{text}</text>
    </g>
  );
};

const DORA_COLOR_PR = "#6366f1";
const DORA_COLOR_ISSUE = "#f59e0b";
const FLOW_COLOR_CLOSED = "#10b981";
const FLOW_COLOR_CREATED = "#94a3b8";

function StatCard({ label, value, unit, color }: { label: string; value: string | number | null; unit?: string; color: string }) {
  return (
    <div className={`rounded-xl border p-5 bg-white shadow-sm`}>
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {value !== null && value !== undefined ? value : "—"}
        {value !== null && value !== undefined && unit ? <span className="text-base font-normal text-slate-400 ml-1">{unit}</span> : null}
      </p>
    </div>
  );
}

export default function ProductivityPage() {
  const [data, setData] = useState<ProductivityData | null>(null);
  const [groupBy, setGroupBy] = useState<"byCategory" | "byOwner">("byCategory");

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/productivity.json`)
      .then((r) => r.json())
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) return <LoadingSpinner />;

  const groups: ProductivityGroupMetric[] = data[groupBy]
    .filter((g) => g.group && g.group.trim() !== "" && g.group !== "nan")
    .slice(0, 20);

  const prLeadData = [...groups]
    .filter((g) => g.medianPRLeadTimeDays !== null)
    .sort((a, b) => (a.medianPRLeadTimeDays ?? 0) - (b.medianPRLeadTimeDays ?? 0))
    .slice(0, 15);

  const issueResData = [...groups]
    .filter((g) => g.medianIssueResolutionDays !== null)
    .sort((a, b) => (a.medianIssueResolutionDays ?? 0) - (b.medianIssueResolutionDays ?? 0))
    .slice(0, 15);

  const flowTimeData = [...groups]
    .filter((g) => g.medianFlowTimeDays !== null)
    .sort((a, b) => (a.medianFlowTimeDays ?? 0) - (b.medianFlowTimeDays ?? 0))
    .slice(0, 15);

  const flowDistData = [...groups]
    .sort((a, b) => b.totalItems - a.totalItems)
    .slice(0, 15);

  const monthlyTrend = data.monthlyTrend.filter((m) => {
    const y = parseInt(m.month.split("-")[0]);
    return y >= 2018 && y <= 2025;
  });

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <Activity size={22} className="text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Productivity Analysis</h1>
            <p className="text-sm text-slate-500">DORA-inspired & Flow Metrics derived from GitHub activity</p>
          </div>
        </div>
        {/* Group-by toggle */}
        <div className="flex rounded-lg border border-slate-200 overflow-hidden text-sm font-medium">
          <button
            onClick={() => setGroupBy("byCategory")}
            className={`px-4 py-2 transition-colors ${groupBy === "byCategory" ? "bg-indigo-600 text-white" : "bg-white text-slate-600 hover:bg-slate-50"}`}
          >
            By Category
          </button>
          <button
            onClick={() => setGroupBy("byOwner")}
            className={`px-4 py-2 transition-colors ${groupBy === "byOwner" ? "bg-indigo-600 text-white" : "bg-white text-slate-600 hover:bg-slate-50"}`}
          >
            By Organization
          </button>
        </div>
      </div>

      {/* ── DORA Section ── */}
      <section>
        <SectionTitle
          title="DORA-Inspired Metrics"
          subtitle="Lead time and throughput metrics derived from GitHub issue and PR lifecycle data. Note: Deployment Frequency and Change Failure Rate require deployment pipeline data not available here."
        />
        {/* Global summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard label="Median PR Lead Time" value={data.global.medianPRLeadTimeDays} unit="days" color="text-indigo-600" />
          <StatCard label="Median Issue Resolution" value={data.global.medianIssueResolutionDays} unit="days" color="text-amber-600" />
          <StatCard label="PR Merge Rate" value={data.global.prMergeRate} unit="%" color="text-emerald-600" />
          <StatCard label="Median Flow Time" value={data.global.medianFlowTimeDays} unit="days" color="text-violet-600" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* PR Lead Time by group */}
          <ChartCard title="Median PR Lead Time" subtitle={`Days from PR creation to close — by ${groupBy === "byCategory" ? "category" : "organization"}`}>
            <ResponsiveContainer width="100%" height={380}>
              <BarChart data={prLeadData} layout="vertical" margin={{ top: 4, right: 20, bottom: 4, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}d`} />
                <YAxis type="category" dataKey="group" width={160} tick={<SingleLineTick maxChars={20} />} />
                <Tooltip formatter={(v) => [`${v} days`, "Median PR Lead Time"]} />
                <Bar dataKey="medianPRLeadTimeDays" name="Median PR Lead Time (days)" fill={DORA_COLOR_PR} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Issue Resolution Time by group */}
          <ChartCard title="Median Issue Resolution Time" subtitle={`Days from issue creation to close — by ${groupBy === "byCategory" ? "category" : "organization"}`}>
            <ResponsiveContainer width="100%" height={380}>
              <BarChart data={issueResData} layout="vertical" margin={{ top: 4, right: 20, bottom: 4, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}d`} />
                <YAxis type="category" dataKey="group" width={160} tick={<SingleLineTick maxChars={20} />} />
                <Tooltip formatter={(v) => [`${v} days`, "Median Issue Resolution"]} />
                <Bar dataKey="medianIssueResolutionDays" name="Median Issue Resolution (days)" fill={DORA_COLOR_ISSUE} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Monthly throughput trend */}
        <div className="mt-6">
          <ChartCard title="Monthly Throughput" subtitle="Issues and PRs closed per month (2018–2025)" className="col-span-full">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={monthlyTrend} margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(0, 7)} interval={5} />
                <YAxis tickFormatter={formatCompact} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v, name) => [Number(v).toLocaleString(), name]} labelFormatter={(l) => `Month: ${l}`} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="prsClosed" name="PRs Closed" stroke={DORA_COLOR_PR} dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="issuesClosed" name="Issues Closed" stroke={DORA_COLOR_ISSUE} dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </section>

      {/* ── Flow Metrics Section ── */}
      <section>
        <SectionTitle
          title="Flow Metrics"
          subtitle="Based on the Flow Framework (Kersten, 2018). Flow Time measures cycle time; Flow Velocity measures throughput; Flow Distribution shows the balance between issues and PRs."
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Flow Time */}
          <ChartCard title="Median Flow Time" subtitle={`Days from creation to close (all items) — by ${groupBy === "byCategory" ? "category" : "organization"}`}>
            <ResponsiveContainer width="100%" height={380}>
              <BarChart data={flowTimeData} layout="vertical" margin={{ top: 4, right: 20, bottom: 4, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}d`} />
                <YAxis type="category" dataKey="group" width={160} tick={<SingleLineTick maxChars={20} />} />
                <Tooltip formatter={(v) => [`${v} days`, "Median Flow Time"]} />
                <Bar dataKey="medianFlowTimeDays" name="Median Flow Time (days)" fill={FLOW_COLOR_CLOSED} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Flow Distribution */}
          <ChartCard title="Flow Distribution" subtitle={`Issues vs PRs by ${groupBy === "byCategory" ? "category" : "organization"} (top 15)`}>
            <ResponsiveContainer width="100%" height={380}>
              <BarChart data={flowDistData} layout="vertical" margin={{ top: 4, right: 20, bottom: 4, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis type="number" tickFormatter={formatCompact} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="group" width={160} tick={<SingleLineTick maxChars={20} />} />
                <Tooltip formatter={(v, name) => [Number(v).toLocaleString(), name]} />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                <Bar dataKey="issues" name="Issues" stackId="a" fill="#f59e0b" />
                <Bar dataKey="prs" name="PRs" stackId="a" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Flow Velocity trend */}
        <div className="mt-6">
          <ChartCard title="Flow Velocity" subtitle="Total items created vs closed per month (2018–2025)" className="col-span-full">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={monthlyTrend} margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(0, 7)} interval={5} />
                <YAxis tickFormatter={formatCompact} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v, name) => [Number(v).toLocaleString(), name]} labelFormatter={(l) => `Month: ${l}`} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="created" name="Items Created" stroke={FLOW_COLOR_CREATED} dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="closed" name="Items Closed" stroke={FLOW_COLOR_CLOSED} dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </section>

      {/* Methodology note */}
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-600">
        <strong className="text-slate-800">Methodology note:</strong> All metrics are derived from GitHub issue and pull request lifecycle data. Lead time is approximated as the interval between creation and closing of a PR. Deployment Frequency, MTTR, and Change Failure Rate (full DORA) require deployment pipeline telemetry not captured in this dataset. Flow Load (open WIP over time) is not shown as it requires event-based state reconstruction.
      </div>
    </div>
  );
}
