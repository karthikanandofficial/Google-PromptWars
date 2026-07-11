"use client";

import { useEffect, useState } from "react";
import { subscribeToReports, Report } from "@/lib/firestore";

function formatTime(ts: string) {
  try {
    return new Date(ts).toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

function ReportSkeleton() {
  return (
    <div className="animate-pulse space-y-2">
      {[...Array(4)].map((_, i) => (
        <div key={i} style={{ padding: "12px", borderRadius: 8, background: "var(--bg-surface)" }}>
          <div style={{ height: 12, width: "30%", background: "var(--border)", borderRadius: 4, marginBottom: 8 }} />
          <div style={{ height: 12, width: "80%", background: "var(--border)", borderRadius: 4 }} />
        </div>
      ))}
    </div>
  );
}

export function ReportFeed() {
  const [reports, setReports] = useState<Report[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsub = subscribeToReports(
      (r) => setReports(r),
      (e) => setError(e.message)
    );
    return unsub;
  }, []);

  if (error) {
    return (
      <div style={{ color: "var(--warn)", padding: 12, fontSize: 13 }}>
        Failed to load reports: {error}
      </div>
    );
  }

  if (reports === null) return <ReportSkeleton />;

  if (reports.length === 0) {
    return (
      <div style={{ color: "var(--text-secondary)", padding: 16, textAlign: "center", fontSize: 13 }}>
        No reports yet. Citizen reports will appear here in real time.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {reports.map((r) => (
        <div
          key={r.report_id}
          style={{
            padding: "12px 14px",
            borderRadius: 8,
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                color: "var(--accent)",
                background: "rgba(79,142,247,0.1)",
                padding: "2px 8px",
                borderRadius: 999,
              }}
            >
              {r.pincode}
            </span>
            <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>
              {formatTime(r.timestamp)}
            </span>
          </div>
          <p style={{ fontSize: 13, color: "var(--text-primary)", margin: 0, lineHeight: 1.4 }}>
            {r.text.length > 120 ? r.text.slice(0, 120) + "…" : r.text}
          </p>
        </div>
      ))}
    </div>
  );
}
