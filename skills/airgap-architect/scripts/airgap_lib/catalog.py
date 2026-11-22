"""Loading and validating the catalog: rules, GPU table, component entries."""
from __future__ import annotations

import math
import re
import tomllib
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .constants import GPU_VENDORS, HARDWARE_CLASSES, LAYERS, SCHEMA_VERSION, TIERS
from .evidence import evidence_problems
from .findings import Finding
from .rules import Rules, load_rules, validate_rules

_ID_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
_PLACEHOLDER = re.compile(r"<[^<>]+>")

_TOP_KEYS = {
    "schema_version", "id", "name", "layer", "summary", "tiers", "requires",
    "version", "license", "last_verified", "evidence", "airgap", "choose",
    "deeper_skills",
}
_EVIDENCE_KEYS = {"level", "sources", "verified_by", "notes"}
_AIRGAP_KEYS = {
    "images", "packages", "runtime_downloads", "telemetry", "license_server",
    "notes",
}
_CHOOSE_KEYS = {"when", "avoid_when", "alternatives", "caveats"}
_IMAGE_KEYS = {"ref", "digest", "hardware"}
_GPU_KEYS = {
    "model", "aliases", "vendor", "vram_gb", "tdp_w", "evidence", "sources",
    "verified_by", "notes", "last_verified",
}


@dataclass(frozen=True)
class Catalog:
    rules: Rules
    gpus: list[dict]
    components: dict[str, dict]

    def gpu(self, model: str) -> dict | None:
        """Look a GPU up by model name or alias, ignoring case and punctuation."""
        wanted = _normalize(model)
        for row in self.gpus:
            names = [row.get("model", "")] + list(row.get("aliases", []))
            if wanted in {_normalize(name) for name in names}:
                return row
        return None


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def default_catalog_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "catalog"


def load_gpus(path: Path) -> list[dict]:
    with Path(path).open("rb") as handle:
        return list(tomllib.load(handle).get("gpu", []))


def load_components(directory: Path) -> tuple[dict[str, dict], list[Finding]]:
    """Read every *.toml file. Unreadable or misnamed files become C2 findings."""
    components: dict[str, dict] = {}
    findings: list[Finding] = []
    for path in sorted(Path(directory).glob("*.toml")):
        try:
            with path.open("rb") as handle:
                entry = tomllib.load(handle)
        except tomllib.TOMLDecodeError as error:
            findings.append(Finding("C2", f"{path.name}: cannot parse ({error})"))
            continue
        except (UnicodeDecodeError, OSError) as error:
            findings.append(Finding("C2", f"{path.name}: cannot read ({error})"))
            continue
        if entry.get("id") != path.stem:
            findings.append(
                Finding("C2", f"{path.name}: id must equal the file name '{path.stem}'")
            )
            continue
        components[path.stem] = entry
    return components, findings


def load_catalog(root: Path) -> tuple[Catalog, list[Finding]]:
    root = Path(root)
    components, findings = load_components(root / "components")
    catalog = Catalog(
        rules=load_rules(root / "rules.toml"),
        gpus=load_gpus(root / "gpus.toml"),
        components=components,
    )
    return catalog, findings


def _is_plain_date(value) -> bool:
    """A TOML date. A datetime is a subclass of date but is not accepted."""
    return isinstance(value, date) and not isinstance(value, datetime)


def _strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _placeholders(value, path: str) -> list[str]:
    """Paths of string values still holding an <angle-bracket> template token."""
    if isinstance(value, str):
        return [path] if _PLACEHOLDER.fullmatch(value.strip()) else []
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found += _placeholders(item, f"{path}[{index}]")
        return found
    if isinstance(value, dict):
        found = []
        for key, item in value.items():
            found += _placeholders(item, f"{path}.{key}" if path else key)
        return found
    return []


def validate_component(entry: dict, known_ids: set[str]) -> list[Finding]:
    name = entry.get("id", "?")
    findings: list[Finding] = []

    def c1(message: str) -> None:
        findings.append(Finding("C1", f"{name}: {message}"))

    for key in sorted(set(entry) - _TOP_KEYS):
        c1(f"unknown key '{key}'")
    if entry.get("schema_version") != SCHEMA_VERSION:
        c1(f"schema_version must be {SCHEMA_VERSION}")
    if not isinstance(entry.get("id"), str) or not _ID_PATTERN.fullmatch(entry["id"]):
        c1("id must be lower-case words joined by hyphens")
    for key in ("name", "summary", "license", "version"):
        if not isinstance(entry.get(key), str) or not entry[key].strip():
            c1(f"{key} must be a non-empty string")
    if isinstance(entry.get("version"), str) and entry["version"].strip().lower() == "latest":
        c1("version must be an exact version, never 'latest'")
    if entry.get("layer") not in LAYERS:
        c1("layer must be one of " + ", ".join(LAYERS))
    tiers = entry.get("tiers")
    if (
        not _strings(tiers)
        or not tiers
        or len(set(tiers)) != len(tiers)
        or any(tier not in TIERS for tier in tiers)
    ):
        c1("tiers must be a non-empty list drawn from T1, T2, T3")
    if not _strings(entry.get("requires")):
        c1("requires must be a list of component IDs")
    if not _is_plain_date(entry.get("last_verified")):
        c1("last_verified must be a date such as 2026-11-20, unquoted and without a time")

    evidence = entry.get("evidence")
    if not isinstance(evidence, dict):
        c1("missing [evidence] table")
    else:
        for key in sorted(set(evidence) - _EVIDENCE_KEYS):
            c1(f"unknown key 'evidence.{key}'")
        for problem in evidence_problems(
            evidence.get("level"),
            evidence.get("sources"),
            evidence.get("verified_by"),
            evidence.get("notes"),
        ):
            findings.append(Finding("C4", f"{name}: {problem}"))

    airgap = entry.get("airgap")
    if not isinstance(airgap, dict):
        c1("missing [airgap] table")
    else:
        for key in sorted(set(airgap) - _AIRGAP_KEYS):
            c1(f"unknown key 'airgap.{key}'")
        images = airgap.get("images")
        if not isinstance(images, list) or any(
            not isinstance(image, dict)
            or not isinstance(image.get("ref"), str)
            or not image["ref"].strip()
            or not isinstance(image.get("digest", ""), str)
            for image in images
        ):
            c1("airgap.images must be a list of { ref, digest, hardware } tables")
        for index, image in enumerate(images if isinstance(images, list) else []):
            if not isinstance(image, dict):
                continue
            for key in sorted(set(image) - _IMAGE_KEYS):
                c1(f"unknown key 'airgap.images[{index}].{key}'")
            hardware = image.get("hardware")
            if "hardware" in image and (
                not _strings(hardware)
                or not hardware
                or len(set(hardware)) != len(hardware)
                or any(item not in HARDWARE_CLASSES for item in hardware)
            ):
                c1(
                    f"airgap.images[{index}].hardware must be a non-empty list of: "
                    + ", ".join(HARDWARE_CLASSES)
                )
        for key in ("packages", "runtime_downloads"):
            if not _strings(airgap.get(key)):
                c1(f"airgap.{key} must be a list of strings")
        telemetry = airgap.get("telemetry")
        if not isinstance(telemetry, list) or any(
            not isinstance(item, dict)
            or not isinstance(item.get("what"), str)
            or not isinstance(item.get("disable"), str)
            for item in telemetry
        ):
            c1("airgap.telemetry must be a list of { what, disable } tables")
        if not isinstance(airgap.get("license_server"), bool):
            c1("airgap.license_server must be true or false")
        if not isinstance(airgap.get("notes", ""), str):
            c1("airgap.notes must be a string")

    choose = entry.get("choose")
    if not isinstance(choose, dict):
        c1("missing [choose] table")
    else:
        for key in sorted(set(choose) - _CHOOSE_KEYS):
            c1(f"unknown key 'choose.{key}'")
        for key in sorted(_CHOOSE_KEYS):
            if not _strings(choose.get(key)):
                c1(f"choose.{key} must be a list of strings")

    skills = entry.get("deeper_skills", [])
    if not isinstance(skills, list) or any(
        not isinstance(skill, dict)
        or not isinstance(skill.get("repo"), str)
        or not isinstance(skill.get("skill"), str)
        for skill in skills
    ):
        c1("deeper_skills must be a list of { repo, skill } tables")

    for path in _placeholders(entry, ""):
        c1(f"{path} still holds a placeholder")

    references = list(entry.get("requires") or [])
    if isinstance(choose, dict):
        references += list(choose.get("alternatives") or [])
    for reference in references:
        if isinstance(reference, str) and reference not in known_ids:
            findings.append(
                Finding("C3", f"{name}: refers to unknown component '{reference}'")
            )
    return findings


def validate_gpus(gpus: list[dict]) -> list[Finding]:
    findings: list[Finding] = []
    first_use: dict[str, int] = {}
    for index, row in enumerate(gpus):
        name = f"gpus.toml: gpu[{index}]"
        for key in sorted(set(row) - _GPU_KEYS):
            findings.append(Finding("C1", f"{name}: unknown key '{key}'"))
        if not isinstance(row.get("model"), str) or not row["model"].strip():
            findings.append(Finding("C1", f"{name}: model must be a non-empty string"))
        if not _strings(row.get("aliases", [])):
            findings.append(Finding("C1", f"{name}: aliases must be a list of strings"))
        if row.get("vendor") not in GPU_VENDORS:
            findings.append(
                Finding("C1", f"{name}: vendor must be one of " + ", ".join(GPU_VENDORS))
            )
        for key, required in (("vram_gb", True), ("tdp_w", False)):
            value = row.get(key)
            if value is None and not required:
                continue
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                findings.append(Finding("C1", f"{name}: {key} must be a number above 0"))
        if not _is_plain_date(row.get("last_verified")):
            findings.append(
                Finding(
                    "C1",
                    f"{name}: last_verified must be a date such as 2026-11-20, "
                    "unquoted and without a time",
                )
            )
        for problem in evidence_problems(
            row.get("evidence"),
            row.get("sources"),
            row.get("verified_by"),
            row.get("notes"),
        ):
            findings.append(Finding("C4", f"{name}: {problem}"))
        for path in _placeholders(row, ""):
            findings.append(Finding("C1", f"{name}: {path} still holds a placeholder"))
        findings += _gpu_name_findings(row, index, name, first_use)
    return findings


def _gpu_name_findings(
    row: dict, index: int, name: str, first_use: dict[str, int]
) -> list[Finding]:
    """Names of one row (model and aliases) that are empty or taken by an earlier row.

    `first_use` maps a normalized name to the row that used it first and is
    updated here, so rows must be passed in file order.
    """
    findings: list[Finding] = []
    aliases = row.get("aliases", [])
    raw_names = [row.get("model")] + (aliases if isinstance(aliases, list) else [])
    own: set[str] = set()
    for raw in raw_names:
        if not isinstance(raw, str):
            continue
        key = _normalize(raw)
        if not key:
            findings.append(Finding("C1", f"{name}: name '{raw}' has no letters or digits"))
        elif key in own:
            continue
        elif key in first_use:
            findings.append(
                Finding(
                    "C1",
                    f"{name}: name '{raw}' is already used by gpu[{first_use[key]}]",
                )
            )
            own.add(key)
        else:
            own.add(key)
    for key in own:
        first_use.setdefault(key, index)
    return findings


def is_stale(last_verified, today: date, freshness_days: int) -> bool:
    return _is_plain_date(last_verified) and (today - last_verified).days > freshness_days


def validate_catalog(catalog: Catalog, today: date) -> list[Finding]:
    """Every check `lint.py --catalog-only` runs, apart from load errors."""
    findings = validate_rules(catalog.rules)
    findings += validate_gpus(catalog.gpus)
    known = set(catalog.components)
    for component_id in sorted(catalog.components):
        findings += validate_component(catalog.components[component_id], known)
    if catalog.rules.has("lint.freshness_days"):
        limit = catalog.rules.value("lint.freshness_days")
        for component_id in sorted(catalog.components):
            entry = catalog.components[component_id]
            if is_stale(entry.get("last_verified"), today, limit):
                findings.append(
                    Finding(
                        "W1",
                        f"{component_id}: last verified {entry['last_verified']}, "
                        f"more than {limit} days ago",
                    )
                )
    return findings
