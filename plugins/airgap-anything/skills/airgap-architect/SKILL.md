---
name: airgap-architect
description: Use when designing, planning or sizing a system that must run in an air-gapped, offline, disconnected or on-premises network - choosing an LLM inference engine or gateway, working out how many GPUs or servers a number of users or departments needs, or listing what has to be carried into the network - before any deployment file is written
---

# Airgap Architect

## Overview

Turn a short interview about an organization into a blueprint for a system that runs without internet access: one decision per layer, GPU sizing, the reason for each choice, and the list of everything to carry in.

You judge trade-offs. Scripts do the arithmetic and the checking. Every component, version and number in a blueprint comes from the catalog or from a script, never from memory.

## When to use

- A system must run where there is no internet: air-gapped, offline, disconnected, classified, or on-premises with restricted egress.
- Someone asks which inference engine or gateway to run, how many GPUs a headcount needs, or what has to be transferred into the network.

Not for operating one specific tool; catalog entries name the per-tool skills for that. Not for cloud designs.

## The pipeline

Work through the steps in order. Read a step's reference file when you reach the step. Paths to `references/`, `scripts/` and `catalog/` are relative to the skill root, the folder that holds this SKILL.md; `docs/` and `AGENTS.md` are in the project root.

| # | Step | What you do | Read |
|---|---|---|---|
| 1 | Interview | Fill `answers`, one question per message | `references/interview.md` |
| 2 | Tier | Run `tier.py` | `references/tiers.md` |
| 3 | Sizing | Run `size.py` | `references/sizing.md` |
| 4 | Decisions | Write one decision per layer into `decisions` | `references/layers/llm-serving.md`, `references/layers/llm-gateway.md`, `references/layers/supporting-defaults.md` |
| 5 | Transfer manifest | Run `manifest.py`; it is the list of what to carry in | |
| 6 | Blueprint | Set `blueprint_path`, then write the blueprint file | `references/blueprint-template.md` |
| 7 | Agent instructions | Add the block to `AGENTS.md`, with the inside-agent rules when `inside.operator` names an agent | `references/agents-snippet.md` |
| 8 | Lint | Run `lint.py`; fix and repeat until it exits 0 | |
| 9 | Hand-off | Show the blueprint and the step that follows approval (third column of the table below), then stop until the user approves | "Blueprint path and superpowers" below |

The state of one design lives in `docs/airgap/blueprint.json`. Scripts write their results into it. To change a result, change an answer or a decision there and run the scripts again; a changed decision also needs `manifest.py` again.

## Scripts

`${CLAUDE_SKILL_DIR}` is the folder that holds this SKILL.md. Claude Code fills it in only when it loads the skill itself. If you see `${CLAUDE_SKILL_DIR}` written out rather than a path, put the path of the folder that holds this SKILL.md in its place before you run a command; the variable is not set in the shell. The scripts need Python 3.11 or newer and nothing else. Run them from the project root, so that `docs/airgap/blueprint.json` resolves:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/tier.py" --blueprint docs/airgap/blueprint.json
python3 "${CLAUDE_SKILL_DIR}/scripts/size.py" --blueprint docs/airgap/blueprint.json
python3 "${CLAUDE_SKILL_DIR}/scripts/manifest.py" --blueprint docs/airgap/blueprint.json
python3 "${CLAUDE_SKILL_DIR}/scripts/lint.py" --blueprint docs/airgap/blueprint.json
```

`manifest.py` writes `docs/airgap/transfer-manifest.md` and `docs/airgap/transfer-manifest.json` next to `blueprint.json`; the JSON file is what the `airgap-transfer` skill reads. `lint.py` reads `blueprint_path` and `AGENTS.md` relative to `--project-root` (default `.`); from another directory, pass `--project-root` with the project root. Each script lists its other options with `--help`.

| Exit code | Meaning | What you do |
|---|---|---|
| 0 | Done | Continue |
| 1 | `lint.py` found errors (E1 to E11) | Fix each one and run it again |
| 2 | An answer is missing or invalid, `blueprint.json` cannot be read, or, in `manifest.py`, a decision names a component that is not in the catalog | Go back to the question or decision the message names |
| 3 | Python is older than 3.11, or the catalog cannot be read | Stop and tell the user |

`lint.py` reports a component that is not in the catalog as error E2, exit 1. Warnings (W1 to W4) and notes (N1) do not change the exit code.

## Decisions

Write one object per layer into `decisions`, for all eight layers: `llm-serving`, `llm-gateway`, `ui`, `identity`, `observability`, `orchestration`, `state`, `registry`. A decision may name more than one component, for example `prometheus` and `grafana`, or `docker-compose` next to `k3s`.

```json
{
  "layer": "llm-gateway",
  "components": ["litellm"],
  "existing": [],
  "custom": [],
  "rationale": "Four departments need separate keys and budgets; audit logging is mandatory.",
  "alternatives_considered": ["kong"],
  "evidence": "estimate",
  "override": null
}
```

| Field | Holds |
|---|---|
| `components` | List of catalog IDs to deploy. The catalog is `${CLAUDE_SKILL_DIR}/catalog/components/`. An ID that is not there does not go here. |
| `existing` | List of strings: infrastructure that already runs and is reused. |
| `custom` | List of strings: a part with no catalog entry. Either something the user insists on, or something the design needs that the catalog lacks (Docker Engine on the Harbor host, the vector database and shared storage of a multi-replica UI; see `references/layers/supporting-defaults.md`). It counts as an estimate. |
| `rationale` | Why this choice; not empty. |
| `alternatives_considered` | List of strings: the options you weighed and passed over. |
| `evidence` | The weakest label among the table row and the chosen components' catalog entries; `estimate` when `custom` is not empty. Weakest to strongest: `estimate`, `docs`, `field`. |
| `override` | `null`, or `{ "reason": "..." }` when the user knowingly goes below a floor or accepts hardware that does not fit. |

A decision may also carry `benchmark`: a list of catalog IDs that are carried in only to be measured against the decision's choice, never deployed, so not in `components`. `references/layers/llm-serving.md` says when to use it. `manifest.py` lists those components marked "(benchmark only)", so the transfer manifest stays the one list of what to carry in.

## Blueprint path and superpowers

| Situation | Blueprint path | After the user approves |
|---|---|---|
| `superpowers:writing-plans` is available | `docs/superpowers/specs/`, then the date, the project name and `-airgap-blueprint-design.md`, for example `docs/superpowers/specs/2026-11-20-example-airgap-blueprint-design.md` | Invoke `superpowers:writing-plans` with that file |
| Superpowers is not installed | `docs/airgap/blueprint.md` | Print the next steps yourself: transfer with `airgap-transfer`, install, benchmark |
| `superpowers:brainstorming` is already running, because it started before this skill; this skill does not start it | As in the first row | Run one interview, not two. Brainstorming owns the rhythm and the approval gates; this skill supplies the questions, tables, scripts and template. Run `lint.py` as part of the spec self-review. |

The interview starts the blueprint with `"blueprint_path": ""`, and lint rejects an empty value. Set it to the path above in `blueprint.json` before you write the blueprint.

## Rules

1. Every number in the blueprint is copied from `blueprint.json`. To get a different number, change an answer and run the script. The one exception is a what-if (`references/sizing.md`): its numbers are `size.py`'s output on a copy, labelled as a what-if, and never in place of the design's own.
2. Every component, version and image name comes from the catalog. Do not supply one from memory, even when you are sure of it.
3. A blueprint is finished only when `lint.py` exits 0. Do not present one with open errors as done.
4. Before the user approves the blueprint, write nothing outside `docs/` and `AGENTS.md`, and install or download nothing. No Compose file, no `.env`, no scripts.
5. Sizing does not predict throughput. Every blueprint carries a benchmark step.

## Common mistakes

| Mistake | Instead |
|---|---|
| Working out GPU counts yourself | Run `size.py` and quote its output |
| Recommending a hosted service or a step that needs internet (a first check that runs "`docker run --rm --gpus all <any cuda image> nvidia-smi`" before anything is carried in) | Use catalog components only; each entry records what it downloads. A step on the air-gapped side uses only what the transfer manifest lists |
| Leaving out a layer because nothing is deployed there | Every layer gets a decision and a rationale |
| Giving one GPU number ("Buy 8 GPUs, in one server. That is the number for your manager.") | Give the range, the assumptions and the benchmark step |
| Naming a component with no reason or no alternative ("`vLLM` is the only service that uses the GPUs", nothing else said) | Fill `rationale` and `alternatives_considered` of every decision, as the layer's reference file says |
| Describing the artifacts in prose ("Load them from removable media with `docker load` and pin the tags.") or leaving image tags blank | Run `manifest.py`. Its output is the list: images, packages and model files to carry in. Link it from the transfer section |
| Saying only "No outbound connections from any host" and naming no telemetry setting for any component | Section 4 of the transfer manifest lists, per component, the telemetry and egress settings to switch off before first start. Copy them into the transfer section of the blueprint |
| Keeping departments apart only in the UI ("Each has its own database and its own AD group filter, so departments cannot see each other's chats.") while they share one engine with `--enable-prefix-caching` | When `org.isolation` is not `none` and departments share an engine, read the caveat on its prefix cache in the engine's catalog entry (`vllm`, `sglang`), and say in the `llm-serving` rationale which separation the design uses |
