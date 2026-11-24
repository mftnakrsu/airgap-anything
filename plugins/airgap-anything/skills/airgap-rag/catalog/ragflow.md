# RAGFlow (`ragflow`)

Standalone RAG server with its own web UI and API, document parsing (DeepDoc) and datasets. The alternative to Open WebUI knowledge bases when scanned or complex PDFs and tables are the core of the corpus.

| Field | Value |
|---|---|
| Kind | `rag-platform` |
| Version | `v1.0.0` |
| License | Apache-2.0, unmodified; enterprise-only features not documented |
| Install | Docker Compose from the repository at tag `v1.0.0`; image `infiniflow/ragflow:v1.0.0` |
| Evidence | docs |
| Last verified | 2026-11-24 |

Released 2026-11-06 (https://api.github.com/repos/infiniflow/ragflow/releases/latest). License from https://raw.githubusercontent.com/infiniflow/ragflow/main/LICENSE. Open WebUI, vLLM and PostgreSQL are in the architect's catalog (`open-webui`, `vllm`, `postgresql`); RAGFlow brings its own database stack and does not use the blueprint's PostgreSQL.

## Choose when

- Scanned or complex PDFs and tables are the core of the corpus, and the user wants a separate server with its own UI and API.
- Per-user datasets are enough, or "Team" sharing is.

## Avoid when

- Group permissions or per-document access control are needed: dataset scope is only "Only me" or "Team".
- The host is small: the README recommends 4 CPU, 16 GB RAM and 50 GB disk (https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/README.md).
- The users already work in Open WebUI and its groups: knowledge bases there need no second server.

## Configuration

- Default profiles: `elasticsearch,cpu,metadata-mysql` (https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/docker/.env). An optional `tei-cpu` profile serves embeddings with the default model `Qwen/Qwen3-Embedding-0.6B` (same file); the skill serves embeddings from vLLM instead.
- Models: RAGFlow bundles no embedding model since v0.22. The `VLLM` and `OpenAI-API-Compatible` providers are tagged LLM and TEXT EMBEDDING (https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/conf/llm_factories.json); point them at the network's vLLM. Reranking through these providers: not documented.
- Permissions: a dataset's scope is "Only me" or "Team"; there is no per-group or per-document access control beyond the creator's rights (https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/docs/guides/team/resource_sharing/resource_sharing_and_permissions.md).
- Data sources: 40 are documented (Confluence, SharePoint, S3, Jira, Slack, IMAP and more); permission sync is not documented (https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/docs/guides/data_source/data_source_categories_and_selection.md). Connector sync is out of scope of the skill.
- Provider API keys are entered in the UI or taken from the environment; none goes in a file of the repository.

## Egress switches

| Connection | Default | Switch | Source |
|---|---|---|---|
| Model downloads through the Hugging Face endpoint | the image sets `HF_ENDPOINT=https://hf-mirror.com` | reset `HF_ENDPOINT` before the first start; the value for an air-gapped host (an internal mirror, or none) is not documented | https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/Dockerfile |
| OpenTelemetry | off | keep `otel.enable: false` in `service_conf.yaml.template` | https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/docker/service_conf.yaml.template |
| Telemetry and update checks | not documented | not documented | https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/docker/service_conf.yaml.template |

## Caveats

- No offline guide was found. The `HF_ENDPOINT` default points at a mirror outside the network, and the `tei-cpu` profile fetches its model at start: stage the model and test with the network cut before relying on it.
- The images bake in the DeepDoc ONNX models and tokenizers (https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/Dockerfile).
- The default stack runs MySQL, Elasticsearch, an object store, a cache and a message queue: it adds five services next to the blueprint and none of them is PostgreSQL 18.
- Image sizes and digests: not documented in the research.
- Conversion on the connected side may only handle public documents; documents from inside the network never leave it.

## Carry in

### Images

Default profile, each with its tag (https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/docker/docker-compose-base.yml and the `.env` above):

| Image | Hardware | Digest |
|---|---|---|
| `infiniflow/ragflow:v1.0.0` (UI, API, admin) | not documented | not recorded |
| `elasticsearch:8.11.3` | not documented | not recorded |
| `mysql:8.0.40` | not documented | not recorded |
| `pgsty/silo:RELEASE.2026-08-06T00-00-00Z` (object store) | not documented | not recorded |
| `apache/kvrocks:2.16.0` (cache and queue) | not documented | not recorded |
| `nats:2.14.2` | not documented | not recorded |

The `tei-cpu` profile adds a text-embeddings-inference image whose tag the research did not record: read it from the `.env` file at tag `v1.0.0` before staging, and only if that profile is used.

### Models

| Repo | Revision | Why | Source |
|---|---|---|---|
| `Qwen/Qwen3-Embedding-0.6B` | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` | only if the `tei-cpu` profile is used | https://huggingface.co/api/models/Qwen/Qwen3-Embedding-0.6B |

DeepDoc models are baked into the image: nothing else to carry.

### Runtime downloads to stage in advance

- The model of the `tei-cpu` profile, as in Models, when that profile is used.
- Anything else fetched through `HF_ENDPOINT`: not documented.

### Telemetry and egress to switch off before the first start

All rows of Egress switches.

## Evidence

- https://api.github.com/repos/infiniflow/ragflow/releases/latest
- https://raw.githubusercontent.com/infiniflow/ragflow/main/LICENSE
- https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/docker/.env
- https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/docker/docker-compose-base.yml
- https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/Dockerfile
- https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/docker/service_conf.yaml.template
- https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/conf/llm_factories.json
- https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/docs/guides/team/resource_sharing/resource_sharing_and_permissions.md
- https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/docs/guides/data_source/data_source_categories_and_selection.md
- https://raw.githubusercontent.com/infiniflow/ragflow/v1.0.0/README.md
- https://huggingface.co/api/models/Qwen/Qwen3-Embedding-0.6B
