import type { CSSProperties } from "react";

/** Shared form styles for the triage and relief pages — one source of truth
 * for the input/label/button look instead of per-page copies. */

export const fieldLabel: CSSProperties = {
  display: "block",
  fontSize: 12,
  fontWeight: 600,
  color: "var(--ms-text-secondary)",
  marginBottom: 6,
};

export const textInput: CSSProperties = {
  width: "100%",
  padding: "10px 14px",
  borderRadius: 8,
  background: "var(--ms-surface)",
  border: "1px solid var(--ms-border)",
  color: "var(--ms-text-primary)",
  fontSize: 14,
  outline: "none",
};

export const errorBox: CSSProperties = {
  padding: "10px 14px",
  borderRadius: 8,
  background: "rgba(239,68,68,0.1)",
  border: "1px solid rgba(239,68,68,0.4)",
  color: "#ef4444",
  fontSize: 13,
};

export function submitButton(loading: boolean, color = "var(--ms-accent)"): CSSProperties {
  return {
    padding: "10px 24px",
    borderRadius: 8,
    background: loading ? "var(--ms-border)" : color,
    color: "white",
    fontWeight: 700,
    fontSize: 14,
    border: "none",
    cursor: loading ? "not-allowed" : "pointer",
    transition: "background 0.15s",
    whiteSpace: "nowrap",
  };
}
