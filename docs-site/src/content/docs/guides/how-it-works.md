---
title: How it works
description: The steps of a design, who does each one, the agent or you, and what the agent reads for it.
---

<div class="figure"><img src="/how-it-works.svg" alt="Eight steps on a connected workstation, done by the agent and you. The files cross the air gap, and the people or the agent inside build the system without internet." /></div>

The design is made outside the air-gapped network, on a machine with internet access. The files it produces cross the gap together with everything they list, and the people or the agent inside build the system from them, without internet. [Carrying it in](/guides/carrying-it-in/) covers the second skill, which packs them.

| # | Step | Who | Reads |
|---|---|---|---|
| 1 | Interview: people, departments, privacy, hardware, operations | the agent, one question at a time | [Interview](/reference/architect/interview/) |
| 2 | Tier and per-layer floors | the agent, from the tier table | [Tiers and floors](/reference/architect/tiers/) |
| 3 | GPU, server and power sizing, every step written out | the agent, from the sizing procedure | [Sizing](/reference/architect/sizing/), [GPU table](/reference/gpus/) |
| 4 | One decision per layer, from the layer guides and the catalog | the agent | [Inference engine](/reference/architect/llm-serving/), [LLM gateway](/reference/architect/llm-gateway/), [Supporting layers](/reference/architect/supporting-layers/), [Catalog](/reference/catalog/) |
| 5 | Transfer manifest | the agent, from the catalog entries | [Transfer manifest](/reference/architect/transfer-manifest-template/) |
| 6 | Blueprint, and the agent block in `AGENTS.md` | the agent | [Blueprint template](/reference/architect/blueprint-template/), [AGENTS.md block](/reference/architect/agents-snippet/) |
| 7 | Self-review against a checklist, until every item holds | the agent | [`SKILL.md`](/reference/architect/) |
| 8 | Your approval, then hand-off to an implementation plan | you | |

In `SKILL.md` the same steps are a checklist of nine items, with the `AGENTS.md` block as an item of its own. The agent copies it into its reply and ticks it off as it goes.

## The agent does the work, the skill holds the facts

`airgap-architect` is plain markdown: `SKILL.md`, a set of references and a catalog. Nothing is installed or run. The agent weighs trade-offs: which gateway fits four departments with an audit duty, whether a small team should run Kubernetes. It also does the arithmetic, following the sizing procedure step by step and writing each step's inputs and result into the blueprint, so that a reader can check every number.

What the agent must not do is fill in facts from memory. From memory, versions, image names and hardware numbers come out plausible but unsourced, and a wrong one is found only inside the network, where nothing can be downloaded to fix it. So every component, version and image reference comes from the [catalog](/reference/catalog/), every GPU's memory and power from the [GPU table](/reference/gpus/), and every number from the [sizing procedure](/reference/architect/sizing/).

## Eight layers

Every design makes one decision for each layer: `llm-serving`, `llm-gateway`, `ui`, `identity`, `observability`, `orchestration`, `state` and `registry`. The inference engine and the gateway are chosen from decision tables; the other six take per-tier defaults. A decision may reuse what you already run, such as an existing directory or registry. "None" is a decision too, with its own rationale.

## The check before approval

Before the hand-off, the agent goes through the self-review list in `SKILL.md` and checks each item against the files it wrote. When one fails, it fixes it and checks all of them again. The list asks, among other things:

- Does each of the eight layers have a decision with a rationale and at least one alternative considered?
- Is each component in the catalog, in its layer, and allowed at the layer's floor, or does the decision record your override?
- Does each version in the blueprint and in the transfer manifest match its catalog entry exactly?
- Does every sizing number follow from the steps shown, with concurrency as a range and every constant in the assumptions table?
- Are the tier's obligations met, and does the verification section have the benchmark step and every `estimate` decision?

Then the agent shows the blueprint path, the tier, the GPU range, the eight decisions in one line each and the open questions, and stops until you approve. Until then it writes nothing outside `docs/` and `AGENTS.md`, and installs or downloads nothing.
