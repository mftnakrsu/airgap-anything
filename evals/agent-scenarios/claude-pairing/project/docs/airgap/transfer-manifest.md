# Transfer manifest: pairing-code-platform

- Blueprint: docs/airgap/blueprint.md, dated 2026-11-24
- Generated: 2026-11-24
- Hardware: nvidia
- Platform: linux/amd64

Replace `REGISTRY_HOST` with the address of the registry inside the network. `airgap-transfer` fills in digests, sizes and checksums when it fetches each artifact.

## 1. Container images

| Component | Version | Image | For | Target path |
|---|---|---|---|---|
| `vllm` | `v0.34.0` | `vllm/vllm-openai:v0.34.0` | nvidia | `REGISTRY_HOST/vllm/vllm-openai:v0.34.0` |
| `litellm` | `v1.110.2` | `ghcr.io/berriai/litellm:v1.110.2` | any | `REGISTRY_HOST/berriai/litellm:v1.110.2` |

## 2. Model artifacts

| Model | Role | Files to carry |
|---|---|---|
| GLM-4.6 | code_assistant | weights, tokenizer and configuration files |

## 3. Packages and binaries

| Component | Version | File | Arch | URL | Publisher checksums |
|---|---|---|---|---|---|
| `harbor` | `v2.16.0` | `harbor-offline-installer-v2.16.0-amd64.tgz` | amd64 | https://github.com/goharbor/harbor/releases/download/v2.16.0/harbor-offline-installer-v2.16.0-amd64.tgz | https://github.com/goharbor/harbor/releases/download/v2.16.0/md5sum |

## 4. Telemetry and egress settings to switch off before first start

| Component | What | Setting |
|---|---|---|
| `vllm` | Anonymous usage statistics sent by default to https://stats.vllm.ai. | VLLM_NO_USAGE_STATS=1 |
| `litellm` | Check for the latest LiteLLM release when the Admin UI notification bell is used; on by default. | LITELLM_DISABLE_LATEST_RELEASE_CHECK=true |

## 5. Runtime downloads to stage in advance

| Component | Download |
|---|---|
| `vllm` | Model weights, configuration and tokenizer, resolved against the Hugging Face Hub on first use unless HF_HUB_OFFLINE=1 and a local path are used. |
| `litellm` | Model cost map fetched from raw.githubusercontent.com at startup; LITELLM_LOCAL_MODEL_COST_MAP=true uses the bundled copy. |

## 6. Per-tool skills

| Component | Repository | Skill |
|---|---|---|
| `vllm` | `air-gapped/skills` | `vllm-configuration` |
| `litellm` | `air-gapped/skills` | `litellm-api` |

## 7. Verification steps

1. On the connected side, record a SHA-256 checksum for every file and the digest of every image.
2. Verify publisher checksums where the publisher provides them.
3. After the transfer, recompute every checksum inside the network before importing anything.
4. Import only artifacts whose checksums match, then apply the settings of section 4 before first start.
