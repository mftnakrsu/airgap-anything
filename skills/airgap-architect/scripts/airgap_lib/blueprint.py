"""blueprint.json: the single state file of one design."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from .constants import EVIDENCE_LEVELS, LAYERS, SCHEMA_VERSION

_TOP_LEVEL = (
    ("schema_version", int),
    ("project", str),
    ("created", str),
    ("language", str),
    ("blueprint_path", str),
    ("answers", dict),
    ("assumptions", list),
    ("tier", dict),
    ("sizing", dict),
    ("decisions", list),
)
_STRING_LISTS = ("components", "existing", "custom", "alternatives_considered")


class BlueprintError(Exception):
    """blueprint.json is missing or is not a JSON object."""


def _reject_constant(name: str):
    raise ValueError(f"non-finite number {name} is not allowed")


def load_blueprint(path: Path) -> dict:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise BlueprintError(f"{path}: file not found") from None
    except UnicodeDecodeError:
        raise BlueprintError(f"{path}: not readable as UTF-8 text") from None
    except OSError as error:
        raise BlueprintError(
            f"{path}: cannot be read ({error.strerror or type(error).__name__})"
        ) from None
    try:
        data = json.loads(text, parse_constant=_reject_constant)
    except json.JSONDecodeError as error:
        raise BlueprintError(f"{path}: invalid JSON ({error})") from None
    except RecursionError:
        raise BlueprintError(f"{path}: invalid JSON (nested too deeply)") from None
    except ValueError as error:
        raise BlueprintError(f"{path}: {error}") from None
    if not isinstance(data, dict):
        raise BlueprintError(f"{path}: the top level must be an object")
    return data


def save_blueprint(path: Path, data: dict) -> None:
    path = Path(path)
    try:
        text = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    except ValueError as error:
        raise BlueprintError(f"{path}: cannot be written ({error})") from None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def inputs_digest(data: dict) -> str:
    """Digest of what the transfer manifest is generated from."""
    payload = {
        "decisions": data.get("decisions", []),
        "models": (data.get("answers") or {}).get("workload.models", []),
        "hardware": (data.get("answers") or {}).get("hardware.gpus", []),
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def decisions_of(data: dict) -> list[dict]:
    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        return []
    return [decision for decision in decisions if isinstance(decision, dict)]


def decision_for(data: dict, layer: str) -> dict | None:
    for decision in decisions_of(data):
        if decision.get("layer") == layer:
            return decision
    return None


def chosen_components(data: dict) -> list[str]:
    """Catalog IDs named in decisions, in order, without duplicates."""
    chosen: list[str] = []
    for decision in decisions_of(data):
        for component_id in decision.get("components") or []:
            if isinstance(component_id, str) and component_id not in chosen:
                chosen.append(component_id)
    return chosen


def benchmark_components(data: dict) -> list[str]:
    """Catalog IDs that decisions carry in only for a benchmark, in order, without
    duplicates, leaving out any ID that is also a chosen component."""
    chosen = set(chosen_components(data))
    benchmark: list[str] = []
    for decision in decisions_of(data):
        value = decision.get("benchmark")
        for component_id in value if isinstance(value, list) else []:
            if isinstance(component_id, str) and component_id not in chosen and component_id not in benchmark:
                benchmark.append(component_id)
    return benchmark


def validate_schema(data: dict) -> list[str]:
    """Structural problems of a finished blueprint.json (lint error E1)."""
    problems: list[str] = []
    for key, kind in _TOP_LEVEL:
        if key not in data:
            problems.append(f"missing key '{key}'")
        elif not isinstance(data[key], kind) or isinstance(data[key], bool):
            problems.append(f"'{key}' must be of type {kind.__name__}")
    if problems:
        return problems
    if data["schema_version"] != SCHEMA_VERSION:
        problems.append(f"'schema_version' must be {SCHEMA_VERSION}")
    if not data["project"].strip():
        problems.append("'project' is empty")
    if not data["blueprint_path"].strip():
        problems.append("'blueprint_path' is empty")
    try:
        date.fromisoformat(data["created"])
    except ValueError:
        problems.append("'created' must be a date like 2026-11-20")
    for index, item in enumerate(data["assumptions"]):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or "value" not in item
            or item.get("evidence") not in EVIDENCE_LEVELS
        ):
            problems.append(f"assumptions[{index}] needs id, value and a valid evidence label")
    seen: set[str] = set()
    for index, decision in enumerate(data["decisions"]):
        where = f"decisions[{index}]"
        if not isinstance(decision, dict):
            problems.append(f"{where} must be an object")
            continue
        layer = decision.get("layer")
        if layer not in LAYERS:
            problems.append(f"{where}.layer must be one of " + ", ".join(LAYERS))
        elif layer in seen:
            problems.append(f"{where}: second decision for layer '{layer}'")
        else:
            seen.add(layer)
        for key in _STRING_LISTS:
            value = decision.get(key)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                problems.append(f"{where}.{key} must be a list of strings")
        if "benchmark" in decision:
            problems += _benchmark_problems(where, decision)
        if not isinstance(decision.get("rationale"), str):
            problems.append(f"{where}.rationale must be a string")
        if decision.get("evidence") not in EVIDENCE_LEVELS:
            problems.append(f"{where}.evidence must be one of " + ", ".join(EVIDENCE_LEVELS))
        if "override" not in decision:
            problems.append(f"{where}.override must be null or an object with a reason")
        elif decision["override"] is not None and not has_override(decision):
            problems.append(f"{where}.override must be null or an object with a reason")
    return problems


def _benchmark_problems(where: str, decision: dict) -> list[str]:
    value = decision["benchmark"]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return [f"{where}.benchmark must be a list of strings"]
    problems: list[str] = []
    components = decision.get("components")
    chosen = components if isinstance(components, list) else []
    for index, item in enumerate(value):
        if item in value[:index]:
            problems.append(f"{where}.benchmark lists '{item}' more than once")
        elif item in chosen:
            problems.append(f"{where}.benchmark lists '{item}', which is also in components")
    return problems


def has_override(decision: dict) -> bool:
    override = decision.get("override")
    return (
        isinstance(override, dict)
        and isinstance(override.get("reason"), str)
        and bool(override["reason"].strip())
    )
