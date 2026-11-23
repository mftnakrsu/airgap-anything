"""pack.py's work: the files of every item, their hashes, the volume plan and bundle.json."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from .archive import ArchiveError, read_image_archive
from .constants import BUNDLE_SCHEMA_VERSION, CONNECTED_ONLY, FETCH_STATE_DIR, PICKLE_SUFFIXES
from .hashing import hash_file, part_count
from .items import checksums_path
from .volumes import MAX_PARTS, assign_volumes, part_size, units_of, volume_capacity

PARTIAL_SUFFIX = ".download"  # what fetch.sh calls a download that has not finished
MANUAL_DIR = "manual"
# verify.sh reads SHA256SUMS and VOLUMES.txt line by line with `read`: a name with a control
# character or a backslash, or a path part with space at either end, would not survive that.
_UNSAFE_PATH = re.compile(r"[\x00-\x1f\x7f\\]")


class PackError(Exception):
    """The bundle cannot be packed as it is; `problems` says why. pack.py exits 2."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = list(problems)


def _hidden(parts) -> bool:
    return any(part.startswith(".") for part in parts)


def _files_under(bundle: Path, relative: str, within: Path | None = None) -> list[str]:
    """Bundle paths of the files at or below `relative`, leaving out dot-files, dot-folders
    (such as the .cache/ that `hf download --local-dir` leaves) and partial downloads.
    With `within`, a file that resolves outside that folder raises PackError."""
    root = bundle / relative
    if within is not None:
        outside = [path for path in ([root] if root.is_file() else Path(root).rglob("*"))
                   if path.is_file() and not _inside(path.resolve(), within.resolve())]
        if outside:
            raise PackError([f"{path.relative_to(bundle).as_posix()}: resolves to {path.resolve()}, outside "
                             f"{within.resolve()}; copy the file itself under manual/" for path in outside])
    if root.is_file():
        return [] if relative.endswith(PARTIAL_SUFFIX) else [relative]
    if not root.is_dir():
        return []
    found = []
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(name for name in dirs if not name.startswith("."))
        for name in names:
            path = Path(folder) / name
            if name.startswith(".") or name.endswith(PARTIAL_SUFFIX) or not path.is_file():
                continue
            found.append(path.relative_to(bundle).as_posix())
    return sorted(found)


def manual_entries(state: dict) -> dict[str, dict]:
    return {entry["item"]: entry for entry in state.get("manual", []) if isinstance(entry, dict)}


def pack_items(state: dict) -> list[dict]:
    """The plan's items plus manual items the user added that the manifest did not name."""
    items = [dict(item) for item in state["plan"]["items"]]
    named = {item["name"] for item in items if item["kind"] == "manual"}
    for name, entry in manual_entries(state).items():
        if name not in named and entry.get("status") == "added":
            items.append({"id": f"manual:{name}", "kind": "manual", "name": name,
                          "text": entry.get("text", "Added by the user."), "path": entry["path"]})
    return items


def item_files(bundle: Path, item: dict, state: dict) -> list[str]:
    """The bundle paths that belong to `item`; empty when its files are missing."""
    if item["kind"] == "image":
        if not (bundle / item["path"]).is_file():
            return []
        companions = [str(Path(item["path"]).with_suffix(suffix)) for suffix in (".digest", ".id")]
        return [item["path"]] + [p for p in companions if (bundle / p).is_file()]
    if item["kind"] == "package":
        listed = checksums_path(item)
        files = [item["path"]] if (bundle / item["path"]).is_file() else []
        if files and listed and (bundle / listed).is_file():
            files.append(listed)
        return files
    if item["kind"] == "manual":
        entry = manual_entries(state).get(item["name"], {})
        return _files_under(bundle, entry["path"], bundle / MANUAL_DIR) if entry.get("status") == "added" else []
    return _files_under(bundle, item["path"])


def _inside(path: Path, root: Path) -> bool:
    return root in path.parents


def manual_path_problems(bundle: Path, entry: dict) -> list[str]:
    """An added manual item must lie inside <bundle>/manual/, and so must every link at or
    under it. manual/ itself must be a real folder. A link to a file that stays inside
    manual/ is allowed; a link to a folder below the added path is refused, because the
    walk does not follow it."""
    bundle = Path(bundle)
    where = f"manual:{entry['item']}: {entry['path']}"
    if (bundle / MANUAL_DIR).is_symlink():
        return [f"{where}: {bundle / MANUAL_DIR} is a link to {(bundle / MANUAL_DIR).resolve()}; "
                "make manual/ a real folder in the bundle folder"]
    root = (bundle / MANUAL_DIR).resolve()
    given = bundle / entry["path"]
    start = given.resolve()
    if not _inside(start, root):
        return [f"{where} lies outside {root}; put the files in a folder under manual/ and name that folder"]
    problems = []
    if start.is_dir():
        for folder, dirs, names in os.walk(start):
            for name in [*dirs, *names]:
                path = Path(folder) / name
                if path.is_symlink() and (path.is_dir() or not _inside(path.resolve(), root)):
                    shown = given / path.relative_to(start)
                    problems.append(f"{where}: {shown.relative_to(bundle).as_posix()} is a link to "
                                    f"{path.resolve()}; copy the file itself under manual/")
    return problems


def leftovers(bundle: Path) -> list[str]:
    """Partial downloads that fetch.sh left: the fetch has not finished."""
    found = []
    for folder, dirs, names in os.walk(bundle):
        dirs[:] = sorted(name for name in dirs if name != FETCH_STATE_DIR)
        found += [(Path(folder) / name).relative_to(bundle).as_posix() for name in names if name.endswith(PARTIAL_SUFFIX)]
    return [f"{path}: a partial download left by fetch.sh; run sh fetch.sh again until it ends "
            "without failures, or delete the file" for path in sorted(found)]


def unsettled(bundle: Path, state: dict) -> list[str]:
    """Items that have neither their files nor, for a manual item, a 'not needed' reason;
    added manual items outside manual/; partial downloads."""
    bundle = Path(bundle)
    problems = []
    manual = manual_entries(state)
    for item in pack_items(state):
        where = item["path"]
        if item["kind"] == "manual":
            entry = manual.get(item["name"])
            if entry is None:
                problems.append(f"{item['id']}: not settled; add its files under manual/ or mark it not needed with a reason")
                continue
            if entry.get("status") == "not_needed":
                continue
            where = entry["path"]
            found = manual_path_problems(bundle, entry)
            if found:
                problems += found
                continue
        if not item_files(bundle, item, state):
            problems.append(f"{item['id']}: no files at {where}")
    return problems + leftovers(bundle)


def _source(bundle: Path, item: dict) -> dict:
    if item["kind"] == "image":
        digest_file = (bundle / item["path"]).with_suffix(".digest")
        digest = digest_file.read_text(encoding="utf-8").strip() if digest_file.is_file() else ""
        return {"ref": item["ref"], "digest": digest or item.get("digest", "")}
    if item["kind"] == "package":
        return {"url": item["url"], "checksums": item.get("checksums", "")}
    if item["kind"] == "model":
        return dict(item["source"])
    return {"text": item.get("text", "")}


def _path_problems(paths: list[str]) -> list[str]:
    return [f"{path}: a file name with a control character, a backslash or space at the end of a "
            "name; rename it" for path in paths
            if _UNSAFE_PATH.search(path) or any(part != part.strip() for part in path.split("/"))]


def _too_many_parts(sizes: dict[str, int], limit: int | None) -> list[str]:
    problems = []
    for path, size in sizes.items():
        count = part_count(size, limit)
        if count > MAX_PARTS:
            problems.append(
                f"{path}: {size:,} bytes would be cut into {count} parts of {limit:,} bytes; at most "
                f"{MAX_PARTS} are possible. Use a larger medium (medium.capacity_gb) or a larger file "
                "limit (channel.max_file_gb)"
            )
    return problems


def build_bundle(bundle: Path, state: dict, manifest: dict, blueprint_meta: dict) -> dict:
    """bundle.json for a fetched bundle: items, files, hashes and volumes.

    `blueprint_meta` holds project, channel, operator and language. Every check that can
    fail runs before the first file is hashed. Raises PackError when an item is unsettled,
    an image archive does not fit or a file would need too many parts.
    """
    bundle = Path(bundle)
    problems = unsettled(bundle, state)
    if problems:
        raise PackError(problems)
    answers = state["answers"]
    channel = blueprint_meta["channel"]
    limit = part_size(channel, answers)
    capacity = volume_capacity(channel, answers)
    platform = state["plan"]["platform"]
    manual = manual_entries(state)
    records = []
    for item in pack_items(state):
        entry = manual.get(item["name"]) if item["kind"] == "manual" else None
        record = {key: item[key] for key in ("id", "kind", "component", "version", "name", "license", "benchmark") if key in item}
        record["source"] = _source(bundle, item)
        if entry and entry.get("status") == "not_needed":
            record.update(status="not_needed", reason=entry["reason"], files=[])
        elif item["kind"] == "image":
            try:
                image = read_image_archive(bundle / item["path"])
            except ArchiveError as error:
                problems.append(str(error))
            else:
                if image["platform"] != platform:
                    problems.append(f"{item['path']}: holds an image for {image['platform']}, not {platform}; fetch it again")
                record["source"]["image_id"] = image["id"]
        if item["kind"] == "model":
            record["allow_pickle"] = item.get("allow_pickle", False)
        if entry and entry.get("status") == "added":
            record["path"] = entry["path"]
        records.append((item, record))
    if problems:
        raise PackError(problems)
    for item, record in records:
        if item["kind"] == "image":
            (bundle / item["path"]).with_suffix(".id").write_text(record["source"]["image_id"] + "\n", encoding="utf-8")
    sizes: dict[str, int] = {}
    for item, record in records:
        if record.get("status") != "not_needed":
            record["files"] = item_files(bundle, item, state)
            for path in record["files"]:
                sizes.setdefault(path, (bundle / path).stat().st_size)
    problems = _path_problems(list(sizes)) + _too_many_parts(sizes, limit)
    if problems:
        raise PackError(problems)
    hashed: dict[str, tuple[str, list[str]]] = {path: hash_file(bundle / path, limit) for path in sorted(sizes)}
    items = []
    for item, record in records:
        if record.get("status") != "not_needed":
            record["files"] = [
                {"path": path, "size": sizes[path], "sha256": hashed[path][0],
                 "pickle": item["kind"] == "model" and path.endswith(PICKLE_SUFFIXES)}
                for path in record["files"]
            ]
        items.append(record)
    files = [{"path": path, "size": sizes[path], "sha256": hashed[path][0], "parts": hashed[path][1]} for path in sorted(sizes)]
    try:
        units = units_of(files, limit)
    except ValueError as error:
        raise PackError([str(error)]) from None
    volumes = assign_volumes(units, capacity)
    where: dict[str, list[int]] = {}
    for number, volume in enumerate(volumes, start=1):
        for unit in volume:
            where.setdefault(unit["of"] or unit["path"], []).append(number)
    for record in items:
        for entry in record["files"]:
            entry["volumes"] = sorted(set(where.get(entry["path"], [])))
    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "project": blueprint_meta["project"],
        "manifest_digest": manifest["inputs_digest"],
        "platform": platform,
        "channel": channel,
        "operator": blueprint_meta["operator"],
        "language": blueprint_meta["language"],
        "packed": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "part_size": limit,
        "volume_capacity": capacity,
        "items": items,
        "volumes": [
            {"number": number, "bytes": sum(unit["size"] for unit in volume),
             "units": [{"path": u["path"], "size": u["size"], "sha256": u["sha256"], "of": u["of"]} for u in volume]}
            for number, volume in enumerate(volumes, start=1)
        ],
    }


def data_files(bundle_data: dict) -> list[dict]:
    """Every original file of the bundle, once, as {path, size, sha256, ...}."""
    seen = {}
    for item in bundle_data["items"]:
        for entry in item["files"]:
            seen.setdefault(entry["path"], entry)
    return [seen[path] for path in sorted(seen)]


def parts_text(bundle_data: dict) -> str:
    lines = ["# parts sha256-of-the-whole-file path; part N is the path followed by .partNNN"]
    counts: dict[str, int] = {}
    for volume in bundle_data["volumes"]:
        for unit in volume["units"]:
            if unit["of"]:
                counts[unit["of"]] = counts.get(unit["of"], 0) + 1
    by_path = {entry["path"]: entry for entry in data_files(bundle_data)}
    lines += [f"{counts[path]} {by_path[path]['sha256']} {path}" for path in sorted(counts)]
    return "\n".join(lines) + "\n"


def volumes_text(bundle_data: dict) -> str:
    lines = ["# volume size sha256 path; a path ending in .partNNN is one part of a split file"]
    for volume in bundle_data["volumes"]:
        lines += [f"{volume['number']} {u['size']} {u['sha256']} {u['path']}" for u in volume["units"]]
    return "\n".join(lines) + "\n"


def sums_text(entries: list[tuple[str, str]]) -> str:
    """coreutils format: '<sha256>  <path>' per line."""
    return "".join(f"{digest}  {path}\n" for path, digest in sorted(entries))


def write_json(path: Path, data: dict) -> None:
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def stray_files(bundle: Path, bundle_data: dict, generated: set[str]) -> list[str]:
    """Files in the bundle folder that no item claims and pack.py did not write.
    fetch.sh, fetch.log, .fetch/ and dot-files belong to the connected side and are not listed."""
    bundle = Path(bundle)
    claimed = {entry["path"] for entry in data_files(bundle_data)} | generated
    found = []
    for folder, dirs, names in os.walk(bundle):
        dirs[:] = sorted(name for name in dirs if not name.startswith("."))
        for name in names:
            rel = (Path(folder) / name).relative_to(bundle).as_posix()
            if rel not in claimed and rel not in CONNECTED_ONLY and not _hidden(Path(rel).parts):
                found.append(rel)
    return sorted(found)
