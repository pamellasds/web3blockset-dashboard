import { useState, useEffect, useRef, useCallback } from "react";
import Papa from "papaparse";
import type { LightRecord, FilterCriteria, FilterOptions } from "../types";

interface FilterDataState {
  records: LightRecord[];
  totalLoaded: number;
  loading: boolean;
  progress: number;
  error: string | null;
  filterOptions: FilterOptions | null;
}

const RECORDS_CACHE: { data: LightRecord[] | null } = { data: null };

export function useFilterData() {
  const [state, setState] = useState<FilterDataState>({
    records: [],
    totalLoaded: RECORDS_CACHE.data?.length ?? 0,
    loading: !RECORDS_CACHE.data,
    progress: RECORDS_CACHE.data ? 100 : 0,
    error: null,
    filterOptions: null,
  });
  const allRecords = useRef<LightRecord[]>(RECORDS_CACHE.data ?? []);
  const [filters, setFilters] = useState<FilterCriteria>({
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
  const [page, setPage] = useState(0);
  const pageSize = 50;

  useEffect(() => {
    const basePath = import.meta.env.BASE_URL || "/";

    fetch(`${basePath}data/filter_options.json`)
      .then((r) => r.json())
      .then((opts: FilterOptions) => {
        setState((s) => ({ ...s, filterOptions: opts }));
      })
      .catch(() => {});

    if (RECORDS_CACHE.data) {
      allRecords.current = RECORDS_CACHE.data;
      setState((s) => ({
        ...s,
        totalLoaded: RECORDS_CACHE.data!.length,
        loading: false,
        progress: 100,
      }));
      return;
    }

    const records: LightRecord[] = [];
    Papa.parse(`${basePath}data/issues_prs_light.csv`, {
      download: true,
      header: true,
      worker: true,
      skipEmptyLines: true,
      step: (result) => {
        const row = result.data as Record<string, string>;
        records.push({
          repository: row.repository || "",
          owner: row.owner || "",
          issue_number: parseInt(row.issue_number) || 0,
          issue_title: row.issue_title || "",
          state: row.state || "",
          created_at: row.created_at || "",
          closed_at: row.closed_at || "",
          type: row.type || "",
          comments_count: parseInt(row.comments_count) || 0,
          labels: row.labels || "",
          repository_category: row.repository_category || "",
          year: parseInt(row.year) || 0,
          data_source: row.data_source || "",
        });
        if (records.length % 50000 === 0) {
          setState((s) => ({
            ...s,
            totalLoaded: records.length,
            progress: Math.min(95, (records.length / 400000) * 100),
          }));
        }
      },
      complete: () => {
        allRecords.current = records;
        RECORDS_CACHE.data = records;
        setState((s) => ({
          ...s,
          totalLoaded: records.length,
          loading: false,
          progress: 100,
        }));
      },
      error: (err) => {
        setState((s) => ({ ...s, loading: false, error: err.message }));
      },
    });
  }, []);

  const filteredRecords = useCallback(() => {
    let result = allRecords.current;
    if (filters.keyword) {
      const kw = filters.keyword.toLowerCase();
      result = result.filter(
        (r) =>
          r.issue_title.toLowerCase().includes(kw) ||
          r.labels.toLowerCase().includes(kw)
      );
    }
    if (filters.owner) result = result.filter((r) => r.owner === filters.owner);
    if (filters.repository) result = result.filter((r) => r.repository === filters.repository);
    if (filters.dataSource) result = result.filter((r) => r.data_source === filters.dataSource);
    if (filters.type) result = result.filter((r) => r.type === filters.type);
    if (filters.state) result = result.filter((r) => r.state === filters.state);
    if (filters.category) result = result.filter((r) => r.repository_category === filters.category);
    if (filters.yearFrom) result = result.filter((r) => r.year >= filters.yearFrom!);
    if (filters.yearTo) result = result.filter((r) => r.year <= filters.yearTo!);
    return result;
  }, [filters]);

  const filtered = state.loading ? [] : filteredRecords();
  const paged = filtered.slice(page * pageSize, (page + 1) * pageSize);
  const totalPages = Math.ceil(filtered.length / pageSize);

  return {
    ...state,
    filters,
    setFilters,
    page,
    setPage,
    pageSize,
    filteredCount: filtered.length,
    pagedRecords: paged,
    totalPages,
  };
}
