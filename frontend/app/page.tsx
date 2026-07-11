"use client";

import Link from "next/link";

const FEATURES = [
  {
    href: "/map",
    title: "Live Reports Map",
    desc: "Real-time citizen reports from WhatsApp, visualized by district. Auto-updating via Firestore.",
    color: "var(--ms-accent)",
    icon: "🗺️",
  },
  {
    href: "/triage",
    title: "Coordinator Triage",
    desc: "Enter a pincode to get a priority-ranked action brief synthesized from recent citizen reports.",
    color: "var(--ms-warn)",
    icon: "📋",
  },
  {
    href: "/relief",
    title: "Relief Scheme Lookup",
    desc: "Describe your losses in any Indian language. Get matched schemes + a draft application.",
    color: "var(--ms-success)",
    icon: "🏛️",
  },
];

export default function Home() {
  return (
    <div style={{ maxWidth: 800, margin: "0 auto", paddingTop: 40 }}>
      <div style={{ marginBottom: 48, textAlign: "center" }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🌧️</div>
        <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 12 }}>
          MonsoonSaathi
        </h1>
        <p style={{ fontSize: 16, color: "var(--ms-text-secondary)", maxWidth: 520, margin: "0 auto", lineHeight: 1.6 }}>
          A phase-aware, multilingual disaster preparedness assistant for monsoon-prone India.
          WhatsApp-native · Powered by Gemini 2.0 Flash · Real-time via Firestore.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
        {FEATURES.map((f) => (
          <Link key={f.href} href={f.href} style={{ textDecoration: "none" }}>
            <div
              style={{
                padding: "24px 20px",
                borderRadius: 12,
                background: "var(--ms-surface)",
                border: "1px solid var(--ms-border)",
                transition: "border-color 0.15s",
                cursor: "pointer",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.borderColor = f.color;
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.borderColor = "var(--ms-border)";
              }}
            >
              <div style={{ fontSize: 28, marginBottom: 10 }}>{f.icon}</div>
              <h2 style={{ fontSize: 15, fontWeight: 700, color: f.color, marginBottom: 6 }}>
                {f.title}
              </h2>
              <p style={{ fontSize: 13, color: "var(--ms-text-secondary)", lineHeight: 1.5 }}>
                {f.desc}
              </p>
            </div>
          </Link>
        ))}
      </div>

      <div
        style={{
          marginTop: 40,
          padding: "20px",
          borderRadius: 10,
          background: "var(--ms-surface)",
          border: "1px solid var(--ms-border)",
          fontSize: 13,
          color: "var(--ms-text-secondary)",
          lineHeight: 1.6,
        }}
      >
        <strong style={{ color: "var(--ms-text-primary)" }}>How it works: </strong>
        Citizens submit ground reports via the web or SMS. Ward coordinators use the{" "}
        <strong style={{ color: "var(--ms-accent)" }}>Triage</strong> board to prioritize responses.
        Affected families use{" "}
        <strong style={{ color: "var(--ms-success)" }}>Relief Schemes</strong> to find and apply for
        government assistance. The{" "}
        <strong style={{ color: "var(--ms-warn)" }}>Live Map</strong> shows real-time report density
        across districts.
      </div>
    </div>
  );
}
