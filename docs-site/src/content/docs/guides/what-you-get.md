---
title: What you get
description: The four files a design leaves in your project, and what is in each.
---

```
your-project/
├── docs/airgap/blueprint.json          answers, tier, sizing, decisions
├── docs/airgap/transfer-manifest.md    images, models, packages and settings to carry in
├── docs/airgap/blueprint.md            the blueprint (under docs/superpowers/specs/ with superpowers)
└── AGENTS.md                           instructions for the agent that builds it inside the network
```

These files travel into the network together with the artifacts the manifest lists.

## `blueprint.json`

The state of the design: the answers, the computed tier and sizing, and one decision per layer with its rationale, the alternatives considered and an evidence label. See [blueprint.json](/reference/blueprint-json/).

## The blueprint

Written in the language of the interview, in ten sections:

1. Context: organization shape and constraints.
2. Tier, floors and overrides.
3. Architecture overview with a component diagram.
4. Layer decisions: choice, version, rationale, alternatives, evidence, caveats.
5. Sizing: inputs, concurrency range, GPUs, servers, power, assumptions.
6. Air-gap transfer plan.
7. Data flow: request path and authentication path.
8. Failure modes and operations, including offline upgrades.
9. Verification plan: benchmarks to run and the list of `estimate` decisions.
10. Out of scope and later layers.

## The transfer manifest

The one list of what to carry in, written by `manifest.py` from the chosen components: container images for your hardware, model artifacts, packages, telemetry and other outbound calls to switch off before first start, files to stage that the software would otherwise download, per-tool skills worth carrying, and checksum and signature steps. Its header records a digest of the decisions, so lint notices when the manifest is older than the design. [Carrying it in](/guides/carrying-it-in/) explains how it is used.

## The block in `AGENTS.md`

A delimited block that tells the agent inside the network to follow the blueprint, use the pinned versions, assume there is no internet, and propose any new dependency as a blueprint change instead of adding it. Running the skill again replaces the block.
