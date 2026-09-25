"use client";
import { useEffect, useRef } from "react";
import type { DocumentCitation, DocumentDetail } from "@/lib/api/types";
import { DocumentDialog } from "./document-dialog";
import { pagesLabel, passageNumber, quoteRange } from "./utils";

export function PassageDrawer({ detail, citation, onClose }: { detail: DocumentDetail; citation?: DocumentCitation; onClose: () => void }) {
  const selected = citation ? passageNumber(citation) : null;
  const target = useRef<HTMLElement>(null);
  useEffect(() => { target.current?.scrollIntoView?.({ block: "start", behavior: "instant" }); }, [selected]);
  const found = selected === null || detail.passages.some((passage) => passage.n === selected);
  return <DocumentDialog title="Your document text" onClose={onClose}>
    <p className="document-drawer-filename">{detail.filename}</p>
    {!found && <p role="status">This cited passage is unavailable. The remaining stored passages are shown below.</p>}
    <div className="document-passages">{detail.passages.map((passage) => {
      const isSelected = passage.n === selected;
      const range = isSelected && citation ? quoteRange(passage.text, citation.quote) : null;
      return <section key={passage.n} ref={isSelected ? target : undefined} className="document-passage" data-selected={isSelected || undefined}>
        <h3>{passage.locator}</h3><p className="citation-meta">{pagesLabel(passage.page_start, passage.page_end)} · Passage {passage.n}</p>
        <p className="source-passage">{range ? <>{passage.text.slice(0, range[0])}<mark>{passage.text.slice(range[0], range[1])}</mark>{passage.text.slice(range[1])}</> : passage.text}</p>
        {isSelected && citation && !range && <p className="citation-meta">The citation quote could not be matched exactly in this passage.</p>}
      </section>;
    })}</div>
  </DocumentDialog>;
}
