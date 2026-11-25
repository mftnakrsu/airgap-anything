# Docker Compose files

## Contents

- Rules for every service
- Template
- `.env.example` template
- Placing the egress settings
- Harbor's `harbor.yml`
- Sources

Goal: `docs/airgap/install/compose/compose.yaml`, `compose/.env.example` and, when the registry is Harbor, `compose/harbor/harbor.yml`, written from the approved `plan.md`. Values come from the catalog entries and the blueprint; anything else carries a comment `# unverified: …` that names the runbook step which checks it.

## Rules for every service

- `image:` is the manifest's reference, with the manifest's tag. When the blueprint has a registry, it is the manifest's Target path (`REGISTRY_HOST/…`): the runbook's registry step tags the loaded image with that name, so the engine holds it locally under exactly the name the file uses. Never `latest`: Compose's `missing` policy pulls `latest` even when it is present.
- `restart: unless-stopped` on every service, so a host reboot brings back what was running (Compose: the policy "restarts the container irrespective of the exit code but stops" only when the container is stopped by hand).
- `pull_policy: never` on every service. Why: "If there is no cached image, a failure is reported", so a missing image fails at once instead of trying a registry that inside the network does not exist. Never pull images inside; a missing image is carried in again.
- GPUs: `deploy.resources.reservations.devices` with `driver: nvidia`, `capabilities: [gpu]` (required), and either `count: N` or `device_ids: ['0', '3']` (mutually exclusive) with N or the IDs from blueprint §5 for this host. Never `count: all` and never leave `count` out: "If `count` is set to `all` or not specified, all GPUs available on the host are used". Two services on one host never list the same device; with more than one GPU service per host, use `device_ids`.
- `--tensor-parallel-size` equals the GPUs per replica of blueprint §5, written in the `command` string, on one line with its number.
- `healthcheck:` only where the catalog entry documents an endpoint. Otherwise the service gets the comment `# unverified: no documented health check`, and its runbook step checks that the container runs.
- `depends_on:` with `condition: service_healthy` on a dependency that has a `healthcheck`, `condition: service_started` on one that has none. Why: with the short syntax, Compose does not wait for health.
- Networks: `backend` with `internal: true` for every service; `frontend` (not internal) only for a service that publishes a port to people or to the runbook's checks. Whether a published port works on a service attached only to an internal network is not documented, so a service with `ports:` also joins `frontend`.
- Volumes: named volumes for data (kept by `docker compose down`, removed by `down -v`); the model folder as a bind mount from `/srv/models`.
- `env_file: .env` on every service that needs a secret; the secret's name appears in `.env.example`, its value never appears in any file the skill writes.
- A component outside the catalog is written from the user's facts (`references/questions.md`, question 7), and every line it adds carries `# unverified: from the user`.

## Template

Fill in the parts in capitals. One service block per component of `plan.md`; the blocks below show the registry, vLLM and the UI, and every other component follows the same rules. Placeholders: `PROJECT` is the project's name; `MODEL_DIR` and `SERVED_NAME` come from manifest section 2 and the blueprint's `llm-serving` decision; `N` and the device IDs from blueprint §5; images and tags from manifest section 1 (`vllm`, `open-webui` and `distribution-registry` catalog entries); the `environment` lines from manifest section 4.

```yaml
name: PROJECT

services:
  registry:
    image: registry:3.1.2
    pull_policy: never
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      OTEL_TRACES_EXPORTER: none
    volumes:
      - registry-data:/var/lib/registry
    networks: [frontend, backend]
    # unverified: no documented health check

  vllm:
    image: REGISTRY_HOST/vllm/vllm-openai:v0.34.0
    pull_policy: never
    restart: unless-stopped
    command: /srv/models/MODEL_DIR --served-model-name SERVED_NAME --tensor-parallel-size N
    env_file: .env
    environment:
      VLLM_NO_USAGE_STATS: "1"
      HF_HUB_DISABLE_TELEMETRY: "1"
      HF_HUB_OFFLINE: "1"
    # vLLM: run with --ipc=host or --shm-size (catalog). unverified: Compose's ipc page lists only
    # shareable and service:NAME; Docker takes host at start, and INSTALL.md step 5 (vLLM healthy) shows whether it worked.
    ipc: host
    volumes:
      - type: bind
        source: /srv/models
        target: /srv/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: N
              capabilities: [gpu]
    healthcheck:
      # /metrics is outside the paths --api-key protects (catalog). unverified: curl inside the image.
      test:
        - CMD
        - curl
        - -f
        - http://localhost:8000/metrics
      # unverified: chosen values, not from the catalog (the Compose page's example uses 1m30s, 10s, 3, 40s).
      # start_period is long because a large model loads for minutes; INSTALL.md waits the same 30 minutes.
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30m
    networks: [backend]

  ui:
    image: REGISTRY_HOST/open-webui/open-webui:v0.13.4
    pull_policy: never
    restart: unless-stopped
    env_file: .env
    environment:
      OPENAI_API_BASE_URL: http://vllm:8000/v1
      OFFLINE_MODE: "true"
      ENABLE_VERSION_UPDATE_CHECK: "false"
      ENABLE_COMMUNITY_SHARING: "false"
    ports:
      - "8080:8080"
    volumes:
      - ui-data:/app/backend/data
    depends_on:
      vllm:
        condition: service_healthy
    networks: [frontend, backend]
    # unverified: no documented health check

networks:
  backend:
    internal: true
  frontend: {}

volumes:
  registry-data:
  ui-data:
```

Notes on the template:

- `interval`, `timeout`, `retries` and `start_period: 30m` are `unverified` chosen values: the catalog gives no load time, and a large model with compiled kernels can take long. The runbook's `--wait-timeout 1800` and `--timeout=30m` are the same 30 minutes, chosen for the same reason; the benchmark of blueprint §9 measures the real start time, and the values follow it.
- vLLM reads its key from `VLLM_API_KEY` in `.env` (the catalog: `--api-key` or `VLLM_API_KEY`); Open WebUI reads the same value as `OPENAI_API_KEY`. With a gateway in the blueprint, the UI points at the gateway (`http://GATEWAY_SERVICE:4000/v1` for LiteLLM), only the gateway reaches vLLM (which stays on `backend` with no `ports:`), and the gateway publishes `"4000:4000"` and joins `frontend`, so step 7 of the runbook reaches it from the host. Without a gateway, vLLM publishes `"127.0.0.1:8000:8000"` (on the host only, because the engine's `--api-key` does not protect every path) and joins `frontend` too, so step 7 reaches it on the host. Step 5's vLLM check runs inside the container (`docker compose exec`) and works in both designs.
- Services reach each other by service name on a shared network (`http://vllm:8000/v1`).
- `device_ids` in place of `count`: `device_ids: ['0', '1']`, strings, as `nvidia-smi` on the host numbers the GPUs.
- One replica spanning 8 GPUs is one service with `count: 8` and `--tensor-parallel-size 8`. Two replicas on one host are two services with disjoint `device_ids`.
- Without a registry in the blueprint, drop the `registry` service and use the manifest's Image column as `image:`.
- AMD, Intel or CPU hosts use the manifest's image for that hardware; the Compose GPU page documents NVIDIA only, so any device setting for the others is `unverified`.
- Compose itself: when the hosts lack the plugin, the manifest's `docker-compose` row carries the binary; if it has none, add one "(from airgap-install)".

## `.env.example` template

Names only, each with the step of `INSTALL.md` that fills it. It is copied by nobody: the runbook writes `.env` itself, so a value can never be copied from here.

```sh
# Filled by INSTALL.md step 4 (openssl rand -hex 32). Never commit .env.
VLLM_API_KEY=
# Filled by INSTALL.md step 4, the same value as VLLM_API_KEY.
OPENAI_API_KEY=
# Filled by INSTALL.md step 4 (openssl rand -hex 32). Keep it stable: a new value logs everyone out.
WEBUI_SECRET_KEY=
```

One line per secret any service reads. A value built from a secret (a database URL with its password) is written only where the component documents it; otherwise it is an open item in `plan.md`.

## Placing the egress settings

Every row of manifest section 4 for a component goes into that component's service, in `environment` (an environment variable) or in `command` (a flag), exactly as the manifest writes it; a setting that lives in the component's own configuration file goes into `compose/config/COMPONENT.EXT`, mounted into the service. A row that names a file to create instead (vLLM's `~/.config/vllm/do_not_track`) uses its environment-variable alternative. A row for the connected staging host only (the `hf` update check) is not placed. `INSTALL.md` step 6 checks each placed setting with `docker compose config`.

## Harbor's `harbor.yml`

When the blueprint's registry is Harbor (also in a Kubernetes design, where Harbor runs with Compose on its own host), the skill writes `compose/harbor/harbor.yml` and nothing else for Harbor. Why the subfolder: Harbor's `./install.sh` renders its own `docker-compose.yml` in the installer folder with `./prepare`; keeping `harbor.yml` apart from `compose/compose.yaml` keeps the two Compose projects from being confused, and the runbook copies the file into the extracted installer.

```yaml
hostname: REGISTRY_HOST
http:
  port: 80
# https: with the internal CA (questions.md, TLS). Without it, Harbor's docs call HTTP acceptable only in air-gapped test or development.
harbor_admin_password: HARBOR_ADMIN_PASSWORD
database:
  password: HARBOR_DB_PASSWORD
data_volume: /data
```

`HARBOR_ADMIN_PASSWORD` and `HARBOR_DB_PASSWORD` are placeholders that the runbook replaces inside with `openssl rand` output; the file never holds Harbor's default password. Copy the remaining keys from `harbor.yml.tmpl` of the carried installer; with `--with-trivy`, set `trivy.offline_scan: true` and `trivy.skip_update: true` (the `harbor` catalog entry). `hostname` is never `localhost` or `127.0.0.1`.

## Sources

| Tool | Command or key | Source |
|---|---|---|
| Docker Compose | `pull_policy: never`, `missing` pulls `latest` | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/reference/compose-file/container-spec.md |
| Docker Compose | `image`, `command`, `environment`, `env_file`, `ipc`, `networks`, `volumes` (long syntax) | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/reference/compose-file/container-spec.md |
| Docker Compose | `deploy.resources.reservations.devices`, `driver`, `count`, `device_ids`, `capabilities: [gpu]` | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/manuals/compose/how-tos/gpu-support.md |
| Docker Compose | `healthcheck` (`test`, `interval`, `timeout`, `retries`, `start_period`), `depends_on` `condition: service_healthy`, `service_started`, `ports` | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/reference/compose-file/workload-spec.md |
| Docker Compose | `restart: unless-stopped` | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/reference/compose-file/services.md |
| Docker Compose | `internal: true` | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/reference/compose-file/networks.md |
| Docker Compose | top-level `volumes` | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/reference/compose-file/volumes.md |
| Docker Compose | service names on a shared network | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/manuals/compose/how-tos/networking.md |
| Docker Compose | `down` keeps named volumes, `-v` removes them | https://github.com/docker/compose/blob/v5.8.0/docs/reference/compose_down.md |
| vLLM | `vllm/vllm-openai:v0.34.0`, port 8000, `--ipc=host` or `--shm-size`, `--api-key` / `VLLM_API_KEY`, `/metrics`, `VLLM_NO_USAGE_STATS`, `HF_HUB_OFFLINE`, `HF_HUB_DISABLE_TELEMETRY` | the `vllm` catalog entry (https://github.com/vllm-project/vllm/blob/v0.34.0/docs/deployment/docker.md, https://github.com/vllm-project/vllm/blob/v0.34.0/docs/usage/usage_stats.md, https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables) |
| vLLM | model path as the first argument after the image | https://github.com/vllm-project/vllm/blob/v0.34.0/docs/deployment/docker.md |
| vLLM | `--tensor-parallel-size` | https://github.com/vllm-project/vllm/blob/v0.34.0/docs/serving/parallelism_scaling.md |
| vLLM | `--served-model-name` | https://docs.vllm.ai/en/stable/cli/serve/ (cited by `airgap-rag`'s models reference) |
| Open WebUI | image `v0.13.4`, port 8080, `/app/backend/data`, `OPENAI_API_BASE_URL`, `OFFLINE_MODE`, `ENABLE_VERSION_UPDATE_CHECK`, `ENABLE_COMMUNITY_SHARING`, `WEBUI_SECRET_KEY` | the `open-webui` catalog entry (https://docs.openwebui.com/reference/env-configuration) |
| Distribution Registry | `registry:3.1.2`, port 5000, `/var/lib/registry`, `OTEL_TRACES_EXPORTER=none` | the `distribution-registry` catalog entry (https://github.com/distribution/distribution/blob/v3.1.2/docs/content/about/deploying.md) |
| Harbor | `hostname`, `http.port`, `harbor_admin_password`, `database.password`, `data_volume`, `trivy.offline_scan`, `trivy.skip_update` | https://github.com/goharbor/harbor/blob/v2.16.0/make/harbor.yml.tmpl |
| Harbor | `./install.sh` renders `docker-compose.yml` with `./prepare` | https://github.com/goharbor/harbor/blob/v2.16.0/make/install.sh |
