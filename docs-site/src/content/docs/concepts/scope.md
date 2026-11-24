---
title: Scope
description: What version 0.3 covers, and what it leaves out.
---

## In version 0.3

- Two skills in plain markdown: `SKILL.md`, references and a catalog, read by Claude Code, Codex, Cursor or any agent that reads Agent Skills. Nothing to install but the skill folder, and no script to run.
- Decision tables for the inference engine and the LLM gateway.
- Fixed per-tier defaults for UI, identity, observability, orchestration, state stores and artifact registry.
- Tier and sizing from organization answers, with every step written out, a transfer manifest, and a self-review before approval.
- `airgap-transfer`: a plan from the transfer manifest, documented fetch commands that run only after your approval, a bundle with checksum lists split across media, and a runbook or agent rules that check it inside with `sha256sum` alone.

## Not in version 0.3

- Deployment files such as Docker Compose or Helm. The skill decides; it does not operate. For running each tool, catalog entries point to existing per-tool skills.
- A recommendation of which model to run.
- Decision tables for data, CI/CD and security layers.
- Compliance mappings.
- Publisher signatures. `airgap-transfer` checks publisher checksums where the manifest names them, not signatures.

## Changed from version 0.2

Version 0.2 shipped Python scripts that computed the tier, the sizing and the manifest and checked the blueprint, shell scripts for the inside, and JSON state files. Version 0.3 removes all of them. The agent follows the references and writes its work into the blueprint and the plan file, a self-review list takes the place of the checks, and the inside needs only `sha256sum` and the runbook.
