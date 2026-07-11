const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface TriageResult {
  response_text: string;
  phase: string;
  confidence: number;
  action_items: string[];
  warnings: string[];
  metadata: { word_count: number; language: string; source: string };
}

export interface SSEChunk {
  stage: string;
  done: boolean;
  result?: TriageResult;
}

/** POST /api/triage and yield SSE chunks as they arrive.
 * Yields progress stages, then a final chunk with `done: true` and the brief. */
export async function* streamTriage(
  pincode: string,
  hours = 6
): AsyncGenerator<SSEChunk> {
  const res = await fetch(`${API_URL}/api/triage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pincode, hours }),
  });
  yield* parseSSE(res);
}

/** POST /api/relief and yield SSE chunks: progress stages, then the matched
 * schemes with a draft application in the requested language. */
export async function* streamRelief(
  description: string,
  language: string
): AsyncGenerator<SSEChunk> {
  const res = await fetch(`${API_URL}/api/relief`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description, language }),
  });
  yield* parseSSE(res);
}

/** Parse a text/event-stream body into typed chunks. Tolerates chunks split
 * across network reads by buffering incomplete lines; stops at [DONE]. */
async function* parseSSE(res: Response): AsyncGenerator<SSEChunk> {
  if (!res.ok || !res.body) throw new Error(`API error: ${res.status}`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (raw === "[DONE]") return;
      try {
        yield JSON.parse(raw) as SSEChunk;
      } catch {
        // skip malformed chunks
      }
    }
  }
}

/** GET recent citizen reports for a pincode (non-streaming). */
export async function fetchReports(pincode: string, hours = 6) {
  const res = await fetch(`${API_URL}/api/reports/${pincode}?hours=${hours}`);
  if (!res.ok) throw new Error(`Reports fetch failed: ${res.status}`);
  return res.json();
}
