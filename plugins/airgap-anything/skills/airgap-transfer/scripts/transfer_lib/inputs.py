"""The files airgap-architect leaves in the project, read without its code.

`architect_digest` repeats airgap-architect's `inputs_digest` (airgap_lib/blueprint.py)
so that this skill can tell whether transfer-manifest.json still matches
blueprint.json. tests/test_transfer_inputs.py checks that the two agree.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .constants import (
    AIRGAP_DIR,
    BLUEPRINT_FILE,
    CHANNELS,
    MANIFEST_FILE,
    MANIFEST_SCHEMA_VERSION,
    OPERATORS,
)

UNKNOWN = "unknown"


class InputError(Exception):
    """A file this skill reads is missing, unreadable or does not fit; exit 2."""


def _reject_constant(name: str):
    raise ValueError(f"non-finite number {name} is not allowed")


def read_json(path: Path) -> dict:
    """A JSON object from `path`; InputError naming the path otherwise."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise InputError(f"{path}: file not found") from None
    except UnicodeDecodeError:
        raise InputError(f"{path}: not readable as UTF-8 text") from None
    except OSError as error:
        raise InputError(f"{path}: cannot be read ({error.strerror or type(error).__name__})") from None
    try:
        data = json.loads(text, parse_constant=_reject_constant)
    except (ValueError, RecursionError) as error:
        raise InputError(f"{path}: invalid JSON ({error})") from None
    if not isinstance(data, dict):
        raise InputError(f"{path}: the top level must be an object")
    return data


def architect_digest(blueprint: dict) -> str:
    """The digest airgap-architect records in its transfer manifest."""
    answers = blueprint.get("answers") or {}
    payload = {
        "decisions": blueprint.get("decisions", []),
        "models": answers.get("workload.models", []),
        "hardware": answers.get("hardware.gpus", []),
        "cpu_arch": answers.get("hardware.cpu_arch"),
    }
    canonical = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def airgap_dir(project_root: Path) -> Path:
    return Path(project_root) / AIRGAP_DIR


def load_inputs(project_root: Path) -> tuple[dict, dict]:
    """(blueprint, manifest) of a project; InputError when either is missing or stale."""
    folder = airgap_dir(project_root)
    if not (folder / BLUEPRINT_FILE).is_file():
        raise InputError(
            f"{AIRGAP_DIR}/{BLUEPRINT_FILE} not found: design the system with airgap-architect first"
        )
    if not (folder / MANIFEST_FILE).is_file():
        raise InputError(
            f"{AIRGAP_DIR}/{MANIFEST_FILE} not found: run airgap-architect's manifest.py first"
        )
    blueprint = read_json(folder / BLUEPRINT_FILE)
    manifest = read_json(folder / MANIFEST_FILE)
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise InputError(
            f"{AIRGAP_DIR}/{MANIFEST_FILE}: schema_version must be {MANIFEST_SCHEMA_VERSION}"
        )
    if manifest.get("inputs_digest") != architect_digest(blueprint):
        raise InputError(
            f"{AIRGAP_DIR}/{MANIFEST_FILE} is older than {BLUEPRINT_FILE}: "
            "run airgap-architect's manifest.py again"
        )
    if not manifest.get("platform"):
        raise InputError(
            f"{AIRGAP_DIR}/{MANIFEST_FILE} names no platform: answer hardware.cpu_arch "
            "with airgap-architect and run its manifest.py again"
        )
    return blueprint, manifest


def blueprint_answer(blueprint: dict, question_id: str):
    """An architect answer, with the default architect applied for 'unknown'.

    The default comes from the assumption airgap-architect recorded for it, so this
    skill needs no copy of architect's rules. None when neither is there.
    """
    value = (blueprint.get("answers") or {}).get(question_id)
    if value != UNKNOWN:
        return value
    for item in blueprint.get("assumptions") or []:
        if isinstance(item, dict) and item.get("id") == f"answers.{question_id}":
            return item.get("value")
    return None


def channel_of(blueprint: dict) -> str:
    channel = blueprint_answer(blueprint, "transfer.channel")
    if channel not in CHANNELS:
        raise InputError(
            "blueprint.json: transfer.channel must be one of " + ", ".join(CHANNELS)
            + "; finish the design with airgap-architect"
        )
    return channel


def operator_of(blueprint: dict) -> str:
    operator = blueprint_answer(blueprint, "inside.operator")
    if operator not in OPERATORS:
        raise InputError(
            "blueprint.json: inside.operator must be one of " + ", ".join(OPERATORS)
            + "; answer it with airgap-architect"
        )
    return operator


def language_of(blueprint: dict) -> str:
    language = blueprint.get("language")
    return language if isinstance(language, str) and language.strip() else "en"
