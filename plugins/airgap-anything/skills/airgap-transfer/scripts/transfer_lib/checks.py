"""Bundle lint: errors B1-B8 and warnings BW1-BW2 (design spec section 8.8)."""
from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Sequence
from pathlib import Path

from .bundle import data_files, manual_entries, pack_items, parse_sums
from .constants import AGENT_RULES_FILE, OPERATORS, PICKLE_SUFFIXES, RUNBOOK_FILE, SUMS_FILE
from .findings import Finding
from .pack_files import generated_names
from .runbook import document_names, documents, lost_commands
from .volumes import max_file_bytes, volume_capacity

TOKEN = re.compile(rb"hf_[A-Za-z0-9]{20,}")
TOKEN_SCAN_LIMIT = 16 * 1024 * 1024  # larger files (weights, archives) are not read for tokens


def _sums(bundle: Path) -> dict[str, str] | str:
    """The digest of each path in SHA256SUMS, or why there is none to compare with."""
    path = bundle / SUMS_FILE
    if not path.is_file():
        return f"{SUMS_FILE} is missing; run pack.py again"
    try:
        return parse_sums(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return f"{SUMS_FILE} is not readable as UTF-8"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _token_files(bundle: Path, project_files: Sequence[Path]) -> list[Path]:
    found = [p for p in sorted(Path(bundle).rglob("*")) if p.is_file() and p.stat().st_size <= TOKEN_SCAN_LIMIT]
    return found + [p for p in project_files if p.is_file()]


def _is(value, kind: type) -> bool:
    return isinstance(value, kind) and not isinstance(value, bool)


def bundle_problems(bundle_data: dict) -> list[str]:
    """Why `bundle_data` cannot be checked: a field that check_bundle or the runbook reads is
    missing or of the wrong type. pack.py never writes such a file; check_bundle relies on that."""
    problems = []

    def need(owner: dict, key: str, kind: type, where: str, what: str) -> bool:
        if _is(owner.get(key), kind):
            return True
        problems.append(f"{where}{key}: missing or not {what}")
        return False

    for key in ("project", "channel"):
        need(bundle_data, key, str, "", "text")
    if bundle_data.get("operator") not in OPERATORS:
        problems.append("operator: must be one of " + ", ".join(OPERATORS))
    if bundle_data.get("volume_capacity") is not None:
        need(bundle_data, "volume_capacity", int, "", "a whole number or null")
    items = bundle_data.get("items")
    volumes = bundle_data.get("volumes")
    if not _is(items, list) or not all(isinstance(item, dict) for item in items):
        problems.append("items: missing or not a list of objects")
        items = []
    if not _is(volumes, list) or not all(isinstance(volume, dict) for volume in volumes):
        problems.append("volumes: missing or not a list of objects")
        volumes = []
    for index, item in enumerate(items):
        where = f"items[{index}]."
        need(item, "id", str, where, "text")
        need(item, "kind", str, where, "text")
        need(item, "source", dict, where, "an object")
        skipped = item.get("status") == "not_needed"
        if skipped:
            need(item, "reason", str, where, "text")
        if skipped or item.get("kind") == "manual":
            need(item, "name", str, where, "text")
        if not need(item, "files", list, where, "a list"):
            continue
        if item.get("kind") == "manual" and item["files"] and not skipped:
            need(item, "path", str, where, "text")
        for number, entry in enumerate(item["files"]):
            if not isinstance(entry, dict):
                problems.append(f"{where}files[{number}]: not an object")
                continue
            for key, kind, what in (("path", str, "text"), ("size", int, "a whole number"), ("sha256", str, "text")):
                need(entry, key, kind, f"{where}files[{number}].", what)
    for index, volume in enumerate(volumes):
        where = f"volumes[{index}]."
        need(volume, "number", int, where, "a whole number")
        need(volume, "bytes", int, where, "a whole number")
        if not need(volume, "units", list, where, "a list"):
            continue
        for number, unit in enumerate(volume["units"]):
            if not isinstance(unit, dict):
                problems.append(f"{where}units[{number}]: not an object")
                continue
            need(unit, "path", str, f"{where}units[{number}].", "text")
            need(unit, "size", int, f"{where}units[{number}].", "a whole number")
    return problems


def check_bundle(
    bundle: Path,
    state: dict,
    bundle_data: dict,
    manifest: dict,
    *,
    operator: str,
    channel: str,
    deep: bool = False,
    project_files: Sequence[Path] = (),
    environ: dict | None = None,
) -> list[Finding]:
    """The findings for a packed bundle. `operator` and `channel` are the blueprint's current
    inside.operator and transfer.channel; B5 reports a bundle packed for others."""
    bundle = Path(bundle)
    environ = os.environ if environ is None else environ
    findings: list[Finding] = []
    packed = {item["id"]: item for item in bundle_data.get("items", [])}
    manual = manual_entries(state)

    # B1: every item has its files, or is a manual item marked not needed with a reason.
    for item in pack_items(state):
        if item["kind"] == "manual":
            entry = manual.get(item["name"])
            if entry is None:
                findings.append(Finding("B1", f"{item['id']}: not settled; add files under manual/ or mark it not needed with a reason"))
                continue
            if entry.get("status") == "not_needed":
                continue
        record = packed.get(item["id"])
        if record is None or not record.get("files"):
            findings.append(Finding("B1", f"{item['id']}: not in bundle.json; fetch it and run pack.py again"))
            continue
        for entry in record["files"]:
            if not (bundle / entry["path"]).is_file():
                findings.append(Finding("B1", f"{item['id']}: {entry['path']} is missing"))

    # B2: every file has a line in SHA256SUMS and the size bundle.json gives. The files pack.py
    # writes are small, so their hashes are always compared: verify.sh checks them too.
    sums = _sums(bundle)
    if isinstance(sums, str):
        findings.append(Finding("B2", sums))
        sums = None
    for entry in data_files(bundle_data):
        path = bundle / entry["path"]
        if sums is not None and sums.get(entry["path"]) != entry["sha256"]:
            findings.append(Finding("B2", f"{entry['path']}: no matching line in {SUMS_FILE}"))
        elif path.is_file() and path.stat().st_size != entry["size"]:
            findings.append(Finding("B2", f"{entry['path']}: {path.stat().st_size} bytes, bundle.json says {entry['size']}"))
        elif deep and path.is_file() and _sha256(path) != entry["sha256"]:
            findings.append(Finding("B2", f"{entry['path']}: its SHA-256 differs from {SUMS_FILE}"))
    wanted = document_names(operator)  # B7 reports these when they are missing
    for name in generated_names(bundle_data):
        path = bundle / name
        if not path.is_file():
            if name not in wanted:
                findings.append(Finding("B2", f"{name} is missing; run pack.py again"))
        elif sums is None:
            continue
        elif name not in sums:
            findings.append(Finding("B2", f"{name}: no line in {SUMS_FILE}; run pack.py again"))
        elif _sha256(path) != sums[name]:
            fix = ("after translating it, run pack.py --refresh-sums, else run pack.py again"
                   if name in (RUNBOOK_FILE, AGENT_RULES_FILE) else "run pack.py again")
            findings.append(Finding("B2", f"{name}: its SHA-256 differs from {SUMS_FILE}; {fix}"))

    # B3: no file on a volume is larger than the channel allows.
    limit = max_file_bytes(channel, state["answers"])
    for volume in bundle_data.get("volumes", []):
        for unit in volume["units"]:
            if limit is not None and unit["size"] > limit:
                findings.append(
                    Finding("B3", f"volume {volume['number']}: {unit['path']} is {unit['size']:,} bytes; the channel allows {limit:,}")
                )

    # B4: every volume fits the medium minus the reserve, as transfer.json gives it now.
    capacity = volume_capacity(channel, state["answers"])
    for volume in bundle_data.get("volumes", []):
        if capacity is not None and volume["bytes"] > capacity:
            findings.append(
                Finding("B4", f"volume {volume['number']}: {volume['bytes']:,} bytes; the medium holds {capacity:,} after the reserve")
            )

    # B5: the bundle was made from the project's current manifest.
    if bundle_data.get("manifest_digest") != manifest.get("inputs_digest"):
        findings.append(Finding("B5", "bundle.json was made from another transfer manifest; run plan.py, fetch.sh and pack.py again"))
    for key, label, now in (("operator", "inside.operator", operator), ("channel", "transfer.channel", channel)):
        if bundle_data.get(key) != now:
            findings.append(Finding(
                "B5", f"bundle.json was packed for {label} {bundle_data.get(key)}; the blueprint now says {now}; run pack.py again"))

    # B6: pickle-based weights need the user's explicit permission.
    for record in bundle_data.get("items", []):
        if record["kind"] == "model" and not record.get("allow_pickle"):
            for entry in record["files"]:
                if entry["path"].endswith(PICKLE_SUFFIXES):
                    findings.append(Finding("B6", f"{entry['path']}: pickle-based weights without the user's permission"))

    # B7: the runbook or agent rules that inside.operator calls for.
    expected = documents({**bundle_data, "operator": operator}, manifest)
    for name in wanted:
        path = bundle / name
        if not path.is_file():
            findings.append(Finding("B7", f"{name} is missing; inside.operator is {operator}"))
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(Finding("B7", f"{name} is not readable as UTF-8"))
            continue
        lost = lost_commands(expected[name], text)
        if lost:
            findings.append(Finding("B7", f"{name} lacks the command line(s): " + "; ".join(lost)))

    # B8: nothing that looks like a token.
    secret = environ.get("HF_TOKEN", "")
    for path in _token_files(bundle, project_files):
        where = path.relative_to(bundle).as_posix() if bundle in path.parents else str(path)
        try:
            data = path.read_bytes()
        except OSError:
            findings.append(Finding("B8", f"{where} cannot be read; check it by hand"))
            continue
        if TOKEN.search(data) or (len(secret) >= 8 and secret.encode() in data):
            findings.append(Finding("B8", f"{where} holds a value that looks like a token; remove it"))

    # BW1 and BW2.
    for record in bundle_data.get("items", []):
        if record["kind"] == "package" and not record["source"].get("checksums"):
            findings.append(
                Finding("BW1", f"{record['id']}: the publisher has no checksum file; its hash was first computed on the connected side")
            )
        if record["kind"] == "image" and not record["source"].get("digest"):
            findings.append(Finding("BW2", f"{record['id']}: no digest recorded"))
    return findings
