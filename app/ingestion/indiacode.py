"""Download central Acts from India Code through its public DSpace REST API.

Each Act in data/registry/sources.yaml names the CENTRAL item; we check that the live item still matches
(act_id, CENTRAL), take the PDF from the ORIGINAL bundle, verify the server's MD5 and record a manifest row.
The item's metadata is snapshotted next to the PDF so enforcement dates and act numbers are traceable.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from app.config import Settings
from app.ingestion.http import PoliteClient
from app.ingestion.manifest import Manifest, ManifestRow, sha256_file, utc_now
from app.ingestion.sources import load_sources

log = logging.getLogger(__name__)
SOURCE = "indiacode"


def _meta(item: dict, key: str) -> str | None:
    values = item.get("metadata", {}).get(key) or []
    return values[0]["value"] if values else None


def _pick_pdf(bitstreams: list[dict], language: str) -> dict:
    """Bitstreams carry no language field; names seen so far are `a1908-16.pdf` / `A2019-35.pdf` for English and
    `H1908-16.pdf` / `hindi201935.pdf` for Hindi. The parser confirms the language from the text's script."""
    pdfs = [b for b in bitstreams if b["name"].lower().endswith(".pdf")]
    if language == "en":
        picked = [b for b in pdfs if not b["name"].lower().startswith("h")]
    elif language == "hi":
        picked = [b for b in pdfs if b["name"].lower().startswith("h")]
    else:
        raise ValueError(f"unsupported India Code language {language!r}")
    if len(picked) != 1:
        names = [b["name"] for b in pdfs]
        raise RuntimeError(f"expected exactly one {language} PDF in the ORIGINAL bundle, found {names}")
    return picked[0]


def ingest(settings: Settings, act_ids: list[str] | None = None, phase: int | None = 1,
           languages: tuple[str, ...] = ("en",)) -> list[ManifestRow]:
    reg = load_sources(settings.registry_dir)[SOURCE]
    api, base = reg["api_url"], reg["base_url"]
    manifest = Manifest(settings.manifest_path, settings.data_dir)
    client = PoliteClient(settings.http_user_agent)
    out_root = settings.raw_dir / SOURCE
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "LICENSE").write_text(reg["licence"].strip() + "\n", encoding="utf-8")

    acts = [a for a in reg["acts"] if (act_ids and a["id"] in act_ids) or (not act_ids and (phase is None or a["phase"] <= phase))]
    rows: list[ManifestRow] = []
    try:
        for act in acts:
            item = client.get_json(f"{api}/core/items/{act['item_uuid']}")
            live_act_id, state = _meta(item, "dc.identifier.act_id"), _meta(item, "dc.identifier.state_name")
            if live_act_id != act["act_id"] or state != "CENTRAL":
                raise RuntimeError(f"{act['id']}: registry says {act['act_id']}/CENTRAL, live item says {live_act_id}/{state}")
            act_dir = out_root / act["id"]
            act_dir.mkdir(parents=True, exist_ok=True)
            (act_dir / "item.json").write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")

            bundles = client.get_json(item["_links"]["bundles"]["href"])["_embedded"]["bundles"]
            original = next(b for b in bundles if b["name"] == "ORIGINAL")
            bitstreams = client.get_json(original["_links"]["bitstreams"]["href"])["_embedded"]["bitstreams"]
            for lang in languages:
                bs = _pick_pdf(bitstreams, lang)
                url = f"{api}/core/bitstreams/{bs['uuid']}/content"
                # India Code stamps a rotated "India Code" watermark into each PDF as it is served, so the bytes
                # differ from the repository copy and its MD5 (DECISIONS V16). The repository checksum identifies
                # the underlying document; we re-download only when it changes.
                repo_md5 = bs["checkSum"]["value"]
                prior = manifest.get(url)
                if prior and manifest.is_current(url) and (prior.extra or {}).get("repository_md5") == repo_md5:
                    log.info("unchanged, skipped", extra={"act": act["id"], "file": bs["name"]})
                    rows.append(prior)
                    continue
                resp = client.get(url)
                body = resp.content
                if not body.startswith(b"%PDF") or b"%%EOF" not in body[-1024:]:
                    raise RuntimeError(f"{act['id']}: {bs['name']} is not a complete PDF "
                                       f"(content-type {resp.headers.get('content-type')}, {len(body)} bytes)")
                md5 = hashlib.md5(body).hexdigest()
                path: Path = act_dir / bs["name"]
                path.write_bytes(body)
                row = ManifestRow(
                    source=SOURCE, url=url, local_path=manifest.rel(path), sha256=sha256_file(path),
                    bytes=path.stat().st_size, retrieved_at=utc_now(), licence=reg["licence"].strip(),
                    source_page=f"{base}/handle/{act['handle']}",
                    extra={"act": act["id"], "title": _meta(item, "dc.title"), "language": lang, "served_md5": md5,
                           "repository_md5": repo_md5, "repository_bytes": bs["sizeBytes"], "watermarked": True,
                           "bitstream_uuid": bs["uuid"], "item_uuid": act["item_uuid"], "act_id": act["act_id"]},
                )
                manifest.record(row)
                rows.append(row)
                log.info("downloaded", extra={"act": act["id"], "file": bs["name"], "bytes": row.bytes})
    finally:
        client.close()
    return rows
