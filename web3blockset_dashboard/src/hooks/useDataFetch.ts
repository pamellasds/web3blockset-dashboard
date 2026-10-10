import { useState, useEffect } from "react";

interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

const cache = new Map<string, unknown>();

export function useDataFetch<T>(filename: string): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({
    data: (cache.get(filename) as T) ?? null,
    loading: !cache.has(filename),
    error: null,
  });

  useEffect(() => {
    if (cache.has(filename)) {
      setState({ data: cache.get(filename) as T, loading: false, error: null });
      return;
    }

    let cancelled = false;
    const basePath = import.meta.env.BASE_URL || "/";
    const url = `${basePath}data/${filename}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to fetch ${filename}: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (!cancelled) {
          cache.set(filename, data);
          setState({ data, loading: false, error: null });
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setState({ data: null, loading: false, error: err.message });
        }
      });

    return () => { cancelled = true; };
  }, [filename]);

  return state;
}
