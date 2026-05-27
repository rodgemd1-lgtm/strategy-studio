"use client";
import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/header";
import { MetricCard } from "@/components/metric-card";
import { GateStatus } from "@/components/gate-status";
import { AuditLog } from "@/components/audit-log";
import type { RusrStatus, QualityGate, AuditEntry } from "@/lib/studio-config";

// ── API ────────────────────────────────────────────────────────────────────

async function fetchRusrStatus(studio = "strategy"): Promise<RusrStatus> {
  const res = await fetch(`/api/rusr?studio=${studio}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

// ── Metric configs ─────────────────────────────────────────────────────────

const METRIC_CONFIGS = [
  {
    key: "budget_used",
    label: "Budget",
    unit: (v: number, m: RusrStatus) => `$${v.toFixed(2)} / $${m.budget_ceiling}`,
    pct: (v: number, m: RusrStatus) => (v / m.budget_ceiling) * 100,
    color: (pct: number) => pct > 80 ? "var(--fail)" : pct > 60 ? "var(--warn)" : "var(--pass)",
  },
  {
    key: "tool_calls",
    label: "Tool Calls",
    unit: (v: number, m: RusrStatus) => `${v} / ${m.tool_ceiling}`,
    pct: (v: number, m: RusrStatus) => (v / m.tool_ceiling) * 100,
    color: (pct: number) => pct > 80 ? "var(--fail)" : pct > 60 ? "var(--warn)" : "var(--pass)",
  },
  {
    key: "wall_elapsed",
    label: "Wall Clock",
    unit: (v: number, m: RusrStatus) => {
      const m_cur = Math.floor(v / 60);
      const s_cur = v % 60;
      const m_max = Math.floor(m.wall_ceiling / 60);
      return `${m_cur}:${String(s_cur).padStart(2, "0")} / ${m_max}:00`;
    },
    pct: (v: number, m: RusrStatus) => (v / m.wall_ceiling) * 100,
    color: (pct: number) => pct > 80 ? "var(--fail)" : pct > 60 ? "var(--warn)" : "var(--pass)",
  },
  {
    key: "context_tokens",
    label: "Context",
    unit: (v: number, m: RusrStatus) => {
      const k = (v / 1000).toFixed(1);
      const k_max = (m.context_ceiling / 1000).toFixed(0);
      return `${k}k / ${k_max}k`;
    },
    pct: (v: number, m: RusrStatus) => (v / m.context_ceiling) * 100,
    color: (pct: number) => pct > 80 ? "var(--fail)" : pct > 60 ? "var(--warn)" : "var(--pass)",
  },
  {
    key: "artifact_count",
    label: "Artifacts",
    unit: (v: number) => String(v),
    pct: (_: number) => 0,
    color: () => "var(--accent)",
  },
  {
    key: "gates_passed",
    label: "Gates",
    unit: (_: number, m: RusrStatus) => {
      const gates = m.gates as Record<string, string>;
      const pass = Object.values(gates).filter(s => s === "PASS").length;
      const total = Object.keys(gates).length;
      return `${pass} / ${total}`;
    },
    pct: (_: number, m: RusrStatus) => {
      const gates = m.gates as Record<string, string>;
      const pass = Object.values(gates).filter(s => s === "PASS").length;
      const total = Object.keys(gates).length;
      return (pass / total) * 100;
    },
    color: (pct: number) => pct === 100 ? "var(--pass)" : pct > 50 ? "var(--warn)" : "var(--locked)",
  },
] as const;

// ── Page ────────────────────────────────────────────────────────────────────

export default function CockpitPage() {
  const [status, setStatus] = useState<RusrStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [studio, setStudio] = useState("strategy");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const s = await fetchRusrStatus(studio);
      setStatus(s);
    } catch {
      // Keep previous state on error
    } finally {
      setLoading(false);
    }
  }, [studio]);

  useEffect(() => { load(); }, [load]);

  const config = status?.config ?? { name: "Strategy Studio", diamond: "D2", bands: ["A1", "A2", "A3"] };

  return (
    <main style={{ minHeight: "100vh", padding: "0 24px 48px", background: "var(--bg)" }}>
      <Header
        studio={config.name}
        diamond={config.diamond}
        bands={config.bands.join(", ")}
        studioKey={studio}
        onStudioChange={setStudio}
      />

      {loading ? (
        <div style={{ padding: "48px", textAlign: "center", color: "var(--muted)" }}>
          Loading RUSR status...
        </div>
      ) : status ? (
        <>
          {/* ── Metric Cards ── */}
          <section style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: "12px",
            margin: "24px 0",
          }}>
            {METRIC_CONFIGS.map(({ key, label, unit, pct, color }) => {
              const val = (status.metrics as Record<string, number>)[key] ?? 0;
              const pct_val = pct(val, status.metrics);
              return (
                <MetricCard
                  key={key}
                  label={label}
                  value={unit(val, status.metrics)}
                  pct={pct_val}
                  barColor={color(pct_val)}
                />
              );
            })}
          </section>

          {/* ── Quality Gates ── */}
          <section style={{ margin: "24px 0" }}>
            <h2 style={{ color: "var(--accent)", fontSize: "11px", letterSpacing: "0.12em", margin: "0 0 12px" }}>
              QUALITY GATES — {config.diamond} BAND
            </h2>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              {status.quality_gates.map((g: QualityGate) => (
                <GateStatus key={g.id} gate={g} />
              ))}
            </div>
          </section>

          {/* ── Audit Log ── */}
          <section style={{ margin: "24px 0" }}>
            <h2 style={{ color: "var(--accent)", fontSize: "11px", letterSpacing: "0.12em", margin: "0 0 12px" }}>
              AUDIT TRAIL
            </h2>
            <AuditLog entries={status.audit_log ?? []} />
          </section>
        </>
      ) : (
        <div style={{ padding: "48px", textAlign: "center", color: "var(--fail)" }}>
          Failed to load RUSR status. Check API connectivity.
        </div>
      )}
    </main>
  );
}