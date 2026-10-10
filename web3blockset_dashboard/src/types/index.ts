export interface OverviewData {
  totalRecords: number;
  totalIssues: number;
  totalPRs: number;
  totalProviderRepos: number;
  totalOrganizations: number;
  totalUniqueAuthors: number;
  totalProviderRecords: number;
  totalCommunityRecords: number;
  totalCommunityRepos: number;
  totalUniqueRepos: number;
  openRecords: number;
  closedRecords: number;
  yearRange: [number, number];
  medianResolutionDays: number | null;
  medianIssueResolutionDays: number | null;
  medianPRResolutionDays: number | null;
  lastUpdated: string;
}

export interface YearlyTrend {
  year: number;
  issues: number;
  prs: number;
  total: number;
  providerIssues: number;
  providerPRs: number;
  communityIssues: number;
  communityPRs: number;
}

export interface CategoryDistribution {
  category: string;
  count: number;
  issues: number;
  prs: number;
  repos: number;
  percentage: number;
}

export interface TopOwner {
  owner: string;
  count: number;
  issues: number;
  prs: number;
  repos: number;
  categories: string[];
}

export interface TopRepository {
  repository: string;
  owner: string;
  count: number;
  issues: number;
  prs: number;
  category: string;
  stars: number;
}

export interface LanguageDistribution {
  language: string;
  repos: number;
  percentage: number;
}

export interface StateDistribution {
  byType: { type: string; open: number; closed: number }[];
  byDataSource: { source: string; open: number; closed: number }[];
}

export interface ResolutionByCategory {
  category: string;
  medianDays: number;
  closedCount: number;
  issueMedian: number | null;
  prMedian: number | null;
}

export interface LabelCount {
  label: string;
  count: number;
}

export interface MonthlyActivity {
  month: string;
  created: number;
  issues: number;
  prs: number;
}

export interface RepositoryMeta {
  organization: string;
  description: string;
  stars: number;
  forks: number;
  language: string;
  archived: boolean;
  category: string;
  htmlUrl: string;
}

export interface FilterOptions {
  owners: string[];
  repositories: { name: string; owner: string }[];
  categories: string[];
  years: number[];
  dataSources: string[];
  types: string[];
  states: string[];
}

export interface LightRecord {
  repository: string;
  owner: string;
  issue_number: number;
  issue_title: string;
  state: string;
  created_at: string;
  closed_at: string;
  type: string;
  comments_count: number;
  labels: string;
  repository_category: string;
  year: number;
  data_source: string;
}

export interface FilterCriteria {
  keyword: string;
  owner: string;
  repository: string;
  dataSource: string;
  type: string;
  state: string;
  category: string;
  yearFrom: number | null;
  yearTo: number | null;
}

export interface ProductivityGroupMetric {
  group: string;
  totalItems: number;
  issues: number;
  prs: number;
  closedItems: number;
  openItems: number;
  medianPRLeadTimeDays: number | null;
  medianIssueResolutionDays: number | null;
  prMergeRate: number | null;
  medianFlowTimeDays: number | null;
  throughputPerMonth: number | null;
  flowVelocityPerMonth: number | null;
}

export interface ProductivityMonthlyTrend {
  month: string;
  created: number;
  closed: number;
  issuesClosed: number;
  prsClosed: number;
}

export interface ProductivityData {
  global: {
    medianPRLeadTimeDays: number | null;
    medianIssueResolutionDays: number | null;
    prMergeRate: number | null;
    medianFlowTimeDays: number | null;
  };
  byCategory: ProductivityGroupMetric[];
  byOwner: ProductivityGroupMetric[];
  monthlyTrend: ProductivityMonthlyTrend[];
}
