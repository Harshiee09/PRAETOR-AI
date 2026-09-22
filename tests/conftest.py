import json
from pathlib import Path

import pytest

from app.parsing.pdf import Line, PageInfo, ParsedPdf

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def parsed_from_fixture(name: str) -> ParsedPdf:
    """Rebuild parser output from a real-excerpt fixture (see scripts/make_fixtures.py)."""
    fx = load_fixture(name)
    lines = [Line(**ln) for ln in fx["lines"]]
    pages = [PageInfo(number=p, text_source="layer", usable=True) for p in fx["pages"]]
    return ParsedPdf(path=Path(fx["download_url"].rsplit("/", 1)[-1]), pages=pages, lines=lines,
                     body_size=fx["body_size"], page_height=fx["page_height"])


@pytest.fixture
def known_states() -> set[str]:
    import yaml

    jur = yaml.safe_load((Path(__file__).parents[1] / "data" / "registry" / "jurisdictions.yaml").read_text(encoding="utf-8"))
    return set(jur["codes"]) | set(jur["aliases"])
