"""Builders for synthetic catalogs and answers. No real product is named here."""
from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

from airgap_lib.catalog import Catalog, load_catalog
from airgap_lib.constants import LAYERS
from tests import CATALOG_DIR

TODAY = date(2026, 11, 20)

GPUS_TOML = """schema_version = 1

[[gpu]]
model = "Test GPU 141"
aliases = ["TG141"]
vendor = "nvidia"
vram_gb = 141
tdp_w = 700
evidence = "estimate"
notes = "Synthetic row for tests."
last_verified = 2026-11-20
"""


def component(component_id: str, layer: str, **overrides) -> dict:
    """A valid synthetic component entry. Dict overrides merge into sub-tables."""
    entry = {
        "schema_version": 1,
        "id": component_id,
        "name": component_id.title(),
        "layer": layer,
        "summary": f"Synthetic {layer} component for tests.",
        "tiers": ["T1", "T2", "T3"],
        "requires": [],
        "version": "1.2.3",
        "license": "MIT",
        "last_verified": TODAY,
        "evidence": {
            "level": "docs",
            "sources": ["https://example.test/docs"],
            "verified_by": "",
            "notes": "",
        },
        "airgap": {
            "images": [
                {"ref": f"registry.example.test/synthetic/{component_id}:1.2.3", "digest": ""}
            ],
            "packages": [],
            "runtime_downloads": [],
            "telemetry": [],
            "license_server": False,
            "notes": "",
        },
        "choose": {
            "when": ["always in tests"],
            "avoid_when": [],
            "alternatives": [],
            "caveats": [],
        },
        "deeper_skills": [],
    }
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(entry.get(key), dict):
            entry[key] = {**entry[key], **value}
        else:
            entry[key] = value
    return entry


def fixture_components() -> list[dict]:
    return [
        component("alpha-engine", "llm-serving"),
        component(
            "beta-engine",
            "llm-serving",
            tiers=["T1", "T2"],
            evidence={"level": "estimate", "sources": [], "notes": "Synthetic estimate."},
        ),
        component("gamma-gateway", "llm-gateway", requires=["delta-db"]),
        component("delta-db", "state"),
        component("epsilon-ui", "ui"),
        component("zeta-idp", "identity"),
        component("eta-metrics", "observability"),
        component("theta-orch", "orchestration"),
        component("iota-registry", "registry"),
    ]


def _toml(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{key} = {_toml(item)}" for key, item in value.items()) + " }"
    raise TypeError(f"cannot write {type(value).__name__} as TOML")


def component_toml(entry: dict) -> str:
    """Serialize a component entry the way catalog files are written."""
    lines: list[str] = []
    tables = {key: value for key, value in entry.items() if isinstance(value, dict)}
    for key, value in entry.items():
        if key != "deeper_skills" and key not in tables:
            lines.append(f"{key} = {_toml(value)}")
    for name, table in tables.items():
        lines += ["", f"[{name}]"]
        lines += [f"{key} = {_toml(value)}" for key, value in table.items()]
    for row in entry.get("deeper_skills", []):
        lines += ["", "[[deeper_skills]]"]
        lines += [f"{key} = {_toml(value)}" for key, value in row.items()]
    return "\n".join(lines) + "\n"


def make_catalog(root: Path, components=None, gpus_toml: str = GPUS_TOML, rules_toml=None) -> Path:
    """Write a catalog directory. Rules default to the shipped rules.toml."""
    root = Path(root)
    (root / "components").mkdir(parents=True, exist_ok=True)
    if rules_toml is None:
        shutil.copy(CATALOG_DIR / "rules.toml", root / "rules.toml")
    else:
        (root / "rules.toml").write_text(rules_toml, encoding="utf-8")
    (root / "gpus.toml").write_text(gpus_toml, encoding="utf-8")
    for entry in fixture_components() if components is None else components:
        path = root / "components" / f"{entry['id']}.toml"
        path.write_text(component_toml(entry), encoding="utf-8")
    return root


def load_fixture_catalog(root: Path, components=None) -> Catalog:
    catalog, findings = load_catalog(make_catalog(root, components))
    assert not findings, findings
    return catalog


def base_answers(**overrides) -> dict:
    """Complete, valid answers for a 180-person, four-department organization."""
    answers = {
        "org.users_total": 180,
        "org.departments": 4,
        "org.isolation": "per_department",
        "org.audit_required": True,
        "org.downtime_tolerance": "planned_only",
        "org.ops_capacity": "small_team",
        "org.kubernetes_experience": False,
        "workload.usage": {"chat": 1.0},
        "workload.models": [
            {"name": "example-70b", "role": "chat", "params_b": 70, "precision": "fp8"}
        ],
        "hardware.gpus": [{"model": "TG141", "count": 8}],
        "hardware.cpu_arch": "amd64",
        "existing.identity": "ad_ldap",
        "existing.api_gateway": "none",
        "existing.kubernetes": "none",
        "transfer.channel": "removable_media",
        "inside.operator": "people",
    }
    answers.update(overrides)
    return answers


def base_decisions() -> list[dict]:
    chosen = {
        "llm-serving": ["alpha-engine"],
        "llm-gateway": ["gamma-gateway"],
        "ui": ["epsilon-ui"],
        "identity": ["zeta-idp"],
        "observability": ["eta-metrics"],
        "orchestration": ["theta-orch"],
        "state": ["delta-db"],
        "registry": ["iota-registry"],
    }
    return [
        {
            "layer": layer,
            "components": list(chosen[layer]),
            "existing": [],
            "custom": [],
            "rationale": f"Synthetic rationale for {layer}.",
            "alternatives_considered": [],
            "evidence": "docs",
            "override": None,
        }
        for layer in LAYERS
    ]
