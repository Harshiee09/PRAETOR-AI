"use client";

import { useId, useMemo, useRef, useState } from "react";
import { Check, Copy, Info, Printer } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { AnswerMarkdown } from "@/components/answer-markdown";
import { CitationCard } from "@/components/citation-card";
import { SourceDrawer } from "@/components/source-drawer";
import type { DocumentAnalysis, DocumentCitation, DocumentInfo } from "@/lib/api/types";
import { DOCUMENT_DISCLAIMER, pagesLabel, TASKS } from "./utils";

export type DocumentResultValue = { answer: DocumentAnalysis; question: string; sampleData: boolean; documents: DocumentInfo[] };

export function DocumentResult({ result, onPassage }: { result: DocumentResultValue; onPassage: (citation: DocumentCitation) => void }) {
  const { answer, question, documents, sampleData } = result;
  const [highlighted, setHighlighted] = useState<string | null>(null);
  const [lawSource, setLawSource] = useState<DocumentCitation | null>(null);
  const [copyStatus, setCopyStatus] = useState("");
  const refs = useRef(new Map<string, HTMLElement>());
  const resultRef = useRef<HTMLElement>(null);
  const tooltipId = useId();
  const ids = useMemo(() => new Set(answer.citations.map((citation) => citation.id)), [answer.citations]);
  const labels = useMemo(() => new Map(answer.citations.filter((citation) => citation.kind === "document").map((citation) => [citation.id, citation.document_id === documents[1]?.document_id ? "B" : "A"] as const)), [answer.citations, documents]);
  const title = answer.task === "ask" ? question : answer.task === "compare" ? `Comparison: ${documents[0]?.filename ?? "Document A"} vs ${documents[1]?.filename ?? "Document B"}` : TASKS.find((task) => task.id === answer.task)?.title ?? "Document research";
  const coverage = answer.documents.map((document) => `${document.filename}: pages ${Array.isArray(document.pages_read) ? document.pages_read.join(", ") : document.pages_read}${document.complete ? "" : " (part of the document)"}`);

  function select(id: string) {
    const card = refs.current.get(id);
    if (!card) return;
    setHighlighted(id);
    card.scrollIntoView?.({ behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "nearest" });
    card.focus({ preventScroll: true });
  }
  async function copy() {
    const checks = Array.from(resultRef.current?.querySelectorAll<HTMLInputElement>(".document-checklist-item input") ?? []);
    let index = 0;
    const markdown = answer.answer_markdown.replace(/^(\s*[-*+]\s+)\[[ xX]\]/gm, (match, prefix: string) => checks[index] ? `${prefix}[${checks[index++].checked ? "x" : " "}]` : match);
    const text = [title, ...coverage, answer.warnings.length ? `Notes\n${answer.warnings.join("\n")}` : "", markdown, "Sources", ...answer.citations.map((citation) => `[${citation.id}] ${citation.title} — ${citation.locator}\n“${citation.quote}”${citation.source_url ? `\n${citation.source_url}` : ""}`), answer.jurisdiction_note, answer.disclaimer, answer.disclaimer === DOCUMENT_DISCLAIMER ? "" : DOCUMENT_DISCLAIMER, `Request ID: ${answer.trace_id}`].filter(Boolean).join("\n\n");
    try { await navigator.clipboard.writeText(text); setCopyStatus("Copied as text, including citations."); }
    catch { setCopyStatus("Copy is unavailable in this browser. Select the text to copy it."); }
  }

  return <section className="document-result" ref={resultRef} aria-labelledby="document-result-title">
    <div className="document-result-topline"><p className="answer-eyebrow">YOUR DOCUMENT, IN CONTEXT</p>{sampleData && <span className="sample-badge">Sample data</span>}</div>
    <h2 id="document-result-title">{title}</h2>
    <div className="document-result-tools"><span className="confidence-help"><button type="button" className="confidence-badge" data-confidence={answer.confidence} aria-describedby={tooltipId}>{answer.confidence.charAt(0).toUpperCase() + answer.confidence.slice(1)} confidence <Info size={14} aria-hidden="true"/></button><span role="tooltip" id={tooltipId} className="confidence-tooltip">How strongly the cited passages support this explanation. This is not a judgment of validity or enforceability.</span></span><button type="button" className="text-button" onClick={() => void copy()}><Copy size={15} aria-hidden="true"/>Copy as text</button><button type="button" className="text-button" onClick={() => window.print()}><Printer size={15} aria-hidden="true"/>Print</button></div>
    <p className="sr-only" role="status">{copyStatus}</p>
    {answer.warnings.length > 0 && <section className="answer-notes document-result-notes" aria-label="Notes"><h3>Notes</h3><ul>{answer.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></section>}
    <div className="document-pages-read"><strong>Pages read</strong>{coverage.map((line) => <p key={line}>{line}</p>)}</div>
    {answer.provider === "extractive" && <p className="extractive-note">The passages themselves (no AI summary)</p>}
    {answer.law_checked && answer.citations.some((citation) => citation.kind === "law") && <p className="document-law-check">Compared with Indian law where a law passage covered the same point</p>}
    {answer.task === "compare" && documents.length === 2 && <section className="document-compare-cards" aria-label="Documents compared"><div className="comparison-grid">{documents.map((document, slot) => {
      const letter = slot === 0 ? "A" : "B";
      const cited = answer.citations.filter((citation) => citation.kind === "document" && citation.document_id === document.document_id);
      const read = answer.documents[slot]; // coverage comes back in request order: A, then B
      return <Card key={document.document_id} data-document={letter}><CardHeader><div className="comparison-card-kicker"><span className="document-letter" aria-hidden="true">{letter}</span><Badge variant={slot === 0 ? "default" : "outline"}>DOCUMENT {letter}</Badge></div><CardTitle>{document.filename}</CardTitle><CardDescription>{read ? `Pages read: ${Array.isArray(read.pages_read) ? read.pages_read.join(", ") : read.pages_read}${read.complete ? "" : " (part of the document)"}` : `${document.pages} pages`}</CardDescription></CardHeader><Separator/><CardContent>{cited.length ? <ul>{cited.map((citation) => <li key={citation.id}><Check size={14} aria-hidden="true"/><button type="button" className="compare-cite" onClick={() => select(citation.id)}><span>{citation.id}</span>{citation.locator}</button></li>)}</ul> : <p className="reference-card-description">No passage of this document is cited in the comparison.</p>}</CardContent></Card>;
    })}</div></section>}
    <div className="document-answer-layout"><div className="document-answer-body"><div className={answer.abstained ? "answer-explanation" : "answer-markdown"}><AnswerMarkdown key={answer.trace_id} markdown={answer.answer_markdown} citationIds={ids} citationLabels={labels} onCitationClick={select} interactiveChecklist={answer.task === "checklist"} taskFormatting/></div><p className="jurisdiction-note">{answer.jurisdiction_note}</p>{answer.disclaimer !== DOCUMENT_DISCLAIMER && <p className="answer-disclaimer">{answer.disclaimer}</p>}<details className="answer-details"><summary>Research details</summary><p>{answer.cached ? "From cache" : "Fresh analysis"} · {(answer.latency_ms / 1000).toFixed(1)} seconds</p></details><p className="request-id">Request ID: {answer.trace_id}</p></div>
      {answer.citations.length > 0 && <aside className="citation-sidebar" aria-label="Document research sources"><h3>{answer.abstained ? "Closest provisions found (not confirmed to answer your question)" : "Sources"}</h3><div className="citation-list">{answer.citations.map((citation) => citation.kind === "law" ? <CitationCard key={citation.id} citation={citation} highlighted={highlighted === citation.id} onReadPassage={() => setLawSource(citation)} ref={(node) => { if (node) refs.current.set(citation.id, node); else refs.current.delete(citation.id); }}/> : <article key={citation.id} className="citation-card document-citation-card" data-document={labels.get(citation.id)} data-highlighted={highlighted === citation.id || undefined} id={`citation-${citation.id}`} tabIndex={-1} aria-label={`Source ${citation.id}: Document ${labels.get(citation.id)}`} ref={(node) => { if (node) refs.current.set(citation.id, node); else refs.current.delete(citation.id); }}><div className="citation-heading"><span className="citation-id">{citation.id}</span><span className="document-source-label">Your document · {labels.get(citation.id)}</span></div><h3>{documents.find((document) => document.document_id === citation.document_id)?.filename ?? citation.title}</h3><p className="citation-locator">{citation.locator}</p><p className="citation-meta">{pagesLabel(citation.page_start, citation.page_end)}</p><blockquote className="citation-quote">“{citation.quote}”</blockquote><button type="button" className="text-button" onClick={() => onPassage(citation)}>Show full passage{" "}<span className="sr-only">{citation.id}</span></button></article>)}</div></aside>}
    </div>
    {lawSource && <SourceDrawer citation={lawSource} onClose={() => setLawSource(null)}/>}
  </section>;
}
