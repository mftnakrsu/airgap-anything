# Transfer manifest: lab-assistant

- Blueprint: docs/airgap/blueprint.md, dated 2026-11-24
- Generated: 2026-11-24
- Hardware: nvidia
- Platform: linux/amd64

Replace `REGISTRY_HOST` with the address of the registry inside the network. `airgap-transfer` fills in digests, sizes and checksums when it fetches each artifact.

## 1. Container images

| Component | Version | Image | For | Target path |
|---|---|---|---|---|
| `ollama` | `0.40.17` | `ollama/ollama:0.40.17` | nvidia, intel, cpu | `REGISTRY_HOST/ollama/ollama:0.40.17` |
| `open-webui` | `v0.13.4` | `ghcr.io/open-webui/open-webui:v0.13.4` | any | `REGISTRY_HOST/open-webui/open-webui:v0.13.4` |
| `distribution-registry` | `v3.1.2` | `registry:3.1.2` | any | `REGISTRY_HOST/registry:3.1.2` |

## 2. Model artifacts

| Model | Role | Files to carry |
|---|---|---|
| lab-8b | chat | weights, tokenizer and configuration files |

## 3. Packages and binaries

| Component | Version | File | Arch | URL | Publisher checksums |
|---|---|---|---|---|---|
| `docker-compose` | `v5.8.0` | `docker-compose-linux-x86_64` | amd64 | https://github.com/docker/compose/releases/download/v5.8.0/docker-compose-linux-x86_64 | https://github.com/docker/compose/releases/download/v5.8.0/checksums.txt |
| custom: Docker Engine (outside the catalog) | | enumerate the artifacts by hand | | | |

## 4. Telemetry and egress settings to switch off before first start

| Component | What | Setting |
|---|---|---|
| `ollama` | Update check of the macOS and Windows apps: the FAQ states that Ollama on macOS and Windows automatically downloads updates; the source at the tag requests https://ollama.com/api/update about every hour with the operating system, architecture and version (and a device ID on macOS). On Linux the documented update path is re-running the install script; no background check is documented there. | No documented switch for the check. The app's auto-update setting (source: app/updater/updater.go, not documentation) stops the download of an update but the source still performs the check; block ollama.com for the app, or use the Linux server or the Docker image. |
| `ollama` | Ollama cloud features (cloud-hosted models and web search) send prompts to ollama.com when the instance is signed in and a cloud model or web search is used; the cloud FAQ says Ollama collects basic account information and limited usage metadata that does not include prompt or response content. | OLLAMA_NO_CLOUD=1, or disable_ollama_cloud set to true in ~/.ollama/server.json; restart Ollama, and the log shows 'Ollama cloud disabled: true'. |
| `open-webui` | Analytics and telemetry switches of bundled libraries (Scarf analytics, DO_NOT_TRACK, ChromaDB anonymized telemetry): the documentation does not describe any phone-home feature; the Dockerfile at the tag (source code, not a documentation page) already sets SCARF_NO_ANALYTICS=true, DO_NOT_TRACK=true and ANONYMIZED_TELEMETRY=false in the image, and .env.example sets the same three. | Keep SCARF_NO_ANALYTICS=true, DO_NOT_TRACK=true and ANONYMIZED_TELEMETRY=false (set in the official images, in .env.example for other installs). |
| `open-webui` | Version update check: the server asks https://api.github.com/repos/open-webui/open-webui/releases/latest (URL from source code, backend/open_webui/main.py), on by default in release builds (the official images built from main or a release tag, and the pip package), with a one-second timeout; the interface then shows an update notice or 'Could not check for updates'. | ENABLE_VERSION_UPDATE_CHECK=false, or OFFLINE_MODE=true (which sets it to false). |
| `open-webui` | Open WebUI Community sharing: options that let users send chats, models, prompts, tools, functions, skills and usage statistics to the Open WebUI Community and links to community content; on by default; the documentation describes them as share options in the interface, not as an automatic report (hardening guide and environment variable reference). | ENABLE_COMMUNITY_SHARING=false |
| `open-webui` | External avatars: the profile-image endpoints redirect the browser to an external http(s) image URL stored in a profile, which exposes the viewer's IP address, User-Agent and Referer to that host; on by default (hardening guide). A 'Gravatar' button in the profile settings makes the user's avatar a www.gravatar.com URL (source code of the settings component, user-initiated). | ENABLE_PROFILE_IMAGE_URL_FORWARDING=false (read at startup only). |
| `open-webui` | OpenTelemetry export of traces, metrics and logs to a collector you name: off by default (ENABLE_OTEL=False; with only the master switch set nothing is exported), so it sends nothing unless an operator turns it on. | Leave ENABLE_OTEL=false (the default); signals are ENABLE_OTEL_TRACES, ENABLE_OTEL_METRICS and ENABLE_OTEL_LOGS. |
| `open-webui` | CUSTOM_NAME (legacy branding variable): the environment variable reference says it 'Sets WEBUI_NAME but polls api.openwebui.com for metadata'. From source code (backend/open_webui/config.py at the tag, not from a documentation page): when CUSTOM_NAME is set, the server requests https://api.openwebui.com/api/v1/custom/<CUSTOM_NAME> at start and, if the answer has a logo or splash image, downloads it from api.openwebui.com (or the URL given) and writes it as the favicon and the splash image. Off while CUSTOM_NAME is unset, which is the default. | Leave CUSTOM_NAME unset (the default). |
| `distribution-registry` | OpenTelemetry trace export: the documentation says the registry uses OpenTelemetry for logs and traces, configured with the standard OTEL environment variables, and by default attempts to export traces to an OTLP collector on localhost:4318 (the deployment page: localhost:4318; the configuration page: https://localhost:4318/v1/traces). The target is the local host, so nothing leaves the host unless an OTEL variable points elsewhere. | OTEL_TRACES_EXPORTER=none (for example docker run -e OTEL_TRACES_EXPORTER=none ...), documented on the deployment and configuration pages; the configuration page also allows setting it to a trace collector. |

## 5. Runtime downloads to stage in advance

| Component | Download |
|---|---|
| `ollama` | Models: Ollama pulls models from the Internet (FAQ: 'Ollama pulls models from the Internet and may require a proxy server', using HTTPS_PROXY). A model that is not in the local model store is fetched when it is pulled or first run. Stage models in advance by importing files (next item). |
| `ollama` | Pointing Ollama at models copied in by hand: the documented route is to import files. Create a Modelfile whose FROM line names a GGUF file (FROM /path/to/file.gguf, or FROM /path/to/model-*.gguf for a split model) or a directory of Safetensors weights (FROM /path/to/safetensors/directory), then run ollama create my-model. Ollama does not quantize GGUF files on import. The model store location is set with OLLAMA_MODELS (default ~/.ollama/models on macOS, /usr/share/ollama/.ollama/models on Linux with the standard installer); on Linux the ollama user needs read and write access to that directory. The documentation does not describe copying a populated model store from another machine. |
| `ollama` | Cloud features: if the instance is signed in, cloud-hosted models and web search go to ollama.com; turn them off with OLLAMA_NO_CLOUD=1 (see telemetry list). |
| `open-webui` | Models the standard images bring with them: the Dockerfile at the tag downloads the default embedding model sentence-transformers/all-MiniLM-L6-v2, the auxiliary embedding model TaylorAI/bge-micro-v2, the faster-whisper model base and the tiktoken encoding cl100k_base at image build time (source code), and the quick-start page says :main bundles the speech-to-text and embedding models. These are in the non-slim images (v0.13.4, -cuda, -cuda126, -ollama); the slim image has none (the page says it never downloads a model). The paths are below /app/backend/data/cache (SENTENCE_TRANSFORMERS_HOME, WHISPER_MODEL_DIR and TIKTOKEN_CACHE_DIR in the Dockerfile). |
| `open-webui` | Models and caches you must stage when you choose something else: a different embedding, reranking or Whisper model. The offline-mode tutorial downloads them on a connected machine with huggingface_hub snapshot_download and copies the cache to /app/backend/data/cache/embedding/models/ (embedding) and /app/backend/data/cache/whisper/models/ (Whisper), keeping the structure, then sets RAG_EMBEDDING_MODEL or WHISPER_MODEL to the matching identifier. A reranking model is prepared the same way. With an external embedding provider (RAG_EMBEDDING_ENGINE set to ollama, openai or azure_openai) none of these is needed. |
| `open-webui` | Hugging Face traffic at start and use: while RAG_EMBEDDING_MODEL_AUTO_UPDATE is true, every start with the default SentenceTransformers engine contacts Hugging Face to check the model, even when it is cached, and the server does not accept connections until that finishes (environment variable reference). Switch: OFFLINE_MODE=true, which disables Hugging Face Hub downloads, version update checks and the automatic updates of the embedding, reranking and Whisper models, and sets HF_HUB_OFFLINE=1 and the three *_AUTO_UPDATE flags to false; the tutorial lists them anyway (OFFLINE_MODE=true, HF_HUB_OFFLINE=1, RAG_EMBEDDING_MODEL_AUTO_UPDATE=false, RAG_RERANKING_MODEL_AUTO_UPDATE=false, WHISPER_MODEL_AUTO_UPDATE=false). With HF_HUB_OFFLINE=1 a missing model cannot be downloaded, so a fresh install without models starts but fails at the first document upload or retrieval with 'No embedding model is loaded'. |
| `open-webui` | Python packages for tools and functions: a tool or function that declares requirements in its frontmatter gets them installed with pip at load time; OFFLINE_MODE skips these installs, so the packages must already be in the image (environment variable reference). ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS=false also turns the installs off (hardening guide). |
| `open-webui` | Slim image only: the token text splitter downloads its tiktoken encoding on first use, so use the character splitter; the code interpreter makes the browser fetch its Python packages from cdn.jsdelivr.net, so leave it off in a disconnected network or use a standard image (quick-start page). Standard images bundle those packages according to the same page. |
| `open-webui` | Content extraction and web loading: PDFs and Office files in the slim image need Tika, Docling or another extraction service; the default pypdf extractor runs inside the standard image. Services you add (Tika, Docling, embedding, web search) are new outbound destinations; keep them on the internal network. |
| `docker-compose` | Images of the application: the Compose file names the images, and docker compose up pulls the ones that are not in the engine's image cache from their registry (pull_policy missing is the default when the Compose file has no build section; the latest tag is always pulled even then). In an air-gapped site, load the images into the engine beforehand (or push them to an internal registry and name that registry in the Compose file) and set pull_policy to never for a service to make Compose fail instead of reaching out (container-spec reference). |
| `distribution-registry` | Images stored in the registry: the registry holds only what is pushed to it. The deployment page's air-gap section says to build the registry's data volume on a connected host that can docker pull the images wanted and then migrate the data volume to the air-gapped network; images with non-distributable layers (its example is the official Microsoft Windows base images) do not carry those layers into a private registry unless the Docker daemon is configured with allow-nondistributable-artifacts for it. |
| `distribution-registry` | Pull-through cache (only when configured): with the proxy section set (remoteurl, for example https://registry-1.docker.io), the registry fetches images from that upstream registry the first time they are requested and, for a tag pull, checks the remote for newer content; the mirror page says one upstream can be mirrored at a time and that Docker Hub mirrors remain subject to Docker's fair usage policy. Leave proxy unset in an air-gapped site. |

## 6. Per-tool skills

| Component | Repository | Skill |
|---|---|---|
| `ollama` | `ScaleDockHQ/llm-skills` | `ollama` |
| `open-webui` | `ScaleDockHQ/llm-skills` | `open-webui` |
| `open-webui` | `air-gapped/skills` | `open-webui-valkey-websocket` |
| `open-webui` | `air-gapped/skills` | `open-webui-embeddings` |

## 7. Verification steps

1. On the connected side, record a SHA-256 checksum for every file and the digest of every image.
2. Verify publisher checksums where the publisher provides them.
3. After the transfer, recompute every checksum inside the network before importing anything.
4. Import only artifacts whose checksums match, then apply the settings of section 4 before first start.
