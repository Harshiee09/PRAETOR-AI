"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, FileText, LoaderCircle, Upload } from "lucide-react";
import { useResearch } from "@/components/research-provider";
import { analyzeDocuments, forgetDocument, getDocument, uploadDocument } from "@/lib/api/client";
import { ApiClientError, documentErrorMessage } from "@/lib/api/errors";
import { validatePdfFile } from "@/lib/api/documents";
import type { DocumentCitation, DocumentDetail, DocumentInfo, DocumentTask } from "@/lib/api/types";
import GatewayFlow from "@/components/ui/gateway-flow";
import { FlowButton } from "@/components/ui/flow-button";
import { DocumentPanel } from "./document-panel";
import { DocumentDialog } from "./document-dialog";
import { DocumentResult, type DocumentResultValue } from "./document-result";
import { PassageDrawer } from "./passage-drawer";
import { DOCUMENT_DISCLAIMER, EXPIRED_MESSAGE, persistDocuments, readSavedDocuments, TASKS, type SavedDocument } from "./utils";

type Uploaded = DocumentInfo & { sampleData?: boolean };
type Operation = { controller: AbortController; kind: "upload" | "analyze" | "passages" | "forget"; filename?: string; slot?: number; started: number };
type Failure = { message: string; requestId?: string };

export function DocumentWorkspace() {
  const research = useResearch();
  const [documents, setDocuments] = useState<(Uploaded | null)[]>([null, null]);
  const documentsRef = useRef(documents);
  const cache = useRef(new Map<string, DocumentDetail>());
  const unresolved = useRef<(SavedDocument | null)[]>([null, null]);
  const active = useRef<Operation | null>(null);
  const restoreController = useRef<AbortController | null>(null);
  const [working, setWorking] = useState<Operation | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [task, setTask] = useState<DocumentTask>("ask");
  const [question, setQuestion] = useState("");
  const [focus, setFocus] = useState("");
  const [now, setNow] = useState(Date.now());
  const [failure, setFailure] = useState<Failure | null>(null);
  const [expired, setExpired] = useState(false);
  const [result, setResult] = useState<DocumentResultValue | null>(null);
  const [drawer, setDrawer] = useState<{ detail: DocumentDetail; citation?: DocumentCitation } | null>(null);
  const [confirm, setConfirm] = useState<number | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const unavailable = research.documentHealth === "offline" || research.documentHealth === "checking";
  const busy = research.operationBusy || Boolean(working) || !hydrated;
  const field = task === "ask" ? question : focus;
  const count = Array.from(field).length;
  const valid = Array.from(field.trim()).length <= 2000 && (task !== "ask" || field.trim().length > 0);
  const ready = Boolean(documents[0]) && (task !== "compare" || Boolean(documents[1])) && valid && !busy && !unavailable;

  function cancel() {
    const operation = active.current;
    if (!operation) return;
    active.current = null;
    operation.controller.abort();
    research.endOperation(operation.controller);
    setWorking(null);
  }

  function removeLocal(ids: string[], expiredDocument = false) {
    for (const id of ids) cache.current.delete(id);
    unresolved.current = unresolved.current.map((record) => record && ids.includes(record.document_id) ? null : record);
    const remaining = documentsRef.current.map((document) => document && ids.includes(document.document_id) ? null : document);
    documentsRef.current = remaining;
    setDocuments(remaining);
    persistDocuments(remaining.map((document, slot) => document ?? unresolved.current[slot]));
    setDrawer(null); setResult(null); setConfirm(null);
    if (expiredDocument) setExpired(true);
  }

  useEffect(() => {
    const controller = new AbortController();
    restoreController.current = controller;
    const saved = readSavedDocuments();
    void Promise.all(saved.map(async (record, slot) => {
      if (!record) return null;
      if (Date.parse(record.expires_at) <= Date.now() || !Number.isFinite(Date.parse(record.expires_at))) { setExpired(true); return null; }
      try {
        const detail = await getDocument(record.document_id, { signal: controller.signal });
        if (!controller.signal.aborted) cache.current.set(record.document_id, detail);
        return detail;
      } catch (error) {
        if (!controller.signal.aborted) {
          if (error instanceof ApiClientError && error.status === 404) setExpired(true);
          else { unresolved.current[slot] = record; setFailure({ message: documentErrorMessage(error), requestId: error instanceof ApiClientError ? error.requestId : "unavailable" }); }
        }
        return null;
      }
    })).then((restored) => {
      if (controller.signal.aborted) return;
      documentsRef.current = restored;
      setDocuments(restored); setHydrated(true);
      if (restored[1]) setTask("compare");
    });
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => { controller.abort(); clearInterval(interval); const operation = active.current; if (operation) { operation.controller.abort(); research.endOperation(operation.controller); } cache.current.clear(); };
    // This effect owns the page lifetime; operation methods use controller identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { documentsRef.current = documents; if (hydrated) persistDocuments(documents.map((document, slot) => document ?? unresolved.current[slot])); }, [documents, hydrated]);
  useEffect(() => {
    const expiredIds = [...documents, ...unresolved.current].filter((document) => document && Date.parse(document.expires_at) <= now).map((document) => document!.document_id);
    if (expiredIds.length) { cancel(); removeLocal(expiredIds, true); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [now, documents]);
  useEffect(() => { if (result) resultRef.current?.focus({ preventScroll: true }); }, [result]);

  async function run(kind: Operation["kind"], action: (controller: AbortController) => Promise<void>, extra: Partial<Operation> = {}) {
    if (active.current || unavailable) return;
    const controller = research.beginOperation();
    if (!controller) return;
    const operation = { controller, kind, started: Date.now(), ...extra };
    active.current = operation;
    setWorking(operation); setFailure(null);
    controller.signal.addEventListener("abort", () => { if (active.current === operation) { active.current = null; setWorking(null); research.endOperation(controller); } }, { once: true });
    try { await action(controller); }
    catch (error) {
      if (controller.signal.aborted) return;
      setFailure({ message: documentErrorMessage(error), requestId: error instanceof ApiClientError ? error.requestId : "unavailable" });
      if (error instanceof ApiClientError && error.status === 404) {
        const ids = extra.slot != null ? [documentsRef.current[extra.slot]?.document_id].filter((id): id is string => Boolean(id)) : documentsRef.current.filter(Boolean).map((document) => document!.document_id);
        removeLocal(ids, true);
      }
    } finally {
      if (active.current === operation) { active.current = null; setWorking(null); research.endOperation(controller); }
    }
  }

  function upload(file: File, slot: number) {
    const message = validatePdfFile(file);
    if (message) { setFailure({ message }); return; }
    void run("upload", async (controller) => {
      const document = await uploadDocument(file, { signal: controller.signal });
      if (controller.signal.aborted) return;
      unresolved.current[slot] = null;
      setDocuments((previous) => previous.map((item, index) => index === slot ? document : item));
      setResult(null); setExpired(false);
    }, { filename: file.name, slot });
  }

  function analyze() {
    if (!ready) return;
    const selected = documents.slice(0, task === "compare" ? 2 : 1).filter((document): document is Uploaded => Boolean(document));
    if (selected.some((document) => Date.parse(document.expires_at) <= Date.now())) { removeLocal(selected.map((document) => document.document_id), true); return; }
    const requestQuestion = field.trim();
    void run("analyze", async (controller) => {
      setResult(null);
      const answer = await analyzeDocuments({ document_ids: selected.map((document) => document.document_id), task, question: requestQuestion || null }, { signal: controller.signal });
      if (!controller.signal.aborted) setResult({ answer, question: requestQuestion, sampleData: answer.sampleData, documents: selected });
    });
  }

  function viewText(slot: number, citation?: DocumentCitation) {
    const document = documents[slot];
    if (!document) return;
    const existing = cache.current.get(document.document_id);
    if (existing) { setDrawer({ detail: existing, citation }); return; }
    void run("passages", async (controller) => {
      const detail = await getDocument(document.document_id, { signal: controller.signal });
      if (controller.signal.aborted) return;
      cache.current.set(document.document_id, detail);
      setDrawer({ detail, citation });
    }, { slot });
  }

  function forget(slot: number) {
    const document = documents[slot];
    if (!document) return;
    void run("forget", async (controller) => {
      await forgetDocument(document.document_id, { signal: controller.signal });
      if (!controller.signal.aborted) removeLocal([document.document_id]);
    }, { slot });
  }

  function retryRestoring() {
    void run("passages", async (controller) => {
      for (let slot = 0; slot < unresolved.current.length; slot++) {
        const record = unresolved.current[slot];
        if (!record) continue;
        if (Date.parse(record.expires_at) <= Date.now()) { removeLocal([record.document_id], true); continue; }
        try {
          const detail = await getDocument(record.document_id, { signal: controller.signal });
          if (controller.signal.aborted) return;
          cache.current.set(record.document_id, detail); unresolved.current[slot] = null;
          setDocuments((previous) => previous.map((document, index) => index === slot ? detail : document));
        } catch (error) {
          if (error instanceof ApiClientError && error.status === 404) removeLocal([record.document_id], true);
          else throw error;
        }
      }
    });
  }

  const elapsed = working ? Math.max(0, Math.floor((now - working.started) / 1000)) : 0;
  return <div className="workspace-content document-workspace">
    <header className="research-intro document-intro">
      <GatewayFlow className="hero-atmosphere document-flow" mode="dark" speed={0.75} density={0.8}/>
      <span className="hero-edition" aria-hidden="true">02 / YOUR DOCUMENT</span>
      <div className="eyebrow"><span/> READ WITH CONTEXT</div>
      <h1>Your document.<br/><em>A clearer understanding.</em></h1>
      <p>Understand the text, follow every citation, and prepare better questions.</p>
      <div className="coverage-strip" aria-label="How documents are handled"><span><strong>PDF · Word · photo</strong> up to 4 MB</span><span><strong>60 min</strong> in memory, never stored</span><span><strong>[D#]</strong> every point cited</span><Link href="/about#privacy">Privacy & limits <ArrowUpRight size={14}/></Link></div>
    </header>
    {research.sampleData && <div className="notice sample-notice" role="status"><strong>Sample data</strong><p>Development preview. Uploaded PDFs are not being analysed by a live service.</p></div>}
    {research.documentHealth === "offline" && <div className="notice offline-notice" role="status"><div><strong>The document research service is offline</strong><p>Reconnect the service to upload and analyse documents.</p><small>Request ID: {research.healthRequestId || "unavailable"}</small></div><button className="text-button" onClick={research.refreshHealth}>Retry</button></div>}
    {research.documentHealth === "limited" && <div className="notice" role="status">Document analysis is limited to quoting the passages (no AI summary)</div>}
    {expired && <div className="notice" role="status">{EXPIRED_MESSAGE}</div>}
    {failure && <div className="notice error-notice" role="alert"><div><p>{failure.message}</p>{failure.requestId && <small>Request ID: {failure.requestId}</small>}</div></div>}
    {hydrated && unresolved.current.some(Boolean) && <button type="button" className="secondary-button" disabled={busy || unavailable} onClick={retryRestoring}>Retry restoring documents</button>}
    <div className="document-layout"><div className="document-controls">
      {!hydrated && <p role="status">Restoring this tab's documents…</p>}
      <DocumentPanel label="A" document={documents[0]} disabled={busy || unavailable} uploading={working?.kind === "upload" && working.slot === 0 ? working.filename ?? "Document A" : null} now={now} onUpload={(file) => upload(file, 0)} onView={() => viewText(0)} onForget={() => setConfirm(0)}/>
      <section className="document-task-section" aria-labelledby="document-task-title"><h2 id="document-task-title">What would you like to understand?</h2><div className="document-task-list">{TASKS.map((option) => <button type="button" key={option.id} className="document-task-button" aria-pressed={task === option.id} disabled={!documents[0] || busy || unavailable} onClick={() => { setTask(option.id); setFailure(null); }}><strong>{option.label}</strong><span>{option.description}</span></button>)}</div></section>
      {task === "compare" && <DocumentPanel label="B" document={documents[1]} disabled={busy || unavailable || !documents[0]} uploading={working?.kind === "upload" && working.slot === 1 ? working.filename ?? "Document B" : null} now={now} onUpload={(file) => upload(file, 1)} onView={() => viewText(1)} onForget={() => setConfirm(1)}/>}
      <form className="document-question-form" onSubmit={(event) => { event.preventDefault(); analyze(); }}>
        <label htmlFor="document-question">{task === "ask" ? "Your question about the document" : task === "compare" ? "Focus on (optional)" : "Anything to focus on? (optional)"}</label>
        <textarea ref={inputRef} id="document-question" rows={3} value={field} disabled={!documents[0] || busy || unavailable} onChange={(event) => task === "ask" ? setQuestion(event.target.value) : setFocus(event.target.value)} aria-describedby="document-question-count document-question-validation" aria-invalid={Array.from(field.trim()).length > 2000} placeholder={task === "compare" ? "For example, refunds and cancellation" : task === "ask" ? "What does the document say about…" : "For example, payment dates or cancellation"} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing && event.keyCode !== 229) { event.preventDefault(); analyze(); } }}/>
        <div className="document-question-meta"><span id="document-question-count">{count.toLocaleString("en-IN")} / 2,000</span><span>Shift + Enter for a new line</span></div>
        <p id="document-question-validation" className="field-validation" aria-live="polite">{Array.from(field.trim()).length > 2000 ? "Please keep this to 2,000 characters or fewer." : ""}</p>
        {task === "ask" && <div className="document-example-chips">{["When must I pay?", "Can I cancel, and what do I lose?", "What happens if possession is delayed?"].map((example) => <button type="button" key={example} disabled={!documents[0] || busy || unavailable} onClick={() => { setQuestion(example); inputRef.current?.focus(); }}>{example}</button>)}</div>}
        <FlowButton type="submit" className="document-submit" disabled={!ready} aria-busy={working?.kind === "analyze" || undefined}>{task === "ask" ? "Research this question" : task === "compare" ? "Compare documents" : "Read my document"}</FlowButton>
      </form>
    </div><div className="document-results-column">
      {working && <div className="document-waiting" role="status"><LoaderCircle className="spin" size={25} aria-hidden="true"/><span className="document-waiting-bar" aria-hidden="true"/><strong>{working.kind === "analyze" ? "Reading your document and checking every citation…" : working.kind === "upload" ? "Reading the uploaded file…" : working.kind === "forget" ? "Forgetting this document…" : "Loading the stored passages…"}</strong><p>{working.kind === "analyze" ? "Usually 10–25 seconds. Your request may be queued." : "Please wait while the service finishes this request."}</p><span aria-label={`${elapsed} seconds elapsed`}>{Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, "0")}</span><button type="button" className="text-button" onClick={cancel}>Cancel wait</button></div>}
      {!working && !result && <div className="document-empty-result"><FileText size={36} aria-hidden="true"/><h2>Start with the source.</h2><p>Upload your document, choose a task, and explore an explanation you can trace back to the text.</p><ol className="document-empty-steps"><li><Upload size={15} aria-hidden="true"/>Upload a text PDF</li><li>Choose what to explore</li><li>Verify the passages</li></ol></div>}
      <div className="sr-only" aria-live="polite" aria-atomic="true">{result ? result.answer.abstained ? "Document research complete. More evidence is needed." : "Document research complete. Your result and citations are available." : ""}</div>
      {result && <div ref={resultRef} tabIndex={-1} className="document-result-focus"><DocumentResult result={result} onPassage={(citation) => { const slot = documents.findIndex((document) => document?.document_id === citation.document_id); if (slot >= 0) viewText(slot, citation); else { setExpired(true); setResult(null); } }}/></div>}
    </div></div>
    <p className="document-disclaimer">{DOCUMENT_DISCLAIMER}</p>
    {drawer && <PassageDrawer detail={drawer.detail} citation={drawer.citation} onClose={() => setDrawer(null)}/>}
    {confirm !== null && documents[confirm] && <DocumentDialog title={`Forget Document ${confirm === 0 ? "A" : "B"}?`} confirmation onClose={() => setConfirm(null)}><p>The file and its passages will be removed from the service. This tab's result and cached passages for this file will be cleared.</p><p><strong>{documents[confirm]?.filename}</strong></p><div className="document-confirm-actions"><button type="button" className="secondary-button" onClick={() => setConfirm(null)}>Keep document</button><button type="button" className="primary-button" disabled={busy} onClick={() => forget(confirm)}>Forget document</button></div></DocumentDialog>}
  </div>;
}
