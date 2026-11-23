"""The files pack.py writes into the bundle folder, and the copy onto one medium."""
from __future__ import annotations

import hashlib
import os
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
    """A volume cannot be written: wrong number, target, not enough room, or a bundle file
    that changed or cannot be read. Exit 2."""


class MediumError(Exception):
    """Writing to or reading back from the medium failed: the medium may be faulty. Exit 1."""


def _sync_folder(folder: Path) -> None:
    """Flush a folder's entries to the medium, where the platform allows opening a folder."""
    try:
        handle = os.open(folder, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(handle)
    except OSError:
        pass
    finally:
        os.close(handle)


def _drop_cache(handle: int) -> None:
    """Ask the kernel to forget the cached pages, so that the read-back reads the medium."""
    if hasattr(os, "posix_fadvise"):
        try:
            os.posix_fadvise(handle, 0, 0, os.POSIX_FADV_DONTNEED)
        except OSError:
            pass


def _copy_range(source: Path, start: int, size: int, target: Path) -> str:
    """Copy `size` bytes of `source` from `start` to `target`, fsync it, and return the SHA-256
    of what was read from `source`."""
    digest = hashlib.sha256()
    try:
        reader = source.open("rb")
    except OSError as error:
        raise WriteError(f"cannot read {source}: {error.strerror or error}") from None
    with reader:
        try:
            writer = target.open("wb")
        except OSError as error:
            raise MediumError(f"cannot write {target}: {error.strerror or error}") from None
        with writer:
            try:
                reader.seek(start)
            except OSError as error:
                raise WriteError(f"cannot read {source}: {error.strerror or error}") from None
            left = size
            while left:
                try:
                    chunk = reader.read(min(CHUNK, left))
                except OSError as error:
                    raise WriteError(f"cannot read {source}: {error.strerror or error}") from None
                if not chunk:
                    raise WriteError(f"{source} is shorter than bundle.json says; run pack.py again")
                try:
                    writer.write(chunk)
                except OSError as error:
                    raise MediumError(f"cannot write {target}: {error.strerror or error}") from None
                digest.update(chunk)
                left -= len(chunk)
            try:
                writer.flush()
                os.fsync(writer.fileno())
                _drop_cache(writer.fileno())
            except OSError as error:
                raise MediumError(f"cannot write {target}: {error.strerror or error}") from None
    return digest.hexdigest()


def _read_back(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checked_read_back(path: Path) -> str:
    try:
        return _read_back(path)
    except OSError as error:
        raise MediumError(f"cannot read back {path}: {error.strerror or error}") from None


def _existing_size(path: Path) -> int:
    try:
        return path.stat().st_size if path.is_file() else 0
    except OSError:
        return 0


def write_volume(bundle: Path, bundle_data: dict, number: int, target: Path, generated: list[str]) -> list[str]:
    """Copy volume `number` to `target`, cutting parts on the way, and read every file back.

    Each file is fsynced before it is read back. Returns the paths whose read-back hash
    differs (empty when the volume is good). Raises WriteError for a wrong request or a
    bundle problem, MediumError when the medium cannot be written or read.
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
    try:
        sizes = {name: (bundle / name).stat().st_size for name in generated}
    except OSError as error:
        raise WriteError(f"cannot read the bundle folder: {error}") from None
    needed = volume["bytes"] + sum(sizes.values())
    # A volume written before is replaced file by file, so its old copies count as room.
    replaced = sum(_existing_size(target / unit["path"]) for unit in volume["units"])
    replaced += sum(_existing_size(target / name) for name in [*generated, VOLUME_LABEL])
    try:
        free = shutil.disk_usage(target).free
    except OSError as error:
        raise MediumError(f"cannot read the free space of {target}: {error.strerror or error}") from None
    if free + replaced < needed:
        raise WriteError(f"{target} has less free space than volume {number} needs ({needed:,} bytes)")
    part_size = bundle_data["part_size"]
    bad = []
    folders = {target}
    for unit in volume["units"]:
        destination = target / unit["path"]
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise MediumError(f"cannot make {destination.parent}: {error.strerror or error}") from None
        folders.add(destination.parent)
        if unit["of"]:
            index = int(unit["path"].rsplit(".part", 1)[1])
            copied = _copy_range(bundle / unit["of"], (index - 1) * part_size, unit["size"], destination)
        else:
            copied = _copy_range(bundle / unit["path"], 0, unit["size"], destination)
        if copied != unit["sha256"]:
            raise WriteError(f"{unit['of'] or unit['path']} changed after pack.py hashed it; run pack.py again")
        if _checked_read_back(destination) != unit["sha256"]:
            bad.append(unit["path"])
    for name in generated:
        copied = _copy_range(bundle / name, 0, sizes[name], target / name)
        if _checked_read_back(target / name) != copied:
            bad.append(name)
    try:
        (target / VOLUME_LABEL).write_text(f"volume {number} of {len(volumes)}\n", encoding="utf-8")
    except OSError as error:
        raise MediumError(f"cannot write {target / VOLUME_LABEL}: {error.strerror or error}") from None
    for folder in sorted(folders):
        _sync_folder(folder)
    return bad
