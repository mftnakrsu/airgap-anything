"""Builders for complete synthetic projects: blueprint.json and the files around it."""
from __future__ import annotations

from pathlib import Path

from airgap_lib.answers import resolve_answers
from airgap_lib.blueprint import load_blueprint, save_blueprint
from airgap_lib.catalog import Catalog
from airgap_lib.constants import (
    AGENT_BLOCK_END,
    AGENT_BLOCK_START,
    ISOLATION_MARKER,
    SECTION_MARKERS,
    section_marker,
)
from airgap_lib.sizing import compute_sizing
from airgap_lib.tiering import compute_tier
from airgap_lib.transfer import MANIFEST_FILENAME, render_manifest
from tests import support

AGENTS_TEXT = f"{AGENT_BLOCK_START}\nFollow the blueprint.\n{AGENT_BLOCK_END}\n"


def blueprint_markdown(blueprint: dict, catalog: Catalog, verification: str = "", isolation: bool = False) -> str:
    """The smallest blueprint file that satisfies lint."""
    lines: list[str] = []
    for name in SECTION_MARKERS:
        lines += [section_marker(name), f"## {name}", ""]
        if name == "decisions":
            for decision in blueprint["decisions"]:
                for component_id in decision["components"]:
                    entry = catalog.components.get(component_id)
                    version = entry["version"] if entry else "unknown"
                    lines.append(f"- {decision['layer']}: {component_id} {version}")
            if isolation:
                lines += ["", section_marker(ISOLATION_MARKER), "### Isolation design"]
        if name == "verification" and verification:
            lines.append(verification)
        lines.append("")
    return "\n".join(lines)


def build_blueprint(catalog: Catalog, answers=None, decisions=None) -> dict:
    answers = support.base_answers() if answers is None else answers
    resolved, defaults_used, problems = resolve_answers(answers, catalog.rules)
    assert not problems, problems
    sizing, constants_used = compute_sizing(resolved, catalog.rules, catalog.gpu)
    return {
        "schema_version": 1,
        "project": "example",
        "created": "2026-11-20",
        "language": "en",
        "blueprint_path": "docs/airgap/blueprint.md",
        "answers": answers,
        "assumptions": defaults_used + constants_used,
        "tier": compute_tier(resolved, catalog.rules),
        "sizing": sizing,
        "decisions": support.base_decisions() if decisions is None else decisions,
    }


def write_project(root: Path, catalog: Catalog, blueprint: dict, verification: str = "", isolation: bool = False) -> Path:
    """Write blueprint.json, the blueprint file, the manifest and AGENTS.md."""
    root = Path(root)
    path = root / "docs" / "airgap" / "blueprint.json"
    save_blueprint(path, blueprint)
    (path.parent / "blueprint.md").write_text(
        blueprint_markdown(blueprint, catalog, verification, isolation), encoding="utf-8"
    )
    (path.parent / MANIFEST_FILENAME).write_text(
        render_manifest(blueprint, catalog, "2026-11-20"), encoding="utf-8"
    )
    (root / "AGENTS.md").write_text(AGENTS_TEXT, encoding="utf-8")
    return path


def make_project(root: Path, catalog: Catalog, answers=None, decisions=None, verification: str = "", isolation: bool = False) -> Path:
    blueprint = build_blueprint(catalog, answers, decisions)
    return write_project(root, catalog, blueprint, verification, isolation)


def edit_blueprint(path: Path, change) -> dict:
    """Load blueprint.json, apply `change(data)`, save it and return it."""
    data = load_blueprint(path)
    change(data)
    save_blueprint(path, data)
    return data
