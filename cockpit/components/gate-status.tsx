"use client";
type GateStatusType = "LOCKED" | "READY" | "PASS" | "FAIL" | "SKIP";

const STATUS_COLORS: Record<GateStatusType, string> = {
  LOCKED: "var(--locked)",
  READY:  "var(--warn)",
  PASS:   "var(--pass)",
  FAIL:   "var(--fail)",
  SKIP:   "var(--muted)",
};

const STATUS_LABELS: Record<GateStatusType, string> = {
  LOCKED: "◌",
  READY:  "◎",
  PASS:   "●",
  FAIL:   "✕",
  SKIP:   "—",
};

interface GateStatusProps {
  gate: { id: string; label: string; status: GateStatusType; blockers: string[] };
}

export function GateStatus({ gate }: GateStatusProps) {
  const color = STATUS_COLORS[gate.status] ?? "var(--muted)";
  const icon  = STATUS_LABELS[gate.status] ?? "?";

  return (
    <div style={{
      background: "var(--surface)",
      border: `1px solid ${gate.status === "FAIL" ? "var(--fail)" : "var(--border)"}`,
      padding: "8px 12px",
      display: "flex",
      alignItems: "flex-start",
      gap: "8px",
      minWidth: "160px",
    }}>
      <span style={{ fontSize: "14px", color }}>{icon}</span>
      <div>
        <div style={{ fontSize: "10px", color: "var(--muted)", letterSpacing: "0.1em" }}>
          {gate.id}
        </div>
        <div style={{ fontSize: "12px", marginTop: "1px" }}>{gate.label}</div>
        {gate.blockers.length > 0 && (
          <div style={{ marginTop: "4px", fontSize: "11px", color: "var(--fail)" }}>
            {gate.blockers.map((b, i) => <div key={i}>⚑ {b}</div>)}
          </div>
        )}
      </div>
    </div>
  );
}