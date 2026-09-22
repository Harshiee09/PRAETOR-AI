"""`praetor` command-line entry point. Every real workflow starts here (see the command table in CLAUDE.md)."""

from __future__ import annotations

import argparse
import os
import sys

# Windows without Developer Mode can't symlink in the HF cache; that works (with more disk), so skip the warning.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from app.config import get_settings
from app.config.logs import setup_logging


def _cmd_gpu_check(args: argparse.Namespace) -> int:
    from app.embeddings.gpu_check import run

    return run(get_settings())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="praetor", description="PRAETOR AI — informational legal RAG (not legal advice)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("gpu-check", help="prove CUDA works and bge-m3 embeds on the GPU")
    p.set_defaults(func=_cmd_gpu_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    # Windows consoles default to a legacy code page; Indic text needs UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    settings = get_settings()
    setup_logging(settings.log_level)
    args = build_parser().parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
