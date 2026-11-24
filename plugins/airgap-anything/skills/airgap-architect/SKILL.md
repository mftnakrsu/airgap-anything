---
name: airgap-architect
description: Designs systems for air-gapped, offline and on-premises networks from a sourced catalog instead of memory. Use when designing, planning or sizing a system that must run in an air-gapped, offline, disconnected or on-premises network - choosing an LLM inference engine or gateway, working out how many GPUs or servers a number of users or departments needs, or listing what has to be carried into the network - before any deployment file is written
---

# Airgap Architect

## Overview

Turn a short interview about an organization into a blueprint for a system that runs without internet access: one decision per layer, GPU sizing with its arithmetic shown, the reason for each choice, and the list of everything to carry in.

Why the skill exists: from memory, versions, image names and hardware numbers come out plausible but unsourced, and a wrong one is found only inside the network, where nothing can be downloaded to fix it. So every component, version and image reference here comes from `catalog/`, and every number from the procedure in `references/sizing.md`, written out so that anyone can check it.

Paths in this skill are relative to the folder that holds this file. `docs/` and `AGENTS.md` are in the user's project.

## When to use

- A system must run where there is no internet: air-gapped, offline, disconnected, classified, or on-premises with restricted egress.
- Someone asks which inference engine or gateway to run, how many GPUs a headcount needs, or what has to be carried into the network.

Not for operating one specific tool: each catalog entry names per-tool skills for that. Not for cloud designs. Packing and carrying the artifacts is the `airgap-transfer` skill.

## Workflow

Copy this checklist into your reply and tick it off as you go:

```
Air-gap design:
- [ ] 1. Interview
- [ ] 2. Tier and floors
- [ ] 3. Sizing
- [ ] 4. One decision per layer
- [ ] 5. Transfer manifest
- [ ] 6. Blueprint
- [ ] 7. AGENTS.md block
- [ ] 8. Self-review, until every item holds
- [ ] 9. Hand-off, then wait for approval
```

1. **Interview.** Read `references/interview.md`. One question per message; skip what the user or their files already said.
2. **Tier and floors.** Read `references/tiers.md`. The tier comes from users and departments only; some answers raise single layers.
3. **Sizing.** Read `references/sizing.md` and `references/gpus.md`. Follow the steps for every model and write each step's numbers into the sizing section.
4. **Decisions.** Read `references/layers/llm-serving.md`, `references/layers/llm-gateway.md` and `references/layers/supporting-defaults.md`, and the catalog entry of every component you consider. All eight layers get a decision: `llm-serving`, `llm-gateway`, `ui`, `identity`, `observability`, `orchestration`, `state`, `registry`.
5. **Transfer manifest.** Read `references/transfer-manifest-template.md` and write `docs/airgap/transfer-manifest.md` from the chosen entries.
6. **Blueprint.** Fill `references/blueprint-template.md` at the blueprint's path.
7. **AGENTS.md.** Add the block of `references/agents-snippet.md`.
8. **Self-review.** Check every item below; fix what fails and check again.
9. **Hand-off.** Show the blueprint path, the tier, the concurrency range and the GPU total, the eight decisions in one line each and the open questions, then the step after approval from the table below. Stop until the user approves.

## Where the blueprint goes

| Situation | Blueprint path | After the user approves |
|---|---|---|
| `superpowers:writing-plans` is available | `docs/superpowers/specs/YYYY-MM-DD-PROJECT-airgap-blueprint-design.md` | Invoke `superpowers:writing-plans` with that file |
| Superpowers is not installed | `docs/airgap/blueprint.md` | Give the next steps yourself: carry the artifacts in with `airgap-transfer`, install, benchmark |
| `superpowers:brainstorming` is already running (it started before this skill) | As in the first row | Run one interview, not two: brainstorming owns the rhythm and the approval gates; this skill supplies the questions, the references and the template, and the self-review becomes part of its spec review |

## The catalog

One file per component. Read an entry before you choose its component; it holds the version, the images, the telemetry to switch off, what it downloads at runtime, the caveats and the sources.

| Layer | Entries |
|---|---|
| `llm-serving` | `catalog/vllm.md`, `catalog/sglang.md`, `catalog/ollama.md` |
| `llm-gateway` | `catalog/litellm.md`, `catalog/kong.md` |
| `ui` | `catalog/open-webui.md` |
| `identity` | `catalog/keycloak.md` |
| `observability` | `catalog/prometheus.md`, `catalog/grafana.md` |
| `orchestration` | `catalog/docker-compose.md`, `catalog/k3s.md`, `catalog/rke2.md` |
| `state` | `catalog/postgresql.md`, `catalog/valkey.md` |
| `registry` | `catalog/harbor.md`, `catalog/distribution-registry.md` |

Every entry and every rule carries an evidence label: `field` (measured in a real deployment), `docs` (read in the official documentation, with the URL), `estimate` (the design's judgment). A decision takes the weakest label among its inputs; a decision with a custom part is `estimate`.

## Rules

1. **Components, versions and image references come from the catalog**, never from memory, even when you are sure. A plausible tag that does not exist costs a trip back to the connected side. A part with no catalog entry is a custom part, labelled `estimate`.
2. **Numbers come from the sizing procedure**, with every step written out. Give concurrency as a range, list the assumptions, and put a benchmark step in every blueprint: memory arithmetic says whether a model fits, not how fast it runs.
3. **Before the user approves the blueprint, write nothing outside `docs/` and `AGENTS.md`, and install or download nothing.** No Compose file, no `.env`, no scripts. Deployment files fix decisions the user has not seen yet, and a hardware order based on them is hard to undo. A throwaway calculation in a temporary folder outside the project is fine; it is not part of the design.
4. **Going below a floor, or accepting hardware that does not fit, is the user's decision.** Record it as an override with the user's reason.

## Self-review

Before the hand-off, check each item against the files you wrote. When one fails, fix it and check all of them again.

1. Each of the eight layers has a decision with a rationale and at least one alternative considered; where the catalog has no other option, the alternative reads "no other `LAYER` option in the catalog".
2. Each component is in `catalog/`, belongs to that layer, and its `Tiers` row includes the layer's floor, or the decision records the user's override.
3. Each chosen component's `Requires` is chosen in its own layer or named under Existing.
4. Each version in the blueprint's decision table matches its catalog entry exactly, and the same holds for every row of the transfer manifest.
5. Every sizing number follows from the steps shown; concurrency is a range; the assumptions table has a row for every interview answer that was `unknown` and for every constant the steps used; the hardware fits, or `llm-serving` records an override.
6. The tier's obligations are met: a gateway when one is required, the isolation design subsection for `multi_level`, at least two replicas when no downtime is accepted.
7. The verification section has the benchmark step, one entry for each decision labelled `estimate`, every benchmark engine, the Kubernetes risk when it applies, and every chosen entry last verified more than 180 days ago.
8. The transfer manifest lists the images for the design's hardware class and the packages for its platform, and every telemetry setting, runtime download and per-tool skill of each chosen entry, none left out; the blueprint's transfer section copies the telemetry settings.
9. Each decision's evidence is the weakest label among its guide's case and its components.

## Common mistakes

| Mistake | Instead |
|---|---|
| Working out GPU counts in your head and giving the result | Follow `references/sizing.md` step by step and write each step's numbers down |
| Giving one GPU number ("Buy 8 GPUs, in one server. That is the number for your manager.") | Give the concurrency range, the assumptions and the benchmark step |
| Recommending a step that needs internet (a first check that runs "`docker run --rm --gpus all <any cuda image> nvidia-smi`" before anything is carried in) | A step on the air-gapped side uses only what the transfer manifest lists |
| Leaving out a layer because nothing is deployed there | Every layer gets a decision and a rationale; "none" is a decision |
| Naming a component with no reason or no alternative ("`vLLM` is the only service that uses the GPUs") | Fill the rationale and the alternatives of every decision, as its layer guide says |
| Describing the artifacts in prose ("Load them from removable media with `docker load` and pin the tags.") or leaving image tags blank | Write the transfer manifest: every image, package and model to carry in, copied from the catalog |
| Saying only "No outbound connections from any host" | Copy each component's telemetry and egress settings from the manifest into the blueprint |
| Keeping departments apart only in the UI while they share one engine with prefix caching on | Read the engine entry's prefix-cache caveat and say in the `llm-serving` rationale which separation the design uses |
| "We are short on time, skip the questions and give me the Compose file" | Ask only what is missing, finish the blueprint, and stop for approval: a Compose file written now fixes decisions the user has not seen |
