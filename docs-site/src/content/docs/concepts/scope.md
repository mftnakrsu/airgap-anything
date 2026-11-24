---
title: Scope
description: What version 0.5 covers, and what it leaves out.
---

## In version 0.5

- Four skills in plain markdown: `SKILL.md`, references and a catalog, read by Claude Code, Codex, Cursor or any agent that reads Agent Skills. Nothing to install but the skill folder, and no script to run.
- Decision tables for the inference engine and the LLM gateway.
- Fixed per-tier defaults for UI, identity, observability, orchestration, state stores and artifact registry.
- Tier and sizing from organization answers, with every step written out, a transfer manifest, and a self-review before approval.
- `airgap-transfer`: a plan from the transfer manifest, documented fetch commands that run only after your approval, a bundle with checksum lists split across media, and a runbook or agent rules that check it inside with `sha256sum` alone.
- `airgap-agent`: the choice of coding-agent tool, its configuration and central policy with outbound connections off, the model server's requirements, offline MCP servers, and three checks for the inside ([Coding agents inside](/guides/coding-agents/)).
- `airgap-rag`: the choice of platform (yours), extraction and OCR, embedding and reranker models, the vector store, a sizing of the first load, the configuration, a bulk-load runbook, and five checks for the inside ([Searchable documents inside](/guides/searchable-documents/)).

## Not in version 0.5

- Deployment files such as Docker Compose or Helm. The skill decides; it does not operate. For running each tool, catalog entries point to existing per-tool skills.
- A recommendation of which model to run, for the architect, the coding agents or the chat model. The embedding and reranker models of `airgap-rag` are chosen with their reasons, not ranked.
- Connectors that sync Confluence, SharePoint or Jira into a knowledge base.
- Decision tables for data, CI/CD and security layers.
- Compliance mappings.
- Publisher signatures. `airgap-transfer` checks publisher checksums where the manifest names them, not signatures.

## Changed from version 0.2

Version 0.2 shipped Python scripts that computed the tier, the sizing and the manifest and checked the blueprint, shell scripts for the inside, and JSON state files. Version 0.3 removes all of them. The agent follows the references and writes its work into the blueprint and the plan file, a self-review list takes the place of the checks, and the inside needs only `sha256sum` and the runbook.
