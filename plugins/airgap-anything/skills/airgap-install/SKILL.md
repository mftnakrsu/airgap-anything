---
name: airgap-install
description: Writes the installation for an approved air-gapped design - the deployment files (Docker Compose, or Kubernetes manifests for k3s, RKE2 or an existing cluster) and a runbook in which every step is a command, the output to expect and what to do when it differs, for the people or the agent inside a network with no internet. Covers the blueprint's components and those chosen by airgap-rag, and adds what the files need to the transfer manifest. Use when an approved airgap-architect blueprint needs install steps, deployment files or a Compose file or manifests to carry into an offline network, or someone asks how to install the design inside
---

# Airgap Install

## Overview

Turn an approved blueprint and its transfer manifest into an install plan, the deployment files and a runbook, written on the connected side so that `airgap-transfer` carries them in as project files.

Why the skill exists: the blueprint leaves deployment files out on purpose, and the transfer's inside runbook ends at "continue with the implementation plan". Without this skill, the people inside write the Compose file or the manifests, place the egress settings, pick a start order and guess what "healthy" looks like, with no internet and often no LLM, at the most expensive moment to get it wrong. So every value comes from the blueprint, the manifest or a catalog entry, and every step says what its output must be.

Audience: the skill runs on the connected side, for whoever prepares the system. Its output is used inside by people who type the commands (`INSTALL.md`), or by an agent inside when one already runs (`AGENTS-INSTALL.md`). No local model is needed: usually the model is what is being installed.

Paths in this skill are relative to the folder that holds this file. `docs/` is in the user's project.

## When to use

- An approved `airgap-architect` blueprint needs install steps, a Compose file or Kubernetes manifests to carry into an offline network.
- Someone asks how to install the design inside, in which order, and how to tell that each part works.

Not for designing or changing the system: that is `airgap-architect`. Not for packing, checksums or loading images from the media: that is `airgap-transfer`, whose `INSIDE.md` runs first. Not for coding agents or the document load: `docs/airgap/agents.md` and `docs/airgap/rag.md` cover those.

## What it does not do

- It runs, installs and downloads nothing. It writes files; a person or an agent runs them inside.
- It installs no operating system, GPU driver or container runtime: those are on the hosts before the install (`nvidia-datacenter-bringup` and the other per-tool skills).
- It adds no high availability beyond what the blueprint decides, and writes no upgrades, no proof that nothing is reached, no CI/CD and no GitOps.
- It assumes one Compose host, or a k3s or RKE2 cluster whose nodes get their files by hand: the bundle sits on one host, and the runbook lists which files a person copies to each other node (`references/clusters.md`, "Files on every node"). It distributes nothing itself.
- It deploys no coding agent: `airgap-agent`'s tools are command-line programs on each developer's machine, so the runbook hands off to `docs/airgap/agents.md`.

## Workflow

Copy this checklist into your reply and tick it off as you go:

```
Air-gap install:
- [ ] 1. Inputs read
- [ ] 2. Questions, with the approval question
- [ ] 3. Install plan (plan.md)
- [ ] 4. Approval: show the plan, then wait
- [ ] 5. Deployment files and manifest rows
- [ ] 6. Runbooks
- [ ] 7. Self-check, until every item holds
- [ ] 8. Hand-off
```

1. **Inputs.** Read `docs/airgap/blueprint.md` and `docs/airgap/transfer-manifest.md`, including its "(from airgap-rag)" and "(from airgap-agent)" rows; `docs/airgap/rag.md` and its configuration under `docs/airgap/rag/`, and `docs/airgap/agents.md`, when they exist. What gets deployed: the blueprint's server components and the "(from airgap-rag)" rows (extractor, vector store, RAG server, embedding and reranking instances). `airgap-agent`'s tools are handed off to `docs/airgap/agents.md`, never deployed. No blueprint, or a request that changes the design: name `airgap-architect` and stop.
2. **Questions.** Read `references/questions.md` ("How to ask", "Questions"). One message, each question with its default. The blueprint's `Status:` line stays "draft" after the architect's approval, so the file cannot show it: unless the user said so in this conversation, the message asks whether the blueprint is approved. When the user says a decision is still open, name `airgap-architect` and write nothing. A component outside the catalog (the user's own service, a custom platform of `rag.md`) is written only from the user's facts, labeled `unverified`; ask for missing facts, never fill them in.
3. **Plan.** Read `references/plan.md` and write `docs/airgap/install/plan.md` from its "Plan template", in its "Start order", with the line "Blueprint approved by the user on DATE". Copy GPUs per replica, replicas and the total from blueprint §5 into the "GPU check against blueprint §5" table. When the numbers do not fit the hosts, report it as a blueprint change for `airgap-architect` and stop.
4. **Approval.** Show the plan and end your turn. The user's yes to the plan is the approval; until then `plan.md` is the only file written.
5. **Files.** Docker Compose: `references/compose.md` ("Rules for every service", "Template", "`.env.example` template", "Placing the egress settings", "Harbor's `harbor.yml`"). k3s, RKE2 or an existing cluster: `references/kubernetes.md` ("Rules for every workload", "Manifests", "GPUs: the NVIDIA device plugin") and `references/clusters.md` (its "k3s", "RKE2" or "Existing cluster" section). Harbor or the Distribution Registry in a Kubernetes design runs with Compose on its host, so it also gets `compose/` (`references/compose.md`). Every tag, port, flag and offline switch is copied from the manifest or the catalog entry (`airgap-architect`'s catalog, and `airgap-rag`'s for its components); anything else is labeled `unverified`. For anything the files need that the manifest lacks, add a row to `docs/airgap/transfer-manifest.md` and list it in `plan.md` ("Manifest rows added"): see the hand-off for the rows. The marker is exactly `(from airgap-install)` at the end of the Component cell, nothing else inside that parenthesis (`` `ticket-search` (from airgap-install) ``; "custom" before it, `unverified` in another column), because `airgap-transfer` accepts such a row only by that mark. Site values are `${NAME}` in Compose files and placeholders filled in a working copy on Kubernetes; no carried file is edited inside (`references/runbook.md`).
6. **Runbooks.** Read `references/runbook.md` ("Rules for both runbooks", "INSTALL.md template", "AGENTS-INSTALL.md template"). `inside.operator` decides: `people` gets `docs/airgap/install/INSTALL.md`, `local_agent` gets `AGENTS-INSTALL.md`, `people_then_agent` both. Step 4b only on Kubernetes with GPUs, before any step 5 rollout.
7. **Self-check.** Check every item below; fix what fails and check again.
8. **Hand-off.** Below.

## Outputs

| Path in the project | Holds |
|---|---|
| `docs/airgap/install/plan.md` | The approved install plan: answers, steps, GPU check, manifest rows added, open items |
| `docs/airgap/install/INSTALL.md` | The runbook for people |
| `docs/airgap/install/AGENTS-INSTALL.md` | Only when `inside.operator` includes an agent: the same steps and the agent's rules |
| `docs/airgap/install/compose/` | When any part runs on Compose (also the registry in a Kubernetes design): `compose.yaml`, `.env.example`, `config/COMPONENT.EXT`; `harbor/harbor.yml` when the registry is Harbor |
| `docs/airgap/install/kubernetes/` | k3s, RKE2 or an existing cluster: `00-namespace.yaml` … `NN-COMPONENT.yaml`, `70-ingress.yaml`; `cluster/` for k3s and RKE2 only (`registries.yaml`; `config.yaml` on RKE2; `traefik-config.yaml` on k3s) |
| `docs/airgap/transfer-manifest.md` | New rows marked "(from airgap-install)"; nothing else changes |

## Rules

1. **Nothing inside needs internet or an LLM.** Every step is a command with the output to expect and what to do when it differs. Why: inside, nobody can ask what a step meant.
2. **No image is pulled inside.** Every Compose service gets `pull_policy: never`; every Kubernetes container names the local registry and sets `imagePullPolicy` as `references/kubernetes.md` says. Tags are the manifest's, never `latest`. Why: a missing image must fail loudly, not try an internet that is not there; it is carried in again.
3. **No secret in any file the skill writes.** `.env.example` holds names only; a runbook step generates each value inside with `openssl rand`, into `.env` with `chmod 600`, or into a Kubernetes Secret. Each Compose service reads only its own secrets, by name in its `environment:` (`${NAME}`), never `env_file: .env`, which would give every container every department's keys. Never ask for a password in the conversation. Why: nobody on the connected side should ever know the inside's secrets.
4. **The skill writes no programs or scripts into the project** (no `.sh`, no `.py`, no render or template helper): only deployment files, configuration, `.env.example`, `plan.md` and the runbooks, and every step is a command typed from the runbook. Allowed, because a component reads them and they run nothing by themselves: configuration and build inputs, such as an SQL init file or a `Dockerfile` that builds offline `FROM` a carried image; `plan.md` records such an image as "built inside from IMAGE" ("Images built inside"), and it needs no manifest row. Why: a person can read and check a command before running it, and a script hides its steps; `airgap-rag` carries the same rule. Checksums and loading the images belong to `airgap-transfer`'s `INSIDE.md`, which runs first.
5. **Before the plan is approved, only `docs/airgap/install/plan.md` is written, and never anything outside `docs/airgap/install/` except the marked manifest rows.** Nothing at all is written while the blueprint is not approved. Why: a wrong host or GPU count is cheap in a table and expensive in a dozen files already carried inside.
6. **The blueprint is not redesigned.** GPU counts, replicas and parallel sizes are copied from blueprint §5, and the components and versions from blueprint §4, into final files, never `count: all` or `NVIDIA_VISIBLE_DEVICES=all`; a conflict goes back to `airgap-architect`. Why: the sizing was checked there, and a second, silent decision here would not be.
7. **An existing cluster gets manifests and their deployment, never a cluster install.** Its owners' process is a step of the runbook (`references/clusters.md`, "Existing cluster"). Why: the cluster is theirs.
8. **Values come from the manifest and the catalog**, or are labeled `unverified` with the step that checks them. A custom component's facts come from the user; a missing one is asked, never guessed. Placeholders in capitals only for what nobody on the connected side knows, listed at the top of the runbook.
9. **The skill that chose a component sets its stricter rules.** When `docs/airgap/rag.md` or `docs/airgap/agents.md` says more than these rules about its component, follow it: `rag.md` keeps docling-serve's key "from the environment of its host, never from a file", so the runbook exports it in the shell instead of writing it into `.env` (`references/compose.md`). Why: that skill read the component's sources; a looser rule here would undo its decision.
10. **Carried files are never edited inside.** The runbook fills site values through `.env` (Compose) or in the working copy `docs/airgap/install/work/` (Kubernetes), never by `sed -i` on a carried file. Why: `airgap-transfer` checksummed them; an edited file cannot be told from a damaged one (`references/runbook.md`).
11. **Per-tool depth stays in per-tool skills.** The runbook names them where a step depends on them: `nvidia-datacenter-bringup` for drivers, `helm`, `keycloak-iam`.

## Self-check

Before the hand-off, check each item against the files you wrote. When one fails, fix it and check all of them again.

1. Every image in the files is in the transfer manifest with the same tag; none is `latest`.
2. Every Compose service has `pull_policy: never`; every Kubernetes workload names the local registry and sets its pull policy.
3. For every service, the GPUs it reserves and its parallel size match blueprint §5; no GPU is used twice on a host; the total equals the blueprint's GPU total.
4. Every applicable manifest section 4 setting (not the rows for the staging host only, nor "None documented" or "Not applicable" rows, as `references/compose.md` says) is applied in a file and checked in the runbook's egress step.
5. Every variable in `.env.example` is generated by exactly one runbook step; no file holds a secret value.
6. Every runbook step and every sub-step (1a, 5a, 5.1, …) has Why, commands, Expect and If not; every file a command names exists under `docs/airgap/install/` or in the bundle; no step edits a carried file (only `compose/.env` and `work/`).
7. Every value not from the catalog is labeled `unverified`, and no cluster install is written for an existing cluster.
8. No program or script file was written; `plan.md` records the blueprint approval and lists every row marked "(from airgap-install)".
9. The transfer manifest holds the project-files row for `docs/airgap/install/` (section 3), and its Component cell, like every added row's, ends with exactly "(from airgap-install)". An empty list in `plan.md` does not pass this item.
10. No Compose service has `env_file`; every `${NAME}` in the Compose files is a line of `.env.example` or a key another skill keeps out of files.

## Hand-off

Tell the user, in their language:

1. What was written: the plan with its steps, and the list of files under `docs/airgap/install/`.
2. The rows added to the transfer manifest, each marked "(from airgap-install)": the project files `docs/airgap/install/` (section 3, a project path, copied, not fetched); the NVIDIA device plugin image on Kubernetes with GPUs; any custom image the user gave, as `plan.md` lists it; any image or file the blueprint chose that the manifest lacked (a TLS proxy, the SELinux policy RPM of `references/clusters.md`).
3. What comes next: bundle not built yet, run `airgap-transfer`; bundle already built, run it again, so the new files get checksums like every other file.
4. What the inside does: `INSIDE.md` first (checksums, images loaded), then `docs/airgap/install/INSTALL.md` (or `AGENTS-INSTALL.md`), and at its end the hand-offs to `docs/airgap/agents.md` and `docs/airgap/rag.md` when they exist.
5. What is still open: placeholders to fill inside, `unverified` values, TLS, the cluster owners' answers, and the plan's open items.

## Common mistakes

| Mistake | Instead |
|---|---|
| Writing the runbook as `docs/airgap/runbook.md` or `INSIDE.md`, or the files under `install/` or `deploy/` at the project root | Write only under `docs/airgap/install/`: `plan.md`, `INSTALL.md` (and `AGENTS-INSTALL.md` when `inside.operator` includes an agent), `compose/` or `kubernetes/`. `INSIDE.md` is `airgap-transfer`'s file; the only file written outside the folder is the transfer manifest, with new rows |
| Writing every file at once, with no plan and no approval | Write `plan.md` first (hosts, order, files, ports, health checks, GPUs) with the date of the blueprint approval, show it and stop; nothing else is written before the yes |
| Writing shell scripts that check checksums, load and push images, render templates or write `registries.yaml`, on an assumed bundle layout | Write no programs or scripts; each step is a command in `INSTALL.md`. Checksums and loading the images are `INSIDE.md`'s; step 1 asks that it is finished, and the install starts from the registry |
| Needing an image or a binary the manifest lacks (a TLS proxy, the device plugin) and only mentioning it in the runbook | Add a row marked "(from airgap-install)" to the transfer manifest and list it in `plan.md`; every image in the files has the manifest's tag. An image built inside from a carried one gets no row: `plan.md` lists it as "built inside from IMAGE" |
| Literal `REGISTRY_HOST`, `MODEL_DIR` or `SERVED_NAME` in `compose.yaml`, filled by `sed -i` in the carried files or by hand, or never filled | Compose: `${REGISTRY_HOST}`, `${MODEL_DIR}`, `${SERVED_NAME}`, with the values written into `.env` by step 3. Kubernetes: step 1b copies `kubernetes/` to `work/` and fills the copy; every apply uses `work/kubernetes/…` |
| `env_file: .env` on every service, so each container holds every department's keys | Each service names its own secrets in `environment:` (`VLLM_API_KEY: ${VLLM_API_KEY}`) |
| No `docs/airgap/install/` row in the manifest, or the marker inside a longer parenthesis ("(custom, from airgap-install)") | Add the project-files row first; end every added Component cell with exactly "(from airgap-install)", other words outside it (self-check item 9) |
| `strategy: Recreate` on every Deployment, or on 18 GPU replicas | `Recreate` only for `replicas: 1` taking all GPUs of its node; other GPU Deployments `RollingUpdate` with `maxSurge: 0`, `maxUnavailable: 1`; others the default (`references/kubernetes.md`) |
| Reserving GPUs as `count: all`, defaulting to `NVIDIA_VISIBLE_DEVICES=all`, or leaving `replicas` and GPU lines to a render step | Copy blueprint §5 into final files: `count: 8` or `device_ids`, `--tensor-parallel-size 8`, `nvidia.com/gpu: 8`; 18 replicas of 1 GPU are `replicas: 18` and `nvidia.com/gpu: 1`. A missing part is a blueprint change |
| Kubernetes containers without a pull policy | Name the local registry and set `imagePullPolicy` on every container, as `references/kubernetes.md` says |
| Reading `people_then_agent` and deferring the agent runbook to a sentence | Write `AGENTS-INSTALL.md` next to `INSTALL.md`: the same steps, and the agent's rules |
| Steps that say "You should see", "Check:" or nothing, with one "If not" for the whole runbook | Every step has Why, commands, **Expect** and **If not**, in those words; a step that only copies a file expects the `ls -l` output |
| Writing "not known" or "(estimate)" in the files an operator follows | Label every value not from the catalog `unverified`, and name the step that checks it |
| Generating secrets with `od` on `/dev/urandom` inside a script | Generate each secret in a runbook step with `openssl rand`, into `.env` with `chmod 600`; `.env.example` holds names only |
