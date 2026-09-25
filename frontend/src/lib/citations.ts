export type CitationSegment =
  | { type: "text"; value: string }
  | { type: "citation"; value: string; id: string };

/** Unknown markers stay verbatim; only IDs supplied by the API become controls. */
export function parseCitationMarkers(
  text: string,
  validIds: ReadonlySet<string>,
): CitationSegment[] {
  const segments: CitationSegment[] = [];
  const marker = /\[([SD]\d+)\]/g;
  let cursor = 0;

  for (const match of text.matchAll(marker)) {
    if (!validIds.has(match[1])) continue;
    if (match.index > cursor)
      segments.push({ type: "text", value: text.slice(cursor, match.index) });
    segments.push({ type: "citation", value: match[0], id: match[1] });
    cursor = match.index + match[0].length;
  }

  if (cursor < text.length)
    segments.push({ type: "text", value: text.slice(cursor) });
  return segments;
}

/** Allow explicit public web URLs only. Never let model text become an executable URL. */
export function safeExternalUrl(
  value: string | null | undefined,
): string | undefined {
  if (
    !value ||
    /[\u0000-\u0020\u007f]/.test(value) ||
    !/^https?:\/\//i.test(value)
  )
    return undefined;
  try {
    const url = new URL(value);
    if (
      !["https:", "http:"].includes(url.protocol) ||
      !url.hostname ||
      url.username ||
      url.password
    )
      return undefined;
    return url.href;
  } catch {
    return undefined;
  }
}

export function formatSourceDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

export function sourceStatusLabel(status: string): string {
  switch (status) {
    case "in_force":
      return "In force";
    case "repealed":
      return "Repealed";
    case "partially_in_force":
      return "Partially in force";
    case "n/a":
      return "Judgment";
    default:
      return status.replaceAll("_", " ");
  }
}
