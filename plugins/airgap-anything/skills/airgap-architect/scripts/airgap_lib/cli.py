"""Argument parsing and exit codes shared by the four scripts."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .answers import validate_defaults
from .blueprint import BlueprintError, load_blueprint, save_blueprint
from .catalog import Catalog, default_catalog_dir, load_catalog, validate_catalog
from .findings import format_text, has_errors

EXIT_OK = 0
EXIT_LINT_ERRORS = 1
EXIT_INPUT = 2
EXIT_ENVIRONMENT = 3


def fail(code: int, lines: list[str]) -> None:
    for line in lines:
        print(line, file=sys.stderr)
    raise SystemExit(code)


def make_parser(description: str, blueprint_required: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--blueprint",
        required=blueprint_required,
        help="path to blueprint.json (usually docs/airgap/blueprint.json)",
    )
    parser.add_argument(
        "--catalog",
        default=str(default_catalog_dir()),
        help="catalog directory (default: the catalog shipped with the skill)",
    )
    return parser


def open_catalog(directory: str) -> Catalog:
    try:
        catalog, findings = load_catalog(Path(directory))
    except (OSError, ValueError) as error:
        fail(EXIT_ENVIRONMENT, [f"cannot read the catalog at {directory}: {error}"])
    findings = findings + validate_catalog(catalog, date.today()) + validate_defaults(catalog.rules)
    if has_errors(findings):
        fail(
            EXIT_ENVIRONMENT,
            [
                format_text(findings),
                "The catalog is invalid. Run lint.py --catalog-only for details.",
            ],
        )
    return catalog


def open_blueprint(path: str) -> dict:
    try:
        return load_blueprint(Path(path))
    except BlueprintError as error:
        fail(EXIT_INPUT, [str(error)])


def answers_of(blueprint: dict) -> dict:
    answers = blueprint.get("answers")
    if not isinstance(answers, dict):
        fail(EXIT_INPUT, ["blueprint.json has no 'answers' object"])
    return answers


def fail_on_answer_problems(problems: list[str]) -> None:
    if problems:
        fail(EXIT_INPUT, ["Missing or invalid answers:"] + [f"  {p}" for p in problems])


def fail_on_unusable_value(error: Exception) -> None:
    fail(EXIT_INPUT, [f"blueprint.json holds a value the scripts cannot use: {error}"])


def save_or_fail(path: str, blueprint: dict) -> None:
    """Write blueprint.json; a computed value that JSON cannot hold is an input problem."""
    try:
        save_blueprint(Path(path), blueprint)
    except BlueprintError as error:
        fail_on_unusable_value(error)
    except OSError as error:
        fail_on_write_error(path, error)


def fail_on_write_error(path, error: OSError) -> None:
    """An output path that cannot be written is invalid input."""
    fail(EXIT_INPUT, [f"cannot write {path}: {error.strerror or type(error).__name__}"])


def iso_date(value: str) -> str:
    """argparse type: a calendar date written exactly as YYYY-MM-DD, returned as given."""
    try:
        if date.fromisoformat(value).isoformat() == value:
            return value
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(f"{value!r} is not a date; write it as YYYY-MM-DD")
