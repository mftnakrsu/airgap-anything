# Transfer manifest: Research lab chat assistant

- Blueprint: `docs/airgap/blueprint.md`, dated 2026-11-25
- Generated: 2026-11-25
- Hardware: nvidia
- Platform: linux/amd64

Replace `REGISTRY_HOST` with the address of the registry inside the network. `airgap-transfer` fills in digests, sizes and checksums when it fetches each artifact.

## 1. Container images

| Component | Version | Image | For | Target path |
|---|---|---|---|---|
| `vllm` | `v0.34.0` | `vllm/vllm-openai:v0.34.0` | nvidia | `REGISTRY_HOST/vllm/vllm-openai:v0.34.0` |
| `open-webui` | `v0.13.4` | `ghcr.io/open-webui/open-webui:v0.13.4` | any | `REGISTRY_HOST/open-webui/open-webui:v0.13.4` |
| `distribution-registry` | `v3.1.2` | `registry:3.1.2` | any | `REGISTRY_HOST/registry:3.1.2` |

Notes:

- `vllm`: the NVIDIA image is a multi-architecture manifest list: copy the platform of the target hosts.
- `docker-compose`: no image rows; it is a binary in section 3.
- Before the registry runs, these images are loaded into Docker Engine directly from the media (`docker load`), then pushed to it.

## 2. Model artifacts

| Model | Role | Files to carry |
|---|---|---|
| `lab-8b`, 8 billion parameters, 8-bit (`fp8` or `int8`; name not given) | chat | weights (about 8 GB by params × bytes; the real files may differ), tokenizer and configuration files including `config.json`; the exact repository and revision are chosen during the transfer |

## 3. Packages and binaries

| Component | Version | File | Arch | URL | Publisher checksums |
|---|---|---|---|---|---|
| `docker-compose` | `v5.8.0` | `docker-compose-linux-x86_64` | amd64 | https://github.com/docker/compose/releases/download/v5.8.0/docker-compose-linux-x86_64 | https://github.com/docker/compose/releases/download/v5.8.0/checksums.txt |
| custom: Docker Engine | | enumerate the artifacts by hand (packages for the server's operating system, which is unknown) | amd64 | | |
| custom: host GPU stack | | enumerate the artifacts by hand (for NVIDIA: the driver and the NVIDIA Container Toolkit) | amd64 | | |

## 4. Telemetry and egress settings to switch off before first start

| Component | What | Setting |
|---|---|---|
| `vllm` | Anonymous usage statistics (hardware, platform, version, model architecture, some engine settings, a random UUID) sent by default to `https://stats.vllm.ai` | `VLLM_NO_USAGE_STATS=1`, or `DO_NOT_TRACK=1`, or create `~/.config/vllm/do_not_track` |
| `vllm` | Hugging Face library telemetry (transformers, huggingface_hub) | `HF_HUB_DISABLE_TELEMETRY=1` |
| `vllm` | Hub update checks of the `hf` command-line tool (connected staging host only) | `HF_HUB_DISABLE_UPDATE_CHECK=1` |
| `open-webui` | Analytics switches of bundled libraries (Scarf, DO_NOT_TRACK, ChromaDB) | Keep `SCARF_NO_ANALYTICS=true`, `DO_NOT_TRACK=true`, `ANONYMIZED_TELEMETRY=false` (set in the official image) |
| `open-webui` | Version update check at `https://api.github.com/repos/open-webui/open-webui/releases/latest`; on by default | `ENABLE_VERSION_UPDATE_CHECK=false`, or `OFFLINE_MODE=true` |
| `open-webui` | Open WebUI Community sharing options; on by default | `ENABLE_COMMUNITY_SHARING=false` |
| `open-webui` | External avatar redirects exposing viewer IP, User-Agent and Referer; on by default | `ENABLE_PROFILE_IMAGE_URL_FORWARDING=false` (read at startup only) |
| `open-webui` | OpenTelemetry export; off by default | Leave `ENABLE_OTEL=false` |
| `open-webui` | `CUSTOM_NAME` polls `api.openwebui.com`; off while unset | Leave `CUSTOM_NAME` unset |
| `docker-compose` | — | None documented |
| `distribution-registry` | OpenTelemetry trace export: by default the registry tries to export traces to an OTLP collector on localhost:4318; nothing leaves the host unless an OTEL variable points elsewhere | `OTEL_TRACES_EXPORTER=none` |

## 5. Runtime downloads to stage in advance

| Component | Download |
|---|---|
| `vllm` | Model weights, configuration and tokenizer: stage on the connected host (for example `hf download <model>`) and give `vllm serve` a local path |
| `vllm` | Hugging Face offline switch: `HF_HUB_OFFLINE=1` so no call reaches the Hub and a missing file fails |
| `vllm` | Internal mirror alternative: `HF_ENDPOINT` to a Hugging Face-compatible mirror (not used by this design) |
| `vllm` | Compiled kernels (CUDA): `vllm download-kernels` installs FlashInfer's precompiled kernels; without them vLLM downloads and compiles kernels at startup. Run it on the connected host and in custom images; check the stock image's offline start (blueprint section 9) |
| `vllm` | API documentation page needs the internet by default: start with `--enable-offline-docs` |
| `vllm` | vLLM Recipes (CPU image only, `serve_with_recipe.sh`) query `recipes.vllm.ai`: not used |
| `open-webui` | Models baked into the standard image (embedding `sentence-transformers/all-MiniLM-L6-v2`, `TaylorAI/bge-micro-v2`, faster-whisper `base`, `cl100k_base`): nothing to stage while the defaults are kept |
| `open-webui` | A different embedding, reranking or Whisper model: stage with `snapshot_download` and copy into `/app/backend/data/cache/...` (not used) |
| `open-webui` | Hugging Face check at every start while `RAG_EMBEDDING_MODEL_AUTO_UPDATE` is true: `OFFLINE_MODE=true` (also `HF_HUB_OFFLINE=1`, `RAG_EMBEDDING_MODEL_AUTO_UPDATE=false`, `RAG_RERANKING_MODEL_AUTO_UPDATE=false`, `WHISPER_MODEL_AUTO_UPDATE=false`) |
| `open-webui` | pip installs of tool and function requirements: `OFFLINE_MODE` skips them; `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS=false` |
| `open-webui` | Slim image only (tiktoken encoding, code interpreter packages from `cdn.jsdelivr.net`): not used, the standard image is carried |
| `open-webui` | Content extraction and web loading services (Tika, Docling, web search): none added; keep any later addition on the internal network |
| `docker-compose` | Images of the application: load them beforehand or name the internal registry, and set `pull_policy: never` per service |
| `distribution-registry` | Images stored in the registry: it holds only what is pushed to it; build the data volume on a connected host that can `docker pull` the images wanted and migrate the volume, or push the carried images from inside |
| `distribution-registry` | Pull-through cache (only when configured): leave `proxy` unset in an air-gapped site |

## 6. Per-tool skills

| Component | Repository | Skill |
|---|---|---|
| `vllm` | `ScaleDockHQ/llm-skills` | `vllm` |
| `vllm` | `air-gapped/skills` | `vllm-configuration` |
| `open-webui` | `ScaleDockHQ/llm-skills` | `open-webui` |
| `open-webui` | `air-gapped/skills` | `open-webui-valkey-websocket` |
| `open-webui` | `air-gapped/skills` | `open-webui-embeddings` |

## 7. Verification steps

1. On the connected side, record a SHA-256 checksum for every file and the digest of every image.
2. Verify publisher checksums where the publisher provides them.
3. After the transfer, recompute every checksum inside the network before importing anything.
4. Import only artifacts whose checksums match, then apply the settings of section 4 before first start.
