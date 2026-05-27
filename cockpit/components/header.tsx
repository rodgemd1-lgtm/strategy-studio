"use client";
interface HeaderProps {
  studio: string;
  diamond: string;
  bands: string;
  studioKey: string;
  onStudioChange: (k: string) => void;
}

const STUDIOS = [
  { key: "strategy", label: "Strategy" },
  { key: "gtm",      label: "GTM" },
  { key: "linkedin", label: "LinkedIn" },
  { key: "app",      label: "App" },
];

export function Header({ studio, diamond, bands, studioKey, onStudioChange }: HeaderProps) {
  return (
    <header style={{
      display: "flex",
      alignItems: "center",
      gap: "24px",
      padding: "16px 0",
      borderBottom: "1px solid var(--border)",
      flexWrap: "wrap",
    }}>
      {/* Studio tabs */}
      <nav style={{ display: "flex", gap: "4px" }}>
        {STUDIOS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => onStudioChange(key)}
            style={{
              padding: "4px 12px",
              background: studioKey === key ? "var(--surface)" : "transparent",
              border: studioKey === key ? "1px solid var(--accent)" : "1px solid transparent",
              color: studioKey === key ? "var(--accent)" : "var(--muted)",
              cursor: "pointer",
              fontFamily: "inherit",
              fontSize: "12px",
              letterSpacing: "0.06em",
            }}
          >
            {label}
          </button>
        ))}
      </nav>

      {/* Title */}
      <div style={{ flex: 1 }}>
        <div style={{ color: "var(--accent)", fontSize: "11px", letterSpacing: "0.18em" }}>
          RUSR COCKPIT
        </div>
        <div style={{ fontSize: "18px", fontWeight: 700, marginTop: "2px" }}>
          {studio}
        </div>
      </div>

      {/* Meta */}
      <div style={{ display: "flex", gap: "16px", color: "var(--muted)", fontSize: "12px" }}>
        <span>
          <span style={{ color: "var(--accent)" }}>◆ </span>
          {diamond}
        </span>
        <span>
          <span style={{ color: "var(--accent)" }}>⊕ </span>
          {bands}
        </span>
        <span>
          <span style={{ color: "var(--accent)" }}>◈ </span>
          17 layers
        </span>
      </div>
    </header>
  );
}