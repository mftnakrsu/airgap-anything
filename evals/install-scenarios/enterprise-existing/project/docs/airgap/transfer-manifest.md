# Transfer manifest: Company chat platform

- Blueprint: `docs/airgap/blueprint.md`, dated 2026-11-25
- Generated: 2026-11-25
- Hardware: nvidia
- Platform: linux/amd64

Replace `REGISTRY_HOST` with the address of the registry inside the network. `airgap-transfer` fills in digests, sizes and checksums when it fetches each artifact.

## 1. Container images

| Component | Version | Image | For | Target path |
|---|---|---|---|---|
| `vllm` | `v0.34.0` | `vllm/vllm-openai:v0.34.0` | nvidia | `REGISTRY_HOST/vllm/vllm-openai:v0.34.0` |
| `litellm` | `v1.110.2` | `ghcr.io/berriai/litellm:v1.110.2` | any | `REGISTRY_HOST/berriai/litellm:v1.110.2` |
| `open-webui` | `v0.13.4` | `ghcr.io/open-webui/open-webui:v0.13.4` | any | `REGISTRY_HOST/open-webui/open-webui:v0.13.4` |
| `keycloak` | `26.8.2` | `quay.io/keycloak/keycloak:26.8.2` | any | `REGISTRY_HOST/keycloak/keycloak:26.8.2` |
| `prometheus` | `v3.16.0` | `prom/prometheus:v3.16.0` | any | `REGISTRY_HOST/prom/prometheus:v3.16.0` |
| `grafana` | `13.3.1` | `grafana/grafana:13.3.1` | any | `REGISTRY_HOST/grafana/grafana:13.3.1` |
| `postgresql` | `18.7` | `postgres:18.7` | any | `REGISTRY_HOST/postgres:18.7` |
| `valkey` | `9.2.0` | `valkey/valkey:9.2.0` | any | `REGISTRY_HOST/valkey/valkey:9.2.0` |

Notes:

- `vllm`: the NVIDIA image is a multi-architecture manifest list: copy the platform of the target hosts.
- `harbor`: no image rows; the offline installer in section 3 carries its twelve images in `harbor.v2.16.0.tar.gz` and loads them with `docker load`.
- The existing OpenShift cluster is not installed by this design: no row for it.
- A reference without a namespace keeps its name in the target path: `postgres:18.7` becomes `REGISTRY_HOST/postgres:18.7`.

## 2. Model artifacts

| Model | Role | Files to carry |
|---|---|---|
| `company-70b`, 70 billion parameters, 8-bit (`fp8` or `int8`; name not given) | chat | weights (about 70 GB by params × bytes; the real files may differ), tokenizer and configuration files including `config.json`; the exact repository and revision are chosen during the transfer |

## 3. Packages and binaries

| Component | Version | File | Arch | URL | Publisher checksums |
|---|---|---|---|---|---|
| `harbor` | `v2.16.0` | `harbor-offline-installer-v2.16.0-amd64.tgz` | amd64 | https://github.com/goharbor/harbor/releases/download/v2.16.0/harbor-offline-installer-v2.16.0-amd64.tgz | https://github.com/goharbor/harbor/releases/download/v2.16.0/md5sum |
| custom: Docker Engine (registry host only) | | enumerate the artifacts by hand (packages for the server's operating system, which is unknown) | amd64 | | |
| custom: Docker Compose (registry host only) | | enumerate the artifacts by hand (Harbor's installer needs Docker Engine and Docker Compose; Compose is not in the catalog at the T3 orchestration floor) | amd64 | | |

## 4. Telemetry and egress settings to switch off before first start

| Component | What | Setting |
|---|---|---|
| `vllm` | Anonymous usage statistics (hardware, platform, version, model architecture, some engine settings, a random UUID) sent by default to `https://stats.vllm.ai` | `VLLM_NO_USAGE_STATS=1`, or `DO_NOT_TRACK=1`, or create `~/.config/vllm/do_not_track` |
| `vllm` | Hugging Face library telemetry (transformers, huggingface_hub) | `HF_HUB_DISABLE_TELEMETRY=1` |
| `vllm` | Hub update checks of the `hf` command-line tool (connected staging host only) | `HF_HUB_DISABLE_UPDATE_CHECK=1` |
| `litellm` | Latest-release check (`docs.litellm.ai`, `api.github.com`) from the Admin UI bell; on by default | `LITELLM_DISABLE_LATEST_RELEASE_CHECK=true`, or `LITELLM_OFFLINE_MODE=true` |
| `litellm` | Breached-password check at `api.pwnedpasswords.com`; on by default | `general_settings.password_policy_check_breached_passwords: false`, or `LITELLM_OFFLINE_MODE=true` |
| `litellm` | Catalog fetches of the model cost map, Anthropic beta headers, auto router presets, policy templates and blog posts; on by default | `LITELLM_LOCAL_MODEL_COST_MAP=true`, `LITELLM_LOCAL_ANTHROPIC_BETA_HEADERS=true`, `LITELLM_LOCAL_AUTOROUTER_PRESETS=true`, `LITELLM_LOCAL_POLICY_TEMPLATES=true`, `LITELLM_LOCAL_BLOG_POSTS=true`, or `LITELLM_OFFLINE_MODE=true`. This design instead serves the cost map from an internal copy at `LITELLM_MODEL_COST_MAP_URL` and sets the other four switches. |
| `litellm` | Prisma CLI update check at `checkpoint.prisma.io`; on by default | `CHECKPOINT_DISABLE=1` |
| `litellm` | License check at `https://license.litellm.ai/verify_license/<key>` for a key that fails the offline signature check; offline mode does not stop it | Not applicable: leave `LITELLM_LICENSE` unset, or use a key that passes the offline signature check |
| `litellm` | Usage telemetry; off unless a group and destination are chosen | Nothing to disable by default; `LITELLM_TELEMETRY_DISABLED=true` forces it off |
| `open-webui` | Analytics switches of bundled libraries (Scarf, DO_NOT_TRACK, ChromaDB) | Keep `SCARF_NO_ANALYTICS=true`, `DO_NOT_TRACK=true`, `ANONYMIZED_TELEMETRY=false` (set in the official image) |
| `open-webui` | Version update check at `https://api.github.com/repos/open-webui/open-webui/releases/latest`; on by default | `ENABLE_VERSION_UPDATE_CHECK=false`, or `OFFLINE_MODE=true` |
| `open-webui` | Open WebUI Community sharing options; on by default | `ENABLE_COMMUNITY_SHARING=false` |
| `open-webui` | External avatar redirects exposing viewer IP, User-Agent and Referer; on by default | `ENABLE_PROFILE_IMAGE_URL_FORWARDING=false` (read at startup only) |
| `open-webui` | OpenTelemetry export; off by default | Leave `ENABLE_OTEL=false` |
| `open-webui` | `CUSTOM_NAME` polls `api.openwebui.com`; off while unset | Leave `CUSTOM_NAME` unset |
| `keycloak` | OpenTelemetry export of traces, logs and metrics; each signal off by default | Leave the three signals off, or build with `--features-disabled=opentelemetry` |
| `prometheus` | — | None documented |
| `grafana` | Anonymous usage statistics to `stats.grafana.org` every 24 hours; on by default | `[analytics] reporting_enabled = false` |
| `grafana` | Check for new Grafana versions every ten minutes; on by default | `[analytics] check_for_updates = false` |
| `grafana` | Check for plugin updates at grafana.com every ten minutes; on by default | `[analytics] check_for_plugin_updates = false` |
| `grafana` | Gravatar profile images from `https://secure.gravatar.com/avatar`; on by default | `[security] disable_gravatar = true` |
| `postgresql` | — | None documented |
| `valkey` | — | None documented |
| `harbor` | Trivy usage telemetry and version check to `https://check.trivy.dev` (only with `--with-trivy`; this design installs without it) | No Harbor setting; block `check.trivy.dev` |
| `harbor` | Trivy Java package lookups at Maven Central (only with `--with-trivy`) | `trivy.offline_scan: true` in `harbor.yml` |

## 5. Runtime downloads to stage in advance

| Component | Download |
|---|---|
| `vllm` | Model weights, configuration and tokenizer: stage on the connected host (for example `hf download <model>`) and give `vllm serve` a local path |
| `vllm` | Hugging Face offline switch: `HF_HUB_OFFLINE=1` so no call reaches the Hub and a missing file fails |
| `vllm` | Internal mirror alternative: `HF_ENDPOINT` to a Hugging Face-compatible mirror (not used by this design) |
| `vllm` | Compiled kernels (CUDA): `vllm download-kernels` installs FlashInfer's precompiled kernels; without them vLLM downloads and compiles kernels at startup. Run it on the connected host and in custom images; check the stock image's offline start (blueprint section 9) |
| `vllm` | API documentation page needs the internet by default: start with `--enable-offline-docs` |
| `vllm` | vLLM Recipes (CPU image only, `serve_with_recipe.sh`) query `recipes.vllm.ai`: not used |
| `litellm` | Model cost map: carry `model_prices_and_context_window.json` from the LiteLLM repository, add this model's internal price, serve it internally and set `LITELLM_MODEL_COST_MAP_URL` (read at startup) |
| `litellm` | Other catalogs (Anthropic beta headers, auto router presets, policy templates, blog posts, release info): bundled copies with the `LITELLM_LOCAL_*` switches of section 4 |
| `litellm` | Tokenizers: legacy tokenizers from `openaipublic.blob.core.windows.net` unless placed in `CUSTOM_TIKTOKEN_CACHE_DIR`; Hugging Face tokenizers unless `litellm_settings.disable_hf_tokenizer_download: true` |
| `litellm` | Hugging Face lookups with no documented switch (context window of `huggingface/` models, chat templates for providers that build a prompt, including vLLM, and the task of `huggingface/` embedding models): a custom prompt template skips the chat-template lookup; check for blocked attempts at first start |
| `litellm` | Model info refresh of `{api_base}/v1/models` every 5 minutes (own backend): `general_settings.disable_model_info_refresh: true` |
| `litellm` | Image URLs in requests are downloaded by token counting: not expected for text chat |
| `litellm` | Prisma CLI, engines and Node.js on a pip install: the Docker image includes them and sets `PRISMA_OFFLINE_MODE=true` |
| `litellm` | Callback packages (supabase, sentry, slack) run `pip install` when missing: not used |
| `litellm` | Admin UI and API docs: `/redoc` loads from `cdn.jsdelivr.net` and `fonts.googleapis.com` (`NO_REDOC=True`); MCP server icons from `cdn.simpleicons.org` do not show when blocked |
| `open-webui` | Models baked into the standard image (embedding `sentence-transformers/all-MiniLM-L6-v2`, `TaylorAI/bge-micro-v2`, faster-whisper `base`, `cl100k_base`): nothing to stage while the defaults are kept |
| `open-webui` | A different embedding, reranking or Whisper model: stage with `snapshot_download` and copy into `/app/backend/data/cache/...` (not used) |
| `open-webui` | Hugging Face check at every start while `RAG_EMBEDDING_MODEL_AUTO_UPDATE` is true: `OFFLINE_MODE=true` (also `HF_HUB_OFFLINE=1`, `RAG_EMBEDDING_MODEL_AUTO_UPDATE=false`, `RAG_RERANKING_MODEL_AUTO_UPDATE=false`, `WHISPER_MODEL_AUTO_UPDATE=false`) |
| `open-webui` | pip installs of tool and function requirements: `OFFLINE_MODE` skips them; `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS=false` |
| `open-webui` | Slim image only (tiktoken encoding, code interpreter packages from `cdn.jsdelivr.net`): not used, the standard image is carried |
| `open-webui` | Content extraction and web loading services (Tika, Docling, web search): none added; keep any later addition on the internal network |
| `grafana` | Default preinstalled plugins downloaded at startup and auto-updated: `[plugins] preinstall_disabled = true`; carry any needed plugin as a ZIP from `https://grafana.com/api/plugins/<plugin id>/versions/<version>/download` |
| `grafana` | Missing bundled plugins are downloaded from grafana.com at startup; the `bundled_plugins` directory decides whether the bundled data sources work (check offline, blueprint section 9) |
| `grafana` | Plugin signature public key: `public_key_retrieval_disabled = true` uses the hard-coded key |
| `harbor` | Trivy vulnerability database (only with `--with-trivy`; not used): stage `ghcr.io/aquasecurity/trivy-db:2` and `ghcr.io/aquasecurity/trivy-java-db:1` by hand or through an internal registry, with `trivy.skip_update: true` |

## 6. Per-tool skills

| Component | Repository | Skill |
|---|---|---|
| `vllm` | `ScaleDockHQ/llm-skills` | `vllm` |
| `vllm` | `air-gapped/skills` | `vllm-configuration` |
| `litellm` | `ScaleDockHQ/llm-skills` | `litellm` |
| `litellm` | `air-gapped/skills` | `litellm-api` |
| `litellm` | `air-gapped/skills` | `litellm-valkey` |
| `open-webui` | `ScaleDockHQ/llm-skills` | `open-webui` |
| `open-webui` | `air-gapped/skills` | `open-webui-valkey-websocket` |
| `open-webui` | `air-gapped/skills` | `open-webui-embeddings` |
| `keycloak` | `air-gapped/skills` | `keycloak-iam` |
| `prometheus`, `grafana` | `air-gapped/skills` | `prometheus-mimir-grafana` |
| `prometheus`, `grafana` | `ScaleDockHQ/llm-skills` | `prometheus-grafana-llm` |
| `valkey` | `air-gapped/skills` | `redis-to-valkey` |
| `harbor` | `air-gapped/skills` | `k8s-components-checker` |

## 7. Verification steps

1. On the connected side, record a SHA-256 checksum for every file and the digest of every image.
2. Verify publisher checksums where the publisher provides them.
3. After the transfer, recompute every checksum inside the network before importing anything.
4. Import only artifacts whose checksums match, then apply the settings of section 4 before first start.
