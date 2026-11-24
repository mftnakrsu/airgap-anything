# enterprise-llm-platform: air-gapped blueprint

Status: approved. Date: 2026-11-24. Fixture for the airgap-transfer evals: only the parts the transfer reads are filled in.

## 1. Context and answers

| Question | Answer | From |
|---|---|---|
| `org.users_total` | 2000 | the user |
| `org.departments` | 12 | the user |
| `org.isolation` | per_department | the user |
| `org.audit_required` | true | the user |
| `org.downtime_tolerance` | none | the user |
| `org.ops_capacity` | platform_team | the user |
| `org.kubernetes_experience` | true | the user |
| `inside.operator` | local_agent | the user |
| `workload.usage` | {"chat": 0.7, "code_assistant": 0.2, "rag": 0.1} | the user |
| `workload.models` | [{"name": "company-70b", "role": "chat", "params_b": 70, "precision": "fp8", "context_tokens": 8192, "arch": {"layers": 80, "kv_heads": 8, "head_dim": 128, "kv_dtype": "fp16"}}] | the user |
| `hardware.gpus` | [{"model": "generic-141gb", "count": 24, "vram_gb": 141, "tdp_w": 700, "vendor": "nvidia"}] | the user |
| `hardware.cpu_arch` | amd64 | the user |
| `existing.identity` | ad_ldap | the user |
| `existing.api_gateway` | kong | the user |
| `existing.kubernetes` | openshift | the user |
| `transfer.channel` | staging_host | the user |
| `transfer.cadence` | monthly | the user |

## 4. Layer decisions

| Layer | Component | Version | Evidence |
|---|---|---|---|
| `llm-serving` | `vllm` | `v0.34.0` | docs |
| `llm-serving` | `sglang` (benchmark only) | `v0.5.23` | docs |
| `llm-gateway` | `litellm` | `v1.110.2` | docs |
| `ui` | `open-webui` | `v0.13.4` | docs |
| `identity` | `keycloak` | `26.8.2` | docs |
| `observability` | `prometheus` | `v3.16.0` | docs |
| `observability` | `grafana` | `13.3.1` | docs |
| `state` | `postgresql` | `18.7` | docs |
| `state` | `valkey` | `9.2.0` | docs |
| `registry` | `harbor` | `v2.16.0` | docs |

### `llm-serving`

- Components: `vllm` `v0.34.0`
- Existing: none
- Custom: none
- Benchmark only: `sglang` `v0.5.23`

### `llm-gateway`

- Components: `litellm` `v1.110.2`
- Existing: Kong
- Custom: none
- Benchmark only: none

### `ui`

- Components: `open-webui` `v0.13.4`
- Existing: none
- Custom: none
- Benchmark only: none

### `identity`

- Components: `keycloak` `26.8.2`
- Existing: Active Directory
- Custom: none
- Benchmark only: none

### `observability`

- Components: `prometheus` `v3.16.0`, `grafana` `13.3.1`
- Existing: none
- Custom: none
- Benchmark only: none

### `orchestration`

- Components: none
- Existing: OpenShift
- Custom: none
- Benchmark only: none

### `state`

- Components: `postgresql` `18.7`, `valkey` `9.2.0`
- Existing: none
- Custom: none
- Benchmark only: none

### `registry`

- Components: `harbor` `v2.16.0`
- Existing: none
- Custom: none
- Benchmark only: none

## 6. Air-gap transfer

The list of everything to carry in is `docs/airgap/transfer-manifest.md`. The next step is `airgap-transfer`.
