"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { ArrowUpRight, FileText, Menu, MessageSquare, Moon, Pause, Play, Plus, Sun, Trash2, X } from "lucide-react";
import { useResearch } from "./research-provider";
import { Header1 } from "./ui/header";

function ThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    let saved: string | null = null;
    try { saved = localStorage.getItem("praetor-theme"); } catch { /* System theme remains available. */ }
    const value = saved ? saved === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    setDark(value); document.documentElement.dataset.theme = value ? "dark" : "light";
  }, []);
  function toggle() {
    const value = !dark; setDark(value);
    document.documentElement.dataset.theme = value ? "dark" : "light";
    try { localStorage.setItem("praetor-theme", value ? "dark" : "light"); } catch { /* Keep the current theme in memory. */ }
  }
  return <button className="icon-button theme-button" onClick={toggle} aria-label={`Switch to ${dark ? "light" : "dark"} theme`} title={`Switch to ${dark ? "light" : "dark"} theme`}>{dark ? <Sun size={17}/> : <Moon size={17}/>}</button>;
}
function MotionToggle() {
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    const preference = matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => {
      let saved: string | null = null;
      try { saved = localStorage.getItem("praetor-motion"); } catch { /* Preference is optional. */ }
      const value = preference.matches || saved === "paused";
      setPaused(value); document.documentElement.dataset.motion = value ? "paused" : "running";
    };
    update(); preference.addEventListener("change", update);
    return () => preference.removeEventListener("change", update);
  }, []);
  function toggle() {
    const value = !paused; setPaused(value);
    document.documentElement.dataset.motion = value ? "paused" : "running";
    try { localStorage.setItem("praetor-motion", value ? "paused" : "running"); } catch { /* The toggle still works. */ }
  }
  return <button className="icon-button motion-toggle" onClick={toggle} aria-label={paused ? "Resume visual motion" : "Pause visual motion"} title={paused ? "Resume visual motion" : "Pause visual motion"} aria-pressed={paused}>{paused ? <Play size={15}/> : <Pause size={15}/>}</button>;
}
export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname(); const router = useRouter(); const research = useResearch();
  const [mobileOpen, setMobileOpen] = useState(false);
  const isAsk = pathname === "/"; const isDocument = pathname === "/document";
  const offline = isDocument ? research.documentHealth === "offline" : research.health === "down";
  const checking = isDocument ? research.documentHealth === "checking" : research.health === "checking";
  const statusText = offline ? "Service offline" : checking ? "Checking service" : research.sampleData ? "Sample data" : isDocument ? research.documentHealth === "ok" ? "Documents ready" : "Passages only" : research.health === "ok" ? "Research service online" : "Limited service";
  function start() { research.newResearch(); router.push("/"); setMobileOpen(false); }
  return <div className={`app-shell monochrome-shell ${isAsk ? "with-history" : "full-workspace"}`}>
    <a className="skip-link" href="#main-content">Skip to content</a>
    <Header1><span className="header-service" data-status={offline ? "down" : checking ? "checking" : "ok"}><span className="status-dot"/>{statusText}</span><MotionToggle/><ThemeToggle/></Header1>
    {isAsk && <>
      <div className="session-mobile-bar"><span>RESEARCH WORKSPACE</span><button className="text-button" onClick={() => setMobileOpen(!mobileOpen)} aria-label={mobileOpen ? "This session: close history" : "This session: open history"} aria-expanded={mobileOpen} aria-controls="sidebar">{mobileOpen ? <X size={16}/> : <Menu size={16}/>} This session</button></div>
      <aside className={`sidebar ${mobileOpen ? "is-open" : ""}`} id="sidebar" aria-label="Session history">
        <div className="sidebar-workspace-label">RESEARCH WORKSPACE</div>
        <button className="new-research" onClick={start} disabled={research.operationBusy}><Plus size={16}/> New research <span className="shortcut">↗</span></button>
        <div className="session-heading"><span>THIS SESSION</span>{research.entries.length > 0 && <button className="icon-button small" onClick={research.clear} aria-label="Clear session history" title="Clear session history"><Trash2 size={14}/></button>}</div>
        <div className="session-list">{research.entries.length ? [...research.entries].reverse().map(entry => <button key={entry.id} className={`session-entry ${research.current?.id === entry.id ? "selected" : ""}`} disabled={research.operationBusy} onClick={() => { research.select(entry.id); setMobileOpen(false); }}><MessageSquare size={15}/><span>{entry.question}</span></button>) : <p className="empty-session">A fresh perspective starts here.<br/>Your research stays in this tab.</p>}</div>
        <div className="sidebar-bottom"><Link className="source-note document-shortcut" href="/document"><FileText size={22}/><p>Start with<br/>your own document.</p><span>Explore a PDF <ArrowUpRight size={14}/></span></Link><div className="sidebar-foot"><span className="tiny-dot"/>INFORMATION, NOT LEGAL ADVICE</div></div>
      </aside>
    </>}
    <div className="main-shell"><main id="main-content" tabIndex={-1}><div key={pathname} className="page-transition">{children}</div></main><footer className="app-footer"><span>PRAETOR AI <span className="footer-separator">/</span> Every answer begins with evidence.</span><Link href="/about#privacy">Privacy & limitations <ArrowUpRight size={12}/></Link></footer></div>
  </div>;
}
