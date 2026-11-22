---
title: Scope
description: What version 0.1 covers, and what it leaves out.
---

## In version 0.1

- Decision tables for the inference engine and the LLM gateway.
- Fixed per-tier defaults for UI, identity, observability, orchestration, state stores and artifact registry.
- Sizing from organization answers, a transfer manifest, and lint.

## Not in version 0.1

- Deployment files such as Docker Compose or Helm. The skill decides; it does not operate. For running each tool, catalog entries point to existing per-tool skills.
- A recommendation of which model to run.
- Decision tables for data, CI/CD and security layers.
- Compliance mappings.
