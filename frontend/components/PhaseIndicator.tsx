"use client";

const PHASE_CONFIG = {
  PREPARE: { label: "PREPARE", color: "var(--accent)", bg: "rgba(79,142,247,0.15)" },
  DURING: { label: "DURING", color: "var(--warn)", bg: "rgba(245,158,11,0.15)" },
  AFTER: { label: "AFTER", color: "var(--success)", bg: "rgba(16,185,129,0.15)" },
  ALERT: { label: "ALERT", color: "var(--warn)", bg: "rgba(245,158,11,0.15)" },
  COORD: { label: "COORD", color: "#a78bfa", bg: "rgba(167,139,250,0.15)" },
};

export function PhaseIndicator({ phase }: { phase: string }) {
  const cfg = PHASE_CONFIG[phase as keyof typeof PHASE_CONFIG] ?? {
    label: phase,
    color: "var(--text-secondary)",
    bg: "rgba(148,163,184,0.1)",
  };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "2px 10px",
        borderRadius: "999px",
        fontSize: "11px",
        fontWeight: 700,
        letterSpacing: "0.05em",
        color: cfg.color,
        background: cfg.bg,
        border: `1px solid ${cfg.color}40`,
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: cfg.color,
          display: "inline-block",
        }}
      />
      {cfg.label}
    </span>
  );
}
