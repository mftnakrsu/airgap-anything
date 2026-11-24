# lab-assistant: air-gapped blueprint

Status: approved. Date: 2026-11-24. Fixture for the airgap-transfer evals: only the parts the transfer reads are filled in.

## 1. Context and answers

| Question | Answer | From |
|---|---|---|
| `org.users_total` | 12 | the user |
| `org.departments` | 1 | the user |
| `org.isolation` | none | the user |
| `org.audit_required` | false | the user |
| `org.downtime_tolerance` | accepted | the user |
| `org.ops_capacity` | part_time_one | the user |
| `org.kubernetes_experience` | false | the user |
| `inside.operator` | people | the user |
| `workload.usage` | {"chat": 1.0} | the user |
| `workload.models` | [{"name": "lab-8b", "role": "chat", "params_b": 8, "precision": "fp8"}] | the user |
| `hardware.gpus` | [{"model": "generic-24gb", "count": 1, "vram_gb": 24, "vendor": "nvidia"}] | the user |
| `hardware.cpu_arch` | amd64 | the user |
| `existing.identity` | none | the user |
| `existing.api_gateway` | none | the user |
| `existing.kubernetes` | none | the user |
| `transfer.channel` | data_diode | the user |

## 4. Layer decisions

| Layer | Component | Version | Evidence |
|---|---|---|---|
| `llm-serving` | `ollama` | `0.40.17` | docs |
| `ui` | `open-webui` | `v0.13.4` | docs |
| `orchestration` | `docker-compose` | `v5.8.0` | docs |
| `registry` | `distribution-registry` | `v3.1.2` | docs |

### `llm-serving`

- Components: `ollama` `0.40.17`
- Existing: none
- Custom: none
- Benchmark only: none

### `llm-gateway`

- Components: none
- Existing: none
- Custom: none
- Benchmark only: none

### `ui`

- Components: `open-webui` `v0.13.4`
- Existing: none
- Custom: none
- Benchmark only: none

### `identity`

- Components: none
- Existing: none
- Custom: none
- Benchmark only: none

### `observability`

- Components: none
- Existing: none
- Custom: none
- Benchmark only: none

### `orchestration`

- Components: `docker-compose` `v5.8.0`
- Existing: none
- Custom: Docker Engine (outside the catalog)
- Benchmark only: none

### `state`

- Components: none
- Existing: none
- Custom: none
- Benchmark only: none

### `registry`

- Components: `distribution-registry` `v3.1.2`
- Existing: none
- Custom: none
- Benchmark only: none

## 6. Air-gap transfer

The list of everything to carry in is `docs/airgap/transfer-manifest.md`. The next step is `airgap-transfer`.
