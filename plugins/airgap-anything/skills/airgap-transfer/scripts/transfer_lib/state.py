"""docs/airgap/transfer.json: the state of one transfer."""
from __future__ import annotations

import json
from pathlib import Path

from .constants import AIRGAP_DIR, STATE_FILE, STATE_SCHEMA_VERSION
from .inputs import InputError, read_json

_TOP_LEVEL = (
    ("schema_version", int),
    ("manifest_digest", str),
    ("answers", dict),
    ("plan", dict),
    ("manual", list),
    ("pack", dict),
)
MANUAL_STATUSES = ("added", "not_needed")


def state_path(project_root: Path) -> Path:
    return Path(project_root) / AIRGAP_DIR / STATE_FILE


def new_state(manifest_digest: str) -> dict:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "manifest_digest": manifest_digest,
        "answers": {},
        "plan": {},
        "manual": [],
        "pack": {},
    }


def state_problems(state: dict) -> list[str]:
    problems = []
    for key, kind in _TOP_LEVEL:
        if not isinstance(state.get(key), kind) or isinstance(state.get(key), bool):
            problems.append(f"'{key}' must be of type {kind.__name__}")
    if not problems and state["schema_version"] != STATE_SCHEMA_VERSION:
        problems.append(f"'schema_version' must be {STATE_SCHEMA_VERSION}")
    for index, entry in enumerate(state.get("manual") if isinstance(state.get("manual"), list) else []):
        where = f"manual[{index}]"
        if not isinstance(entry, dict) or not isinstance(entry.get("item"), str) or not entry["item"].strip():
            problems.append(f"{where} needs an 'item' name")
            continue
        status = entry.get("status")
        if status not in MANUAL_STATUSES:
            problems.append(f"{where}.status must be one of " + ", ".join(MANUAL_STATUSES))
        elif status == "added" and not (isinstance(entry.get("path"), str) and entry["path"].startswith("manual/")):
            problems.append(f"{where}: an added item needs a 'path' under manual/")
        elif status == "not_needed" and not (isinstance(entry.get("reason"), str) and entry["reason"].strip()):
            problems.append(f"{where}: an item marked not needed needs a 'reason'")
    return problems


def load_state(path: Path) -> dict:
    state = read_json(path)
    problems = state_problems(state)
    if problems:
        raise InputError(f"{path}: " + "; ".join(problems))
    return state


def save_state(path: Path, state: dict) -> None:
    path = Path(path)
    text = json.dumps(state, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
