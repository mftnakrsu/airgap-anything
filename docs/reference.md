# Reference: scripts, lint codes and blueprint.json

The source of the generated pages Scripts, Lint codes and blueprint.json on the documentation site. Change the scripts, the lint rules or the state file and this file together, then run `python3 docs-site/scripts/generate_reference.py`.

## 1. Scripts

All scripts require Python 3.11 or newer, import only standard-library modules, and take `--blueprint <path>` and `--catalog <dir>` (default: the skill's own catalog).

| Script | Reads | Writes | Exit codes |
|---|---|---|---|
| `tier.py` | `answers` | `tier` | 0 ok, 2 missing or invalid answers (listed by ID), 3 environment |
| `size.py` | `answers` | `sizing`, `assumptions` | 0 ok, 2 missing or invalid answers, 3 environment |
| `manifest.py` | `decisions`, and `workload.models`, `hardware.gpus` and `hardware.cpu_arch` from `answers`, catalog | `transfer-manifest.md`, `transfer-manifest.json` | 0 ok, 2 unknown component or no `answers` object, 3 environment |
| `lint.py` | Everything | Report as text or JSON | 0 clean, 1 errors found, 3 environment |

Every script also exits 2 when `blueprint.json` cannot be read, holds a value the scripts cannot use, or, for a script that writes, cannot be written. Exit 3, environment, means that Python is older than 3.11 or that the catalog cannot be read or fails validation; the skill then stops and tells the user.

`lint.py --catalog-only` validates the catalog alone and is used in CI. It reports catalog problems as findings with exit 1; its exit 3 means that Python is too old or that the catalog folder cannot be read.

Lint errors:

| Code | Check |
|---|---|
| E1 | `blueprint.json` matches the schema |
| E2 | Every component ID in `decisions` exists in the catalog |
| E3 | Every chosen component allows the layer's floor tier, or the decision has an override with a reason |
| E4 | Every v1 layer has a decision with a rationale |
| E5 | No escalator is violated without an override |
| E6 | `tier` and `sizing` equal a fresh computation from `answers` |
| E7 | The blueprint file has all template sections, names every chosen component with its version, and has an "Isolation design" subsection when `org.isolation = multi_level` |
| E8 | Both transfer manifest files, `transfer-manifest.md` and `transfer-manifest.json`, exist and their recorded digest matches the current `decisions`, `workload.models`, `hardware.gpus` and `hardware.cpu_arch` |
| E9 | Every decision labeled `estimate` appears in the blueprint's verification section, and so does every component in a decision's `benchmark` list |
| E10 | `sizing.fits` is true, or an override explains how the gap is closed |
| E11 | Everything listed in a chosen component's `requires` is itself chosen or named in `existing` |

Lint warnings:

| Code | Check |
|---|---|
| W1 | A catalog entry used by the blueprint was last verified more than 180 days ago |
| W2 | A required answer is "unknown" and a default was used |
| W3 | The agent instruction block is missing from `AGENTS.md` |
| W4 | `inside.operator` is `local_agent` or `people_then_agent` and the agent instruction block lacks the section "Rules for an agent inside the network" |

Lint notes:

| Code | Check |
|---|---|
| N1 | A decision has an override in effect; the report repeats its reason |

## 2. `blueprint.json`

The single state file, at `docs/airgap/blueprint.json` in the target project. An abbreviated example:

```json
{
  "schema_version": 1,
  "project": "example",
  "created": "2026-11-20",
  "language": "tr",
  "blueprint_path": "docs/superpowers/specs/2026-11-20-example-airgap-blueprint-design.md",
  "answers": { "org.users_total": 180, "org.departments": 4 },
  "assumptions": [
    { "id": "sizing.chat.active", "value": 0.2, "evidence": "estimate", "note": "default" }
  ],
  "tier": {
    "base": "T2",
    "floors": { "llm-gateway": "T2", "identity": "T2" },
    "reasons": ["org.audit_required raises llm-gateway to T2"]
  },
  "sizing": { "concurrency": { "low": 9, "high": 18 }, "total_gpus": 8, "servers": 1, "power_kw": 10.1, "fits": true },
  "decisions": [
    {
      "layer": "llm-gateway",
      "components": ["litellm"],
      "existing": [],
      "custom": [],
      "rationale": "Four departments need separate keys and budgets; audit logging is mandatory.",
      "alternatives_considered": ["kong"],
      "evidence": "docs",
      "override": null
    }
  ]
}
```

- `components` holds catalog IDs to deploy; it may be empty.
- `existing` names infrastructure that is reused and not carried in.
- `custom` names components the user insists on that are not in the catalog. They are labeled `estimate` and appear in the transfer manifest as "enumerate artifacts manually".
- `benchmark` is optional: catalog IDs that are carried in only to be measured against the decision's choice and are never deployed, so they are not in `components`. `references/layers/llm-serving.md` says when an engine goes there. Lint reports a list that is not a list of strings, repeats an ID or repeats one of `components` as E1, an unknown ID as E2, and an ID that the verification section does not name as E9.
- `override` is `null` or `{ "reason": "..." }`.
