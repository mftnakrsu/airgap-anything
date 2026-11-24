# pairing-code-platform: air-gapped blueprint

Status: approved. Date: 2026-11-24. Fixture for the airgap-agent evals: only the parts the agent skill reads are filled in. The format follows `examples/department/blueprint.md`.

## 1. Context and answers

| Question | Answer | From |
|---|---|---|
| `org.users_total` | 25 | the user |
| `org.departments` | 1 | the user |
| `org.isolation` | none | the user |
| `org.audit_required` | true | the user |
| `org.downtime_tolerance` | planned_only | the user |
| `org.ops_capacity` | small_team | the user |
| `org.kubernetes_experience` | false | the user |
| `inside.operator` | people | the user |
| `workload.usage` | {"code_assistant": 1.0} | the user |
| `workload.models` | [{"name": "GLM-4.6", "role": "code_assistant", "params_b": 355, "precision": "fp8", "context_tokens": 65536}] | the user |
| `hardware.gpus` | [{"model": "generic-141gb", "count": 8, "vram_gb": 141, "tdp_w": 700, "vendor": "nvidia"}] | the user |
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
| `identity` | `keycloak` | `26.8.2` | docs |
| `observability` | `prometheus` | `v3.16.0` | docs |
| `observability` | `grafana` | `13.3.1` | docs |
| `state` | `postgresql` | `18.7` | docs |
| `registry` | `harbor` | `v2.16.0` | docs |

### `llm-serving`

- Components: `vllm` `v0.34.0`
- Existing: none
- Custom: none
- Benchmark only: none

The engine serves GLM-4.6 across all eight GPUs with `--max-model-len 65536`, `--enable-auto-tool-choice` and `--tool-call-parser glm45`. Agents reach it only through the gateway.

### `llm-gateway`

- Components: `litellm` `v1.110.2`
- Existing: none
- Custom: none
- Benchmark only: none

## 6. Air-gap transfer

The list of everything to carry in is `docs/airgap/transfer-manifest.md`. The next step is `airgap-transfer`.
