---
title: Privacy
description: What the airgap-anything plugin reads, writes and sends. It has no code and no server, and collects nothing.
---

Last updated: 2026-11-24.

The airgap-anything plugin is Markdown, JSON and an icon. It contains no code, runs no server and has no account system. It collects nothing and sends nothing to its authors or to anyone else. Your agent (Claude Code, Codex, Cursor or another) reads the skill files and works under that agent's own terms and privacy policy.

## What the skills read

The files in your project that you point the agent to, and your answers in the conversation. The interview asks about the organization (headcount, departments, rules, hardware), not about people, so a design holds no personal data unless you write some into it.

## What the skills write

- `airgap-architect` writes the blueprint (under `docs/airgap/` or, with superpowers, `docs/superpowers/specs/`), `docs/airgap/transfer-manifest.md` and a block in `AGENTS.md`, all in your project.
- `airgap-transfer` writes `docs/airgap/transfer-plan.md` in your project and the bundle in a folder you choose.
- `airgap-agent` writes `docs/airgap/agents.md` and the configuration under `docs/airgap/agents/` in your project, and adds rows to the transfer manifest. It writes no key or token: keys come from environment variables.

Nothing is written anywhere else, and nothing leaves your machine through the plugin.

## Network access

- `airgap-architect` needs none.
- `airgap-agent` downloads nothing and runs nothing: it writes configuration and the steps to check it. The tools it sets up make outbound connections of their own; the skill switches them off, and its egress check shows inside whether any remain.
- `airgap-transfer` proposes download commands for what your transfer manifest lists: container images from their registries (for example Docker Hub, `ghcr.io` and `quay.io`), model files from Hugging Face, and packages from the release pages that the catalog names. It runs them only after you approve the plan in the conversation. The requests go from your machine straight to those services, under their terms. A Hugging Face token is read only from the `HF_TOKEN` variable in your environment; the skill never asks for it and never writes it to a file.
- Inside the air-gapped network, nothing needs a network connection.

## Retention

The plugin keeps no data: it has nowhere to keep it. The files the skills write stay in your project and your bundle folder, under your control.

## Contact

Questions about this policy: [open an issue](https://github.com/mftnakrsu/airgap-anything/issues).
