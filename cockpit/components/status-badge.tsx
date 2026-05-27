"use client";
interface StatusBadgeProps {
  label: string;
  variant?: "pass" | "fail" | "warn" | "muted" | "accent";
}

const COLORS = {
  pass:   "var(--pass)",
  fail:   "var(--fail)",
  warn:   "var(--warn)",
  muted:  "var(--muted)",
  accent: "var(--accent)",
};

export function StatusBadge({ label, variant = "muted" }: StatusBadgeProps) {
  const color = COLORS[variant] ?? "var(--muted)";
  return (
    <span style={{
      display: "inline-block",
      padding: "1px 6px",
      border: `1px solid ${color}`,
      color,
      fontSize: "10px",
      letterSpacing: "0.08em",
    }}>
      {label}
    </span>
  );
}