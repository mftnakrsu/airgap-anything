---
title: Installing inside
description: How airgap-install turns an approved blueprint into deployment files and a runbook of commands for a network without internet, who runs what and where, and what it hands off to other skills.
---

The blueprint leaves deployment files out on purpose, and the transfer's runbook ends at "continue with the implementation plan". Without a plan, the people inside write the Compose file or the manifests, place the egress settings, pick a start order and guess what "healthy" looks like, with no internet and often no LLM, at the moment a mistake costs the most. `airgap-install` is the fifth skill: it writes the installation while you still have internet, so that the inside only types commands and compares their output. Like the other four it is plain markdown. It downloads nothing and runs nothing, and it writes no programs or scripts into your project; it writes deployment files, a plan and a runbook. Its pages are on the [airgap-install reference](/reference/install/).

## Who runs what, and where

| Who | Where | What |
|---|---|---|
| You and the agent | The connected side, after the blueprint is approved | `airgap-install` asks its questions, writes `plan.md`, waits for your yes, then writes the deployment files and the runbook and adds the rows the files need to the transfer manifest |
| You and the agent | The connected side | `airgap-transfer` builds the bundle, or builds it again so that the new files get checksums like every other file |
| The people inside, or an agent on a local model | The network without internet | `INSIDE.md` first (checksums, images loaded), then `docs/airgap/install/INSTALL.md` (people) or `AGENTS-INSTALL.md` (an agent): the registry, the services in their start order, the checks |
| The same people | Inside, after the install | The hand-offs: the benchmark of the blueprint, then `docs/airgap/agents.md` and `docs/airgap/rag.md` when they exist |

Who works inside comes from the blueprint's `inside.operator`: `people` gets `INSTALL.md`, `local_agent` gets `AGENTS-INSTALL.md`, and `people_then_agent` gets both.

## What it asks

After the blueprint exists, ask in your own words, for example "write the install for our design". The skill reads the blueprint, the transfer manifest and, when they exist, `rag.md` and `agents.md`, then asks in one message the few things they leave open, each with a default: whether the blueprint is approved as it stands (the file's `Status:` line stays "draft" after the architect's approval, so it cannot show this), the host name and address of each server, where data and models live, TLS, and who runs the install. A decision you say is still open sends you back to `airgap-architect`, and nothing is written. [Install questions](/reference/install/questions/) lists them.

It never asks for a password, a token or a key. Each secret is generated inside the network by a runbook step with `openssl rand`, written to `.env` with `chmod 600` or to a Kubernetes Secret; `.env.example` holds names only.

## The plan comes first

The skill writes `docs/airgap/install/plan.md` and shows it before anything else: the start order, the files, the ports, the health checks, a table that copies the GPUs per replica, the replicas and the total from blueprint section 5, and the rows it will add to the manifest. It records "Blueprint approved by the user on DATE". The skill stops there; your yes to the plan is the approval. When the blueprint's GPU numbers do not fit the hosts, it reports a blueprint change for `airgap-architect` and stops, because the install does not redesign ([Install plan](/reference/install/plan/)).

## What it writes

| Path in the project | Holds |
|---|---|
| `docs/airgap/install/plan.md` | The approved plan: answers, steps, GPU check, manifest rows added, open items |
| `docs/airgap/install/INSTALL.md` | The runbook for people |
| `docs/airgap/install/AGENTS-INSTALL.md` | Only when an agent works inside: the same steps and the agent's rules |
| `docs/airgap/install/compose/` | Docker Compose: `compose.yaml`, `.env.example`, `config/` (also Harbor's installer in a Kubernetes design) |
| `docs/airgap/install/kubernetes/` | Manifests for k3s, RKE2 or an existing cluster; `cluster/` with `registries.yaml` and `config.yaml` for k3s and RKE2 only |
| `docs/airgap/transfer-manifest.md` | New rows marked "(from airgap-install)": the project files, the NVIDIA device plugin image on Kubernetes with GPUs, any custom image you gave and anything the manifest lacked; nothing else changes |

Every step of a runbook has the same four parts: a **Why**, the commands, the output to **Expect**, and what to do **If not**, which is to stop, report the command and its output, and change nothing. Inside, nobody can ask what a step meant, so every step says how to tell success from failure ([Install runbooks](/reference/install/runbook/)).

## No image is pulled inside

Every image tag is the manifest's, never `latest`. In Compose each service has `pull_policy: never`; in Kubernetes each container names the local registry and sets its pull policy ([Docker Compose files](/reference/install/compose/), [Kubernetes manifests](/reference/install/kubernetes/)). A missing image then fails at once, instead of trying an internet that is not there, and it is carried in again. GPU counts are the blueprint's numbers written out (`count: 8`, `--tensor-parallel-size 8`, `nvidia.com/gpu: 1` with `replicas: 18`), never `all`. Every outbound switch of the manifest's section 4 is applied in a file and checked in the runbook's egress step.

## Which cluster

| Your design | What you get |
|---|---|
| A small team or a lab on Docker Compose | `compose/` and a runbook of about the same size as the design: registry, secrets, services in order, egress check, smoke test |
| A department on k3s or RKE2 | `kubernetes/` manifests and `cluster/` configuration that points the cluster at the local registry; the runbook installs the cluster from the bundle first. Harbor, when the design has it, still runs from its own installer in `compose/` |
| An enterprise on a cluster you already run | `kubernetes/` manifests and their deployment, and a step that lists what the cluster's owners must answer. The skill writes no cluster install: the cluster is theirs |
| A design with a service of your own, such as an in-house search | That service is written only from the facts you give (image, port, health endpoint) and labeled `unverified`; a missing fact is asked, never filled in |
| A blueprint with an open decision | Nothing is written; the skill names `airgap-architect` |

On Kubernetes with GPUs there is one more step before any serving rollout: the NVIDIA device plugin is applied and every GPU node must report the blueprint's GPU count, so no inference pod starts before the GPUs are proven ([Clusters](/reference/install/clusters/)).

## What it hands off

It deploys the blueprint's server components and the ones `airgap-rag` chose (the extractor, the vector store, the RAG server, the embedding and reranking instances). The tools of `airgap-agent` are command-line programs on each developer's machine, so the runbook ends by pointing at `docs/airgap/agents.md` and `docs/airgap/rag.md`. Drivers, Helm and Keycloak depth stay in their own per-tool skills, which the runbook names where a step depends on them.

## Not in scope

It installs no operating system, GPU driver or container runtime: those are on the hosts before the install. It adds no high availability beyond what the blueprint decides, and writes no upgrades, no CI/CD and no GitOps. A value that is not from the manifest or a catalog entry is labeled `unverified`, with the step that checks it. For more ideas, see [#12](https://github.com/mftnakrsu/airgap-anything/issues/12).
