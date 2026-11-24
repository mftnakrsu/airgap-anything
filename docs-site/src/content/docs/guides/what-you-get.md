---
title: What you get
description: The files a design and a transfer leave in your project and in the bundle folder, and what is in each.
---

```
your-project/
├── docs/airgap/blueprint.md            the blueprint: answers, tier, sizing, decisions
├── docs/airgap/transfer-manifest.md    images, models, packages and settings to carry in
├── docs/airgap/transfer-plan.md        the transfer's answers, items and volumes
└── AGENTS.md                           instructions for the agent that builds it inside the network
```

With superpowers installed, the blueprint goes to `docs/superpowers/specs/YYYY-MM-DD-PROJECT-airgap-blueprint-design.md` instead ([With superpowers](/guides/with-superpowers/)). `airgap-architect` writes the blueprint, the manifest and the `AGENTS.md` block; `airgap-transfer` writes the plan and the bundle.

Everything is markdown that a person can read. There is no separate state file: the blueprint holds the design's state and the plan file the transfer's, so an interrupted interview or transfer resumes from them.

These files travel into the network together with the artifacts the manifest lists. Inside, people follow the bundle's `INSIDE.md`, an agent follows `AGENTS-INSIDE.md` and `AGENTS.md`, and nobody needs internet access.

## The blueprint

Written from the [blueprint template](/reference/architect/blueprint-template/), in the language of the interview; question IDs, choice values, component IDs and versions stay exactly as the interview and the catalog write them. Its header gives the status, the date and the oldest catalog entry the design uses. Then ten sections:

1. Context and answers: who the system is for, what constrains it, every answer with where it came from, and the open questions.
2. Tier, floors and overrides.
3. Architecture overview with a component diagram.
4. Layer decisions: a table of components and versions, then per layer the components, existing infrastructure, custom parts, engines carried in only to be benchmarked, rationale, alternatives, evidence and override.
5. Sizing: inputs, every step of the procedure with its numbers, concurrency range, GPUs, servers, power, whether the hardware fits, and the assumptions table.
6. Air-gap transfer: the channel, the telemetry settings to switch off, and who works inside.
7. Data flow: request path and authentication path.
8. Failure modes and operations, including offline upgrades.
9. Verification plan: the benchmark before production, every `estimate` decision, the Kubernetes risk where it applies, and catalog entries that need re-checking.
10. Out of scope.

## The transfer manifest

The one list of what to carry in, written by the agent from the [transfer manifest template](/reference/architect/transfer-manifest-template/), with every row copied from the catalog entries of the chosen components. Its header names the blueprint and its date, the hardware class (the GPU vendor, or `cpu`) and the platform (`linux/amd64` or `linux/arm64`). Seven sections: container images for that hardware class, model artifacts, packages for that architecture, telemetry and other outbound calls to switch off before first start, files to stage that the software would otherwise download, the per-tool skills of each component, and verification steps. Every item of each chosen entry is copied; whether one is needed inside is decided during the transfer. `airgap-transfer` fills in digests, sizes and checksums when it fetches. [Carrying it in](/guides/carrying-it-in/) explains how it is used.

## The transfer plan

`docs/airgap/transfer-plan.md` is the state of one transfer: the channel, the platform, the bundle folder, when and in which words you approved, the answers, one item per row of the manifest with its source, bundle path, size and status, and the volume plan. [The plan file and the bundle](/reference/transfer/bundle/) shows its layout.

## The bundle

A folder outside the git repository, since it can be hundreds of gigabytes:

| File | What it holds |
|---|---|
| `images/`, `models/`, `packages/`, `manual/` | Single-platform image archives with their digests, model files at the pinned commit, packages with the publisher's checksum files, and the files you added for manual items |
| `SHA256SUMS` | The SHA-256 of every file of the bundle, documents included |
| `PARTS.sha256` | The SHA-256 of every part of a split file; empty when nothing was split |
| `VOLUMES.txt` | One line per file or part: its volume, size and path |
| `INVENTORY.md` | Every item, largest first, with kind, version, source, license, size and notes, for the people who approve the transfer and for scanning stations |
| `INSIDE.md` | The runbook for people: one command per step, with the output to expect |
| `AGENTS-INSIDE.md` | The same steps, after the rules for an agent inside |
| `SEND-ORDER.txt` | Data diode only: the sending order, checksum lists first |

`INSIDE.md` and `AGENTS-INSIDE.md` are written as the interview's answer on who works inside calls for: one of them, or both. Every volume carries the shared files and a `VOLUME.txt` that says "volume N of TOTAL".

## The block in `AGENTS.md`

A delimited block that tells the agent inside the network to follow the blueprint, use the pinned versions, assume there is no internet, and propose any new dependency as a blueprint change instead of adding it. When an agent will work inside, the block adds its rules: one command per step, stop at the first non-zero exit code, never download, never edit `SHA256SUMS`. Running the skill again replaces the block. If your `CLAUDE.md` does not import `AGENTS.md`, the agent asks before adding the line `@AGENTS.md`. The text is on [AGENTS.md block](/reference/architect/agents-snippet/).
