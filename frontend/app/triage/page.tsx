"use client";

import { useState } from "react";
import { streamTriage, TriageResult } from "@/lib/api";
import { fieldLabel, textInput, errorBox, submitButton } from "@/lib/styles";
import { WorkflowProgress } from "@/components/WorkflowProgress";
import { TriageBoard } from "@/components/TriageBoard";

export default function TriagePage() {
  const [pincode, setPincode] = useState("");
  const [hours, setHours] = useState(6);
  const [stage, setStage] = useState<string | null>(null);
  const [result, setResult] = useState<TriageResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(pincode)) {
      setError("Please enter a valid 6-digit pincode.");
      return;
    }
    setError(null);
    setResult(null);
    setLoading(true);
    setStage("Fetching reports...");

    try {
      for await (const chunk of streamTriage(pincode, hours)) {
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
        Coordinator Triage
      </h1>
      <p style={{ fontSize: 13, color: "var(--ms-text-secondary)", marginBottom: 24 }}>
        Enter a pincode to generate a priority-ranked triage brief from citizen reports.
      </p>

      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 24 }}
      >
        <div style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div style={{ flex: "1 1 160px" }}>
            <label
              htmlFor="pincode-input"
              style={fieldLabel}
            >
              PINCODE
            </label>
            <input
              id="pincode-input"
              type="text"
              value={pincode}
              onChange={(e) => setPincode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder="e.g. 682001"
              aria-label="Enter pincode"
              maxLength={6}
              style={textInput}
            />
          </div>
          <div style={{ flex: "1 1 120px" }}>
            <label
              htmlFor="hours-select"
              style={fieldLabel}
            >
              TIME WINDOW
            </label>
            <select
              id="hours-select"
              value={hours}
              onChange={(e) => setHours(Number(e.target.value))}
              aria-label="Select time window"
              style={textInput}
            >
              <option value={3}>Last 3 hours</option>
              <option value={6}>Last 6 hours</option>
              <option value={12}>Last 12 hours</option>
              <option value={24}>Last 24 hours</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={loading}
            aria-label="Generate triage brief"
            style={{ ...submitButton(loading), alignSelf: "flex-end" }}
          >
            {loading ? "Generating..." : "Generate Triage Brief"}
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

      {loading && stage && <WorkflowProgress currentStage={stage} />}

      <div aria-live="polite" aria-label="Triage results">
        {result && <TriageBoard result={result} />}
      </div>
    </div>
  );
}
