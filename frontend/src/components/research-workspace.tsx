"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronRight,
  CircleHelp,
  FileCheck2,
  Fingerprint,
  LoaderCircle,
  LockKeyhole,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useResearch } from "./research-provider";
import dynamic from "next/dynamic";
// Markdown rendering is needed only once an answer arrives, so it is not part of the first load.
const AnswerView = dynamic(() => import("./answer-view").then((m) => m.AnswerView), {
  loading: () => <p className="answer-loading" role="status">Loading the answer…</p>,
});
import Velaris from "./ui/velaris";
import ComparisonBlock from "./ui/comparison-2";
import { FlowButton } from "./ui/flow-button";

const examples = [
  {
    category: "PROPERTY LAW",
    text: "What does the Transfer of Property Act say about a lease?",
    icon: BookOpen,
  },
  {
    category: "CONSUMER PROTECTION",
    text: "How is a consumer defined under the Consumer Protection Act?",
    icon: ShieldCheck,
  },
  {
    category: "RESEARCH IN HINDI",
    text: "अनुबंध के आवश्यक तत्व क्या हैं?",
    icon: FileCheck2,
    hindi: true,
  },
];
export const DISCLAIMER =
  "PRAETOR AI provides information for legal research. It is not a lawyer and does not provide legal advice.";

export function ResearchWorkspace() {
  const research = useResearch();
  const textarea = useRef<HTMLTextAreaElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const [elapsed, setElapsed] = useState(0);
  const count = Array.from(research.draft).length;
  const trimmedCount = Array.from(research.draft.trim()).length;
  const unavailable =
    research.health === "down" || research.health === "checking";
  const valid = trimmedCount > 0 && trimmedCount <= 2000;
  useEffect(() => {
    if (!research.startedAt) {
      setElapsed(0);
      return;
    }
    const start = research.startedAt;
    const tick = () => setElapsed(Math.floor((Date.now() - start) / 1000));
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [research.startedAt]);
  useEffect(() => {
    if (research.current) resultRef.current?.focus({ preventScroll: true });
  }, [research.current]);
  function choose(value: string) {
    research.setDraft(value);
    textarea.current?.focus();
  }
  return (
    <div className="workspace-content">
      <section className="research-intro" aria-labelledby="workspace-title">
        <Velaris className="hero-atmosphere" height="100%" speed={0.7}/>
        <span className="hero-edition" aria-hidden="true">01 / THE RESEARCH LIBRARY</span>
        <div className="eyebrow">
          <span /> YOUR INDIAN LAW RESEARCH COMPANION
        </div>
        <h1 id="workspace-title">
          A clearer view of<br/><em>Indian law.</em>
        </h1>
        <p>Ask a question. Explore the evidence. Go straight to the source.</p>
        <div className="coverage-strip" aria-label="Corpus scope">
          <span>
            <strong>12</strong> central Acts
          </span>
          <span>
            <strong>1,000</strong> Supreme Court judgments
          </span>
          <Link href="/about">
            Explore coverage <ArrowUpRight size={14} />
          </Link>
        </div>
      </section>

      {research.sampleData && (
        <div className="notice sample-notice" role="status">
          <Sparkles size={18} />
          <div>
            <strong>Sample data</strong>
            <p>
              Development preview with labelled placeholders. No live legal
              research is being performed.
            </p>
          </div>
        </div>
      )}
      {research.health === "down" && (
        <div className="notice offline-notice" role="status">
          <CircleHelp size={19} />
          <div>
            <strong>The research service is offline</strong>
            <p>Research will be available when the service reconnects.</p>
            <small>
              Request ID: {research.healthRequestId || "unavailable"}
            </small>
          </div>
          <button className="text-button" onClick={research.refreshHealth}>
            <RefreshCw size={14} /> Retry
          </button>
        </div>
      )}
      {research.health === "degraded" && (
        <div className="notice" role="status">
          <FileCheck2 size={19} />
          <div>
            <strong>Limited service</strong>
            <p>Answers are limited to verbatim source passages.</p>
          </div>
        </div>
      )}

      <section className="question-section" aria-labelledby="question-label">
        <div className="section-heading">
          <label id="question-label" htmlFor="question">
            What would you like to understand?
          </label>
          <span className="language-label">
            English <span>/</span> <span lang="hi">हिन्दी</span>
          </span>
        </div>
        <form
          className={`question-card ${research.pending ? "is-searching" : ""}`}
          onSubmit={(event) => {
            event.preventDefault();
            void research.submit(research.draft);
          }}
        >
          <textarea
            ref={textarea}
            id="question"
            name="question"
            value={research.draft}
            onChange={(event) => research.setDraft(event.target.value)}
            placeholder="Ask about an Act, a legal concept, or a Supreme Court judgment…"
            rows={3}
            disabled={unavailable || research.operationBusy}
            aria-describedby="question-hint question-count question-validation"
            aria-invalid={trimmedCount > 2000}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing &&
                event.keyCode !== 229
              ) {
                event.preventDefault();
                if (valid && !unavailable && !research.operationBusy)
                  event.currentTarget.form?.requestSubmit();
              }
            }}
          />
          <div className="question-toolbar">
            <div className="question-meta">
              <span id="question-hint">
                <kbd>↵</kbd> to ask <span className="hint-divider">·</span>{" "}
                Shift + Enter for a new line
              </span>
              <span
                id="question-count"
                className={count > 2000 ? "over-limit" : ""}
              >
                {count.toLocaleString("en-IN")} / 2,000
              </span>
            </div>
            <FlowButton
              type="submit"
              className="ask-submit"
              disabled={!valid || unavailable || research.pending}
              aria-busy={research.pending || undefined}
            >
              {research.pending ? "Researching" : "Research question"}
            </FlowButton>
          </div>
        </form>
        <div className="input-footnote">
          <span>
            <LockKeyhole size={12} /> History stays in this tab
          </span>
          {(research.draft ||
            research.entries.length > 0 ||
            research.pending) && (
            <button className="text-button" onClick={research.clear}>
              Clear
            </button>
          )}
        </div>
        <p
          id="question-validation"
          className="field-validation"
          aria-live="polite"
        >
          {trimmedCount > 2000
            ? "Please keep your question to 2,000 characters or fewer."
            : ""}
        </p>
      </section>

      {research.pending && (
        <div className="search-progress" role="status" aria-live="polite">
          <div className="search-orbit">
            <Search size={22} />
          </div>
          <div>
            <strong>Searching and checking sources…</strong>
            <p>
              Answers usually take 10–20 seconds. Your question may be queued.
            </p>
          </div>
          <span className="elapsed" aria-label={`${elapsed} seconds elapsed`}>
            {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, "0")}
          </span>
        </div>
      )}
      {research.error && (
        <div className="notice error-notice" role="alert">
          <CircleHelp size={20} />
          <div>
            <strong>{research.error.message}</strong>
            <p>
              Request ID:{" "}
              <span className="request-id">{research.error.requestId}</span>
            </p>
          </div>
        </div>
      )}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {research.current
          ? research.current.answer.abstained
            ? "Research complete. The sources were insufficient to answer this question."
            : "Research complete. Your answer and citations are available below."
          : ""}
      </div>
      {research.current ? (
        <div className="research-result" ref={resultRef} tabIndex={-1}>
          <div className="result-question">
            <span className="eyebrow">YOUR QUESTION</span>
            <h2>{research.current.question}</h2>
          </div>
          <AnswerView
            answer={research.current.answer}
            sampleData={research.current.sampleData}
          />
        </div>
      ) : (
        !research.pending && (
          <>
            <section
              className="examples-section"
              aria-labelledby="examples-title"
            >
              <div className="section-heading">
                <h2 id="examples-title">A starting point for your research</h2>
                <span>TRY A QUESTION</span>
              </div>
              <div className="example-grid">
                {examples.map(({ category, text, icon: Icon, hindi }) => (
                  <button
                    key={category}
                    className="example-card"
                    onClick={() => choose(text)}
                    disabled={unavailable}
                  >
                    <div className="example-top">
                      <Icon size={18} />
                      <ArrowUpRight size={16} />
                    </div>
                    <span className="example-category">{category}</span>
                    <span className="example-text" lang={hindi ? "hi" : "en"}>
                      {text}
                    </span>
                    <span className="example-bottom">
                      Explore this question <ChevronRight size={13} />
                    </span>
                  </button>
                ))}
              </div>
            </section>
            <ComparisonBlock />
            <section
              className="research-principles"
              aria-label="Research principles"
            >
              <div>
                <span className="principle-icon">
                  <BookOpen size={18} />
                </span>
                <h3>Grounded in the text</h3>
                <p>Central Acts and Supreme Court judgments, with context.</p>
              </div>
              <div>
                <span className="principle-icon">
                  <Fingerprint size={18} />
                </span>
                <h3>Sources you can verify</h3>
                <p>Every citation leads back to the original stored passage.</p>
              </div>
              <div>
                <span className="principle-icon">
                  <Check size={18} />
                </span>
                <h3>Clear about its limits</h3>
                <p>When evidence is insufficient, the system says so.</p>
              </div>
            </section>
          </>
        )
      )}
      {!research.current && (
        <p className="persistent-disclaimer">
          <ShieldCheck size={16} />
          {DISCLAIMER}
        </p>
      )}
    </div>
  );
}
