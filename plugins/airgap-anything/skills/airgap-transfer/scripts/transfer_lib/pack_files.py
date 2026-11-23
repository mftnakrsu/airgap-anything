"""The files pack.py writes into the bundle folder, and the copy onto one medium."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from .bundle import data_files, parts_text, sums_text, volumes_text, write_json
from .constants import (
    AGENT_RULES_FILE,
    BUNDLE_JSON,
    INSIDE_SCRIPTS,
    INVENTORY_CSV,
    INVENTORY_MD,
    PARTS_FILE,
    RUNBOOK_FILE,
    SEND_ORDER_FILE,
    SUMS_FILE,
    VOLUME_LABEL,
    VOLUMES_FILE,
)
from .hashing import CHUNK
from .inventory import render_csv, render_markdown
from .runbook import documents
from .tools import COMMANDS, TEMPLATE_COMMANDS

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


def render_template(name: str) -> str:
    """The template with each {{key}} of TEMPLATE_COMMANDS replaced by its command line."""
    text = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    for key in TEMPLATE_COMMANDS:
        text = text.replace("{{" + key + "}}", COMMANDS[key].line)
    return text


def write_generated(bundle: Path, bundle_data: dict, manifest: dict) -> list[str]:
    """Write every generated file and SHA256SUMS; return the generated names, SHA256SUMS last."""
    bundle = Path(bundle)
    write_json(bundle / BUNDLE_JSON, bundle_data)
    texts = {
        PARTS_FILE: parts_text(bundle_data),
        VOLUMES_FILE: volumes_text(bundle_data),
        INVENTORY_MD: render_markdown(bundle_data),
        INVENTORY_CSV: render_csv(bundle_data),
    }
    texts.update(documents(bundle_data, manifest))
    for name in (RUNBOOK_FILE, AGENT_RULES_FILE, SEND_ORDER_FILE):
        if name not in texts:
            (bundle / name).unlink(missing_ok=True)
    for name, text in texts.items():
        (bundle / name).write_text(text, encoding="utf-8")
    for name in INSIDE_SCRIPTS:
        (bundle / name).write_text(render_template(name), encoding="utf-8")
    generated = [BUNDLE_JSON, *texts, *INSIDE_SCRIPTS]
    if bundle_data["channel"] == "data_diode":
        order = [BUNDLE_JSON, SUMS_FILE, SEND_ORDER_FILE] + [n for n in generated if n != BUNDLE_JSON]
        order += [unit["path"] for volume in bundle_data["volumes"] for unit in volume["units"]]
        (bundle / SEND_ORDER_FILE).write_text("\n".join(order) + "\n", encoding="utf-8")
        generated.append(SEND_ORDER_FILE)
    entries = [(entry["path"], entry["sha256"]) for entry in data_files(bundle_data)]
    for name in generated:
        entries.append((name, hashlib.sha256((bundle / name).read_bytes()).hexdigest()))
    (bundle / SUMS_FILE).write_text(sums_text(entries), encoding="utf-8")
    return generated + [SUMS_FILE]


class WriteError(Exception):
    """A volume cannot be written: wrong number, target, or not enough room. Exit 2."""


def _copy_range(source: Path, start: int, size: int, target: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as reader, target.open("wb") as writer:
        reader.seek(start)
        left = size
        while left:
            chunk = reader.read(min(CHUNK, left))
            if not chunk:
                raise WriteError(f"{source} is shorter than bundle.json says; run pack.py again")
            writer.write(chunk)
            digest.update(chunk)
            left -= len(chunk)
    return digest.hexdigest()


def _read_back(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_volume(bundle: Path, bundle_data: dict, number: int, target: Path, generated: list[str]) -> list[str]:
    """Copy volume `number` to `target`, cutting parts on the way, and read every file back.

    Returns the paths whose read-back hash differs (empty when the volume is good).
    """
    bundle, target = Path(bundle).resolve(), Path(target).resolve()
    volumes = bundle_data["volumes"]
    if not 1 <= number <= len(volumes):
        raise WriteError(f"there is no volume {number}; this bundle has {len(volumes)}")
    if not target.is_dir():
        raise WriteError(f"{target} is not a folder; mount the medium and give its folder")
    if target == bundle or bundle in target.parents:
        raise WriteError(f"{target} is inside the bundle folder; give the folder of the medium")
    volume = volumes[number - 1]
    extra = sum((bundle / name).stat().st_size for name in generated)
    if shutil.disk_usage(target).free < volume["bytes"] + extra:
        raise WriteError(f"{target} has less free space than volume {number} needs ({volume['bytes'] + extra:,} bytes)")
    part_size = bundle_data["part_size"]
    bad = []
    for unit in volume["units"]:
        destination = target / unit["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if unit["of"]:
            index = int(unit["path"].rsplit(".part", 1)[1])
            copied = _copy_range(bundle / unit["of"], (index - 1) * part_size, unit["size"], destination)
        else:
            copied = _copy_range(bundle / unit["path"], 0, unit["size"], destination)
        if copied != unit["sha256"]:
            raise WriteError(f"{unit['of'] or unit['path']} changed after pack.py hashed it; run pack.py again")
        if _read_back(destination) != unit["sha256"]:
            bad.append(unit["path"])
    for name in generated:
        shutil.copyfile(bundle / name, target / name)
        if _read_back(target / name) != _read_back(bundle / name):
            bad.append(name)
    (target / VOLUME_LABEL).write_text(f"volume {number} of {len(volumes)}\n", encoding="utf-8")
    return bad
