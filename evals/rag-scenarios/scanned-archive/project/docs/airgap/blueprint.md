# archive-rag-platform: air-gapped blueprint

Status: approved. Date: 2026-11-24. Fixture for the airgap-rag evals: only the parts the RAG skill reads are filled in. The format follows `examples/department/blueprint.md`.

## 1. Context and answers

| Question | Answer | From |
|---|---|---|
| `org.users_total` | 60 | the user |
| `org.departments` | 2 | the user |
| `org.isolation` | none | the user |
| `org.audit_required` | true | the user |
| `org.downtime_tolerance` | planned_only | the user |
| `org.ops_capacity` | small_team | the user |
| `org.kubernetes_experience` | false | the user |
| `inside.operator` | people | the user |
| `workload.usage` | {"chat": 0.5, "rag": 0.5} | the user |
| `workload.models` | [{"name": "Qwen3-8B", "role": "chat", "params_b": 8, "precision": "fp8", "context_tokens": 32768}] | the user |
| `hardware.gpus` | [] | the user; no GPU yet |
| `hardware.cpu_arch` | amd64 | the user |
| `existing.identity` | ad_ldap | the user |
| `existing.api_gateway` | none | the user |
| `existing.kubernetes` | none | the user |
| `transfer.channel` | removable_media | the user |

## 4. Layer decisions

| Layer | Component | Version | Evidence |
|---|---|---|---|
| `llm-serving` | `vllm` | `v0.34.0` | docs |
| `llm-gateway` | `litellm` | `v1.110.2` | docs |
| `ui` | `open-webui` | `v0.13.4` | docs |
| `state` | `postgresql` | `18.7` | docs |

### `llm-serving`

- Components: `vllm` `v0.34.0`
- Existing: none
- Custom: none
- Benchmark only: none

The engine serves the chat model behind the gateway. Open WebUI reaches it only through the gateway.

### `ui`

- Components: `open-webui` `v0.13.4`
- Existing: none
- Custom: none
- Benchmark only: none

The `rag` share of the usage is the part of the users who ask questions over documents.

## 6. Air-gap transfer

The list of everything to carry in is `docs/airgap/transfer-manifest.md`. The next step is `airgap-transfer`.
