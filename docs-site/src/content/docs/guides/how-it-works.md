---
title: How it works
description: The eight steps of a design, and who does each one, the model, the scripts or you.
---

<div class="figure"><img src="/how-it-works.svg" alt="Eight steps on a connected workstation, done by the model, the scripts and you. The files cross the air gap, and the people or the agent inside build the system without internet." /></div>

The design is made outside the air-gapped network, on a machine with internet access. The files it produces cross the gap together with everything they list, and the people or the agent inside build the system from them, without internet.

| # | Step | Who |
|---|---|---|
| 1 | Interview: people, departments, privacy, hardware, operations | the agent, one question at a time |
| 2 | Tier and per-layer floors | `tier.py` |
| 3 | GPU, server and power sizing | `size.py` |
| 4 | One decision per layer, from decision tables and the catalog | the agent |
| 5 | Transfer manifest | `manifest.py` |
| 6 | Blueprint, and the agent block in `AGENTS.md` | the agent |
| 7 | Consistency check | `lint.py` |
| 8 | Your approval, then hand-off to an implementation plan | you |

## The model judges, the scripts compute

The agent weighs trade-offs: which gateway fits four departments with an audit duty, whether a small team should run Kubernetes. Arithmetic and checking are left to [four scripts](/reference/scripts/) that use only the Python standard library. Every component, version and number in a blueprint comes from the [catalog](/reference/catalog/) or from a script, never from the model's memory.

## Eight layers

Every design makes one decision for each layer: `llm-serving`, `llm-gateway`, `ui`, `identity`, `observability`, `orchestration`, `state` and `registry`. The inference engine and the gateway are chosen from decision tables; the other six take per-tier defaults. A decision may reuse what you already run, such as an existing directory or registry.

## The check before approval

`lint.py` compares the blueprint with the catalog and with a fresh run of the scripts. It catches a component that is not in the catalog, a layer without a rationale, a tier or sizing that no longer matches the answers, and a manifest older than the decisions. [Lint codes](/reference/lint-codes/) lists every check.
