"""The item list of a transfer: one item per image, model, package and manual item."""
from __future__ import annotations

import re

from .questions import include_benchmark

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_name(text: str) -> str:
    """A file or folder name from free text: letters, digits, '.', '_' and '-' only."""
    name = _UNSAFE.sub("_", str(text)).strip("._-")
    return name or "item"


def image_archive(component: str, ref: str) -> str:
    """Bundle path of an image archive, relative to the bundle folder."""
    return f"images/{safe_name(component)}/{safe_name(ref)}.tar"


def _unique(path: str, taken: set[str]) -> str:
    candidate, number = path, 2
    while candidate in taken:
        candidate, number = f"{path}-{number}", number + 1
    taken.add(candidate)
    return candidate


def manual_items(manifest: dict, keep_benchmark: bool = True) -> list[dict]:
    """Custom parts and runtime downloads of the manifest, as items the user settles by hand."""
    items = []
    for row in manifest.get("custom", []):
        items.append(
            {
                "kind": "manual",
                "name": row["name"],
                "text": f"A custom part of the {row.get('layer') or 'design'} layer, outside the catalog.",
            }
        )
    counts: dict[str, int] = {}
    for row in manifest.get("runtime_downloads", []):
        if row.get("benchmark") and not keep_benchmark:
            continue
        counts[row["component"]] = counts.get(row["component"], 0) + 1
        items.append(
            {
                "kind": "manual",
                "name": f"{row['component']}: runtime download {counts[row['component']]}",
                "text": row["text"],
            }
        )
    return items


def build_items(manifest: dict, answers: dict) -> list[dict]:
    """Every item of the plan, each with a unique `id` and a bundle `path`."""
    keep_benchmark = include_benchmark(answers)
    sources = answers.get("models") or {}
    items: list[dict] = []
    taken: set[str] = set()
    for row in manifest.get("images", []):
        if row.get("benchmark") and not keep_benchmark:
            continue
        items.append(
            {
                "id": f"image:{row['component']}:{row['ref']}",
                "kind": "image",
                "component": row["component"],
                "version": row["version"],
                "ref": row["ref"],
                "digest": row.get("digest", ""),
                "license": row.get("license", ""),
                "benchmark": bool(row.get("benchmark")),
                "path": _unique(image_archive(row["component"], row["ref"]), taken),
            }
        )
    for row in manifest.get("models", []):
        source = dict(sources.get(row["name"]) or {})
        items.append(
            {
                "id": f"model:{row['name']}",
                "kind": "model",
                "name": row["name"],
                "role": row.get("role", ""),
                "source": {key: source[key] for key in ("source", "repo", "revision", "path") if key in source},
                "allow_pickle": source.get("allow_pickle") is True,
                "path": _unique(f"models/{safe_name(row['name'])}", taken),
            }
        )
    for row in manifest.get("packages", []):
        if row.get("benchmark") and not keep_benchmark:
            continue
        items.append(
            {
                "id": f"package:{row['component']}:{row['file']}",
                "kind": "package",
                "component": row["component"],
                "version": row["version"],
                "file": row["file"],
                "arch": row["arch"],
                "url": row["url"],
                "checksums": row.get("checksums", ""),
                "license": row.get("license", ""),
                "benchmark": bool(row.get("benchmark")),
                "path": _unique(f"packages/{safe_name(row['component'])}/{safe_name(row['file'])}", taken),
            }
        )
    for item in manual_items(manifest, keep_benchmark):
        items.append(
            dict(item, id=f"manual:{item['name']}", path=_unique(f"manual/{safe_name(item['name'])}", taken))
        )
    return items


def checksums_path(item: dict) -> str | None:
    """Where fetch.sh keeps the publisher's checksum file of a package item."""
    url = item.get("checksums") or ""
    if item.get("kind") != "package" or not url:
        return None
    return f"packages/{safe_name(item['component'])}/checksums/{safe_name(url.rsplit('/', 1)[-1])}"
