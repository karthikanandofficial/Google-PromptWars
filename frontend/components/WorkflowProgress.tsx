"use client";

import { motion, AnimatePresence } from "framer-motion";

const STAGES = ["Fetching reports...", "Analyzing...", "Generating brief..."];

export function WorkflowProgress({ currentStage }: { currentStage: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, padding: "16px 0" }}>
      {STAGES.map((stage, i) => {
        const currentIdx = STAGES.indexOf(currentStage);
        const isDone = i < currentIdx || currentStage === "Complete";
        const isActive = stage === currentStage;

        return (
          <motion.div
            key={stage}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "8px 12px",
              borderRadius: 8,
              background: isActive
                ? "rgba(79,142,247,0.1)"
                : isDone
                ? "rgba(16,185,129,0.08)"
                : "transparent",
              border: `1px solid ${isActive ? "var(--accent)" : isDone ? "var(--success)" : "var(--border)"}`,
              transition: "all 0.2s ease",
            }}
          >
            <span style={{ fontSize: 14 }}>
              {isDone ? "✓" : isActive ? "⟳" : "○"}
            </span>
            <span
              style={{
                fontSize: 13,
                color: isDone
                  ? "var(--success)"
                  : isActive
                  ? "var(--accent)"
                  : "var(--text-secondary)",
                fontWeight: isActive ? 600 : 400,
              }}
            >
              {stage}
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}
