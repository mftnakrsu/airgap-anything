# Verification inside

Goal: three checks, in this order, that a person runs inside the network on a developer machine or a jump host, following `docs/airgap/agents.md`. No LLM is needed. Each check has a pass and a fail criterion. The checks also go to section 7 of the transfer manifest.

## Contents

- 1. Install check
- 2. Smoke test
- 3. Egress check
- Unexpected address to switch

## 1. Install check

Pass: the archive's checksum matches and the tool prints its version, equal to the version pinned in the catalog entry. Fail: a mismatch, or any other version. Do not install a file that fails.

| Tool | Checksum | Version |
|---|---|---|
| Qwen Code | `sha256sum -c SHA256SUMS --ignore-missing` with `SHA256SUMS` next to the archive | `qwen --version` |
| opencode | `sha256sum -c SHA256SUMS --ignore-missing` with `SHA256SUMS` from the same release | `opencode --version` |
| Codex CLI | the release lists no checksum file in the research; `.sigstore` files are carried but not verified by `airgap-transfer`. Record the SHA-256 of the archive when it is carried in and compare it here | `codex --version` |
| Claude Code | the SHA-256 for the platform in `$version/manifest.json`; npm installs use the npm integrity value | `claude --version` |

`--ignore-missing` skips the files of `SHA256SUMS` that are not in the folder, so one archive can be checked against the full list.

## 2. Smoke test

Run one non-interactive prompt that forces a tool call, against the internal model. Use the same prompt for every tool, for example: "List the files in this folder using your tool."

| Tool | Non-interactive command |
|---|---|
| Qwen Code | not documented in the research; see the tool's docs (the pages read are in `catalog/qwen-code.md`, Evidence) |
| Codex CLI | not documented in the research; see the tool's docs (`catalog/codex-cli.md`, Evidence) |
| opencode | not documented in the research for V2; see the tool's docs (`catalog/opencode.md`, Evidence) |
| Claude Code | not documented in the research; see the tool's docs (`catalog/claude-code.md`, Evidence); the `claude-code-ci-harness` skill of `air-gapped/skills` runs it headless |

For Codex CLI also send one `POST /v1/responses` request with streaming to the gateway first: a working Chat Completions endpoint does not prove Responses compatibility (`catalog/codex-cli.md`).

- Pass: the tool call is executed and the answer names the files in the folder.
- Fail: a plain text answer without a tool call. This usually means a wrong or missing parser on the engine: check `--enable-auto-tool-choice`, `--tool-call-parser` and `--reasoning-parser` against `references/serving.md`, then the tool's own switch for tools (opencode: `"capabilities": {"tools": true}`).
- Fail: an error from the endpoint. Read it before changing the tool: a 400 on `/v1/responses` or `/v1/messages` points to the route in the gateway (`references/serving.md`, LiteLLM).

For Codex CLI, also confirm whether an edit inside `workspace-write` asked for approval: the research does not say, and the stance in `agents.md` depends on it.

## 3. Egress check

Run during the smoke test, on the same command. Pass: every address is the gateway, the engine, loopback or a local socket. Fail: any other address.

- Linux: run the smoke test command under `strace -f -e trace=connect -o egress.log`, as in `strace -f -e trace=connect -o egress.log <smoke test command>`, then read `egress.log`. `-f` follows child processes and `-e trace=connect` records only connection attempts. Both are documented in strace(1): https://man7.org/linux/man-pages/man1/strace.1.html. The log shows addresses, not names: compare them with the gateway's and the engine's addresses, and resolve any other address with the internal resolver before you judge it.
- macOS and Windows, where strace is not available: the firewall's deny log for the developer machine during the smoke test must be empty. A deny entry is a fail.

A failed egress check does not mean the tool is broken: name the switch in the next table, write it into the central file, and run the check again.

## Unexpected address to switch

Hosts are those the catalog entries name. A connection the table does not list is a finding: record it in `agents.md` as "not documented" and keep the host's firewall rule.

| Unexpected address | Tool | Switch to check | Catalog |
|---|---|---|---|
| models.dev (catalog download) | Qwen Code | `model.catalogRefresh: false`; `QWEN_CODE_MODELS_DEV=off` | `catalog/qwen-code.md` |
| An Alibaba Cloud RUM collection endpoint | Qwen Code | `privacy.usageStatisticsEnabled: false` | `catalog/qwen-code.md` |
| A DashScope or Qwen search service | Qwen Code | `tools.webSearch.enabled: false` | `catalog/qwen-code.md` |
| ghcr.io | Qwen Code | sandbox image pull: stage the image, or choose no Docker or Podman sandbox | `catalog/qwen-code.md` |
| models.opencode.ai | opencode | no documented switch in V2: block it on the host; the bundled snapshot is the fallback | `catalog/opencode.md` |
| An npm registry | opencode | npm plugins: configure none, deny `plugin.use` | `catalog/opencode.md` |
| An OAuth discovery address of a remote MCP server | opencode | `"oauth": false` | `catalog/opencode.md` |
| An OpenAI search index | Codex CLI | `web_search = "disabled"` | `catalog/codex-cli.md` |
| An analytics or feedback endpoint | Codex CLI | `[analytics] enabled = false`, `[feedback] enabled = false` | `catalog/codex-cli.md` |
| An update host | Codex CLI | `check_for_update_on_startup = false` | `catalog/codex-cli.md` |
| downloads.claude.ai | Claude Code | `DISABLE_UPDATES=1` | `catalog/claude-code.md` |
| http-intake.logs.us5.datadoghq.com, browser-intake-us5-datadoghq.com | Claude Code | `DISABLE_TELEMETRY`, `DISABLE_ERROR_REPORTING` | `catalog/claude-code.md` |
| api.anthropic.com (feature flags, WebFetch check, first-run check) | Claude Code | `CLAUDE_CODE_DISABLE_FEATURE_FLAGS`, `skipWebFetchPreflight: true`; the first-run check has no documented switch | `catalog/claude-code.md` |
| mcp-proxy.anthropic.com | Claude Code | `ENABLE_CLAUDEAI_MCP_SERVERS=false` | `catalog/claude-code.md` |
| github.com, raw.githubusercontent.com, storage.googleapis.com, code.claude.com | Claude Code | marketplace auto-install, release notes (the nonessential-traffic flag), plugin install counts and docs lookups (no documented switch) | `catalog/claude-code.md` |
