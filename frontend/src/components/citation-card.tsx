"use client";

import { forwardRef } from "react";
import { ArrowUpRight, BookOpen } from "lucide-react";
import type { Citation } from "@/lib/api/types";
import {
  formatSourceDate,
  safeExternalUrl,
  sourceStatusLabel,
} from "@/lib/citations";

type CitationCardProps = {
  citation: Citation;
  highlighted: boolean;
  onReadPassage: (citation: Citation) => void;
};

export const CitationCard = forwardRef<HTMLElement, CitationCardProps>(
  function CitationCard({ citation, highlighted, onReadPassage }, ref) {
    const sourceUrl = safeExternalUrl(citation.source_url);
    return (
      <article
        id={`citation-${citation.id}`}
        ref={ref}
        className="citation-card"
        data-highlighted={highlighted || undefined}
        tabIndex={-1}
        aria-label={`Source ${citation.id}: ${citation.title}`}
      >
        <div className="citation-heading">
          <span className="citation-id">{citation.id}</span>
          <span className="status-badge" data-status={citation.status}>
            {sourceStatusLabel(citation.status)}
          </span>
        </div>
        <h3>{citation.title}</h3>
        <p className="citation-locator">{citation.locator}</p>
        {citation.section_heading && (
          <p className="citation-section">{citation.section_heading}</p>
        )}
        {(citation.court || citation.decision_date) && (
          <p className="citation-meta">
            {[
              citation.court,
              citation.decision_date
                ? formatSourceDate(citation.decision_date)
                : null,
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
        )}
        {citation.citation && (
          <p className="citation-meta">{citation.citation}</p>
        )}
        <blockquote className="citation-quote">“{citation.quote}”</blockquote>
        <p className="citation-meta">
          {citation.authority} · {citation.jurisdiction}
        </p>
        <p className="citation-meta">
          Retrieved{" "}
          <time dateTime={citation.retrieved_at}>
            {formatSourceDate(citation.retrieved_at)}
          </time>
        </p>
        <div className="citation-footer">
          <button
            type="button"
            className="text-button"
            onClick={() => onReadPassage(citation)}
          >
            <BookOpen size={15} aria-hidden="true" />
            Read full passage
          </button>
          {sourceUrl && (
            <a
              className="source-link"
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              referrerPolicy="no-referrer"
            >
              Original source
              <ArrowUpRight size={14} aria-hidden="true" />
              <span className="sr-only"> (opens in a new tab)</span>
            </a>
          )}
        </div>
      </article>
    );
  },
);
