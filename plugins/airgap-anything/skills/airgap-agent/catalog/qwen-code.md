# Qwen Code (`qwen-code`)

Terminal coding agent from the Qwen team that talks to any OpenAI-compatible endpoint. The default tool for an open-weight model inside the network.

| Field | Value |
|---|---|
| Kind | `coding-agent` |
| Version | `v0.28.4` |
| License | Apache-2.0 |
| Speaks | `chat-completions` (default), `responses` (optional, `"wireApi": "responses"`) |
| Install | release archive `qwen-code-linux-{x64,arm64}.tar.gz` with `SHA256SUMS`, installer `--archive PATH`; or npm `@qwen-code/qwen-code` (Node 22 or newer) |
| Evidence | docs |
| Last verified | 2026-11-24 |

## Choose when

- The model is open-weight and served by vLLM, SGLang or a gateway in front of them.
- The install must come from a checked archive: the docs describe `--archive PATH` with `SHA256SUMS` next to it.

## Avoid when

- Central enforcement must also cover the sandbox and command rules beyond settings: prefer `codex-cli` if its `/v1/responses` smoke test passes.

## Serving needs

- Sends tool definitions on every request: vLLM needs `--enable-auto-tool-choice`, a `--tool-call-parser` for the model family (`references/serving.md`) and the matching `--reasoning-parser`.
- Streams responses; `streamIdleTimeoutMs` sets the idle timeout.
- `id` in `modelProviders` equals `--served-model-name`; set `model.name` to the same value, as the docs' examples do. When the id does not start with `qwen`, the docs also set `"capabilities":{"reasoning":{"profile":"qwen-chat-template"}}`.

## Configuration

User file `~/.qwen/settings.json` (project: `.qwen/settings.json`); the key goes in `~/.qwen/.env`, named by `envKey`. The environment route is `OPENAI_API_KEY`, `OPENAI_BASE_URL` and `OPENAI_MODEL`. Template: `references/templates.md`, section Qwen Code.

Non-interactive run (smoke test): `qwen -p "<prompt>"` or `--prompt`; `--approval-mode` overrides `tools.approvalMode` for one run (https://qwenlm.github.io/qwen-code-docs/en/users/features/headless/).

## Egress switches

| Connection | Default | Switch | Source |
|---|---|---|---|
| Usage statistics and crash data to an Alibaba Cloud RUM endpoint | on | `privacy.usageStatisticsEnabled: false` or `QWEN_USAGE_STATISTICS_ENABLED=false` | https://qwenlm.github.io/qwen-code-docs/en/users/support/tos-privacy/ |
| Daily models.dev catalog download | on | `model.catalogRefresh: false`; `QWEN_CODE_MODELS_DEV=off` disables the catalog | https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/ |
| Auto update | on | `general.enableAutoUpdate: false` | https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/ |
| Web search (DashScope or Qwen service) | not auto-enabled for local models | `tools.webSearch.enabled: false` or `ENABLE_WEB_SEARCH=false` | https://qwenlm.github.io/qwen-code-docs/en/developers/tools/web-search/ |
| Web fetch tool | not documented | deny `"WebFetch"` in `permissions.deny` | https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/ |
| OpenTelemetry | off | keep `telemetry.enabled: false` (`--no-telemetry`) | https://qwenlm.github.io/qwen-code-docs/en/developers/development/telemetry/ |

## Permissions and central policy

- `tools.approvalMode`: `plan`, `default`, `auto-edit`, `auto`, `yolo`. Always write it: the settings reference gives `auto` (an LLM classifier) as the default, the approval-mode page calls ask-first the initial mode. Read only: `plan`. Edit with approval: `default`. Edit freely in the workspace: `auto-edit`.
- `permissions.allow`, `ask`, `deny` with patterns such as `"Bash(git *)"`, `"Read(./secrets/**)"`, `"WebFetch(api.example.com)"`.
- Sandbox: `-s`, `tools.sandbox` or `QWEN_SANDBOX` (`sandbox-exec`, `docker`, `podman`).
- Central: `/etc/qwen-code/settings.json` overrides user and project settings (`QWEN_CODE_SYSTEM_SETTINGS_PATH` moves it); `security.auth.enforcedType` fixes the auth type.

## Skills, context and MCP

- Skills: `~/.qwen/skills`, `~/.agents/skills`, `.qwen/skills`, `.agents/skills`, `skills.directories` and extensions.
- Context: `~/.qwen/QWEN.md`, project `QWEN.md`, `.qwen/QWEN.local.md`. It also reads an existing `AGENTS.md`; `context.fileName` sets the name.
- MCP: `mcpServers` in user or project settings; `mcp.allowed` and `mcp.excluded`.

## Caveats

- The default approval mode is documented two ways (see above).
- The Docker or Podman sandbox pulls `ghcr.io/qwenlm/qwen-code:<version>` on first use: stage it (Carry in). The research did not settle whether the image tag carries the `v` prefix; check the sandbox page before staging.
- The download URLs below are the `browser_download_url` values of the release API for tag `v0.28.4`, read 2026-11-24. The installer comes from the repository at the same tag; it has no publisher checksum.
- Not documented: an offline install procedure beyond the archive installer, and a switch for the models.dev catalog other than the two listed.

## Carry in

### Packages

| File | Architecture | Source | Checksum |
|---|---|---|---|
| `qwen-code-linux-x64.tar.gz` | amd64 | https://github.com/QwenLM/qwen-code/releases/download/v0.28.4/qwen-code-linux-x64.tar.gz | https://github.com/QwenLM/qwen-code/releases/download/v0.28.4/SHA256SUMS |
| `qwen-code-linux-arm64.tar.gz` | arm64 | https://github.com/QwenLM/qwen-code/releases/download/v0.28.4/qwen-code-linux-arm64.tar.gz | https://github.com/QwenLM/qwen-code/releases/download/v0.28.4/SHA256SUMS |
| `install-qwen-standalone.sh` | any | https://raw.githubusercontent.com/QwenLM/qwen-code/v0.28.4/scripts/installation/install-qwen-standalone.sh | none |

The installer script is run with `--archive PATH` and `SHA256SUMS` next to the archive (https://qwenlm.github.io/qwen-code-docs/en/users/overview/).

### Runtime downloads to stage in advance

- Sandbox image `ghcr.io/qwenlm/qwen-code:<version>` (tag form: see Caveats), only when a Docker or Podman sandbox is chosen.

### Telemetry and egress to switch off before the first start

All rows of Egress switches, in the system settings file.

## Evidence

- https://api.github.com/repos/QwenLM/qwen-code/releases/latest
- https://api.github.com/repos/QwenLM/qwen-code/releases/tags/v0.28.4
- https://api.github.com/repos/QwenLM/qwen-code/contents/scripts/installation?ref=v0.28.4
- https://api.github.com/repos/QwenLM/qwen-code
- https://qwenlm.github.io/qwen-code-docs/en/users/overview/
- https://qwenlm.github.io/qwen-code-docs/en/users/features/headless/
- https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/
- https://qwenlm.github.io/qwen-code-docs/en/users/configuration/model-providers/
- https://qwenlm.github.io/qwen-code-docs/en/users/support/tos-privacy/
- https://qwenlm.github.io/qwen-code-docs/en/developers/tools/web-search/
- https://qwenlm.github.io/qwen-code-docs/en/developers/development/telemetry/
- https://qwenlm.github.io/qwen-code-docs/en/users/features/approval-mode/
- https://qwenlm.github.io/qwen-code-docs/en/users/features/sandbox/
- https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/
- https://qwenlm.github.io/qwen-code-docs/en/users/features/memory/
- https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/
- https://registry.npmjs.org/@qwen-code/qwen-code/latest
