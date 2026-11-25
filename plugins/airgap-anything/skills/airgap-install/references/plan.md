# Install plan

Goal: `docs/airgap/install/plan.md`, one row per step, shown to the user before any other file is written. The user's yes to it is the approval; until then the skill writes only this file. Why: a wrong host, port or GPU count is cheap to fix in a table and expensive in a dozen deployment files and a runbook already carried inside.

## Plan template

Fill in the parts in capitals. One row per step of the start order below, one row per component; a component that runs on several hosts gets one row per host.

````markdown
# Install plan: PROJECT NAME

Blueprint approved by the user on DATE.
Blueprint: `docs/airgap/blueprint.md`, dated BLUEPRINT DATE. Transfer manifest: `docs/airgap/transfer-manifest.md`.
Orchestration: ORCHESTRATION (`docker-compose`, `k3s`, `rke2` or existing cluster). Runbooks: RUNBOOKS (from `inside.operator` = OPERATOR).

## Answers

| ID | Answer | From |
|---|---|---|
| hosts | HOST_1 = NAME (ADDRESS or placeholder) | the user, or default |

## Hosts

| Host | Role | Components | Files a person copies to it from the bundle host |
|---|---|---|---|
| HOST_1 | registry, Compose host, or k3s/RKE2 server | COMPONENTS | none: the bundle is here |
| HOST_2 | k3s/RKE2 agent | COMPONENTS | the list of `references/clusters.md`, "Files on every node" |

## Steps

| Step | Host | Component | Files | Port | Health check | GPUs |
|---|---|---|---|---|---|---|
| 1 | HOST_1 | registry: COMPONENT VERSION | `compose/compose.yaml` | PORT | HEALTH CHECK or `unverified`: container running | none |
| 4 | HOST_1 | `vllm` v0.34.0, MODEL | `compose/compose.yaml` | 8000 | `/v1/models` lists MODEL | GPUS PER REPLICA × REPLICAS, device IDs DEVICE IDS (blueprint §5) |

## GPU check against blueprint §5

| Model | GPUs per replica | Replicas | Parallel size | Total | Blueprint §5 total |
|---|---|---|---|---|---|
| MODEL | N | R | N | N × R | SAME NUMBER |

## Registry paths (Harbor only)

| Manifest Target path | Path in the files and the push |
|---|---|
| `REGISTRY_HOST/postgres:18.7` | `REGISTRY_HOST/library/postgres:18.7` |

## Manifest rows added "(from airgap-install)"

- SECTION: ROW (why the files need it)

## Open items

- ITEM: who decides, and which step waits for it
````

One row per host in Hosts, as blueprint §3 and §5 place the components: the runbook assumes one Compose host, or a cluster whose other nodes get their files by hand, so the last column says what each host needs. On Kubernetes, the Answers table also records the exposure host names (`references/questions.md`, question 8) and, when Harbor shares a host with a k3s node, Harbor's port (`references/compose.md`, "Harbor's `harbor.yml`"). Registry paths lists, with Harbor, every manifest Target path without a project segment and the `library/` path the files use instead (`references/compose.md`); leave the table out otherwise.

The GPUs column copies blueprint §5: GPUs per replica, replicas and the total, never "all". On one host, no GPU appears in two rows; the GPU check table's total equals the blueprint's. When the numbers do not fit the hosts, the plan reports it as a blueprint change for `airgap-architect` and stops: the install does not redesign.

The Health check column copies the catalog entry: vLLM's OpenAI API (`/v1/models`, port 8000), LiteLLM's port 4000, Open WebUI's port 8080. An entry that documents no health endpoint gets "`unverified`: container running", and the runbook step checks only that.

A component the files need and the manifest lacks (a TLS proxy the blueprint chose, the NVIDIA device plugin image, the Compose plugin binary) gets a row in the matching manifest section ending "(from airgap-install)", and the plan lists it. Everything else in the manifest stays as it is.

## Start order

1. registry: the blueprint's registry first, and the loaded images pushed to it. In a Kubernetes design Harbor's installer (Compose, on its host) runs before any push to the cluster's registry and before the cluster pulls anything.
2. GPU nodes (Kubernetes with GPUs only): the NVIDIA device plugin applied on k3s and RKE2, and every GPU node reports `nvidia.com/gpu` with blueprint §5's count (`INSTALL.md` step 4b, `references/runbook.md`).
3. state: databases, caches and the vector store (from `airgap-rag`, for example pgvector or Qdrant).
4. serving: the inference engine, including the embedding and reranking instances of `airgap-rag`.
5. extraction: docling-serve or another extractor of `rag.md`.
6. gateway: the LLM gateway and the identity provider in front of it.
7. UI and RAG server: the chat interface, and RAGFlow or the user's own platform.
8. observability: metrics and dashboards last, because they scrape what is already running.

Why this order: each step depends only on steps above it, so a failed health check points at one component; the registry comes first because every later start reads images from it, and observability last because a scrape target that does not run yet looks like a monitoring fault. A step whose layer the blueprint does not have is left out; the numbers stay in this order.

The cluster itself (k3s or RKE2, `references/clusters.md`) comes before step 1 and after the preconditions; an existing cluster has no such step. Row 2 exists only on Kubernetes with GPUs, so no inference pod starts before the GPUs are proven.

## Sources

| Tool | Command or key | Source |
|---|---|---|
| vLLM | port 8000, OpenAI API under `/v1` | the `vllm` catalog entry (https://github.com/vllm-project/vllm/blob/v0.34.0/docs/serving/online_serving/openai_compatible_server.md) |
| LiteLLM | port 4000 | the `litellm` catalog entry (https://github.com/BerriAI/litellm-docs/blob/d6ae56ec9fa4b0c232b5cb88ccb25482bcdf3ee8/docs/proxy/docker_quick_start.md) |
| Open WebUI | port 8080 | the `open-webui` catalog entry (https://github.com/open-webui/docs/blob/307b3ad867f4bfa2d36598c7ab3a858b47763a63/docs/getting-started/quick-start/tab-docker/DockerCompose.md) |
| Harbor | installer runs before any push | https://github.com/goharbor/website/blob/1ce1ac23f8d4969ce587b7ced8afb7954f76115d/docs/install-config/run-installer-script.md |
