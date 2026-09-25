import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowUpRight,
  BookOpen,
  FileText,
  Languages,
  ShieldCheck,
} from "lucide-react";
export const metadata: Metadata = { title: "About & coverage" };
export default function About() {
  return (
    <div className="about-content">
      <Link className="back-link" href="/">
        <ArrowLeft size={15} /> Back to research
      </Link>
      <div className="eyebrow">
        <span /> ABOUT PRAETOR AI
      </div>
      <h1>
        Research starts with
        <br />
        <em>knowing the limits.</em>
      </h1>
      <p className="about-lead">
        A focused workspace for exploring Indian law through source material.
        Designed to help you read, verify, and understand.
      </p>
      <div className="about-disclaimer">
        <ShieldCheck size={22} />
        <p>
          PRAETOR AI is an informational legal-research assistant. It is not a
          lawyer and does not provide legal advice or predict case outcomes.
        </p>
      </div>
      <section className="about-section" id="coverage">
        <div className="section-heading">
          <h2>What the research covers</h2>
          <span>DEFINED SCOPE</span>
        </div>
        <div className="about-grid">
          <article>
            <BookOpen size={23} />
            <h3>12 central Acts</h3>
            <p>
              English texts sourced from India Code. Citation cards identify the
              authority, jurisdiction, and stored legal status of each passage.
            </p>
            <a
              href="https://www.indiacode.nic.in/"
              target="_blank"
              rel="noopener noreferrer"
            >
              India Code <ArrowUpRight size={14} />
            </a>
          </article>
          <article>
            <FileText size={23} />
            <h3>1,000 Supreme Court judgments</h3>
            <p>
              Selected judgments from 2016–2025, in English. This is a focused
              collection, rather than a complete record of Indian case law.
            </p>
            <a
              href="https://www.sci.gov.in/"
              target="_blank"
              rel="noopener noreferrer"
            >
              Supreme Court of India <ArrowUpRight size={14} />
            </a>
          </article>
        </div>
        <p className="coverage-caveat">
          These figures describe the intended corpus scope. Service availability
          and the actual indexed collection depend on the connected research
          backend. State laws, state rules, and other rules are not covered.
        </p>
      </section>
      <section className="about-section" id="citations">
        <h2>Follow the answer back to its source</h2>
        <div className="citation-explainer">
          <span className="demo-marker">S1</span>
          <p>
            Numbered source markers connect an answer to a citation card. Select
            a marker to find the card, then choose{" "}
            <strong>Read full passage</strong> to inspect the stored text. The
            original source link is provided when available.
          </p>
        </div>
        <p>
          Cards show the title, section or paragraph, verbatim excerpt,
          authority, jurisdiction, retrieval date, and legal status. Repealed
          provisions are clearly marked. Stored status and retrieval dates
          matter: laws can change after a source is indexed.
        </p>
        <p>
          A confidence label describes how strongly the retrieved sources
          support the answer. It is not a guarantee of correctness. If the
          available evidence is too thin, the system explains the gap instead of
          generating an answer.
        </p>
        <p>
          When the answer model is unavailable, a limited service can display
          verbatim source passages. Those responses are explicitly labelled “no
          AI summary”.
        </p>
      </section>
      <section className="about-section language-section">
        <Languages size={24} />
        <div>
          <h2>Ask in English or Hindi</h2>
          <p lang="hi">आप अपना प्रश्न हिन्दी में भी पूछ सकते हैं।</p>
          <p>
            Hindi questions are supported; source texts and answers are in
            English.
          </p>
        </div>
      </section>
      <section className="about-section" id="privacy">
        <h2>Your research, your tab</h2>
        <p>
          Session history is held in this browser tab’s memory. Clear removes it
          from the interface; closing or reloading the tab removes it too. Your
          question is sent through this application’s server to the owner’s
          research backend to produce an answer.
        </p>
        <p>
          This frontend has no analytics or tracking scripts and does not log
          question or answer text. The backend’s own retention and caching
          policies are separate. Avoid including unnecessary personal or
          confidential details.
        </p>
        <p className="about-limit">
          For decisions about a specific legal situation, information from this
          tool cannot replace advice from a qualified legal professional.
        </p>
      </section>
      <Link className="primary-button about-cta" href="/">
        Open research workspace <ArrowUpRight size={16} />
      </Link>
    </div>
  );
}
