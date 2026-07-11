"use client";

import { useState } from "react";
import { streamRelief, TriageResult } from "@/lib/api";
import { StreamingResponse } from "@/components/StreamingResponse";

const LANGUAGES = [
  { value: "English", label: "English" },
  { value: "Hindi", label: "Hindi / हिंदी" },
  { value: "Tamil", label: "Tamil / தமிழ்" },
  { value: "Telugu", label: "Telugu / తెలుగు" },
  { value: "Kannada", label: "Kannada / ಕನ್ನಡ" },
  { value: "Malayalam", label: "Malayalam / മലയാളം" },
];

export default function ReliefPage() {
  const [description, setDescription] = useState("");
  const [language, setLanguage] = useState("English");
  const [result, setResult] = useState<TriageResult | null>(null);
  const [stage, setStage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) {
      setError("Please describe your loss or damage.");
      return;
    }
    setError(null);
    setResult(null);
    setLoading(true);
    setStage("Reading your description...");

    try {
      for await (const chunk of streamRelief(description, language)) {
        setStage(chunk.stage);
        if (chunk.done && chunk.result) {
          setResult(chunk.result);
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>
        Relief Scheme Lookup
      </h1>
      <p style={{ fontSize: 13, color: "var(--ms-text-secondary)", marginBottom: 24 }}>
        Describe your loss in any language. We'll match applicable government relief schemes and generate a draft application.
      </p>

      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", flexDirection: "column", gap: 14, marginBottom: 24 }}
      >
        <div>
          <label
            htmlFor="loss-description"
            style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--ms-text-secondary)", marginBottom: 6 }}
          >
            DESCRIBE YOUR LOSS OR DAMAGE
          </label>
          <textarea
            id="loss-description"
            value={description}
            onChange={(e) => setDescription(e.target.value.slice(0, 1000))}
            placeholder="Describe your loss in any language... (e.g. My house was flooded, ground floor fully damaged. Lost cattle and crops.)"
            aria-label="Describe your loss in any language"
            rows={5}
            style={{
              width: "100%",
              padding: "12px 14px",
              borderRadius: 8,
              background: "var(--ms-surface)",
              border: "1px solid var(--ms-border)",
              color: "var(--ms-text-primary)",
              fontSize: 14,
              resize: "vertical",
              outline: "none",
              lineHeight: 1.6,
            }}
          />
          <div style={{ fontSize: 11, color: "var(--ms-text-secondary)", marginTop: 4, textAlign: "right" }}>
            {description.length}/1000
          </div>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div style={{ flex: "1 1 200px" }}>
            <label
              htmlFor="language-select"
              style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--ms-text-secondary)", marginBottom: 6 }}
            >
              RESPONSE LANGUAGE
            </label>
            <select
              id="language-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              aria-label="Select response language"
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: 8,
                background: "var(--ms-surface)",
                border: "1px solid var(--ms-border)",
                color: "var(--ms-text-primary)",
                fontSize: 14,
                outline: "none",
              }}
            >
              {LANGUAGES.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            aria-label="Find matching relief schemes"
            style={{
              padding: "10px 24px",
              borderRadius: 8,
              background: loading ? "var(--ms-border)" : "var(--ms-success)",
              color: "white",
              fontWeight: 700,
              fontSize: 14,
              border: "none",
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background 0.15s",
              whiteSpace: "nowrap",
            }}
          >
            {loading ? stage ?? "Processing..." : "Find Schemes"}
          </button>
        </div>

        {error && (
          <div
            role="alert"
            style={{
              padding: "10px 14px",
              borderRadius: 8,
              background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.4)",
              color: "#ef4444",
              fontSize: 13,
            }}
          >
            {error}
          </div>
        )}
      </form>

      <div aria-live="polite" aria-label="Relief scheme results">
        {result && <StreamingResponse result={result} />}
      </div>
    </div>
  );
}
