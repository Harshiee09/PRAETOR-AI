"""Legal-aware splitting of India Code bare-Act PDFs into sections (spec: chunk-schema note).

Built against the real India Code PDFs of the Registration Act 1908, Transfer of Property Act 1882 and Consumer
Protection Act 2019 (fixtures in tests/fixtures/). Layout facts relied on:
- An "Arrangement of Sections" precedes the body, which starts at the `ACT NO. <n> OF <year>` line. Its entries give
  the expected order of section numbers, so a body line only starts a section when its number is one of the next
  few expected ones. Cross-references and state-inserted sections therefore can't start a central section.
- Section starts look like `23. Time for presenting documents.—` (bold heading) or `[53A. Part performance.—`
  for inserted sections (the footnote marker is lifted out by the parser).
- `STATE AMENDMENT(S)` blocks follow the section they amend: a bold state name, the amending text, and a
  `[Vide <State> Act ...]` line. They are state law, so they become separate chunks with the state's
  jurisdiction and never mix into central text.
- `PART`/`CHAPTER` headings are centred, with the title on the next centred line.
- Footnotes are a block of small-font lines at the page bottom, numbered `1.` or `*.`, with continuation lines
  indented; they carry amendment history and are linked to sections through the markers on their lines.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from app.parsing.pdf import Line, ParsedPdf

log = logging.getLogger(__name__)

SECTION_START = re.compile(r"^\[?\s*(?P<num>\d{1,3}[A-Z]{0,3})\s*\.\s*(?P<rest>\S.*)$")
TOC_ENTRY = re.compile(r"^(?P<num>\d{1,3}[A-Z]{0,3})\.\s+(?P<heading>\S.*)$")
PART_RE = re.compile(r"^(?P<kind>PART|CHAPTER)\s+(?P<num>[IVXLC]+[A-Z]?)\b\.?\s*(?P<title>.*)$")
SCHEDULE_RE = re.compile(r"^THE\s+(?:(?P<ord>FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)\s+)?SCHEDULE\b", re.I)
STATE_AMENDMENT_RE = re.compile(r"^STATE\s+AMENDMENTS?\b", re.I)
SUBPART_RE = re.compile(r"^\([A-Z]\)\s+\S")
ARRANGEMENT_RE = re.compile(r"^ARRANGEMENT\s+OF\s+SECTIONS\b", re.I)
ORDER_RE = re.compile(r"^ORDER\s+(?P<num>[IVXLC]+[A-Z]?)\b\.?\s*(?P<title>.*)$")
APPENDIX_RE = re.compile(r"^APPENDIX\s+(?P<letter>[A-Z])\b")
# Some India Code PDFs append the Bill's Statement of Objects and Reasons after the last section: not law, dropped.
OBJECTS_RE = re.compile(r"^STATEMENT\s+OF\s+OBJECTS\s+AND\s+REASONS\b", re.I)
FOOTNOTE_START = re.compile(r"^(?P<m>\d{1,3}|\*{1,3})\s*\.\s*(?P<text>.*)$")
BODY_START = re.compile(r"^ACT\s+NO\.", re.I)
AMENDMENT_VERB = re.compile(r"^(Amendment|Insertion|Substitution|Omission|Repeal|Addition)s?\b", re.I)
QUOTES = "“\"‘'"
WINDOW = 6  # how many upcoming ToC entries a section start may match (sections omitted from the body are skipped)


@dataclass
class TocEntry:
    num: str
    heading: str


@dataclass
class StateBlock:
    state: str
    lines: list[Line] = field(default_factory=list)


@dataclass
class SectionDraft:
    kind: str  # section | preamble | schedule | rule (a rule inside an Order of a schedule, e.g. CPC O. XXXIX r. 1)
    num: str
    heading: str
    part: str | None
    chapter: str | None
    lines: list[Line] = field(default_factory=list)
    state_blocks: list[StateBlock] = field(default_factory=list)

    @property
    def markers_by_page(self) -> dict[int, set[str]]:
        out: dict[int, set[str]] = {}
        for ln in self.lines:
            out.setdefault(ln.page, set()).update(ln.markers)
        return out


@dataclass
class StatuteParse:
    toc: list[TocEntry]
    sections: list[SectionDraft]
    footnotes: dict[int, dict[str, str]]
    missing: list[str]


def split_footnotes(doc: ParsedPdf) -> tuple[list[Line], dict[int, dict[str, str]]]:
    """Separate each page's bottom footnote block from the body lines."""
    by_page: dict[int, list[Line]] = {}
    for ln in doc.lines:
        by_page.setdefault(ln.page, []).append(ln)
    small = doc.body_size - 1.5
    body: list[Line] = []
    notes: dict[int, dict[str, str]] = {}
    for page, lines in by_page.items():
        # The footnote block is everything after the page's last body-size line, starting at the first `N.` entry
        # at the left margin. Continuation lines can be indented (nested lists inside a footnote).
        k = len(lines)
        while k > 0 and lines[k - 1].size <= small:
            k -= 1
        block = lines[k:]
        while block and not (FOOTNOTE_START.match(block[0].text) and block[0].x0 <= 76):
            k += 1
            block = block[1:]
        body.extend(lines[:k])
        page_notes: dict[str, str] = {}
        current = None
        for ln in block:
            m = FOOTNOTE_START.match(ln.text)
            if m and ln.x0 <= 76:
                current = m.group("m")
                page_notes[current] = m.group("text").strip()
            elif current is not None:
                page_notes[current] = (page_notes[current] + " " + ln.text.strip()).strip()
        if page_notes:
            notes[page] = page_notes
    return body, notes


def parse_toc(lines: list[Line]) -> list[TocEntry]:
    """Section entries between "ARRANGEMENT OF SECTIONS" (when present; the CPC prints a numbered list of amending
    Acts before it) and the first schedule / Order heading (the CPC's arrangement also lists the rules of each
    Order, whose numbers are not section numbers)."""
    start = next((i + 1 for i, ln in enumerate(lines) if ARRANGEMENT_RE.match(ln.text.strip())), 0)
    toc, seen = [], set()
    for ln in lines[start:]:
        text = ln.text.strip()
        if SCHEDULE_RE.match(text) or ORDER_RE.match(text):
            break
        m = TOC_ENTRY.match(ln.text)
        if m and m.group("num") not in seen:
            seen.add(m.group("num"))
            toc.append(TocEntry(m.group("num"), m.group("heading").strip()))
    return toc


def _heading_from(line: Line, num: str) -> str:
    source = line.bold_prefix if len(line.bold_prefix) > len(num) + 2 else line.text
    rest = SECTION_START.match(source.strip())
    text = rest.group("rest") if rest else source
    for dash in ("—", "--", "–"):
        if dash in text:
            text = text.split(dash, 1)[0]
            break
    return text.strip().rstrip(".").strip() if line.bold_prefix or "—" in line.text else ""


def _is_centred(ln: Line) -> bool:
    return ln.x0 > 150


def _is_state_name(ln: Line, known: set[str]) -> bool:
    name = ln.text.strip().rstrip(".:").strip()
    if not ln.bold_prefix or ln.x0 > 100 or AMENDMENT_VERB.match(name) or SECTION_START.match(name):
        return False
    if not re.search(r"[A-Za-z]{3}", name):  # "* * * * *" omission marks
        return False
    return name in known or (len(name.split()) <= 5 and ln.bold_prefix.strip().rstrip(".:") == name)


def split_statute(doc: ParsedPdf, known_states: set[str]) -> StatuteParse:
    body_lines, footnotes = split_footnotes(doc)
    start = next((i for i, ln in enumerate(body_lines) if BODY_START.match(ln.text)), None)
    if start is None:
        raise ValueError(f"{doc.path.name}: no 'ACT NO.' line, cannot find where the Act body starts")
    toc = parse_toc(body_lines[:start])
    toc_nums = [t.num for t in toc]
    toc_heading = {t.num: t.heading for t in toc}

    part = chapter = None
    title_for: str | None = None  # "part" or "chapter" when the next centred line is its title
    preamble = SectionDraft("preamble", "Preamble", "Long title and preamble", None, None)
    sections: list[SectionDraft] = [preamble]
    current = preamble
    state_mode = False
    expected = 0
    found: set[str] = set()
    schedule_name: str | None = None   # inside a schedule / appendix
    order: str | None = None           # inside an Order of a schedule (CPC First Schedule)
    order_label: str | None = None
    rules_seen: set[str] = set()

    for ln in body_lines[start + 1:]:
        text = ln.text.strip()
        if title_for and _is_centred(ln) and not SECTION_START.match(text) and not STATE_AMENDMENT_RE.match(text):
            if title_for == "order":
                order_label = f"{order_label} — {text}"
            elif title_for == "part":
                part = f"{part} — {text.title()}"
            else:
                chapter = f"{chapter} — {text.title()}"
            title_for = None
            continue
        title_for = None

        pm = PART_RE.match(text)
        if pm and _is_centred(ln):
            kind = pm.group("kind").lower()
            label = f"{pm.group('kind').title()} {pm.group('num')}"
            if pm.group("title"):
                label += f" — {pm.group('title').strip().title()}"
            else:
                title_for = kind
            if kind == "part":
                part, chapter = label, None
            else:
                chapter = label
            state_mode = False
            continue
        sm = SCHEDULE_RE.match(text)
        am = APPENDIX_RE.match(text)
        if (sm or (am and schedule_name)) and _is_centred(ln) and len(found) > 0:
            if sm:
                name = f"{sm.group('ord').title()} Schedule" if sm.group("ord") else "Schedule"
            else:
                name = f"Appendix {am.group('letter')}"
            schedule_name, order, order_label = name, None, None
            current = SectionDraft("schedule", name, text.strip(), part, chapter, [ln])
            sections.append(current)
            state_mode = False
            continue
        if OBJECTS_RE.match(text):
            current = SectionDraft("discard", "SOR", "Statement of Objects and Reasons", part, chapter)
            schedule_name, order, state_mode = "Statement of Objects and Reasons", None, False
            continue
        om = ORDER_RE.match(text)
        if om and schedule_name and _is_centred(ln):
            order, rules_seen = om.group("num"), set()
            order_label = f"Order {order}"
            if om.group("title").strip():
                order_label += f" — {om.group('title').strip()}"
            else:
                title_for = "order"
            state_mode = False
            continue
        if STATE_AMENDMENT_RE.match(text) and ln.bold_prefix:
            state_mode = True
            continue
        if _is_centred(ln) and SUBPART_RE.match(text) and current.kind == "section" and not state_mode:
            continue  # sub-part headings like "(C) Special duties of Sub-Registrar"

        m = SECTION_START.match(text)
        if order and m and text[:1] not in QUOTES and ln.bold_prefix and m.group("num") not in rules_seen:
            n = m.group("num")
            rules_seen.add(n)
            current = SectionDraft("rule", f"O. {order} r. {n}", _heading_from(ln, n), schedule_name, order_label, [ln])
            sections.append(current)
            state_mode = False
            continue
        if m and text[:1] not in QUOTES and current.kind not in ("schedule", "rule") and schedule_name is None \
                and (ln.bold_prefix or "—" in text[:200]):
            num = m.group("num")
            window = toc_nums[expected:expected + WINDOW] if toc_nums else [num]
            if num in window and num not in found:
                if toc_nums:
                    expected = toc_nums.index(num, expected) + 1
                found.add(num)
                heading = _heading_from(ln, num)
                toc_h = toc_heading.get(num, "").rstrip(".").strip()
                if not heading or (toc_h.startswith(heading) and len(toc_h) > len(heading)):
                    heading = toc_h  # body heading wrapped onto the next line
                current = SectionDraft("section", num, heading, part, chapter, [ln])
                sections.append(current)
                state_mode = False
                continue

        if state_mode:
            if _is_state_name(ln, known_states):
                current.state_blocks.append(StateBlock(text.rstrip(".:").strip(), [ln]))
            elif current.state_blocks:
                current.state_blocks[-1].lines.append(ln)
            else:
                current.state_blocks.append(StateBlock("", [ln]))  # no state named: rejected at validation
            continue
        current.lines.append(ln)

    if not preamble.lines:
        sections.remove(preamble)
    missing = [n for n in toc_nums if n not in found]
    if missing:
        log.info("ToC sections not found in body", extra={"file": doc.path.name, "missing": missing})
    return StatuteParse(toc=toc, sections=sections, footnotes=footnotes, missing=missing)
