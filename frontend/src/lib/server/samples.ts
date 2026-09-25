import "server-only";

import type { AskResponse } from "@/lib/api/types";

/** A UI placeholder, never a legal answer or an invented authority. */
export function sampleAnswer(requestId: string): AskResponse {
  return {
    answer_markdown:
      "Sample data — no legal research was performed.\n\nThe research backend is not connected in this development preview. A supported answer requires retrieved passages from the indexed Acts or Supreme Court judgments, with their original source records.\n\nJurisdiction and date: no jurisdiction or date was verified in this sample.",
    language: "en",
    confidence: "low",
    abstained: true,
    citations: [],
    warnings: [
      "Sample data. This placeholder contains no legal findings or verified citations.",
    ],
    jurisdiction_note:
      "Coverage and current law have not been checked in this sample.",
    disclaimer:
      "For informational legal research only. PRAETOR AI is not a lawyer and does not provide legal advice.",
    trace_id: requestId,
    provider: null,
    model: null,
    classification: {
      domain: "sample",
      intent: "development_preview",
      high_stakes: false,
    },
    cached: false,
    latency_ms: 0,
    explain: null,
  };
}
