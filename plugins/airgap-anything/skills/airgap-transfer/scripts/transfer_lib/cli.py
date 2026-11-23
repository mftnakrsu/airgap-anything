"""Argument parsing and exit codes shared by plan.py, pack.py and check.py."""
from __future__ import annotations

import argparse
import sys


def fail(code: int, lines: list[str]) -> None:
    for line in lines:
        print(line, file=sys.stderr)
    raise SystemExit(code)


def make_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--project-root",
        default=".",
        help="the project that holds docs/airgap/ (default: .)",
    )
    return parser
