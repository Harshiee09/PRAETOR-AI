import type { Metadata } from "next";
import { DocumentWorkspace } from "@/components/document/document-workspace";

export const metadata: Metadata = { title: "Your document · PRAETOR AI", description: "Read your own PDF with clear explanations and citations to its passages." };
export default function DocumentPage() { return <DocumentWorkspace />; }
