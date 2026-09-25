"use client";

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { ArrowUpRight, LoaderCircle, X } from "lucide-react";
import { getSource } from "@/lib/api/client";
import { ApiClientError, errorMessage } from "@/lib/api/errors";
import type { Citation, SourceResponse } from "@/lib/api/types";
import {
  formatSourceDate,
  safeExternalUrl,
  sourceStatusLabel,
} from "@/lib/citations";

type Passage = SourceResponse & { sampleData?: boolean };
type SourceDrawerProps = { citation: Citation; onClose: () => void };

export function SourceDrawer({ citation, onClose }: SourceDrawerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const [passage, setPassage] = useState<Passage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{
    message: string;
    requestId: string;
  } | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const previousFocus =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const dialog = dialogRef.current;
    dialog?.showModal();
    closeRef.current?.focus();
    return () => {
      dialog?.close();
      if (previousFocus?.isConnected)
        previousFocus.focus({ preventScroll: true });
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError(null);
    setPassage(null);
    getSource(citation.chunk_id, { signal: controller.signal })
      .then((result) => {
        if (active) setPassage(result);
      })
      .catch((failure: unknown) => {
        if (!active || controller.signal.aborted) return;
        setError({
          message: errorMessage(failure),
          requestId:
            failure instanceof ApiClientError
              ? failure.requestId
              : "Unavailable",
        });
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [citation.chunk_id, attempt]);

  function containFocus(event: KeyboardEvent<HTMLDialogElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      onClose();
      return;
    }
    if (event.key !== "Tab") return;
    const controls = Array.from(
      event.currentTarget.querySelectorAll<HTMLElement>(
        "button:not([disabled]), a[href], [tabindex='0']",
      ),
    );
    const first = controls[0];
    const last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first?.focus();
    }
  }

  const sourceUrl = safeExternalUrl(passage?.source_url);
  const pageRange =
    passage?.page_start != null
      ? passage.page_end != null && passage.page_end !== passage.page_start
        ? `Pages ${passage.page_start}–${passage.page_end}`
        : `Page ${passage.page_start}`
      : passage?.page_end != null
        ? `Page ${passage.page_end}`
        : null;

  return (
    <dialog
      ref={dialogRef}
      className="source-dialog"
      aria-labelledby="source-drawer-title"
      aria-describedby="source-drawer-description"
      onKeyDown={containFocus}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <header className="source-dialog-header">
        <div>
          <p className="answer-eyebrow">SOURCE {citation.id}</p>
          <h2 id="source-drawer-title">Full passage</h2>
        </div>
        <button
          ref={closeRef}
          type="button"
          className="icon-button"
          aria-label="Close full passage"
          onClick={onClose}
        >
          <X size={21} aria-hidden="true" />
        </button>
      </header>
      <div className="source-dialog-body">
        <p id="source-drawer-description" className="source-context">
          The complete stored passage, with its source metadata.
        </p>
        {loading && (
          <div className="source-loading" role="status">
            <LoaderCircle
              className="loading-spinner"
              aria-hidden="true"
              size={22}
            />
            <p>Loading the source passage…</p>
            <button type="button" className="text-button" onClick={onClose}>
              Cancel loading
            </button>
          </div>
        )}
        {error && (
          <div className="source-error" role="alert">
            <h3>The passage could not be loaded</h3>
            <p>{error.message}</p>
            <p className="request-id">Request ID: {error.requestId}</p>
            <button
              type="button"
              className="secondary-button"
              onClick={() => setAttempt((value) => value + 1)}
            >
              Try again
            </button>
          </div>
        )}
        {passage && (
          <>
            <div className="source-passage-heading">
              {passage.sampleData && (
                <span className="sample-badge">Sample data</span>
              )}
              <span className="status-badge" data-status={passage.status}>
                {sourceStatusLabel(passage.status)}
              </span>
              <h3>{passage.title}</h3>
              <p>
                {passage.locator}
                {pageRange ? ` · ${pageRange}` : ""}
              </p>
              {passage.section_heading && <p>{passage.section_heading}</p>}
            </div>
            <div
              className="source-passage"
              tabIndex={0}
              aria-label="Full source text"
            >
              {passage.text}
            </div>
            <dl className="source-metadata">
              <div>
                <dt>Authority</dt>
                <dd>{passage.authority}</dd>
              </div>
              <div>
                <dt>Jurisdiction</dt>
                <dd>{passage.jurisdiction}</dd>
              </div>
              <div>
                <dt>Document type</dt>
                <dd>{passage.doc_type}</dd>
              </div>
              <div>
                <dt>Language</dt>
                <dd>{passage.language}</dd>
              </div>
              {passage.act_title && (
                <div>
                  <dt>Act</dt>
                  <dd>{passage.act_title}</dd>
                </div>
              )}
              {passage.section && (
                <div>
                  <dt>Section</dt>
                  <dd>{passage.section}</dd>
                </div>
              )}
              {passage.case_title && (
                <div>
                  <dt>Case</dt>
                  <dd>{passage.case_title}</dd>
                </div>
              )}
              {passage.court && (
                <div>
                  <dt>Court</dt>
                  <dd>{passage.court}</dd>
                </div>
              )}
              {passage.decision_date && (
                <div>
                  <dt>Decision date</dt>
                  <dd>{formatSourceDate(passage.decision_date)}</dd>
                </div>
              )}
              {passage.citation && (
                <div>
                  <dt>Citation</dt>
                  <dd>{passage.citation}</dd>
                </div>
              )}
              <div>
                <dt>Retrieved</dt>
                <dd>
                  <time dateTime={passage.retrieved_at}>
                    {formatSourceDate(passage.retrieved_at)}
                  </time>
                </dd>
              </div>
              <div>
                <dt>Licence</dt>
                <dd>{passage.licence}</dd>
              </div>
            </dl>
            {sourceUrl && (
              <a
                className="source-link"
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                referrerPolicy="no-referrer"
              >
                Open original source
                <ArrowUpRight size={16} aria-hidden="true" />
                <span className="sr-only"> (opens in a new tab)</span>
              </a>
            )}
          </>
        )}
      </div>
    </dialog>
  );
}
