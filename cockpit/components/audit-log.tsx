"use client";
import type { AuditEntry } from "@/lib/studio-config";

interface AuditLogProps {
  entries: AuditEntry[];
}

const LAYER_COLORS: Record<number, string> = {
  1:  "#00e5ff",
  2:  "#7c4dff",
  3:  "#00c853",
  4:  "#ff6d00",
  5:  "#d500f9",
  6:  "#304ffe",
  7:  "#ff1744",
  8:  "#ffc400",
  9:  "#00bcd4",
  10: "#76ff03",
  11: "#ff4081",
  12: "#18ffff",
  13: "#ffab40",
  14: "#69f0ae",
  15: "#e040fb",
  16: "#40c4ff",
  17: "#ff6e40",
};

export function AuditLog({ entries }: AuditLogProps) {
  if (!entries.length) {
    return <div style={{ color: "var(--muted)", padding: "12px" }}>No events yet.</div>;
  }

  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      maxHeight: "320px",
      overflowY: "auto",
    }}>
      {entries.map((entry, i) => (
        <div key={i} style={{
          display: "grid",
          gridTemplateColumns: "100px 40px 1fr auto",
          gap: "8px",
          padding: "6px 12px",
          borderBottom: i < entries.length - 1 ? "1px solid var(--border)" : "none",
          alignItems: "start",
          fontSize: "11px",
        }}>
          <span style={{ color: "var(--muted)" }}>
            {entry.ts.replace("T", " ").replace("Z", "")}
          </span>
          <span style={{ color: LAYER_COLORS[entry.layer] ?? "var(--accent)", fontWeight: 700 }}>
            L{entry.layer}
          </span>
          <span style={{ color: "var(--text)" }}>
            <span style={{ color: "var(--accent)" }}>{entry.event}</span>
            {" "}{entry.detail}
          </span>
          <span style={{ color: "var(--muted)" }}>{entry.user}</span>
        </div>
      ))}
    </div>
  );
}