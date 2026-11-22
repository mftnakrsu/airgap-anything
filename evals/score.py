#!/usr/bin/env python3
"""Score the decisions in a blueprint.json against a scenario's expected.json."""
import argparse
import json
from pathlib import Path


def check_layer(decision, checks):
    """Return (check name, passed) for every check of one layer."""
    components = list((decision or {}).get("components") or [])
    existing = list((decision or {}).get("existing") or [])
    custom = list((decision or {}).get("custom") or [])
    results = []
    for name, expected in checks.items():
        if name == "components":
            passed = decision is not None and sorted(components) == sorted(expected)
        elif name == "includes":
            passed = all(component_id in components for component_id in expected)
        elif name == "mentions":
            text = " ".join(components + existing).lower()
            passed = all(word.lower() in text for word in expected)
        elif name == "empty":
            is_empty = not (components or existing or custom)
            passed = decision is not None and is_empty == expected
        else:
            raise ValueError(f"unknown check '{name}'")
        results.append((name, passed))
    return results


def score(blueprint, expected):
    """Return (layer, check name, passed) for every check in expected['decisions']."""
    by_layer = {
        decision.get("layer"): decision
        for decision in blueprint.get("decisions", [])
        if isinstance(decision, dict)
    }
    rows = []
    for layer, checks in expected.get("decisions", {}).items():
        for name, passed in check_layer(by_layer.get(layer), checks):
            rows.append((layer, name, passed))
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blueprint", required=True, help="the agent's docs/airgap/blueprint.json")
    parser.add_argument("--expected", required=True, help="the scenario's expected.json")
    args = parser.parse_args(argv)
    blueprint = json.loads(Path(args.blueprint).read_text(encoding="utf-8"))
    expected = json.loads(Path(args.expected).read_text(encoding="utf-8"))
    rows = score(blueprint, expected)
    for layer, name, passed in rows:
        print(f"{'PASS' if passed else 'FAIL'}  {layer}: {name}")
    failed = sum(1 for _, _, passed in rows if not passed)
    print(f"{len(rows) - failed} of {len(rows)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
