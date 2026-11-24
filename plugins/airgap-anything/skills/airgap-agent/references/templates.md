# Configuration templates

Goal: the files the skill writes into `docs/airgap/agents/<tool>/`, one section per tool. Each template uses only keys that appear in the tool's catalog entry; the switch for every line, with its source, is in that entry's Egress table. Fill in the placeholders and change nothing else; where a value is not documented, the template says so.

## Contents

- Placeholders and layout
- Qwen Code
- Codex CLI
- opencode
- Claude Code

## Placeholders and layout

| Placeholder | Meaning |
|---|---|
| `GATEWAY_URL` | Base URL of the gateway or engine, for example the internal host with `/v1` |
| `SERVED_MODEL_NAME` | The `--served-model-name` of the engine, without `/` (`references/serving.md`) |
| `CONTEXT_WINDOW` | Tokens, equal to or below the engine's `--max-model-len` |
| `KEY_ENV_VAR` | Name of the environment variable that holds the key |

Keys always come from environment variables. No template holds a key, and `agents.md` names the variable for each tool.

Layout of a tool's folder:

- `docs/airgap/agents/<tool>/user/` holds the user file, to be placed at the path the section names.
- `docs/airgap/agents/<tool>/central/` holds the central policy file, written when `central` is yes, to be placed at its documented path (`references/interview.md`).
- The permission stance in the Qwen Code, Codex CLI and opencode templates is `edit with approval`; for another stance use the mapping in `references/decisions.md`. The Claude Code template sets no edit rules (see its notes).

## Qwen Code

Catalog: `catalog/qwen-code.md`. Chat Completions.

User file, placed at `~/.qwen/settings.json` (project: `.qwen/settings.json`). The key goes in `~/.qwen/.env`, named by `envKey`:

```json
{
  "modelProviders": {
    "openai": [
      {
        "id": "SERVED_MODEL_NAME",
        "name": "Internal model",
        "envKey": "KEY_ENV_VAR",
        "baseUrl": "GATEWAY_URL",
        "generationConfig": { "contextWindowSize": CONTEXT_WINDOW }
      }
    ]
  },
  "security": { "auth": { "selectedType": "openai" } },
  "model": { "name": "SERVED_MODEL_NAME", "catalogRefresh": false },
  "privacy": { "usageStatisticsEnabled": false },
  "general": { "enableAutoUpdate": false },
  "telemetry": { "enabled": false },
  "tools": {
    "approvalMode": "default",
    "webSearch": { "enabled": false }
  },
  "permissions": { "deny": ["WebFetch"] }
}
```

- `id` equals `--served-model-name`, and `model.name` is set to the same value, as the docs' examples do.
- When the id does not start with `qwen`, add `"capabilities": { "reasoning": { "profile": "qwen-chat-template" } }` to the `modelProviders` entry, as the docs do.
- Set the environment variable `QWEN_CODE_MODELS_DEV=off` as well when the models.dev catalog must be off entirely.
- `tools.approvalMode` is always written: `plan` (read only), `default` (edit with approval), `auto-edit` (edit freely in the workspace).

Central file, placed at `/etc/qwen-code/settings.json` (`QWEN_CODE_SYSTEM_SETTINGS_PATH` moves it). It overrides user and project settings, so it carries the switches and the permission stance, not the provider:

```json
{
  "security": { "auth": { "enforcedType": "openai" } },
  "model": { "catalogRefresh": false },
  "privacy": { "usageStatisticsEnabled": false },
  "general": { "enableAutoUpdate": false },
  "telemetry": { "enabled": false },
  "tools": {
    "approvalMode": "default",
    "webSearch": { "enabled": false }
  },
  "permissions": { "deny": ["WebFetch"] }
}
```

The value `"openai"` for `enforcedType` follows the `selectedType` of the docs' example; the research does not list other values.

## Codex CLI

Catalog: `catalog/codex-cli.md`. Responses API only: the endpoint must pass the `/v1/responses` smoke test.

User file, placed at `~/.codex/config.toml` (or under `CODEX_HOME`):

```toml
model = "SERVED_MODEL_NAME"
model_provider = "enterprise-gateway"
web_search = "disabled"
check_for_update_on_startup = false
approval_policy = "on-request"
sandbox_mode = "workspace-write"
model_catalog_json = "/etc/codex/gateway-models.json"

[model_providers.enterprise-gateway]
name = "Organization Gateway"
base_url = "GATEWAY_URL"
wire_api = "responses"
requires_openai_auth = false
env_key = "KEY_ENV_VAR"

[analytics]
enabled = false

[feedback]
enabled = false
```

- Leave `[otel]` out. Leave `sandbox_workspace_write.network_access` unset: the sandbox then keeps network off.
- `model_catalog_json` points to a local file the skill writes. The format of that file is not in the research: take it from https://learn.chatgpt.com/docs/enterprise/connect-to-a-gateway.md.
- The context window setting is not documented in the research. Private CA: `CODEX_CA_CERTIFICATE`.

Central files, placed at `/etc/codex/managed_config.toml` (defaults: the same lines as the user file above, without the provider block when users keep their own) and `/etc/codex/requirements.toml` (limits users cannot exceed):

```toml
allowed_approval_policies = ["on-request"]
allowed_sandbox_modes = ["read-only", "workspace-write"]
allowed_web_search_modes = ["disabled"]
```

- The list syntax follows the key names in the managed-configuration page (https://learn.chatgpt.com/docs/enterprise/managed-configuration.md); confirm it there before shipping.
- `[rules] prefix_rules` and an `mcp_servers` allowlist also live in `requirements.toml`; their entry shape is not in the research. An empty `mcp_servers` allowlist disables all MCP servers.
- Skills for all users go in `/etc/codex/skills`.

## opencode

Catalog: `catalog/opencode.md`. Chat Completions. Pinned to V2 2.4.1; V2 documents no switch for the `models.opencode.ai` fetch, so the egress check is mandatory.

User file, placed at `~/.config/opencode/opencode.json`. `update` is read from the global config only, so it must be here:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "update": "disable",
  "share": "disabled",
  "websearch": false,
  "providers": {
    "internal": {
      "name": "Internal gateway",
      "env": ["KEY_ENV_VAR"],
      "package": "@opencode/ai/providers/openai-compatible",
      "settings": { "baseURL": "GATEWAY_URL" },
      "models": {
        "SERVED_MODEL_NAME": {
          "name": "Internal model",
          "capabilities": { "tools": true }
        }
      }
    }
  }
}
```

- The model is referenced as `internal/SERVED_MODEL_NAME`.
- `"capabilities": {"tools": true}` is required for vLLM models, which start with tools disabled.
- Use file paths only in `instructions` and `skills`: URL entries are fetched. Configure no plugins. For a remote MCP server set `"oauth": false`.
- The key for the context window is not documented in the research. Private CA: `NODE_EXTRA_CA_CERTS`; keep `localhost,127.0.0.1,::1` in `NO_PROXY`. Set the environment variable `OPENCODE_DISABLE_FREE_MODELS=1` in the user's profile.

Central file, placed at `/etc/opencode/opencode.json`. `policies` outrank user and project config:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "policies": [
    { "action": "websearch.use", "resource": "*", "effect": "deny" },
    { "action": "plugin.use", "resource": "*", "effect": "deny" },
    { "action": "integration.use", "resource": "*", "effect": "deny" },
    { "action": "integration.connect", "resource": "*", "effect": "deny" }
  ]
}
```

The research gives the action names and says `permissions` entries are `{action, resource, effect}`; it shows no `policies` example, so the entry shape above is carried over from `permissions` and must be confirmed at https://opencode.ai/docs/policies/. macOS MDM: `ai.opencode.managed`. No sandbox is documented: enforce the network boundary on the host.

## Claude Code

Catalog: `catalog/claude-code.md`.

The file below is for a private Claude route only; never point Claude Code at an open-weight model (https://code.claude.com/docs/en/llm-gateway).

Central file, placed at `/etc/claude-code/managed-settings.json` (Linux and WSL). macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`. Windows: `C:\Program Files\ClaudeCode\managed-settings.json`.

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "GATEWAY_URL",
    "ANTHROPIC_MODEL": "CLAUDE_MODEL_ID",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "DISABLE_TELEMETRY": "1",
    "DISABLE_ERROR_REPORTING": "1",
    "DISABLE_UPDATES": "1",
    "CLAUDE_CODE_DISABLE_FEATURE_FLAGS": "1",
    "DISABLE_FEEDBACK_COMMAND": "1",
    "CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY": "1",
    "CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL": "1",
    "ENABLE_CLAUDEAI_MCP_SERVERS": "false",
    "CLAUDE_CODE_DISABLE_ARTIFACT": "1"
  },
  "allowedProviders": ["customEndpoint"],
  "skipWebFetchPreflight": true,
  "permissions": {
    "deny": ["WebSearch"],
    "disableBypassPermissionsMode": "disable"
  },
  "sandbox": { "enabled": true, "failIfUnavailable": true }
}
```

- `CLAUDE_MODEL_ID` is the Claude model name the private route accepts. The credential is not in this file: users set `ANTHROPIC_AUTH_TOKEN` or `ANTHROPIC_API_KEY` in their environment, or an `apiKeyHelper` hands it out.
- Set both `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` and `DISABLE_TELEMETRY`: operational telemetry still flows behind a gateway or a custom base URL.
- The value `1` follows the docs for the variables the catalog writes as `=1`; for the others the research names the variable without a value, so confirm it on https://code.claude.com/docs/en/env-vars.
- Not documented, so not switched off: plugin install counts, docs lookups, the first-run connectivity check and the release-notes fetch (only the nonessential-traffic flag covers the last). The egress check shows them.
- The permission stance for edits is written with `permissions.ask` or `allow` rules; the tool names are not in the research (`references/decisions.md`).
- The sandbox needs bubblewrap and socat on Linux and WSL2; on native Windows Claude Code runs commands unsandboxed.
- Skills for all users: `/etc/claude-code/.claude/skills/<name>/`. Plugins come from a local marketplace or `CLAUDE_CODE_PLUGIN_SEED_DIR`, never from the official marketplace.
