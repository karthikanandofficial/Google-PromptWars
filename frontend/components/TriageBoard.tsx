"use client";

import { motion } from "framer-motion";
import { TriageResult } from "@/lib/api";

const PRIORITY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CRITICAL: { bg: "rgba(239,68,68,0.1)", text: "#ef4444", border: "#ef4444" },
  HIGH: { bg: "rgba(245,158,11,0.1)", text: "var(--ms-warn)", border: "var(--ms-warn)" },
  MEDIUM: { bg: "rgba(79,142,247,0.1)", text: "var(--ms-accent)", border: "var(--ms-accent)" },
};

function parsePriority(item: string): "CRITICAL" | "HIGH" | "MEDIUM" {
  const upper = item.toUpperCase();
  if (upper.includes("CRITICAL")) return "CRITICAL";
  if (upper.includes("HIGH")) return "HIGH";
  return "MEDIUM";
}

function TriageCard({ item, index }: { item: string; index: number }) {
  const priority = parsePriority(item);
  const cfg = PRIORITY_COLORS[priority];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      style={{
        padding: "14px 16px",
        borderRadius: 10,
        background: cfg.bg,
        border: `1px solid ${cfg.border}40`,
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
        <span
          style={{
            flexShrink: 0,
            fontSize: 10,
            fontWeight: 800,
            letterSpacing: "0.08em",
            color: cfg.text,
            background: `${cfg.border}20`,
            border: `1px solid ${cfg.border}`,
            padding: "2px 8px",
            borderRadius: 999,
            marginTop: 1,
          }}
        >
          {priority}
        </span>
        <p style={{ margin: 0, fontSize: 13, color: "var(--ms-text-primary)", lineHeight: 1.5 }}>
          {item.replace(/^(CRITICAL:|HIGH:|MEDIUM:)\s*/i, "")}
        </p>
      </div>
    </motion.div>
  );
}

export function TriageBoard({ result }: { result: TriageResult }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div
        style={{
          padding: "16px",
          borderRadius: 10,
          background: "var(--ms-surface)",
          border: "1px solid var(--ms-border)",
          marginBottom: 4,
        }}
      >
        <p style={{ margin: 0, fontSize: 14, color: "var(--ms-text-primary)", lineHeight: 1.6 }}>
          {result.response_text}
        </p>
        <div style={{ marginTop: 8, fontSize: 11, color: "var(--ms-text-secondary)" }}>
          Confidence: {Math.round(result.confidence * 100)}% · Source: {result.metadata.source}
        </div>
      </div>

      {result.action_items.length > 0 && (
        <>
          <h3 style={{ margin: "8px 0 4px", fontSize: 13, fontWeight: 700, color: "var(--ms-text-secondary)", letterSpacing: "0.05em" }}>
            PRIORITY ACTIONS
          </h3>
          {result.action_items.map((item, i) => (
            <TriageCard key={i} item={item} index={i} />
          ))}
        </>
      )}

      {result.warnings.length > 0 && (
        <div
          style={{
            padding: "10px 14px",
            borderRadius: 8,
            background: "rgba(245,158,11,0.08)",
            border: "1px solid rgba(245,158,11,0.3)",
            fontSize: 12,
            color: "var(--ms-warn)",
          }}
        >
          {result.warnings.join(" · ")}
        </div>
      )}
    </div>
  );
}
