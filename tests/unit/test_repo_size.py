"""The GitHub repository must stay under 10 MB (DECISIONS D49): a guard with headroom on tracked files."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
TOTAL_LIMIT = 8 * 1024 * 1024
FILE_LIMIT = 1024 * 1024  # anything bigger is a model file, a PDF or a data dump that belongs in data/ (gitignored)


def test_tracked_files_stay_small():
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    sizes = {f: (ROOT / f).stat().st_size for f in out.decode("utf-8").split("\0") if f and (ROOT / f).exists()}
    largest = sorted(sizes.items(), key=lambda kv: -kv[1])[:5]
    assert sum(sizes.values()) < TOTAL_LIMIT, f"tracked files total {sum(sizes.values()) / 1e6:.1f} MB; largest {largest}"
    assert all(s < FILE_LIMIT for s in sizes.values()), f"file over 1 MB: {largest[0]}"
