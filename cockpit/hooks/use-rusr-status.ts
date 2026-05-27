import { useState, useEffect, useCallback } from "react";
import type { RusrStatus } from "@/lib/studio-config";
import { loadRusrStatus } from "@/lib/rusr-api";

export interface UseRusrStatusOptions {
  studio?: string;
  refreshInterval?: number;  // ms, 0 = manual only
}

export function useRusrStatus(opts: UseRusrStatusOptions = {}) {
  const { studio = "strategy", refreshInterval = 0 } = opts;

  const [status, setStatus] = useState<RusrStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const s = await loadRusrStatus(studio);
      setStatus(s);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [studio]);

  useEffect(() => {
    setLoading(true);
    void load();
  }, [load]);

  useEffect(() => {
    if (refreshInterval <= 0) return;
    const id = setInterval(() => void load(), refreshInterval);
    return () => clearInterval(id);
  }, [load, refreshInterval]);

  return { status, loading, error, lastRefresh, refresh: load };
}