"""Supreme Court judgments from the AWS Open Data bucket (unsigned reads; CC-BY-4.0).

Flow: fetch the per-year metadata parquet -> profile it -> select judgments by rule -> download each PDF with a
JSON sidecar carrying the metadata fields that citations are rendered from.

Selection uses the headnotes inside `raw_html` only to *find* judgments about the corpus Acts. Headnotes are
editorial additions, so they are never indexed or shown (docs/topics/data/data-sources.md, licensing notes).
"""

from __future__ import annotations

import html
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from app.config import Settings
from app.ingestion.manifest import Manifest, ManifestRow, sha256_file, utc_now
from app.ingestion.sources import load_sources

log = logging.getLogger(__name__)
SOURCE = "sc-judgments"
EMPTY = {"", "none", "nan", "<na>", "-"}

# Selection rule: headnotes that name a corpus Act with its year (a bare "Registration Act" also matches
# marriage-registration statutes and the like). Repealed predecessors are included on purpose: judgments under
# them are what transition questions need, and their status comes from statutes.yaml.
ACT_PATTERNS = {
    "registration-1908": re.compile(r"Registration\s+Act,?\s*1908", re.I),
    "tpa-1882": re.compile(r"Transfer\s+of\s+Property\s+Act,?\s*1882", re.I),
    "cpa-2019": re.compile(r"Consumer\s+Protection\s+Act,?\s*2019", re.I),
    "cpa-1986": re.compile(r"Consumer\s+Protection\s+Act,?\s*1986", re.I),
    "rfctlarr-2013": re.compile(r"Right\s+to\s+Fair\s+Compensation\s+and\s+Transparency|Resettlement\s+Act,?\s*2013", re.I),
    "laa-1894": re.compile(r"Land\s+Acquisition\s+Act,?\s*1894", re.I),
    "rera-2016": re.compile(r"Real\s+Estate\s*\(\s*Regulation\s+and\s+Development\s*\)\s*Act,?\s*2016|\bRERA\b"),
    "limitation-1963": re.compile(r"Limitation\s+Act,?\s*1963", re.I),
    "ica-1872": re.compile(r"Contract\s+Act,?\s*1872", re.I),
    "sra-1963": re.compile(r"Specific\s+Relief\s+Act,?\s*1963", re.I),
    "cpc-1908": re.compile(r"Code\s+of\s+Civil\s+Procedure,?\s*1908", re.I),
    "crpc-1973": re.compile(r"Code\s+of\s+Criminal\s+Procedure,?\s*1973", re.I),
    "bnss-2023": re.compile(r"Bharatiya\s+Nagarik\s+Suraksha\s+Sanhita", re.I),
}
# Seed landmark cases (data-sources note) are lookups against dataset records, never typed-in facts. Only those
# inside the selected years and demo domains are looked up; constitutional ones (1967-1980) are out of scope.
LANDMARKS = [{"year": 2020, "title_has": ["INDORE DEVELOPMENT AUTHORITY", "MANOHARLAL"]}]


def _s3(region: str):
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    return boto3.client("s3", region_name=region, config=Config(signature_version=UNSIGNED, retries={"max_attempts": 5}))


def _cfg(settings: Settings) -> dict:
    return load_sources(settings.registry_dir)[SOURCE]


def _download(s3, cfg: dict, key: str, dest: Path, manifest: Manifest, extra: dict | None = None) -> ManifestRow:
    url = f"s3://{cfg['bucket']}/{key}"
    head = s3.head_object(Bucket=cfg["bucket"], Key=key)
    etag = head["ETag"].strip('"')
    prior = manifest.get(url)
    if prior and (prior.extra or {}).get("etag") == etag and manifest.is_current(url):
        return prior
    dest.parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(cfg["bucket"], key, str(dest))
    row = ManifestRow(
        source=SOURCE, url=url, local_path=manifest.rel(dest), sha256=sha256_file(dest), bytes=dest.stat().st_size,
        retrieved_at=utc_now(), licence=cfg["licence"], source_page=cfg["registry_page"],
        extra={"etag": etag, **(extra or {})},
    )
    manifest.record(row)
    return row


def fetch_metadata(settings: Settings, years: list[int]) -> list[Path]:
    cfg = _cfg(settings)
    s3, manifest = _s3(cfg["region"]), Manifest(settings.manifest_path, settings.data_dir)
    root = settings.raw_dir / SOURCE
    root.mkdir(parents=True, exist_ok=True)
    (root / "LICENSE").write_text(
        f"{cfg['licence']}\n{cfg['attribution'].strip()}\nhttps://creativecommons.org/licenses/by/4.0/\n", encoding="utf-8"
    )
    paths = []
    for y in years:
        key = f"{cfg['metadata_prefix']}/year={y}/metadata.parquet"
        dest = root / "metadata" / f"year={y}" / "metadata.parquet"
        _download(s3, cfg, key, dest, manifest, extra={"kind": "metadata", "year": y})
        paths.append(dest)
    return paths


def load_metadata(settings: Settings, years: list[int]) -> pd.DataFrame:
    frames = []
    for y in years:
        p = settings.raw_dir / SOURCE / "metadata" / f"year={y}" / "metadata.parquet"
        frames.append(pd.read_parquet(p))
    return pd.concat(frames, ignore_index=True)


def _is_empty(s: pd.Series) -> pd.Series:
    return s.isna() | s.astype(str).str.strip().str.lower().isin(EMPTY)


def parse_decision_date(value: str) -> date | None:
    try:
        return datetime.strptime(str(value).strip(), "%d-%m-%Y").date()
    except ValueError:
        return None


def profile_markdown(df: pd.DataFrame, years: list[int]) -> str:
    """Row count, columns, null/empty rates and value checks for the metadata parquet."""
    lines = [f"# SC judgments metadata profile", "",
             f"_Generated {utc_now()} from `metadata/parquet/year=YYYY/metadata.parquet`, years {years[0]}–{years[-1]}._", "",
             f"**Rows:** {len(df)} · **Columns:** {df.shape[1]}", "",
             "| year | rows |", "|---|---|"]
    lines += [f"| {y} | {n} |" for y, n in df["year"].value_counts().sort_index().items()]
    lines += ["", "| column | dtype | null or empty | distinct | example |", "|---|---|---|---|---|"]
    for col in df.columns:
        empty = _is_empty(df[col]).mean()
        example = "" if col == "raw_html" else str(df[col].dropna().astype(str).iloc[0])[:60].replace("|", "/") if df[col].notna().any() else ""
        lines.append(f"| `{col}` | {df[col].dtype} | {empty:.1%} | {df[col].nunique()} | {example} |")
    dates = df["decision_date"].map(parse_decision_date)
    lines += ["", "## Checks",
              f"- `decision_date` unparseable (expected DD-MM-YYYY): {dates.isna().sum()}",
              f"- `decision_date` range: {dates.min()} to {dates.max()}",
              f"- `decision_date` before 1950-01-28 or in the future: {int(((dates < date(1950, 1, 28)) | (dates > date.today())).sum())}",
              f"- duplicate `cnr`: {df['cnr'].duplicated().sum()} · duplicate `path`: {df['path'].duplicated().sum()}",
              f"- rows with English available (`ENG` in `available_languages`): {df['available_languages'].str.contains('ENG').sum()}",
              "", "## Top values", ""]
    for col in ("disposal_nature", "available_languages", "court"):
        lines.append(f"**{col}**: " + "; ".join(f"{k or '(empty)'} ({v})" for k, v in df[col].value_counts().head(8).items()))
        lines.append("")
    lines += ["## Notes",
              "- `raw_html` holds the listing card: coram (author marked `*`) and the Editorial Section's headnotes. "
              "Headnotes are used only to select judgments, never indexed.",
              "- `author_judge` is always empty and `description` mostly empty; the bench and author come from the coram "
              "in `raw_html`.",
              "- Rows with empty `available_languages` are excluded from selection (English availability unknown)."]
    return "\n".join(lines) + "\n"


def _html_text(raw: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw or ""))).strip()


def parse_coram(raw: str) -> tuple[list[str], str | None]:
    m = re.search(r"Coram\s*:\s*(.*?)</strong>", raw or "", re.S | re.I)
    if not m:
        return [], None
    segment = m.group(1)
    author = None
    am = re.search(r"([^,>]+?)\s*<sup[^>]*data-tooltip=\"Author\"", segment)
    if am:
        author = _html_text(am.group(1)).strip(" ,")
    judges = [j.strip(" *") for j in _html_text(re.sub(r"<sup.*?</sup>", "", segment, flags=re.S)).split(",")]
    return [j for j in judges if j], author


def select(df: pd.DataFrame, limit: int = 50, min_year: int = 2019) -> pd.DataFrame:
    """Deterministic: newest-first judgments whose headnotes name a corpus Act, English PDF available.
    First up to ceil(limit / n_acts) per Act, then leftover slots go to the newest remaining hits of any Act."""
    df = df.copy()
    df["_text"] = df["raw_html"].map(_html_text)
    df["_date"] = df["decision_date"].map(parse_decision_date)
    df = df[df["available_languages"].fillna("").str.contains("ENG") & df["_date"].notna()]
    df = df[df["_date"] >= date(min_year, 1, 1)]
    per_act = -(-limit // len(ACT_PATTERNS))
    picked, seen, pools = [], set(), []
    for act_id, pat in ACT_PATTERNS.items():
        hits = df[df["_text"].str.contains(pat)].sort_values("_date", ascending=False).assign(matched_act=act_id)
        pools.append(hits)
        take = hits[~hits["path"].isin(seen)].head(per_act)
        seen.update(take["path"])
        picked.append(take)
    # Leftover slots go round-robin across Acts (newest first within each), so one prolific Act can't take them all.
    remaining = limit - sum(len(p) for p in picked)
    queues = [h[~h["path"].isin(seen)] for h in pools]
    cursors = [0] * len(queues)
    extra_rows = []
    while remaining > 0 and any(c < len(q) for c, q in zip(cursors, queues)):
        for i, q in enumerate(queues):
            while cursors[i] < len(q) and q.iloc[cursors[i]]["path"] in seen:
                cursors[i] += 1
            if remaining > 0 and cursors[i] < len(q):
                row = q.iloc[cursors[i]]
                seen.add(row["path"])
                extra_rows.append(row)
                cursors[i] += 1
                remaining -= 1
    if extra_rows:
        picked.append(pd.DataFrame(extra_rows))
    for lm in LANDMARKS:
        cand = df[(df["_date"].map(lambda d: d.year) == lm["year"])
                  & df["title"].map(lambda t: all(s in t.upper() for s in lm["title_has"]))]
        if cand.empty:
            log.warning("landmark case not found in the dataset", extra={"landmark": lm})
        picked.append(cand[~cand["path"].isin(seen)].assign(matched_act="landmark"))
    out = pd.concat(picked, ignore_index=True)
    out["matched_acts"] = out["_text"].map(lambda t: [a for a, p in ACT_PATTERNS.items() if p.search(t)])
    return out.drop(columns=["_text"])


def _sidecar(rec: dict) -> dict:
    judges, author = parse_coram(rec["raw_html"])
    return {
        "case_title": rec["title"].replace("  ", " ").strip(), "petitioner": rec["petitioner"],
        "respondent": rec["respondent"], "court": rec["court"],
        "decision_date": rec["_date"].isoformat(), "judges": judges, "author_judge": author,
        "citation": rec["citation"], "neutral_citation": rec["case_id"], "cnr": rec["cnr"],
        "disposal_nature": rec["disposal_nature"] or None, "available_languages": rec["available_languages"],
        "path": rec["path"], "year": int(rec["year"]), "matched_acts": rec["matched_acts"],
    }


def _targets(settings: Settings, cfg: dict, rec: dict) -> tuple[str, str, Path]:
    year = str(rec["year"])
    name = f"{rec['path']}_EN.pdf"
    key = f"{cfg['pdf_prefix']}/year={year}/english/{name}"
    return name, key, settings.raw_dir / SOURCE / "pdf" / f"year={year}" / "english" / name


def download_selected(settings: Settings, selected: pd.DataFrame) -> list[ManifestRow]:
    """Individual objects from data/pdf/ — the dataset's path for targeted access (a few hundred files)."""
    cfg = _cfg(settings)
    s3, manifest = _s3(cfg["region"]), Manifest(settings.manifest_path, settings.data_dir)
    rows = []
    for rec in selected.to_dict("records"):
        _, key, dest = _targets(settings, cfg, rec)
        row = _download(s3, cfg, key, dest, manifest, extra={"kind": "judgment_pdf", "cnr": rec["cnr"]})
        dest.with_suffix(".json").write_text(json.dumps(_sidecar(rec), ensure_ascii=False, indent=2), encoding="utf-8")
        rows.append(row)
        log.info("judgment ready", extra={"cnr": rec["cnr"], "path": rec["path"]})
    return rows


def download_selected_via_tar(settings: Settings, selected: pd.DataFrame) -> list[ManifestRow]:
    """Bulk path the maintainers ask for: per year, download the English tar part(s) that hold selected judgments
    into data/scratch/, extract only those PDFs, then delete the tar (DECISIONS D18). Manifest rows keep the
    canonical data/pdf/ key as `url` (so doc_ids match individually fetched copies) and record the tar in `via`."""
    import tarfile

    cfg = _cfg(settings)
    s3, manifest = _s3(cfg["region"]), Manifest(settings.manifest_path, settings.data_dir)
    scratch = settings.data_dir / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    rows: list[ManifestRow] = []
    by_year: dict[str, list[dict]] = {}
    for rec in selected.to_dict("records"):
        by_year.setdefault(str(rec["year"]), []).append(rec)
    for year, recs in sorted(by_year.items()):
        need: dict[str, tuple[dict, str, Path]] = {}
        for rec in recs:
            name, key, dest = _targets(settings, cfg, rec)
            url = f"s3://{cfg['bucket']}/{key}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.with_suffix(".json").write_text(json.dumps(_sidecar(rec), ensure_ascii=False, indent=2), encoding="utf-8")
            if manifest.is_current(url):
                rows.append(manifest.get(url))
            else:
                need[name] = (rec, url, dest)
        if not need:
            continue
        index = json.loads(s3.get_object(Bucket=cfg["bucket"], Key=f"data/tar/year={year}/english/english.index.json")["Body"].read())
        for part in index["parts"]:
            wanted = set(part["files"]) & set(need)
            if not wanted:
                continue
            tar_key = f"data/tar/year={year}/english/{part['name']}"
            tar_path = scratch / f"sc-{year}-{part['name']}"
            size = s3.head_object(Bucket=cfg["bucket"], Key=tar_key)["ContentLength"]
            log.warning("downloading tar", extra={"key": tar_key, "mb": round(size / 2**20), "wanted": len(wanted)})
            s3.download_file(cfg["bucket"], tar_key, str(tar_path))
            try:
                with tarfile.open(tar_path) as tf:
                    for member in tf:
                        base = member.name.rsplit("/", 1)[-1]
                        if not member.isfile() or base not in wanted:
                            continue
                        rec, url, dest = need[base]
                        dest.write_bytes(tf.extractfile(member).read())
                        row = ManifestRow(
                            source=SOURCE, url=url, local_path=manifest.rel(dest), sha256=sha256_file(dest),
                            bytes=dest.stat().st_size, retrieved_at=utc_now(), licence=cfg["licence"],
                            source_page=cfg["registry_page"],
                            extra={"kind": "judgment_pdf", "cnr": rec["cnr"], "via": f"s3://{cfg['bucket']}/{tar_key}"},
                        )
                        manifest.record(row)
                        rows.append(row)
            finally:
                tar_path.unlink(missing_ok=True)
        missing = [n for n, (_, url, _) in need.items() if manifest.get(url) is None]
        if missing:
            log.warning("selected judgments not found in the year's tar", extra={"year": year, "missing": missing[:10], "n": len(missing)})
    return rows
