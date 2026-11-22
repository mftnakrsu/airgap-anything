"""The transfer manifest: everything that has to be carried into the network."""
from __future__ import annotations

from .blueprint import benchmark_components, chosen_components, decisions_of, inputs_digest
from .catalog import Catalog
from .constants import GPU_VENDORS
from .sizing import SizingInputError, pick_primary_gpu

MANIFEST_FILENAME = "transfer-manifest.md"
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


def _for_hardware(image: dict, hardware: str | None) -> bool:
    return hardware is None or "hardware" not in image or hardware in image["hardware"]


def render_manifest(blueprint: dict, catalog: Catalog, generated: str) -> str:
    chosen_ids = chosen_components(blueprint)
    benchmark_ids = benchmark_components(blueprint)
    unknown = [cid for cid in chosen_ids + benchmark_ids if cid not in catalog.components]
    if unknown:
        raise UnknownComponentError(unknown)
    # Benchmark components follow the chosen ones; their rows carry a marker in the
    # Component cell, so a reader cannot take them for part of the design.
    entries = [(catalog.components[cid], catalog.components[cid]["id"]) for cid in chosen_ids]
    entries += [
        (catalog.components[cid], catalog.components[cid]["id"] + BENCHMARK_MARK)
        for cid in benchmark_ids
    ]
    custom = [
        name for decision in decisions_of(blueprint) for name in decision.get("custom") or []
    ]
    models = (blueprint.get("answers") or {}).get("workload.models") or []
    hardware = hardware_class(blueprint.get("answers"), catalog)

    images, packages, telemetry, downloads, skills = [], [], [], [], []
    missing_variant = []
    for entry, label in entries:
        airgap = entry.get("airgap", {})
        component_images = airgap.get("images", [])
        wanted = [image for image in component_images if _for_hardware(image, hardware)]
        if component_images and not wanted:
            missing_variant.append(
                f"- {label}: the catalog lists no image for {hardware} hardware; "
                "check the entry's notes before carrying."
            )
        for image in wanted:
            _, remainder = split_image_ref(image["ref"])
            images.append(
                [
                    label,
                    entry["version"],
                    image["ref"],
                    ", ".join(image["hardware"]) if "hardware" in image else "any",
                    image.get("digest", ""),
                    "",
                    f"{REGISTRY_TOKEN}/{remainder}",
                ]
            )
        for package in airgap.get("packages", []):
            packages.append([label, entry["version"], package])
        for item in airgap.get("telemetry", []):
            telemetry.append([label, item["what"], item["disable"]])
        for download in airgap.get("runtime_downloads", []):
            downloads.append([label, download])
        for skill in entry.get("deeper_skills", []):
            skills.append([label, skill["repo"], skill["skill"]])
    for name in custom:
        packages.append([f"custom: {name}", "", "enumerate artifacts manually"])

    model_rows = [
        [
            model.get("name") or f"model {index + 1}",
            model.get("role", ""),
            "weights, tokenizer and configuration files",
            "",
        ]
        for index, model in enumerate(models)
        if isinstance(model, dict)
    ]

    lines = [
        f"# Transfer manifest: {blueprint.get('project', '')}",
        "",
        f"- Generated: {generated}",
        f"{DIGEST_PREFIX}{inputs_digest(blueprint)}",
        "- Hardware: "
        + (
            hardware
            if hardware
            else "unknown; carry only the image rows for your hardware"
        ),
        "",
        "Fill the digest, size and checksum columns when you pull each artifact. "
        f"Replace `{REGISTRY_TOKEN}` with the address of the registry inside the network.",
        "",
        "## 1. Container images",
        "",
    ]
    lines += _table(
        ["Component", "Version", "Image", "For", "Digest", "Size", "Target path"], images
    )
    if missing_variant:
        lines += [*missing_variant, ""]
    lines += ["## 2. Model artifacts", ""]
    lines += _table(["Model", "Role", "Files to carry", "SHA-256"], model_rows)
    lines += ["## 3. Packages and binaries", ""]
    lines += _table(["Component", "Version", "Artifact"], packages)
    lines += ["## 4. Telemetry and egress settings to switch off before first start", ""]
    lines += _table(["Component", "What", "Setting"], telemetry)
    lines += ["## 5. Runtime downloads to stage in advance", ""]
    lines += _table(["Component", "Download"], downloads)
    lines += ["## 6. Per-tool skills worth carrying inside", ""]
    lines += _table(["Component", "Repository", "Skill"], skills)
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
