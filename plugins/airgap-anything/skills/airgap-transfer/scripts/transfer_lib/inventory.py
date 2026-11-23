"""INVENTORY.md and INVENTORY.csv: what the people who approve the transfer read."""
from __future__ import annotations

import csv
import io

from .bundle import data_files

COLUMNS = ("path", "size", "sha256", "kind", "component", "version", "source", "licence", "pickle")


def _source_text(item: dict) -> str:
    source = item["source"]
    if item["kind"] == "image":
        return f"{source['ref']} {source.get('digest') or '(no digest recorded)'}"
    if item["kind"] == "package":
        return source["url"]
    if item["kind"] == "model":
        if source.get("source") == "huggingface":
            return f"huggingface {source['repo']} at {source['revision']}"
        return f"local folder {source.get('path', '')}"
    return "added by the user"


def _licence(item: dict) -> str:
    if item["kind"] == "model":
        names = [entry["path"].rsplit("/", 1)[-1] for entry in item["files"]]
        licences = [name for name in names if name.upper().startswith(("LICENSE", "LICENCE"))]
        return "see " + ", ".join(sorted(set(licences))) if licences else "not stated: no licence file in the model folder"
    if item["kind"] == "manual":
        return "as supplied by the user"
    return item.get("license") or "not stated"


def rows(bundle_data: dict) -> list[dict]:
    """One row per file, largest first: scanning hundreds of gigabytes takes time."""
    owner = {}
    for item in bundle_data["items"]:
        for entry in item["files"]:
            owner.setdefault(entry["path"], (item, entry))
    result = []
    for entry in data_files(bundle_data):
        item, own = owner[entry["path"]]
        result.append(
            {
                "path": entry["path"],
                "size": entry["size"],
                "sha256": entry["sha256"],
                "kind": item["kind"],
                "component": item.get("component") or item.get("name", ""),
                "version": item.get("version", ""),
                "source": _source_text(item),
                "licence": _licence(item),
                "pickle": "pickle, allowed by the user" if own.get("pickle") else "",
            }
        )
    return sorted(result, key=lambda row: (-row["size"], row["path"]))


def render_csv(bundle_data: dict) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows(bundle_data))
    return buffer.getvalue()


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(bundle_data: dict) -> str:
    table = rows(bundle_data)
    total = sum(row["size"] for row in table)
    lines = [
        f"# Transfer inventory: {bundle_data['project']}",
        "",
        f"- Made from the transfer manifest with digest {bundle_data['manifest_digest']}",
        f"- Platform: {bundle_data['platform']}",
        f"- Channel: {bundle_data['channel']}",
        f"- Files: {len(table)}, {total:,} bytes in all, on {len(bundle_data['volumes'])} volume(s)",
        f"- Packed: {bundle_data['packed']}",
        "",
        "Every file is listed with its SHA-256, largest first. Model weights are safetensors unless the "
        "pickle column says the user allowed pickle files. Publisher checksum files were checked on the "
        "connected side where the publisher has one; publisher signatures are not checked by this version.",
        "",
        "| Path | Size | SHA-256 | Kind | Component | Version | Source | Licence | Pickle |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    lines += ["| " + " | ".join(_cell(row[key]) for key in COLUMNS) + " |" for row in table]
    skipped = [item for item in bundle_data["items"] if item.get("status") == "not_needed"]
    lines += ["", "## Not carried", ""]
    lines += [f"- {item['name']}: {item['reason']}" for item in skipped] or ["Nothing: every item is carried."]
    return "\n".join(lines) + "\n"
