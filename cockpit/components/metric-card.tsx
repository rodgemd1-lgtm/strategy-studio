"use client";
interface MetricCardProps {
  label: string;
  value: string;
  pct: number;
  barColor: string;
}

export function MetricCard({ label, value, pct, barColor }: MetricCardProps) {
  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      padding: "12px 16px",
    }}>
      <div style={{ color: "var(--muted)", fontSize: "11px", letterSpacing: "0.1em", marginBottom: "6px" }}>
        {label}
      </div>
      <div style={{ fontSize: "20px", fontWeight: 700, color: barColor }}>
        {value}
      </div>
      {pct > 0 && (
        <div style={{ marginTop: "8px", height: "3px", background: "var(--border)", borderRadius: "2px" }}>
          <div style={{
            width: `${Math.min(pct, 100)}%`,
            height: "100%",
            background: barColor,
            borderRadius: "2px",
            transition: "width 0.3s",
          }} />
        </div>
      )}
      {pct > 0 && (
        <div style={{ marginTop: "4px", fontSize: "11px", color: "var(--muted)" }}>
          {pct.toFixed(1)}%
        </div>
      )}
    </div>
  );
}