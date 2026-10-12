import { useFilterData } from "../hooks/useFilterData";
import { formatNumber } from "../utils/formatNumber";
import { Search, ChevronLeft, ChevronRight, ExternalLink, X, Download } from "lucide-react";

export default function FilterPage() {
  const {
    loading,
    progress,
    totalLoaded,
    error,
    filterOptions,
    filters,
    setFilters,
    page,
    setPage,
    filteredCount,
    pagedRecords,
    totalPages,
  } = useFilterData();

  const updateFilter = (key: string, value: string | number | null) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
  };

  const clearFilters = () => {
    setFilters({
      keyword: "",
      owner: "",
      repository: "",
      dataSource: "",
      type: "",
      state: "",
      category: "",
      yearFrom: null,
      yearTo: null,
    });
    setPage(0);
  };

  const hasActiveFilters = filters.keyword || filters.owner || filters.repository ||
    filters.dataSource || filters.type || filters.state || filters.category ||
    filters.yearFrom || filters.yearTo;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Explore Dataset</h1>
        <p className="text-slate-500 mt-1">
          Search and filter through all issues and pull requests in the Web3BlockSet.
        </p>
      </div>

      {/* Loading indicator */}
      {loading && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 border-3 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-800">
                Loading dataset... {formatNumber(totalLoaded)} records loaded
              </p>
              <div className="mt-2 h-2 bg-blue-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Filter Panel */}
      <div className="bg-white rounded-xl border border-border p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-slate-700">Filters</h2>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1 text-xs text-red-500 hover:text-red-700"
            >
              <X size={14} /> Clear all
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Keyword Search */}
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium text-slate-500 mb-1">Keyword Search</label>
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search in titles and labels..."
                value={filters.keyword}
                onChange={(e) => updateFilter("keyword", e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Owner */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Owner</label>
            <select
              value={filters.owner}
              onChange={(e) => updateFilter("owner", e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="">All owners</option>
              {filterOptions?.owners.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </div>

          {/* Data Source */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Data Source</label>
            <select
              value={filters.dataSource}
              onChange={(e) => updateFilter("dataSource", e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="">All sources</option>
              {filterOptions?.dataSources.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Type */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Type</label>
            <select
              value={filters.type}
              onChange={(e) => updateFilter("type", e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="">All types</option>
              {filterOptions?.types.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          {/* State */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">State</label>
            <select
              value={filters.state}
              onChange={(e) => updateFilter("state", e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="">All states</option>
              {filterOptions?.states.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Category */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Repository Category</label>
            <select
              value={filters.category}
              onChange={(e) => updateFilter("category", e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="">All categories</option>
              {filterOptions?.categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Year From */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Year From</label>
            <select
              value={filters.yearFrom ?? ""}
              onChange={(e) => updateFilter("yearFrom", e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="">Any</option>
              {filterOptions?.years.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>

          {/* Year To */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Year To</label>
            <select
              value={filters.yearTo ?? ""}
              onChange={(e) => updateFilter("yearTo", e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="">Any</option>
              {filterOptions?.years.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Results Count & Export */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-slate-600">
          {loading ? (
            "Loading..."
          ) : (
            <>
              Showing <strong>{formatNumber(filteredCount)}</strong> results
              {hasActiveFilters && <span className="text-slate-400"> (filtered)</span>}
            </>
          )}
        </p>
        {!loading && filteredCount > 0 && (
          <a
            href={`${import.meta.env.BASE_URL || "/"}data/issues_prs_light.csv`}
            download
            className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 font-medium"
          >
            <Download size={14} /> Download lightweight CSV
          </a>
        )}
      </div>

      {/* Results Table */}
      {!loading && (
        <div className="bg-white rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-border">
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Title</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600 whitespace-nowrap">Repository</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Type</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">State</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600 whitespace-nowrap">Created</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Category</th>
                </tr>
              </thead>
              <tbody>
                {pagedRecords.map((r, i) => (
                  <tr key={`${r.owner}-${r.repository}-${r.issue_number}-${i}`} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3 max-w-md">
                      <a
                        href={`https://github.com/${r.owner}/${r.repository}/issues/${r.issue_number}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-800 hover:underline line-clamp-2"
                      >
                        {r.issue_title || "(no title)"}
                        <ExternalLink size={12} className="inline ml-1 opacity-50" />
                      </a>
                    </td>
                    <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                      <span className="text-slate-400">{r.owner}/</span>{r.repository}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                        r.type === "Issue"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-blue-100 text-blue-800"
                      }`}>
                        {r.type === "Pull Request" ? "PR" : r.type}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                        r.state === "open"
                          ? "bg-green-100 text-green-800"
                          : "bg-purple-100 text-purple-800"
                      }`}>
                        {r.state}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap">{r.created_at}</td>
                    <td className="px-4 py-3 text-xs text-slate-500 max-w-[180px] truncate">{r.repository_category}</td>
                  </tr>
                ))}
                {pagedRecords.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center text-slate-400">
                      {hasActiveFilters ? "No results match your filters." : "No data loaded yet."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-slate-50">
              <p className="text-xs text-slate-500">
                Page {page + 1} of {formatNumber(totalPages)}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="p-1.5 rounded-lg border border-slate-200 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronLeft size={16} />
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                  className="p-1.5 rounded-lg border border-slate-200 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
