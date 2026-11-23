"""Build a transfer scenario on disk: a finished architect project, and with --fetched a
fake fetched bundle of small files, so that pack.py, check.py and verify.sh run without
downloads. Used by tests/test_transfer_scenarios.py and by the behavior runs of evals/README.md.

    python3 evals/transfer_fixture.py --scenario department --out DIR [--variant fat32] [--fetched]

DIR gets project/ (docs/airgap/blueprint.json, both manifest files, transfer.json) and,
with --fetched, bundle/. Standard library only; the architect side is made by
airgap-architect's own scripts with the shipped catalog.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = REPO_ROOT / "evals" / "transfer-scenarios"
ARCHITECT = REPO_ROOT / "plugins" / "airgap-anything" / "skills" / "airgap-architect" / "scripts"
FAT32_MAX_FILE_BYTES = 4 * 1024**3 - 1
LAYERS = ("llm-serving", "llm-gateway", "ui", "identity", "observability", "orchestration", "state", "registry")


def blueprint_of(scenario: dict) -> dict:
    decisions = []
    for layer in LAYERS:
        chosen = scenario["decisions"].get(layer, {})
        decision = {
            "layer": layer,
            "components": list(chosen.get("components", [])),
            "existing": list(chosen.get("existing", [])),
            "custom": list(chosen.get("custom", [])),
            "rationale": f"Scenario fixture for {layer}.",
            "alternatives_considered": [],
            "evidence": "estimate",
            "override": None,
        }
        if chosen.get("benchmark"):
            decision["benchmark"] = list(chosen["benchmark"])
        decisions.append(decision)
    return {
        "schema_version": 1,
        "project": scenario["project"],
        "created": "2026-11-22",
        "language": scenario.get("language", "en"),
        "blueprint_path": "docs/airgap/blueprint.md",
        "answers": scenario["answers"],
        "assumptions": [],
        "tier": {},
        "sizing": {},
        "decisions": decisions,
    }


def build(name: str, out: Path, variant: str | None = None, fetched: bool = False) -> tuple[Path, Path]:
    folder = SCENARIOS / name
    scenario = json.loads((folder / "architect.json").read_text(encoding="utf-8"))
    project, bundle = Path(out) / "project", Path(out) / "bundle"
    target = project / "docs" / "airgap" / "blueprint.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(blueprint_of(scenario), indent=2) + "\n", encoding="utf-8")
    for script, extra in (("tier.py", []), ("size.py", []), ("manifest.py", ["--date", "2026-11-22"])):
        subprocess.run([sys.executable, "-B", str(ARCHITECT / script), "--blueprint", str(target), *extra],
                       check=True, capture_output=True, text=True)
    if not fetched:
        return project, bundle
    sys.path.insert(0, str(REPO_ROOT))
    import tests  # noqa: F401  (puts both skills' scripts on sys.path)
    from tests.transfer_projects import fake_fetch, settle_manual, write_state
    from transfer_lib.inputs import channel_of
    from transfer_lib.items import build_items

    answers = json.loads((folder / f"transfer{'-' + variant if variant else ''}.json").read_text(encoding="utf-8"))
    answers["bundle.path"] = str(bundle.resolve())
    bundle.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((target.parent / "transfer-manifest.json").read_text(encoding="utf-8"))
    blueprint = json.loads(target.read_text(encoding="utf-8"))
    items = build_items(manifest, answers)
    plan = {"items": items, "tools": {}, "platform": manifest["platform"], "channel": channel_of(blueprint),
            "planned": "2026-11-22T10:00:00Z"}
    write_state(project, answers, plan=plan)
    fake_fetch(bundle, items)
    if variant == "fat32":
        # One model file one byte over the FAT32 limit, as a sparse file: it takes no room.
        model = next(item for item in items if item["kind"] == "model")
        weights = bundle / model["path"] / "model.safetensors"
        with weights.open("r+b") as handle:
            handle.truncate(FAT32_MAX_FILE_BYTES + 1)
    settle_manual(project)
    return project, bundle


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--scenario", required=True, choices=sorted(p.name for p in SCENARIOS.iterdir() if p.is_dir()))
    parser.add_argument("--out", required=True)
    parser.add_argument("--variant")
    parser.add_argument("--fetched", action="store_true")
    args = parser.parse_args(argv)
    project, bundle = build(args.scenario, Path(args.out), args.variant, args.fetched)
    print(f"project: {project}")
    if args.fetched:
        print(f"bundle: {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
