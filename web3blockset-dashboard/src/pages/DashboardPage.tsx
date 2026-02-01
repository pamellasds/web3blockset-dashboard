import { useDataFetch } from "../hooks/useDataFetch";
import LoadingSpinner from "../components/common/LoadingSpinner";
import SectionTitle from "../components/common/SectionTitle";
import OverviewStats from "../components/dashboard/OverviewStats";
import YearlyTrendsChart from "../components/dashboard/YearlyTrendsChart";
import ProviderCommunityChart from "../components/dashboard/ProviderCommunityChart";
import CategoryBarChart from "../components/dashboard/CategoryBarChart";
import TopOwnersChart from "../components/dashboard/TopOwnersChart";
import TopReposChart from "../components/dashboard/TopReposChart";
import LanguagePieChart from "../components/dashboard/LanguagePieChart";
import ResolutionChart from "../components/dashboard/ResolutionChart";
import StateDistChart from "../components/dashboard/StateDistChart";
import DataSourceComparison from "../components/dashboard/DataSourceComparison";
import DownloadCitation from "../components/dashboard/DownloadCitation";
import TopLabelsChart from "../components/dashboard/TopLabelsChart";
import type {
  OverviewData,
  YearlyTrend,
  CategoryDistribution,
  TopOwner,
  TopRepository,
  LanguageDistribution,
  StateDistribution,
  ResolutionByCategory,
  LabelCount,
} from "../types";

export default function DashboardPage() {
  const overview = useDataFetch<OverviewData>("overview.json");
  const yearly = useDataFetch<YearlyTrend[]>("yearly_trends.json");
  const categories = useDataFetch<CategoryDistribution[]>("category_distribution.json");
  const owners = useDataFetch<TopOwner[]>("top_owners.json");
  const repos = useDataFetch<TopRepository[]>("top_repositories.json");
  const languages = useDataFetch<LanguageDistribution[]>("language_distribution.json");
  const states = useDataFetch<StateDistribution>("state_distribution.json");
  const resolution = useDataFetch<ResolutionByCategory[]>("resolution_by_category.json");
  const labels = useDataFetch<LabelCount[]>("top_labels.json");

  if (overview.loading) return <LoadingSpinner message="Loading dashboard data..." />;
  if (overview.error || !overview.data) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 text-center">
        <p className="text-red-500">Failed to load dashboard data. Make sure data files are generated.</p>
        <p className="text-sm text-slate-400 mt-2">{overview.error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Web3BlockSet Dashboard</h1>
        <p className="text-slate-500 mt-2 max-w-3xl">
          A curated dataset of {overview.data.totalRecords.toLocaleString()} GitHub Issues and Pull Requests
          for empirical research in Blockchain-Oriented Software Engineering (BOSE).
          Spanning {overview.data.yearRange[0]}–{overview.data.yearRange[1]} across {overview.data.totalOrganizations} organizations.
        </p>
      </div>

      {/* Section 1: Overview Stats */}
      <section className="mb-10">
        <OverviewStats data={overview.data} />
      </section>

      {/* Section 2: Temporal Trends */}
      {yearly.data && (
        <section className="mb-10">
          <SectionTitle title="Temporal Trends" subtitle="How the dataset evolved over the years" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <YearlyTrendsChart data={yearly.data} />
            <ProviderCommunityChart data={yearly.data} />
          </div>
        </section>
      )}

      {/* Section 3: Repository Categories */}
      {categories.data && (
        <section className="mb-10">
          <SectionTitle title="Repository Categories" subtitle="Distribution of records across blockchain stack categories" />
          <CategoryBarChart data={categories.data} />
        </section>
      )}

      {/* Section 4: Top Organizations & Repositories */}
      {owners.data && repos.data && (
        <section className="mb-10">
          <SectionTitle title="Top Organizations & Repositories" subtitle="Most active projects in the dataset" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <TopOwnersChart data={owners.data} />
            <TopReposChart data={repos.data} />
          </div>
        </section>
      )}

      {/* Section 5: Languages & Labels */}
      {languages.data && labels.data && (
        <section className="mb-10">
          <SectionTitle title="Languages & Labels" subtitle="Programming languages in provider repos and most used labels" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <LanguagePieChart data={languages.data} />
            <TopLabelsChart data={labels.data} />
          </div>
        </section>
      )}

      {/* Section 6: Resolution Patterns */}
      {resolution.data && states.data && (
        <section className="mb-10">
          <SectionTitle title="Resolution Patterns" subtitle="How quickly issues and PRs are resolved" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ResolutionChart data={resolution.data} />
            <StateDistChart data={states.data} />
          </div>
        </section>
      )}

      {/* Section 7: Data Source Comparison */}
      <section className="mb-10">
        <SectionTitle title="Data Source Comparison" subtitle="Provider (official) vs Community (adopter) datasets" />
        <DataSourceComparison data={overview.data} />
      </section>

      {/* Section 8: Download & Citation */}
      <section className="mb-10">
        <SectionTitle title="Download & Citation" />
        <DownloadCitation data={overview.data} />
      </section>
    </div>
  );
}
