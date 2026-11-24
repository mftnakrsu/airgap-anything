# opencode (`opencode`)

Terminal coding agent with provider-neutral configuration and central `policies`. Pinned to V2: the docs describe V2 while GitHub "latest" still returns V1.

| Field | Value |
|---|---|
| Kind | `coding-agent` |
| Version | `v2.4.1` |
| License | MIT |
| Speaks | `chat-completions` |
| Install | release archives `opencode-linux-x64[-baseline][-musl].tar.gz`, `opencode-linux-arm64[-musl].tar.gz` with `SHA256SUMS`; or npm `@opencode/cli` |
| Evidence | docs |
| Last verified | 2026-11-24 |

## Choose when

- The team already uses opencode.
- Central `policies` (provider, tool, MCP, skill, plugin and web search use) must outrank user and project config.

## Avoid when

- The network allows no egress capture: V2 documents no switch for the model-catalog fetch or for telemetry, so the egress check in `references/verification.md` is mandatory for this tool.
- A documented sandbox or a documented offline install procedure is required: neither is documented.

## Serving needs

- Speaks Chat Completions (`/chat/completions`). It sends `stream: true` (SSE), `stream_options.include_usage` unless `streamUsage` is false, and `tools` and `tool_choice`. The engine needs the tool-call and reasoning parsers for the model family (`references/serving.md`).
- Discovered vLLM models start with tools disabled. Enable them per model with `"capabilities": {"tools": true}`.
- Private CA: `NODE_EXTRA_CA_CERTS`. Keep `localhost,127.0.0.1,::1` in `NO_PROXY`.

## Configuration

`opencode.json` or `opencode.jsonc` in `~/.config/opencode/`, in the project, or in `/etc/opencode/`. A custom provider sets `baseURL` under `settings` and the key variable under `env`; models are referenced as `<provider>/<model>`. Template: `references/templates.md`, section opencode.

Non-interactive run (smoke test): `opencode run "<prompt>"` (https://opencode.ai/docs/cli/). That page documents no flag of `run` and does not say whether it describes V1 or V2: confirm with `opencode run --help` on the pinned version.

## Egress switches

| Connection | Default | Switch | Source |
|---|---|---|---|
| Model catalog `models.opencode.ai` (5-minute TTL, bundled snapshot fallback) | on | not documented for V2 | https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/core/src/models-dev.ts |
| Updates | not documented | `"update": "disable"`, read from the global config only | https://opencode.ai/docs/config/ |
| Share | not documented | `"share": "disabled"` | https://opencode.ai/config.json |
| Web search | not documented | `"websearch": false`; deny `websearch.use` in policies | https://opencode.ai/docs/websearch/ |
| Free models and Console | not documented | `OPENCODE_DISABLE_FREE_MODELS=1`, or deny `integration.use` and `integration.connect` | https://opencode.ai/docs/enterprise/ |
| URL entries in `instructions` | fetched | use file paths only | https://opencode.ai/docs/instructions/ |
| URL entries in `skills` | fetched | use file paths only | https://opencode.ai/docs/skills/ |
| Remote-MCP OAuth discovery and dynamic client registration | not documented | `"oauth": false` | https://opencode.ai/docs/mcp-servers/ |
| npm plugins (installed in the background) | on when configured | configure none; deny `plugin.use` in policies | https://opencode.ai/docs/plugins/ |

## Permissions and central policy

- `permissions` is an ordered list of `{action, resource, effect}` with effect `allow`, `ask` or `deny`. The last match wins, and the base policy allows `*`.
- No sandbox is documented, and no documented setting restricts the tool's network access: enforce it on the host.
- Central: `policies` (allow or deny on `provider.use`, `tool.use`, `mcp.use`, `skill.use`, `plugin.use`, `websearch.use`, `integration.*`) in `/etc/opencode/opencode.json`, or macOS MDM `ai.opencode.managed`. They outrank user and project config.

## Skills, context and MCP

- Skills: `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills`, project `.opencode/skills`, `.claude/skills`, `.agents/skills`, plus the `skills` array.
- Context: `~/.config/opencode/AGENTS.md` (else `~/.claude/CLAUDE.md`), then `AGENTS.md` from the working directory upward with `CLAUDE.md` as fallback. `OPENCODE_DISABLE_CLAUDE_CODE=1` turns the Claude files off.
- MCP: `mcp.servers`.

## Caveats

- Version split: the docs describe OpenCode 2 (V2). GitHub "latest" still returns V1 `1.19.6` (2026-11-17), and V1 gets critical fixes only. This entry pins V2 `v2.4.1` (2026-11-23).
- V2 documents no switch for the `models.opencode.ai` catalog fetch and none for telemetry or error reporting. V1 documents `OPENCODE_DISABLE_MODELS_FETCH`, `OPENCODE_MODELS_PATH`, `OPENCODE_DISABLE_AUTOUPDATE` and `OPENCODE_DISABLE_LSP_DOWNLOAD` (V1 docs); do not assume they work in V2 and do not write them for V2. Confirm with an egress capture.
- No documented offline install procedure and no documented sandbox.
- The repository moved: `sst/opencode` resolves to `anomalyco/opencode`.

## Carry in

### Packages

| File | Architecture | Source | Checksum |
|---|---|---|---|
| `opencode-linux-x64.tar.gz` (variants `-baseline`, `-musl`, `-baseline-musl`: the same URL with the variant before `.tar.gz`) | amd64 | https://github.com/anomalyco/opencode/releases/download/v2.4.1/opencode-linux-x64.tar.gz | https://github.com/anomalyco/opencode/releases/download/v2.4.1/SHA256SUMS |
| `opencode-linux-arm64.tar.gz` (variant `-musl`: the same URL with the variant before `.tar.gz`) | arm64 | https://github.com/anomalyco/opencode/releases/download/v2.4.1/opencode-linux-arm64.tar.gz | https://github.com/anomalyco/opencode/releases/download/v2.4.1/SHA256SUMS |

The URLs are the `browser_download_url` values of the release API for the tag (Evidence), read 2026-11-24. The npm route (`@opencode/cli`) has no direct URL here: it goes to section 5 of the manifest as a manual item.

### Runtime downloads to stage in advance

- Model catalog snapshot: V2 falls back to a bundled snapshot when `models.opencode.ai` is unreachable. No documented way to pre-stage a newer one.
- npm plugins, only if the team insists on them: not documented for offline use.

### Telemetry and egress to switch off before the first start

All rows of Egress switches, in the global config and in `/etc/opencode/opencode.json`. Then run the egress check: the catalog fetch has no documented switch.

## Evidence

- https://api.github.com/repos/anomalyco/opencode/releases/tags/v2.4.1
- https://api.github.com/repos/anomalyco/opencode/releases/latest
- https://api.github.com/repos/anomalyco/opencode
- https://api.github.com/repos/sst/opencode
- https://registry.npmjs.org/@opencode/cli
- https://github.com/anomalyco/opencode/issues/38723
- https://opencode.ai/docs/config/
- https://opencode.ai/docs/cli/
- https://opencode.ai/docs/providers/
- https://opencode.ai/docs/models/
- https://opencode.ai/docs/network/
- https://opencode.ai/docs/websearch/
- https://opencode.ai/docs/enterprise/
- https://opencode.ai/docs/instructions/
- https://opencode.ai/docs/skills/
- https://opencode.ai/docs/mcp-servers/
- https://opencode.ai/docs/plugins/
- https://opencode.ai/docs/permissions/
- https://opencode.ai/docs/policies/
- https://opencode.ai/config.json
- https://opencode.ai/v1/docs/cli/
- https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/core/src/models-dev.ts
- https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/ai/src/protocols/openai-compatible-chat.ts
- https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/ai/src/protocols/openai-chat.ts
