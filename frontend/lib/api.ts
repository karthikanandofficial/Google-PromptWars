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

export async function fetchReports(pincode: string, hours = 6) {
  const res = await fetch(`${API_URL}/api/reports/${pincode}?hours=${hours}`);
  if (!res.ok) throw new Error(`Reports fetch failed: ${res.status}`);
  return res.json();
}
