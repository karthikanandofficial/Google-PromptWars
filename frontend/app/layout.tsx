import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "MonsoonSaathi — Disaster Preparedness Assistant",
  description: "Phase-aware monsoon preparedness for Indian households. WhatsApp-native, multilingual.",
};

const NAV_LINKS = [
  { href: "/map", label: "Live Map" },
  { href: "/triage", label: "Triage" },
  { href: "/relief", label: "Relief Schemes" },
];

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full">
      <body
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          background: "var(--ms-bg)",
          color: "var(--ms-text-primary)",
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
        }}
      >
        <nav
          style={{
            background: "var(--ms-surface)",
            borderBottom: "1px solid var(--ms-border)",
            padding: "0 24px",
            display: "flex",
            alignItems: "center",
            gap: 32,
            height: 56,
          }}
          aria-label="Main navigation"
        >
          <Link href="/" style={{ fontWeight: 700, fontSize: 15, color: "var(--ms-text-primary)" }}>
            🌧 MonsoonSaathi
          </Link>
          <div style={{ display: "flex", gap: 20 }}>
            {NAV_LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                style={{ fontSize: 13, color: "var(--ms-text-secondary)", fontWeight: 500 }}
              >
                {l.label}
              </Link>
            ))}
          </div>
        </nav>
        <main style={{ flex: 1, padding: "24px" }} role="main">
          {children}
        </main>
      </body>
    </html>
  );
}
