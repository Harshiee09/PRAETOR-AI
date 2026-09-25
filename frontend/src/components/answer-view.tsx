"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Info, ShieldCheck } from "lucide-react";
import type { AskResponse, Citation } from "@/lib/api/types";
import { AnswerMarkdown } from "@/components/answer-markdown";
import { CitationCard } from "@/components/citation-card";
import { SourceDrawer } from "@/components/source-drawer";

export type AnswerViewProps = { answer: AskResponse; sampleData?: boolean };

function ConfidenceBadge({
  confidence,
}: {
  confidence: AskResponse["confidence"];
}) {
  const tooltipId = useId();
  const [open, setOpen] = useState(false);
  return (
    <span
      className="confidence-help"
      data-open={open}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={(event) => {
        if (!event.currentTarget.contains(document.activeElement))
          setOpen(false);
      }}
    >
      <button
        type="button"
        className="confidence-badge"
        data-confidence={confidence}
        aria-describedby={tooltipId}
        onFocus={() => setOpen(true)}
        onClick={() => setOpen((value) => !value)}
        onBlur={() => setOpen(false)}
        onKeyDown={(event) => {
          if (event.key === "Escape") setOpen(false);
        }}
      >
        <ShieldCheck size={14} aria-hidden="true" />
        {confidence.charAt(0).toUpperCase() + confidence.slice(1)} confidence
        <Info size={13} aria-hidden="true" />
      </button>
      <span id={tooltipId} role="tooltip" className="confidence-tooltip">
        How strongly the retrieved sources support this answer. This is not a
        prediction of a legal outcome.
      </span>
    </span>
  );
}

export function AnswerView({ answer, sampleData = false }: AnswerViewProps) {
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const [activeSource, setActiveSource] = useState<Citation | null>(null);
  const highlightTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cardRefs = useRef(new Map<string, HTMLElement>());
  const citationIds = useMemo(
    () => new Set(answer.citations.map((citation) => citation.id)),
    [answer.citations],
  );
  const titleId = useId();
  const citationsTitleId = useId();

  useEffect(
    () => () => {
      if (highlightTimer.current) clearTimeout(highlightTimer.current);
    },
    [],
  );
  useEffect(() => {
    setActiveSource(null);
    setHighlightedId(null);
  }, [answer]);

  function highlightCitation(id: string) {
    const card = cardRefs.current.get(id);
    if (!card) return;
    if (highlightTimer.current) clearTimeout(highlightTimer.current);
    setHighlightedId(id);
    const reducedMotion = window.matchMedia?.(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    card.scrollIntoView?.({
      behavior: reducedMotion ? "instant" : "smooth",
      block: "nearest",
    });
    card.focus({ preventScroll: true });
    highlightTimer.current = setTimeout(() => setHighlightedId(null), 2400);
  }

  return (
    <section
      className="answer-layout"
      data-has-sources={answer.citations.length > 0}
      aria-labelledby={titleId}
    >
      <div
        className={
          answer.abstained ? "answer-main answer-abstained" : "answer-main"
        }
      >
        <div className="answer-topline">
          <div>
            <p className="answer-eyebrow">
              {answer.abstained
                ? "RESEARCH RESULT"
                : "SOURCE-GROUNDED RESEARCH"}
            </p>
            <h2 id={titleId}>
              {answer.abstained
                ? "More evidence is needed"
                : "Your research answer"}
            </h2>
          </div>
          <div className="answer-badges">
            {sampleData && <span className="sample-badge">Sample data</span>}
            <ConfidenceBadge confidence={answer.confidence} />
          </div>
        </div>
        {answer.provider === "extractive" && (
          <p className="extractive-note">
            Verbatim source passages (no AI summary)
          </p>
        )}
        <div
          className={
            answer.abstained ? "answer-explanation" : "answer-markdown"
          }
        >
          <AnswerMarkdown
            markdown={answer.answer_markdown}
            citationIds={citationIds}
            onCitationClick={highlightCitation}
          />
        </div>
        {answer.warnings.length > 0 && (
          <section className="answer-notes" aria-label="Notes">
            <h3>Notes</h3>
            <ul>
              {answer.warnings.map((warning, index) => (
                <li key={`${index}-${warning}`}>{warning}</li>
              ))}
            </ul>
          </section>
        )}
        <p className="jurisdiction-note">{answer.jurisdiction_note}</p>
        <p className="answer-disclaimer">
          <Info size={16} aria-hidden="true" />
          <span>{answer.disclaimer}</span>
        </p>
        <details className="answer-details">
          <summary>Research details</summary>
          <dl>
            <div>
              <dt>Response</dt>
              <dd>{answer.cached ? "From cache" : "Fresh search"}</dd>
            </div>
            <div>
              <dt>Time</dt>
              <dd>{(answer.latency_ms / 1000).toFixed(1)} seconds</dd>
            </div>
            <div>
              <dt>Request ID</dt>
              <dd className="request-id">{answer.trace_id}</dd>
            </div>
          </dl>
        </details>
      </div>
      {answer.citations.length > 0 && (
        <aside className="citation-sidebar" aria-labelledby={citationsTitleId}>
          <div className="citation-sidebar-heading">
            <h2 id={citationsTitleId}>
              {answer.abstained
                ? "Closest provisions found (not confirmed to answer your question)"
                : "Sources"}
            </h2>
            <span
              className="source-count"
              aria-label={`${answer.citations.length} sources`}
            >
              {String(answer.citations.length).padStart(2, "0")}
            </span>
          </div>
          <div className="citation-list">
            {answer.citations.map((citation) => (
              <CitationCard
                key={citation.id}
                citation={citation}
                highlighted={highlightedId === citation.id}
                onReadPassage={setActiveSource}
                ref={(element) => {
                  if (element) cardRefs.current.set(citation.id, element);
                  else cardRefs.current.delete(citation.id);
                }}
              />
            ))}
          </div>
        </aside>
      )}
      {activeSource && (
        <SourceDrawer
          citation={activeSource}
          onClose={() => setActiveSource(null)}
        />
      )}
    </section>
  );
}
