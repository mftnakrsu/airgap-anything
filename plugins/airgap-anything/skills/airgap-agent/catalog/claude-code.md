# Claude Code (`claude-code`)

Anthropic's terminal coding agent. It speaks the Anthropic Messages API and is configured here only against Claude models.

| Field | Value |
|---|---|
| Kind | `coding-agent` |
| Version | `v2.1.331` |
| License | Proprietary: "All rights reserved. Use is subject to Anthropic's Commercial Terms of Service." |
| Speaks | `anthropic-messages` |
| Install | native install script, signed apt, dnf and apk repositories on downloads.claude.ai, Homebrew, WinGet, or npm `@anthropic-ai/claude-code` (deprecated, Node 22 or newer); no documented offline procedure |
| Evidence | docs |
| Last verified | 2026-11-24 |

## Choose when

- The organization reaches Claude models through a private route (for example a private Bedrock or Vertex endpoint behind its gateway) and holds a Claude account: Pro, Max, Ultra, Team, Enterprise or Console.
- Managed settings, a sandbox and local plugin marketplaces are wanted.

## Avoid when

- Never with an open-weight model. Anthropic "doesn't support routing Claude Code to non-Claude models through any gateway" (https://code.claude.com/docs/en/llm-gateway). The docs describe gateways only in front of Claude models. vLLM documents a Claude Code integration, but this skill does not use it.
- The organization has no Claude account or no private route to Claude models: the setup page says "Claude Code requires a Pro, Max, Ultra, Team, Enterprise, or Console account" and "Network: internet connection required."

## Serving needs

These apply to the gateway or provider route in front of Claude models.

- Anthropic Messages at `/v1/messages` (called with `?beta=true`). `/v1/messages/count_tokens` is optional; without it Claude Code uses a character-based estimate.
- Streaming: SSE events in order through `message_delta` and `message_stop`, unbuffered, `ping` events kept. The `anthropic-beta` and `anthropic-version` headers must be forwarded.
- Tools arrive with `name`, `description`, `input_schema` and `cache_control`, plus beta fields (`strict`, `defer_loading`). `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` strips pre-release fields but keeps `thinking`, `output_config.effort` and system messages.
- Optional `GET /v1/models` discovery (`CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`) keeps only IDs that contain `claude` or `anthropic`. A `HEAD /api/hello` probe also arrives; the endpoint can reject it.
- Behind `ANTHROPIC_BASE_URL`, background tasks use the main model unless `ANTHROPIC_DEFAULT_HAIKU_MODEL` pins one, and some background sub-calls request a built-in ID regardless of the override.

## Configuration

`ANTHROPIC_BASE_URL` names the route. The credential goes in `ANTHROPIC_AUTH_TOKEN` (`Authorization: Bearer`), `ANTHROPIC_API_KEY` (`x-api-key`) or `apiKeyHelper` (both headers, cached 5 minutes, `CLAUDE_CODE_API_KEY_HELPER_TTL_MS`). Extra headers: `ANTHROPIC_CUSTOM_HEADERS`. Models: `ANTHROPIC_MODEL` or `model`, `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU}_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL`. `ANTHROPIC_SMALL_FAST_MODEL` is deprecated. Unrecognized model IDs get an assumed 1M context (since v2.1.323); correct it with `CLAUDE_CODE_MAX_CONTEXT_TOKENS`. Put the settings in the managed settings file. Template: `references/templates.md`, section Claude Code.

## Egress switches

| Connection | Default | Switch | Source |
|---|---|---|---|
| All nonessential traffic: auto-updates, telemetry, error reporting, `/feedback`, release notes, PR status badge checks, availability checks, feature-flag fetching | on | `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`; setting it to `0` or `false` still disables the traffic; official marketplace auto-install is not covered; it also turns off plugin auto-update | https://code.claude.com/docs/en/env-vars https://code.claude.com/docs/en/plugins/org.md |
| Operational telemetry (metrics, http-intake.logs.us5.datadoghq.com); still flows behind a gateway or a custom `ANTHROPIC_BASE_URL` | on | `DISABLE_TELEMETRY` or `DO_NOT_TRACK` | https://code.claude.com/docs/en/managed-settings https://code.claude.com/docs/en/network-config |
| Error reports (browser-intake-us5-datadoghq.com) | on | `DISABLE_ERROR_REPORTING` | https://code.claude.com/docs/en/network-config |
| Update checks (downloads.claude.ai) | on | `DISABLE_AUTOUPDATER=1` stops background updates only; `DISABLE_UPDATES=1` blocks all updates including `claude update` and `claude install` | https://code.claude.com/docs/en/setup https://code.claude.com/docs/en/env-vars |
| Feature flags (api.anthropic.com) | on | `CLAUDE_CODE_DISABLE_FEATURE_FLAGS` (v2.1.319 and later; the older name is `DISABLE_GROWTHBOOK`) | https://code.claude.com/docs/en/env-vars |
| `/feedback` and surveys | on | `DISABLE_FEEDBACK_COMMAND`; `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY` | https://code.claude.com/docs/en/data-usage |
| Release notes (raw.githubusercontent.com) | on | only the nonessential-traffic flag; a dedicated switch is not documented | https://code.claude.com/docs/en/network-config |
| WebFetch domain check (api.anthropic.com), not affected by the nonessential-traffic flag | on | `skipWebFetchPreflight: true` | https://code.claude.com/docs/en/data-usage |
| WebSearch, which "runs a query against Anthropic's web search backend" | available | deny `WebSearch` in `permissions.deny` | https://code.claude.com/docs/en/tools-reference |
| Official plugin marketplace (github.com) | auto-installs | `CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL=1` | https://code.claude.com/docs/en/env-vars https://code.claude.com/docs/en/network-config |
| claude.ai connectors (mcp-proxy.anthropic.com) | on | `ENABLE_CLAUDEAI_MCP_SERVERS=false` or `disableClaudeAiConnectors` | https://code.claude.com/docs/en/network-config |
| Artifacts (*.frame.claudeusercontent.com) | on | `CLAUDE_CODE_DISABLE_ARTIFACT=1` | https://code.claude.com/docs/en/network-config |
| Plugin install counts (storage.googleapis.com) | on | not documented | https://code.claude.com/docs/en/network-config |
| Docs lookups (code.claude.com) | on | not documented | https://code.claude.com/docs/en/network-config |
| First-run connectivity check (api.anthropic.com, platform.claude.com) | on | not documented | https://code.claude.com/docs/en/network-config |

## Permissions and central policy

- `permissions.allow`, `ask` and `deny`. "Rules are evaluated in order: deny, then ask, then allow." Example rules: `Bash(npm run *)`, `WebFetch(domain:example.com)`, `mcp__server__*`. Related keys: `permissions.disableBypassPermissionsMode: "disable"` and `allowManagedPermissionRulesOnly`.
- Managed settings file: Linux and WSL `/etc/claude-code/managed-settings.json`; macOS `/Library/Application Support/ClaudeCode/managed-settings.json`; Windows `C:\Program Files\ClaudeCode\managed-settings.json`. `managed-settings.d/` and `managed-mcp.json` sit in the same directory. MDM: the `com.anthropic.claudecode` plist, or `HKLM\SOFTWARE\Policies\ClaudeCode`.
- `allowedProviders: ["customEndpoint"]` locks sessions to the base URL set in managed settings (v2.1.285 and later).
- Sandbox: the OS enforces it around Bash, PowerShell and Monitor commands. macOS uses Seatbelt; Linux and WSL2 use bubblewrap plus socat. "On native Windows, Claude Code runs commands unsandboxed." Keys: `sandbox.enabled`, `sandbox.network.allowedDomains`, `sandbox.failIfUnavailable`. Hooks, local MCP servers and the built-in file and web tools run outside it.
- Local marketplaces for plugins: see below.

## Skills, context and MCP

- Skills: personal `~/.claude/skills/<name>/SKILL.md`, project `.claude/skills/`, plugin `<plugin>/skills/`. Enterprise skills: `.claude/skills/` inside the managed settings directory, for example `/etc/claude-code/.claude/skills/<skill-name>/`.
- Plugins: a local marketplace is a directory with `.claude-plugin/marketplace.json`; add it with `claude plugin marketplace add ./my-marketplace`, then `claude plugin install <plugin>@<marketplace>`. Organization marketplace sources include `{ "source": "directory", "path": "/opt/marketplace/plugins" }` and `file`; `CLAUDE_CODE_PLUGIN_SEED_DIR` pre-populates plugins in images. For fleets with no outbound git access, combine a seed with `directory` or `file` marketplace sources on a shared mount.
- MCP: local and user scope live in `~/.claude.json`, project scope in `.mcp.json`. Add a server with `claude mcp add --transport stdio <name> -- <command>`. For an organization: `managed-mcp.json`, `allowedMcpServers` and `deniedMcpServers`.

## Caveats

- Terms: use is subject to the Commercial Terms for Team, Enterprise and Claude API users and to the Consumer Terms for Free, Pro, Max and Ultra users, "regardless of the platform through which it is accessed". A Commercial Terms clause on non-Anthropic models: not documented.
- The docs name the Anthropic API, Bedrock, Agent Platform and Foundry as gateway targets. A private Vertex route is not named in the research; check the gateway page.
- No documented offline installation and no documented way to skip the first-run connectivity check.
- The MCP registry connection: not documented.
- The CHANGELOG carries no dates; the version date comes from the GitHub release (2026-11-23).

## Carry in

### Packages

| File | Architecture | Source | Checksum |
|---|---|---|---|
| native `claude` binary, `$version/$platform/claude` | amd64, arm64 | https://downloads.claude.ai/claude-code-releases/bootstrap.sh names the download base; the base URL is not recorded here | `$version/manifest.json` lists a SHA256 per platform; `manifest.json.sig` (2.1.89 and later) is GPG-signed, fingerprint `31DD DE24 DDFA B679 F42D 7BD2 BAA9 29FF 1A7E CACE` |
| npm `@anthropic-ai/claude-code@2.1.331` with the per-platform packages `-linux-x64`, `-linux-arm64`, `-linux-x64-musl`, `-linux-arm64-musl` | amd64, arm64 | https://registry.npmjs.org/@anthropic-ai/claude-code/latest | npm integrity |

The bootstrap script fetches the binary, checks it against `manifest.json`, then runs the binary's `install` subcommand. Linux needs Ubuntu 20.04 or newer, Debian 10 or newer, or Alpine 3.19 or newer.

### Runtime downloads to stage in advance

- None documented beyond the binary. Plugins come from a local marketplace or a seed directory, not from the official marketplace.

### Telemetry and egress to switch off before the first start

All rows of Egress switches, in the managed settings file (`env` block). Set `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` and `DISABLE_TELEMETRY`: operational telemetry still flows behind a gateway.

## Evidence

- https://api.github.com/repos/anthropics/claude-code/releases/latest
- https://registry.npmjs.org/@anthropic-ai/claude-code/latest
- https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
- https://raw.githubusercontent.com/anthropics/claude-code/main/README.md
- https://github.com/anthropics/claude-code/blob/main/LICENSE.md
- https://www.anthropic.com/legal/commercial-terms
- https://downloads.claude.ai/claude-code-releases/bootstrap.sh
- https://code.claude.com/docs/en/legal-and-compliance
- https://code.claude.com/docs/en/setup
- https://code.claude.com/docs/en/llm-gateway
- https://code.claude.com/docs/en/llm-gateway-connect.md
- https://code.claude.com/docs/en/llm-gateway-protocol.md
- https://code.claude.com/docs/en/llm-gateway-rollout.md
- https://code.claude.com/docs/en/model-config
- https://code.claude.com/docs/en/network-config
- https://code.claude.com/docs/en/env-vars
- https://code.claude.com/docs/en/data-usage
- https://code.claude.com/docs/en/managed-settings
- https://code.claude.com/docs/en/tools-reference
- https://code.claude.com/docs/en/permissions
- https://code.claude.com/docs/en/sandboxing
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/plugin-marketplaces
- https://code.claude.com/docs/en/plugins/org.md
- https://code.claude.com/docs/en/mcp
- https://docs.vllm.ai/en/v0.34.0/serving/integrations/claude_code/
