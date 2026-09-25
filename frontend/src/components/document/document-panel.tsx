"use client";

import { useId, useRef, useState } from "react";
import { FileText, LoaderCircle, Upload, X } from "lucide-react";
import type { DocumentInfo } from "@/lib/api/types";

type Props = {
  label: "A" | "B"; document: (DocumentInfo & { sampleData?: boolean }) | null; disabled: boolean; uploading: string | null; now: number;
  onUpload: (file: File) => void; onView: () => void; onForget: () => void;
};

export function DocumentPanel({ label, document, disabled, uploading, now, onUpload, onView, onForget }: Props) {
  const id = useId();
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  return <section className="document-panel" data-document={label} aria-labelledby={id}>
    <div className="document-panel-heading"><span className="document-letter">{label}</span><h2 id={id}>Document {label}</h2>{document?.sampleData && <span className="sample-badge">Sample data</span>}</div>
    {uploading ? <div className="document-uploading" role="status"><LoaderCircle className="spin" size={22} aria-hidden="true"/><strong>Reading PDF…</strong><span>{uploading}</span><span className="document-uploading-note">Scanned pages are read with OCR and take a few seconds more.</span></div> : document ? <>
      <div className="document-file"><FileText size={28} aria-hidden="true"/><h3>{document.filename}</h3></div>
      <p className="document-stats">{document.pages} pages · {document.passage_count} passages · {document.words.toLocaleString("en-IN")} words</p>
      <p className="document-expiry">Expires in {Math.max(0, Math.ceil((Date.parse(document.expires_at) - now) / 60_000))} min</p>
      {document.warnings.length > 0 && <ul className="document-upload-notes" aria-label={`Document ${label} notes`}>{document.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>}
      {document.unreadable_pages.length > 0 && <p className="document-upload-notes">Unreadable pages: {document.unreadable_pages.join(", ")}</p>}
      <div className="document-file-actions"><button type="button" className="text-button" disabled={disabled} onClick={onView}>View text{" "}<span className="sr-only">of Document {label}</span></button><button type="button" className="text-button" disabled={disabled} onClick={onForget}><X size={14} aria-hidden="true"/>Forget this document{" "}<span className="sr-only">{label}</span></button></div>
    </> : <div className="document-dropzone" data-dragging={dragging || undefined} onDragOver={(event) => { event.preventDefault(); if (!disabled) setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); if (!disabled && event.dataTransfer.files[0]) onUpload(event.dataTransfer.files[0]); }}>
      <Upload size={25} aria-hidden="true"/><p>Upload a PDF, typed or scanned (up to 4 MB). Scanned pages are read with OCR. It is kept for 60 minutes and never stored.</p>
      <input ref={input} className="sr-only" type="file" accept="application/pdf" id={`${id}-file`} aria-label={`Upload Document ${label}`} disabled={disabled} onChange={(event) => { const file = event.target.files?.[0]; if (file) onUpload(file); event.target.value = ""; }}/>
      <button type="button" className="secondary-button" disabled={disabled} onClick={() => input.current?.click()}>Choose PDF{" "}<span className="sr-only">for Document {label}</span></button><span className="document-drop-hint">or drop it here</span>
    </div>}
  </section>;
}
