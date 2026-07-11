"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { TriageResult } from "@/lib/api";

export function StreamingResponse({ result }: { result: TriageResult }) {
  const [copied, setCopied] = useState(false);

  const copyText = async () => {
    await navigator.clipboard.writeText(result.response_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ display: "flex", flexDirection: "column", gap: 16 }}
    >
      <div
        style={{
          padding: "20px",
          borderRadius: 12,
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: "var(--success)",
              background: "rgba(16,185,129,0.1)",
              padding: "2px 10px",
              borderRadius: 999,
              border: "1px solid rgba(16,185,129,0.3)",
            }}
          >
            AFTER — Relief Guidance
          </span>
          <button
            onClick={copyText}
            aria-label="Copy response text"
            style={{
              fontSize: 12,
              color: copied ? "var(--success)" : "var(--accent)",
              background: "transparent",
              border: "1px solid currentColor",
              borderRadius: 6,
              padding: "3px 10px",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            {copied ? "✓ Copied!" : "Copy"}
          </button>
        </div>
        <p
          style={{
            margin: 0,
            fontSize: 14,
            color: "var(--text-primary)",
            lineHeight: 1.7,
            whiteSpace: "pre-wrap",
          }}
        >
          {result.response_text}
        </p>
      </div>

      {result.action_items.length > 0 && (
        <div>
          <h3 style={{ margin: "0 0 10px", fontSize: 12, fontWeight: 700, color: "var(--text-secondary)", letterSpacing: "0.07em" }}>
            STEPS TO CLAIM
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {result.action_items.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                style={{
                  display: "flex",
                  gap: 10,
                  padding: "10px 14px",
                  borderRadius: 8,
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border)",
                }}
              >
                <span style={{ color: "var(--success)", fontWeight: 700, flexShrink: 0 }}>
                  {i + 1}.
                </span>
                <span style={{ fontSize: 13, color: "var(--text-primary)" }}>{item}</span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {result.warnings.length > 0 && (
        <div
          style={{
            padding: "10px 14px",
            borderRadius: 8,
            background: "rgba(245,158,11,0.08)",
            border: "1px solid rgba(245,158,11,0.3)",
            fontSize: 12,
            color: "var(--warn)",
          }}
        >
          {result.warnings.join(" · ")}
        </div>
      )}
    </motion.div>
  );
}
