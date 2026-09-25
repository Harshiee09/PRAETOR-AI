"use client";

import { useId, useMemo, useState, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Root, RootContent, Link, Text } from "mdast";
import { parseCitationMarkers, safeExternalUrl } from "@/lib/citations";

type MarkdownNode = Root | RootContent;

function citationPlugin(validIds: ReadonlySet<string>, taskFormatting: boolean) {
  return function remarkCitations() {
    return function transform(tree: Root) {
      function visit(node: MarkdownNode) {
        if (taskFormatting && node.type === "listItem" && typeof node.checked === "boolean") {
          node.data = { ...node.data, hProperties: { ...node.data?.hProperties, "data-checklist": "true", "data-initial-checked": String(node.checked) } };
        }
        if (taskFormatting && node.type === "paragraph" && node.children.length === 1 && node.children[0].type === "strong") {
          node.data = { ...node.data, hName: "h3" };
        }
        // Code, existing links and image alt text retain their original meaning.
        if (
          [
            "code",
            "inlineCode",
            "link",
            "linkReference",
            "image",
            "imageReference",
            "html",
          ].includes(node.type)
        )
          return;
        if (!("children" in node)) return;
        const children: RootContent[] = [];
        for (const child of node.children) {
          if (child.type !== "text") {
            visit(child);
            children.push(child);
            continue;
          }
          for (const segment of parseCitationMarkers(child.value, validIds)) {
            if (segment.type === "text") {
              children.push({ type: "text", value: segment.value } as Text);
            } else {
              children.push({
                type: "link",
                url: `#citation-${segment.id}`,
                children: [{ type: "text", value: segment.value }],
                data: { hProperties: { "data-citation-id": segment.id } },
              } as Link);
            }
          }
        }
        // Every replacement preserves its text parent's permissible inline content.
        node.children = children as typeof node.children;
      }
      visit(tree);
    };
  };
}

type AnswerMarkdownProps = {
  markdown: string;
  citationIds: ReadonlySet<string>;
  onCitationClick: (id: string) => void;
  citationLabels?: ReadonlyMap<string, "A" | "B">;
  interactiveChecklist?: boolean;
  taskFormatting?: boolean;
};

function ChecklistItem({ children, initialChecked }: { children: ReactNode; initialChecked: boolean }) {
  const id = useId();
  const [checked, setChecked] = useState(initialChecked);
  return <li className="document-checklist-item" data-checked={checked}><input type="checkbox" checked={checked} onChange={(event) => setChecked(event.target.checked)} aria-labelledby={id} /><div id={id}>{children}</div></li>;
}

export function AnswerMarkdown({
  markdown,
  citationIds,
  onCitationClick,
  citationLabels,
  interactiveChecklist = false,
  taskFormatting = false,
}: AnswerMarkdownProps) {
  const remarkCitations = useMemo(
    () => citationPlugin(citationIds, taskFormatting || interactiveChecklist),
    [citationIds, taskFormatting, interactiveChecklist],
  );

  return (
    <ReactMarkdown
      skipHtml
      remarkPlugins={[remarkGfm, remarkCitations]}
      urlTransform={(url) =>
        url.startsWith("#citation-") ? url : (safeExternalUrl(url) ?? "")
      }
      components={{
        // Remote images can disclose the reader's IP and must never be requested.
        img: () => null,
        input: ({ checked }) => interactiveChecklist ? null : <input type="checkbox" disabled checked={checked} readOnly />,
        li: ({ node, children, ...props }) => {
          const checklist = node?.properties?.["data-checklist"] ?? node?.properties?.dataChecklist;
          const checked = node?.properties?.["data-initial-checked"] ?? node?.properties?.dataInitialChecked;
          return interactiveChecklist && checklist === "true" ? <ChecklistItem initialChecked={checked === "true"}>{children}</ChecklistItem> : <li {...props}>{children}</li>;
        },
        a: ({ node, href, children }) => {
          const id =
            node?.properties?.["data-citation-id"] ??
            node?.properties?.dataCitationId;
          if (typeof id === "string" && citationIds.has(id)) {
            return (
              <button
                type="button"
                className="citation-chip"
                data-document={citationLabels?.get(id)}
                aria-label={`View source ${id}${citationLabels?.has(id) ? `, Document ${citationLabels.get(id)}` : ""}`}
                onClick={() => onCitationClick(id)}
              >
                {id}{citationLabels?.has(id) && <span className="chip-document-label"> · {citationLabels.get(id)}</span>}
              </button>
            );
          }
          const safeUrl = safeExternalUrl(href);
          return safeUrl ? (
            <a
              href={safeUrl}
              target="_blank"
              rel="noopener noreferrer"
              referrerPolicy="no-referrer"
            >
              {children}
              <span className="sr-only"> (opens in a new tab)</span>
            </a>
          ) : (
            <span>{children}</span>
          );
        },
      }}
    >
      {markdown}
    </ReactMarkdown>
  );
}
