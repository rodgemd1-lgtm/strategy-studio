/**
 * RUSR API helper — fetches cockpit state from the Python backend.
 *
 * In production, Next.js API routes proxy to the Python RusrCockpit class.
 * For local dev, calls the Python script directly via fetch to localhost.
 */

import type { RusrStatus } from "./studio-config";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:3456";

export async function loadRusrStatus(studio = "strategy"): Promise<RusrStatus> {
  const res = await fetch(`${API_BASE}/api/rusr?studio=${studio}`, {
    signal: AbortSignal.timeout(10_000),
  });
  if (!res.ok) throw new Error(`RUSR API error: ${res.status} ${res.statusText}`);
  return res.json() as Promise<RusrStatus>;
}

export async function exportRunSummary(runId: string, format: "pptx" | "json" = "json") {
  const res = await fetch(`${API_BASE}/api/export?run_id=${runId}&format=${format}`, {
    signal: AbortSignal.timeout(30_000),
  });
  if (!res.ok) throw new Error(`Export error: ${res.status}`);
  return res.blob();
}