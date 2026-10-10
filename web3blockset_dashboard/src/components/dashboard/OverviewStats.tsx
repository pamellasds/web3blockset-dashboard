import { Database, CircleDot, GitPullRequest, GitFork, Building2, Users, Calendar, Clock } from "lucide-react";
import StatCard from "../common/StatCard";
import type { OverviewData } from "../../types";

export default function OverviewStats({ data }: { data: OverviewData }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <StatCard label="Total Records" value={data.totalRecords} icon={Database} color="text-primary-600" />
      <StatCard label="Issues" value={data.totalIssues} icon={CircleDot} color="text-amber-500" subtitle="GitHub Issues" />
      <StatCard label="Pull Requests" value={data.totalPRs} icon={GitPullRequest} color="text-blue-500" subtitle="GitHub PRs" />
      <StatCard label="Provider Repos" value={data.totalProviderRepos} icon={GitFork} color="text-teal-500" subtitle={`${data.totalOrganizations} organizations`} />
      <StatCard label="Unique Authors" value={data.totalUniqueAuthors} icon={Users} color="text-violet-500" />
      <StatCard label="Year Span" value={`${data.yearRange[0]}–${data.yearRange[1]}`} icon={Calendar} color="text-emerald-500" />
      <StatCard label="Median Resolution" value={data.medianResolutionDays ? `${data.medianResolutionDays}d` : "N/A"} icon={Clock} color="text-orange-500" subtitle="All closed records" />
      <StatCard label="Community Repos" value={data.totalCommunityRepos} icon={Building2} color="text-pink-500" subtitle={`${data.totalCommunityRecords.toLocaleString()} records`} />
    </div>
  );
}
