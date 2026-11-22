"""The transfer manifest: everything that has to be carried into the network.

`build_manifest` collects the rows once; `render_markdown` and `render_json` write the
same rows as transfer-manifest.md, for people, and transfer-manifest.json, for the
airgap-transfer skill, which reads the JSON file and never imports this package.
"""
from __future__ import annotations

import json

from .blueprint import benchmark_components, chosen_components, decisions_of, inputs_digest
from .catalog import Catalog
from .constants import CPU_ARCHES, GPU_VENDORS
from .sizing import SizingInputError, pick_primary_gpu

MANIFEST_FILENAME = "transfer-manifest.md"
MANIFEST_JSON_FILENAME = "transfer-manifest.json"
MANIFEST_JSON_SCHEMA_VERSION = 1
DIGEST_PREFIX = "- Decisions digest: "
REGISTRY_TOKEN = "REGISTRY_HOST"
BENCHMARK_MARK = " (benchmark only)"


class UnknownComponentError(Exception):
    def __init__(self, component_ids: list[str]):
        super().__init__("unknown component(s): " + ", ".join(component_ids))
        self.component_ids = list(component_ids)


def split_image_ref(ref: str) -> tuple[str, str]:
    """Split 'registry.example/repo/name:tag' into (registry, 'repo/name:tag')."""
    first, slash, rest = ref.partition("/")
    if slash and ("." in first or ":" in first or first == "localhost"):
        return first, rest
    return "", ref


def read_manifest_digest(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(DIGEST_PREFIX):
            return line[len(DIGEST_PREFIX):].strip()
    return None


def read_manifest_json_digest(text: str) -> str | None:
    """The inputs digest recorded in transfer-manifest.json, or None."""
    try:
        data = json.loads(text)
    except (ValueError, RecursionError):
        return None
    digest = data.get("inputs_digest") if isinstance(data, dict) else None
    return digest if isinstance(digest, str) else None


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    if not rows:
        return ["None.", ""]
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(_cell(cell) for cell in row) + " |" for row in rows]
    lines.append("")
    return lines


def hardware_class(answers: dict, catalog: Catalog) -> str | None:
    """'cpu' without GPUs, else the vendor of the primary GPU; None when unknown."""
    entries = (answers or {}).get("hardware.gpus")
    if not isinstance(entries, list):
        return None
    if not entries:
        return "cpu"
    try:
        primary = pick_primary_gpu(entries, catalog.gpu)
    except (SizingInputError, KeyError, TypeError):
        return None
    if primary is None:
        return None
    for entry in entries:
        if entry["model"] == primary["model"] and entry["count"] == primary["count"]:
            if entry.get("vendor") in GPU_VENDORS:
                return entry["vendor"]
            break
    row = catalog.gpu(primary["model"]) or {}
    return row.get("vendor") if row.get("vendor") in GPU_VENDORS else None


def cpu_arch(answers: dict, catalog: Catalog) -> str | None:
    """The answer to hardware.cpu_arch; for 'unknown' the default in rules.toml.

    None when the question is unanswered or holds something else, so that the
    manifest lists every package row instead of guessing.
    """
    value = (answers or {}).get("hardware.cpu_arch")
    if value == "unknown":
        default = catalog.rules.default_answer("hardware.cpu_arch")
        value = default.get("value") if default else None
    return value if value in CPU_ARCHES else None


def _for_hardware(image: dict, hardware: str | None) -> bool:
    return hardware is None or "hardware" not in image or hardware in image["hardware"]


def _for_arch(package: dict, arch: str | None) -> bool:
    return arch is None or package["arch"] in (arch, "any")


def build_manifest(blueprint: dict, catalog: Catalog, generated: str) -> dict:
    """Every row of the manifest, in the shape of transfer-manifest.json."""
    chosen_ids = chosen_components(blueprint)
    benchmark_ids = benchmark_components(blueprint)
    unknown = [cid for cid in chosen_ids + benchmark_ids if cid not in catalog.components]
    if unknown:
        raise UnknownComponentError(unknown)
    entries = [(catalog.components[cid], False) for cid in chosen_ids]
    entries += [(catalog.components[cid], True) for cid in benchmark_ids]
    answers = blueprint.get("answers")
    hardware = hardware_class(answers, catalog)
    arch = cpu_arch(answers, catalog)

    data = {
        "schema_version": MANIFEST_JSON_SCHEMA_VERSION,
        "project": blueprint.get("project", ""),
        "generated": generated,
        "inputs_digest": inputs_digest(blueprint),
        "hardware_class": hardware or "",
        "platform": f"linux/{arch}" if arch else "",
        "images": [],
        "models": [],
        "packages": [],
        "custom": [],
        "telemetry": [],
        "runtime_downloads": [],
        "skills": [],
        "missing_variants": [],
    }
    for entry, benchmark in entries:
        cid = entry["id"]
        label = cid + (BENCHMARK_MARK if benchmark else "")
        airgap = entry.get("airgap", {})
        component_images = airgap.get("images", [])
        wanted = [image for image in component_images if _for_hardware(image, hardware)]
        if component_images and not wanted:
            data["missing_variants"].append(
                f"{label}: the catalog lists no image for {hardware} hardware; "
                "check the entry's notes before carrying."
            )
        for image in wanted:
            _, remainder = split_image_ref(image["ref"])
            data["images"].append(
                {
                    "component": cid,
                    "version": entry["version"],
                    "ref": image["ref"],
                    "hardware": list(image.get("hardware", [])),
                    "digest": image.get("digest", ""),
                    "target": f"{REGISTRY_TOKEN}/{remainder}",
                    "license": entry["license"],
                    "benchmark": benchmark,
                }
            )
        component_packages = airgap.get("packages", [])
        packages = [package for package in component_packages if _for_arch(package, arch)]
        if component_packages and not packages:
            data["missing_variants"].append(
                f"{label}: the catalog lists no package for linux/{arch}; "
                "check the entry's notes before carrying."
            )
        for package in packages:
            data["packages"].append(
                {
                    "component": cid,
                    "version": entry["version"],
                    "file": package["file"],
                    "arch": package["arch"],
                    "url": package["url"],
                    "checksums": package.get("checksums", ""),
                    "license": entry["license"],
                    "benchmark": benchmark,
                }
            )
        for item in airgap.get("telemetry", []):
            data["telemetry"].append(
                {"component": cid, "what": item["what"], "disable": item["disable"], "benchmark": benchmark}
            )
        for download in airgap.get("runtime_downloads", []):
            data["runtime_downloads"].append({"component": cid, "text": download, "benchmark": benchmark})
        for skill in entry.get("deeper_skills", []):
            data["skills"].append(
                {"component": cid, "repo": skill["repo"], "skill": skill["skill"], "benchmark": benchmark}
            )
    for decision in decisions_of(blueprint):
        for name in decision.get("custom") or []:
            data["custom"].append({"layer": decision.get("layer", ""), "name": name})
    models = ((answers or {}).get("workload.models") if isinstance(answers, dict) else None) or []
    for index, model in enumerate(models if isinstance(models, list) else []):
        if isinstance(model, dict):
            data["models"].append(
                {"name": model.get("name") or f"model {index + 1}", "role": model.get("role", "")}
            )
    return data


def _label(row: dict) -> str:
    return row["component"] + (BENCHMARK_MARK if row.get("benchmark") else "")


def render_markdown(data: dict) -> str:
    """transfer-manifest.md from the rows of build_manifest."""
    arch = data["platform"]
    lines = [
        f"# Transfer manifest: {data['project']}",
        "",
        f"- Generated: {data['generated']}",
        f"{DIGEST_PREFIX}{data['inputs_digest']}",
        "- Hardware: "
        + (data["hardware_class"] or "unknown; carry only the image rows for your hardware"),
        "- Platform: "
        + (arch or "unknown; carry only the package rows for your CPU architecture"),
        "",
        "Fill the digest, size and checksum columns when you pull each artifact, or let the "
        "airgap-transfer skill do it from transfer-manifest.json. "
        f"Replace `{REGISTRY_TOKEN}` with the address of the registry inside the network.",
        "",
        "## 1. Container images",
        "",
    ]
    images = [
        [
            _label(row),
            row["version"],
            row["ref"],
            ", ".join(row["hardware"]) or "any",
            row["digest"],
            "",
            row["target"],
        ]
        for row in data["images"]
    ]
    lines += _table(["Component", "Version", "Image", "For", "Digest", "Size", "Target path"], images)
    image_gaps = [line for line in data["missing_variants"] if "lists no image for" in line]
    if image_gaps:
        lines += [f"- {line}" for line in image_gaps] + [""]
    lines += ["## 2. Model artifacts", ""]
    lines += _table(
        ["Model", "Role", "Files to carry", "SHA-256"],
        [[row["name"], row["role"], "weights, tokenizer and configuration files", ""] for row in data["models"]],
    )
    lines += ["## 3. Packages and binaries", ""]
    packages = [
        [_label(row), row["version"], row["file"], row["arch"], row["url"], row["checksums"]]
        for row in data["packages"]
    ]
    packages += [
        [f"custom: {row['name']}", "", "enumerate artifacts manually", "", "", ""] for row in data["custom"]
    ]
    lines += _table(["Component", "Version", "File", "Arch", "URL", "Checksums"], packages)
    package_gaps = [line for line in data["missing_variants"] if "lists no package for" in line]
    if package_gaps:
        lines += [f"- {line}" for line in package_gaps] + [""]
    lines += ["## 4. Telemetry and egress settings to switch off before first start", ""]
    lines += _table(
        ["Component", "What", "Setting"],
        [[_label(row), row["what"], row["disable"]] for row in data["telemetry"]],
    )
    lines += ["## 5. Runtime downloads to stage in advance", ""]
    lines += _table(["Component", "Download"], [[_label(row), row["text"]] for row in data["runtime_downloads"]])
    lines += ["## 6. Per-tool skills worth carrying inside", ""]
    lines += _table(
        ["Component", "Repository", "Skill"],
        [[_label(row), row["repo"], row["skill"]] for row in data["skills"]],
    )
    lines += [
        "## 7. Verification steps",
        "",
        "1. On the connected side, record a SHA-256 checksum for every file and the digest of every image.",
        "2. Verify publisher signatures where the publisher provides them.",
        "3. After the transfer, recompute every checksum inside the network before importing anything.",
        "4. Import only artifacts whose checksums match, then set the items in section 4 before first start.",
        "",
    ]
    return "\n".join(lines)


def render_json(data: dict) -> str:
    """transfer-manifest.json from the rows of build_manifest."""
    return json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def render_manifest(blueprint: dict, catalog: Catalog, generated: str) -> str:
    """transfer-manifest.md for a blueprint."""
    return render_markdown(build_manifest(blueprint, catalog, generated))
