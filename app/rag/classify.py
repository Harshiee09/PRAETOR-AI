"""Rules-first query classification (retrieval-pipeline note, step 2).

Output drives filters, exact lookup, the temporal rule for the criminal codes and high-stakes handling. The local
LLM classifier (LLM_CLASSIFY=ollama) is not built: rules decide, and an unmatched query is domain `other`.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

import regex
import yaml

from app.retrieval.registry import ActMention, Registry

DOMAINS = ["property_land", "contract_civil", "consumer", "criminal_procedure", "constitutional"]

# Keyword cues per domain (English, plus a few common Hindi words). Deliberately short: Act mentions decide first.
DOMAIN_CUES = {
    "property_land": r"propert|land\b|plot|flat|apartment|house|sale deed|registr|mortgage|lease|tenan|landlord|gift deed|"
                     r"immov|possession|title deed|mutation|stamp duty|acquisition|builder|allottee|real estate|"
                     r"संपत्ति|जमीन|ज़मीन|रजिस्ट्री|मकान|किराय",
    "contract_civil": r"contract|agreement|breach|damages|specific performance|injunction|civil suit|\bsuit\b|decree|"
                      r"plaint|summons|limitation|time.?barred|execution|appeal|guarantee|indemnity|agent|अनुबंध|मुकदमा",
    "consumer": r"consumer|defective|deficiency|refund|warranty|e-?commerce|district commission|ncdrc|"
                r"state commission|product liability|unfair trade|seller|manufacturer|उपभोक्ता",
    "criminal_procedure": r"\bfir\b|police|arrest|\bbail\b|charge.?sheet|magistrate|cognizable|investigation|accused|"
                          r"offence|crime|custody|remand|summons to accused|\bipc\b|\bbns\b|crpc|bnss|evidence act|"
                          r"गिरफ्तार|जमानत|पुलिस|अपराध|एफआईआर",
    "constitutional": r"constitution|fundamental right|article \d+|\bwrit\b|habeas corpus|संविधान",
}
ACT_DOMAIN = {"crpc-1973": "criminal_procedure", "bnss-2023": "criminal_procedure", "ipc-1860": "criminal_procedure",
              "bns-2023": "criminal_procedure", "iea-1872": "criminal_procedure", "bsa-2023": "criminal_procedure",
              "cpa-2019": "consumer", "cpa-1986": "consumer", "registration-1908": "property_land",
              "tpa-1882": "property_land", "rfctlarr-2013": "property_land", "laa-1894": "property_land",
              "rera-2016": "property_land", "limitation-1963": "contract_civil", "ica-1872": "contract_civil",
              "sra-1963": "contract_civil", "cpc-1908": "contract_civil"}

HIGH_STAKES = (r"\barrest|detain|detention|in custody|police (?:took|picked|came)|\bbail\b|threat|violence|beat(?:en|ing)|"
               r"assault|abuse|harass|rape|suicide|kill|kidnap|missing|evict|dispossess|thrown out|demolish|"
               r"deadline|last date|limitation (?:is )?(?:expir|end)|tomorrow|\bchild\b|minor\b|"
               r"गिरफ्तार|जमानत|धमकी|हिंसा|मारपीट|बेदखल")
PROCEDURE = r"^\s*how\b|how (?:do|can|to|should)|procedure|process|steps?\b|apply|file (?:a|an|my)|lodge|register (?:a|my)|कैसे|प्रक्रिया"
CASE_LAW = r"\bcase\b|judgment|judgement|supreme court|high court|precedent|landmark|held that|ruled|निर्णय|फैसला"
DRAFTING = r"\bdraft|format|template|sample (?:notice|letter|agreement)|मसौदा"
DEFINE = r"what (?:is|are|does)|define|definition|meaning|means|explain|क्या है|परिभाषा"
SECTION_REF = regex.compile(
    r"(?:\b(?:section|sec\.?|s\.|u/s\.?|ss\.)\s*|धारा\s*)(?P<num>\d{1,3}[A-Z]{0,2})(?P<sub>(?:\s*\(\w{1,4}\))*)", regex.I)
ORDER_RULE = regex.compile(r"\bOrder\s+(?P<order>[IVXLC]+|\d{1,2})\s*,?\s*(?:Rule|r\.)\s*(?P<rule>\d{1,3}[A-Z]?)", regex.I)
YEAR = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")
DATE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](19|20)(\d{2})\b")


@dataclass
class Classification:
    domain: str
    intent: str
    high_stakes: bool
    jurisdiction_hint: list[str] = field(default_factory=list)
    event_dates: list[str] = field(default_factory=list)
    acts: list[str] = field(default_factory=list)           # ids the query names
    search_acts: list[str] = field(default_factory=list)    # ids to search (names + successors/predecessors)
    section_refs: list[dict] = field(default_factory=list)  # [{"act": id|None, "section": "438", "sub": "(1)"}]
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


@lru_cache(maxsize=2)
def _states(registry_dir: str) -> dict[str, str]:
    jur = yaml.safe_load((Path(registry_dir) / "jurisdictions.yaml").read_text(encoding="utf-8"))
    names = {n: c for n, c in jur["codes"].items()}
    names.update({a: jur["codes"][t] for a, t in jur["aliases"].items()})
    return names


def roman(n: int) -> str:
    vals = [(50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in vals:
        while n >= v:
            out, n = out + s, n - v
    return out


def _nearest_act(mentions: list[ActMention], pos: int) -> str | None:
    """The Act mention closest to a section reference (after it first: 'section 23 of the Registration Act')."""
    if not mentions:
        return None
    return min(mentions, key=lambda m: (abs(m.start - pos) if m.start >= pos else abs(pos - m.end) + 5)).names


def classify(query: str, registry: Registry, registry_dir: Path) -> Classification:
    q = query.strip()
    low = q.lower()
    reasons = []
    mentions = registry.find_acts(q)
    acts = list(dict.fromkeys(m.names for m in mentions))
    search_acts = list(dict.fromkeys(i for m in mentions for i in m.expands_to))

    # domain: an Act mention decides; else keyword cues
    domain = None
    for a in acts:
        if a in ACT_DOMAIN:
            domain = ACT_DOMAIN[a]
            reasons.append(f"domain from Act {a}")
            break
    if domain is None:
        scores = {d: len(regex.findall(p, low)) for d, p in DOMAIN_CUES.items()}
        best = max(scores, key=scores.get)
        domain = best if scores[best] else "other"
        reasons.append(f"domain from cues {scores}")

    refs = []
    for m in SECTION_REF.finditer(q):
        refs.append({"act": _nearest_act(mentions, m.start()), "section": m.group("num").upper(),
                     "sub": re.sub(r"\s+", "", m.group("sub") or "") or None})
    for m in ORDER_RULE.finditer(q):
        order = m.group("order").upper()
        if order.isdigit():
            order = roman(int(order))
        refs.append({"act": "cpc-1908", "section": f"O. {order} r. {m.group('rule').upper()}", "sub": None})

    if refs:
        intent = "statute_lookup"
    elif regex.search(DRAFTING, low):
        intent = "drafting"
    elif regex.search(CASE_LAW, low):
        intent = "case_law"
    elif regex.search(PROCEDURE, low):
        intent = "procedure"
    elif regex.search(DEFINE, low):
        intent = "explain"
    else:
        intent = "explain"

    high = bool(regex.search(HIGH_STAKES, low))
    states = _states(str(registry_dir))
    juris = sorted({code for name, code in states.items() if regex.search(rf"\b{regex.escape(name)}\b", q, regex.I)})
    masked = q  # years inside Act titles ("Consumer Protection Act 1986") are not event dates
    for m in sorted(mentions, key=lambda m: -m.start):
        masked = masked[:m.start] + " " * (m.end - m.start) + masked[m.end:]
    dates = sorted(set(YEAR.findall(masked)) | {f"{d[2]}{d[3]}-{int(d[1]):02d}-{int(d[0]):02d}" for d in DATE.findall(masked)})
    return Classification(domain=domain, intent=intent, high_stakes=high, jurisdiction_hint=juris, event_dates=dates,
                          acts=acts, search_acts=search_acts, section_refs=refs, reasons=reasons)
