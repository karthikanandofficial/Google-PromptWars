"use client";

import { useEffect, useState } from "react";
import { subscribeToReports, Report } from "@/lib/firestore";
import { ReportFeed } from "@/components/ReportFeed";

const ZONES = [
  { id: "ernakulam", label: "Ernakulam", pincodes: ["682"], cx: 195, cy: 390, r: 22 },
  { id: "mumbai",    label: "Mumbai",    pincodes: ["400"], cx: 148, cy: 260, r: 22 },
  { id: "guwahati",  label: "Guwahati",  pincodes: ["781"], cx: 370, cy: 135, r: 22 },
  { id: "bhubaneswar", label: "Bhubaneswar", pincodes: ["751"], cx: 305, cy: 255, r: 22 },
  { id: "chennai",   label: "Chennai",   pincodes: ["600"], cx: 270, cy: 375, r: 22 },
  { id: "bengaluru", label: "Bengaluru", pincodes: ["560"], cx: 228, cy: 340, r: 22 },
];

function zoneColor(count: number): string {
  if (count === 0) return "transparent";
  if (count <= 3) return "rgba(245,158,11,0.5)";
  if (count <= 10) return "rgba(249,115,22,0.6)";
  return "rgba(239,68,68,0.7)";
}

function zoneBorder(count: number): string {
  if (count === 0) return "#1E293B";
  if (count <= 3) return "#F59E0B";
  if (count <= 10) return "#F97316";
  return "#EF4444";
}

export default function MapPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsub = subscribeToReports(
      (r) => {
        setReports(r);
        setLoading(false);
      },
      () => setLoading(false)
    );
    return unsub;
  }, []);

  const countForZone = (zone: (typeof ZONES)[0]) =>
    reports.filter((r) =>
      zone.pincodes.some((p) => r.pincode.startsWith(p))
    ).length;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>
        Live Reports Map
      </h1>
      <p style={{ fontSize: 13, color: "var(--ms-text-secondary)", marginBottom: 24 }}>
        Real-time citizen reports from WhatsApp. Updates automatically.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 24, alignItems: "start" }}>
        {/* SVG Map */}
        <div
          style={{
            background: "var(--ms-surface)",
            border: "1px solid var(--ms-border)",
            borderRadius: 12,
            padding: 24,
            overflow: "hidden",
          }}
        >
          <svg
            viewBox="0 0 460 480"
            style={{ width: "100%", maxHeight: 480 }}
            aria-label="India flood zone map with report counts"
            role="img"
          >
            {/* Simplified India outline */}
            <path
              d="M180,60 L280,55 L350,80 L420,100 L440,160 L430,200 L390,220 L400,260 L370,300 L340,330 L310,370 L280,410 L260,440 L240,460 L220,450 L210,420 L190,400 L160,380 L140,350 L110,310 L90,270 L80,230 L70,180 L80,140 L110,100 L150,70 Z"
              fill="rgba(79,142,247,0.06)"
              stroke="var(--ms-border)"
              strokeWidth="1.5"
            />

            {/* Zone circles */}
            {ZONES.map((zone) => {
              const count = countForZone(zone);
              return (
                <g key={zone.id}>
                  <circle
                    cx={zone.cx}
                    cy={zone.cy}
                    r={zone.r}
                    fill={zoneColor(count)}
                    stroke={zoneBorder(count)}
                    strokeWidth="1.5"
                  />
                  {count > 0 && (
                    <text
                      x={zone.cx}
                      y={zone.cy + 1}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fontSize="11"
                      fontWeight="700"
                      fill="white"
                    >
                      {count}
                    </text>
                  )}
                  <text
                    x={zone.cx}
                    y={zone.cy + zone.r + 12}
                    textAnchor="middle"
                    fontSize="10"
                    fill="var(--ms-text-secondary)"
                  >
                    {zone.label}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Legend */}
          <div style={{ display: "flex", gap: 16, marginTop: 12, flexWrap: "wrap" }}>
            {[
              { color: "transparent", border: "#1E293B", label: "0 reports" },
              { color: "rgba(245,158,11,0.5)", border: "#F59E0B", label: "1–3" },
              { color: "rgba(249,115,22,0.6)", border: "#F97316", label: "4–10" },
              { color: "rgba(239,68,68,0.7)", border: "#EF4444", label: "10+" },
            ].map((l) => (
              <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: "50%",
                    background: l.color,
                    border: `1.5px solid ${l.border}`,
                  }}
                />
                <span style={{ fontSize: 11, color: "var(--ms-text-secondary)" }}>{l.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Report Feed */}
        <div
          style={{
            background: "var(--ms-surface)",
            border: "1px solid var(--ms-border)",
            borderRadius: 12,
            padding: 16,
          }}
        >
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: "var(--ms-text-secondary)", letterSpacing: "0.05em" }}>
            LATEST REPORTS
          </h2>
          <ReportFeed />
        </div>
      </div>
    </div>
  );
}
