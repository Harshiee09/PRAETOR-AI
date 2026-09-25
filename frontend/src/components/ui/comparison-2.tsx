import Link from "next/link";
import { ArrowUpRight, Check, BookOpen, FileText } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./card";
import { Badge } from "./badge";
import { Separator } from "./separator";
import { Button } from "./button";

/** The supplied comparison layout, adapted to the two supported research workflows. */
export default function ComparisonBlock() {
  const modes = [
    { title: "The research library", label: "ASK", icon: BookOpen, description: "Begin with a question about Indian law.", href: "/", action: "Ask a question", points: ["12 central Acts and 1,000 selected judgments", "English and Hindi questions", "Citations linked to stored law passages", "Explicit limitations when evidence is thin"] },
    { title: "Your own document", label: "YOUR DOCUMENT", icon: FileText, description: "Begin with the words on your page.", href: "/document", action: "Explore a document", points: ["Selectable-text PDFs up to 4 MB", "Questions, summaries, clauses and checklists", "Compare two documents with A/B source labels", "Temporary processing with a 60-minute expiry"] },
  ];
  return <section className="comparison-block" aria-labelledby="comparison-heading"><div className="comparison-intro"><Badge variant="outline">ONE STANDARD. EVERY SOURCE.</Badge><h2 id="comparison-heading">Two ways in.<br/><em>The same care for evidence.</em></h2><p>Choose a starting point. Every finding stays connected to its source.</p></div><div className="comparison-grid">{modes.map(({title,label,icon:Icon,description,href,action,points}) => <Card key={label}><CardHeader><div className="comparison-card-kicker"><Icon size={21}/><Badge variant="secondary">{label}</Badge></div><CardTitle>{title}</CardTitle><CardDescription>{description}</CardDescription></CardHeader><Separator/><CardContent><ul>{points.map(point => <li key={point}><Check size={14} aria-hidden="true"/><span>{point}</span></li>)}</ul></CardContent><CardFooter><Button asChild variant="outline" className="comparison-link"><Link href={href}>{action}<ArrowUpRight size={16}/></Link></Button></CardFooter></Card>)}</div></section>;
}
