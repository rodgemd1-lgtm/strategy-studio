/**
 * Next.js API Route: /api/rusr
 *
 * Proxies to the Python RusrCockpit backend for local dev,
 * or reads directly from the receipt store in production.
 */
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const studio = req.nextUrl.searchParams.get("studio") ?? "strategy";

  try {
    // Try Python backend
    const base = process.env.RUSR_BACKEND ?? "http://localhost:3456";
    const res = await fetch(`${base}/api/rusr?studio=${studio}`, {
      signal: AbortSignal.timeout(5_000),
    });
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
  } catch {
    // Fall through to embedded mock
  }

  // Embedded mock data (local dev without Python backend)
  return NextResponse.json(getMockStatus(studio));
}

function getMockStatus(studio: string) {
  return {
    studio,
    config: {
      name: "Strategy Studio",
      diamond: "D2",
      bands: ["A1", "A2", "A3"],
      budget: { per_run: 50, per_step: 1 },
      gates: ["G10", "G25", "G50", "G75", "G90", "G100"],
      mcp: ["filesystem", "git", "github", "postgres", "qdrant", "fetch"],
    },
    metrics: {
      run_id: "run-2026-05-27",
      status: "ACTIVE",
      layer: 17,
      gates: { G10: "PASS", G25: "PASS", G50: "READY", G75: "LOCKED", G90: "LOCKED", G100: "LOCKED" },
      budget_used: 14.32,
      budget_ceiling: 50,
      tool_calls: 187,
      tool_ceiling: 250,
      wall_elapsed: 1847,
      wall_ceiling: 2700,
      context_tokens: 42180,
      context_ceiling: 60000,
      artifact_count: 3,
      latest_artifact: "artifact-2026-05-27-soul-id-fix",
    },
    quality_gates: [
      { id: "G10",  label: "Architecture Review",  status: "PASS",   blockers: [] },
      { id: "G25",  label: "Foundation Check",       status: "PASS",   blockers: [] },
      { id: "G50",  label: "Full Team Audit",        status: "READY",  blockers: ["Missing 3 evidence sources"] },
      { id: "G75",  label: "UX + Security + Perf",   status: "LOCKED", blockers: [] },
      { id: "G90",  label: "Final Audit Sweep",       status: "LOCKED", blockers: [] },
      { id: "G100", label: "Ship Decision",           status: "LOCKED", blockers: [] },
    ],
    artifacts: [
      { id: "artifact-2026-05-27-soul-id-fix", type: "strategy", rig_l: 42, sigma: 31.2, sigma_pass: true, source_count: 5, genesis: "fix: soul_id bypass", created_at: "2026-05-27T18:30:00Z" },
      { id: "artifact-2026-05-27-cold-start",  type: "strategy", rig_l: 38, sigma: 30.8, sigma_pass: true, source_count: 4, genesis: "cold-start receipts", created_at: "2026-05-27T16:45:00Z" },
    ],
    audit_log: [
      { ts: "2026-05-27T18:30:00Z", layer: 1,  event: "ARTIFACT_FROZEN",    detail: "artifact-2026-05-27-soul-id-fix frozen", user: "rusr" },
      { ts: "2026-05-27T18:29:55Z", layer: 3,  event: "SKILL_HASH_CHANGE",  detail: "rig-linkedin-studio hash changed", user: "rusr" },
      { ts: "2026-05-27T18:29:00Z", layer: 11, event: "APPROVAL_TIMEOUT",   detail: "G50: approval timeout → blocked", user: "rusr" },
      { ts: "2026-05-27T18:28:00Z", layer: 6,  event: "CROSS_FAMILY_VERIFY", detail: "gpt-5.5 ↔ gpt-4o verified", user: "rusr" },
      { ts: "2026-05-27T18:27:00Z", layer: 1,  event: "TOOL_CALL",          detail: "text2image_soul_v2(soul_id) — PASS", user: "rusr" },
      { ts: "2026-05-27T18:26:30Z", layer: 1,  event: "TOOL_CALL_BLOCKED",  detail: "cinema_studio_2_5(soul_id) — BLOCKED", user: "rusr" },
      { ts: "2026-05-27T18:25:00Z", layer: 9,  event: "BUDGET_WARNING",     detail: "strategy: $14.32 / $50.00 (28.6%)", user: "rusr" },
    ],
  };
}