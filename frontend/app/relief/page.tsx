"use client";

import { useState } from "react";
import { streamRelief, TriageResult } from "@/lib/api";
import { StreamingResponse } from "@/components/StreamingResponse";
import { fieldLabel, textInput, errorBox, submitButton } from "@/lib/styles";

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
        Describe your loss in any language. We&apos;ll match applicable government relief schemes and generate a draft application.
      </p>

      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", flexDirection: "column", gap: 14, marginBottom: 24 }}
      >
        <div>
          <label
            htmlFor="loss-description"
            style={fieldLabel}
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
            style={{ ...textInput, padding: "12px 14px", resize: "vertical", lineHeight: 1.6 }}
          />
          <div style={{ fontSize: 11, color: "var(--ms-text-secondary)", marginTop: 4, textAlign: "right" }}>
            {description.length}/1000
          </div>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div style={{ flex: "1 1 200px" }}>
            <label
              htmlFor="language-select"
              style={fieldLabel}
            >
              RESPONSE LANGUAGE
            </label>
            <select
              id="language-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              aria-label="Select response language"
              style={textInput}
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
            style={submitButton(loading, "var(--ms-success)")}
          >
            {loading ? stage ?? "Processing..." : "Find Schemes"}
          </button>
        </div>

        {error && (
          <div
            role="alert"
            style={errorBox}
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
