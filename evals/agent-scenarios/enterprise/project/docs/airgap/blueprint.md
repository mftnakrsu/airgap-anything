# enterprise-code-platform: air-gapped blueprint

Status: approved. Date: 2026-11-24. Fixture for the airgap-agent evals: only the parts the agent skill reads are filled in. The format follows `examples/department/blueprint.md`. LiteLLM routes the model as `hosted_vllm/gpt-oss-120b`, so `/v1/responses` reaches vLLM natively.

## 1. Context and answers

| Question | Answer | From |
|---|---|---|
| `org.users_total` | 800 | the user |
| `org.departments` | 6 | the user |
| `org.isolation` | per_department | the user |
| `org.audit_required` | true | the user |
| `org.downtime_tolerance` | planned_only | the user |
| `org.ops_capacity` | platform_team | the user |
| `org.kubernetes_experience` | true | the user |
| `inside.operator` | people | the user |
| `workload.usage` | {"chat": 0.625, "code_assistant": 0.375} | the user |
| `workload.models` | [{"name": "gpt-oss-120b", "role": "code_assistant", "params_b": 117, "precision": "mxfp4", "context_tokens": 131072}] | the user |
| `hardware.gpus` | [{"model": "generic-141gb", "count": 8, "vram_gb": 141, "tdp_w": 700, "vendor": "nvidia"}] | the user |
| `hardware.cpu_arch` | amd64 | the user |
| `existing.identity` | ad_ldap | the user |
| `existing.api_gateway` | none | the user |
| `existing.kubernetes` | openshift | the user |
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

The engine serves gpt-oss-120b with `--max-model-len 131072`. Agents reach it only through the gateway.

### `llm-gateway`

- Components: `litellm` `v1.110.2`
- Existing: none
- Custom: none
- Benchmark only: none

## 6. Air-gap transfer

The list of everything to carry in is `docs/airgap/transfer-manifest.md`. The next step is `airgap-transfer`.
