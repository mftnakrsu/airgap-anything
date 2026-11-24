---
name: airgap-agent
description: Sets up coding agents (Qwen Code, Codex CLI, opencode, Claude Code) to run inside an air-gapped or offline network against the organization's own model server - picks the tool, writes its configuration and central policy with telemetry, updates and web access off, checks the model server's API and parsers, chooses MCP servers that work offline and adds everything to the transfer manifest. Use when someone wants a coding agent, AI coding assistant or agentic CLI to work without internet access, on a local vLLM, SGLang or Ollama model, or asks which agent tool to use inside a closed network
---

# Airgap Agent

## Overview

Turn a short interview into the files that let a coding agent work inside a network with no internet: the chosen tool, its user configuration and central policy with every outbound connection switched off, the requirements the model server must meet, MCP servers that work offline, and rows in the transfer manifest so that `airgap-transfer` carries it all in.

Why the skill exists: a coding agent installed as-is tries to reach a model catalog, telemetry, update servers and web search on its first start, and may not speak the API the internal model server offers. Inside the network nothing can be downloaded to fix that. So every switch, version and path here comes from `catalog/`, and every setting is proved inside by a smoke test and an egress check.

Paths in this skill are relative to the folder that holds this file. `docs/` is in the user's project.

## When to use

- Someone wants a coding agent, AI coding assistant or agentic CLI to work without internet, on a model the organization serves itself (vLLM, SGLang, Ollama, or a gateway in front of them).
- Someone asks which agent tool to use in a closed network, or how to enforce its settings centrally.

Not for sizing or serving the model: that is `airgap-architect`. Not for packing and carrying files: that is `airgap-transfer`. Not for operating one tool day to day: the catalog names per-tool skills for that.

## What it does not do

- It ranks no models: card scores are self-reported and the one cross-model board found is flagged "Flawed" by Epoch. The model comes from the blueprint or the user.
- It configures no editor extension (Cline, Kilo Code, Continue) or other CLI (Goose, Crush, Aider) beyond the one line each in `references/decisions.md`.
- It never configures Claude Code against an open-weight model. Anthropic "doesn't support routing Claude Code to non-Claude models through any gateway" (https://code.claude.com/docs/en/llm-gateway). Claude Code is for a private Claude route only, for example a private Bedrock or Agent Platform endpoint.
- It runs no tool. It writes files and the checks; a person runs them inside.

## Workflow

Copy this checklist into your reply and tick it off as you go:

```
Air-gap agent:
- [ ] 1. Blueprint read
- [ ] 2. Interview
- [ ] 3. Tools chosen
- [ ] 4. Serving requirements
- [ ] 5. MCP servers and skills
- [ ] 6. Configuration files
- [ ] 7. docs/airgap/agents.md
- [ ] 8. Manifest rows
- [ ] 9. Verification steps
- [ ] 10. Self-check, until every item holds
- [ ] 11. Hand-over to airgap-transfer
```

1. **Blueprint.** Read `docs/airgap/blueprint.md` (or the path `AGENTS.md` names) and `docs/airgap/transfer-manifest.md`. Take the engine, model, gateway and `code_assistant` headcount from them. With no blueprint, ask for the engine and model in the interview.
2. **Interview.** Read `references/interview.md`. Ask only the questions the user's message and the blueprint leave open. When the user has asked you to set it up, state the defaults you take for the open ones, list them as assumptions in `agents.md`, and continue. Otherwise ask them in one message.
3. **Tools.** Read `references/decisions.md` and the catalog entry of every tool you consider. Decline an open-weight pairing with Claude Code and state the reason. When Codex CLI is chosen, also carry Qwen Code as its fallback, and say in `agents.md`: if `/v1/responses` fails inside, switch to Qwen Code without a second transfer.
4. **Serving.** Read `references/serving.md`. For each tool and model write the API the tool speaks, the parser (or "not documented"), the context window, a served model name without `/`, and the LiteLLM route when a gateway exists.
5. **MCP and skills.** Read `references/mcp.md`. Map each `internal_tools` answer to a server; `fetch` and web search stay off.
6. **Configuration.** Read `references/templates.md`. Write `docs/airgap/agents/<tool>/user/` and, when `central` is yes, `docs/airgap/agents/<tool>/central/`, for each chosen tool. `<tool>` is the catalog slug: `qwen-code`, `codex-cli`, `opencode`, `claude-code`.
7. **agents.md.** Write `docs/airgap/agents.md`: decisions with reasons and alternatives, assumptions (every default used), serving requirements, the environment variable that holds each key, which switches are enforced centrally and which are defaults only (the host firewall is the backstop for both), open items (every Egress switches row without a documented switch, and what the templates leave undocumented), the components added to the manifest (the tool slugs, the MCP servers, and `airgap-agent` for the row of `agents.md` itself), and the steps to verify inside.
8. **Manifest.** Add rows to `docs/airgap/transfer-manifest.md` as the table below shows. Do not rewrite the blueprint. Mark every row you add by writing "(from airgap-agent)" after the component in its Component cell, for example `qwen-code` (from airgap-agent): the manifest has no notes column, and `airgap-transfer` accepts rows so marked, without a blueprint row, when `agents.md` lists their component. In section 3, Component is the catalog slug, Version the pinned version, File the file name, Arch `amd64` or `arm64`, URL the direct download URL from the catalog's Packages table (or the project path for a project file), and Publisher checksums the checksum file URL from that table (empty when it has none).
9. **Verification.** Read `references/verification.md`. Put the three checks into `agents.md` for each tool, and into section 7 of the manifest.
10. **Self-check.** Check every item below; fix what fails and check again.
11. **Hand-over.** Below.

## The catalog

One file per tool. Read an entry before you write about its tool; it holds the pinned version, the install, the egress switches with their sources, the permission settings and what to carry in.

| Tool | Entry | Pinned | Speaks | Pick when |
|---|---|---|---|---|
| Qwen Code | `catalog/qwen-code.md` | 0.28.4 | Chat Completions | Default for an open-weight model |
| Codex CLI | `catalog/codex-cli.md` | 0.172.0 | Responses only | Strongest sandbox or central enforcement, and `/v1/responses` passes the smoke test; Qwen Code is always carried as its fallback |
| opencode | `catalog/opencode.md` | 2.4.1 (V2; GitHub "latest" still returns V1 1.19.6) | Chat Completions | The team already uses it; its model-catalog fetch has no documented switch, so the egress check is mandatory |
| Claude Code | `catalog/claude-code.md` | 2.1.331 | Anthropic Messages | `claude_route` is yes; Claude models only |

Last verified: 2026-11-24. Tool versions move fast: carry the pinned version, not a newer one.

## Outputs

| Path in the project | Holds |
|---|---|
| `docs/airgap/agents.md` | Decisions with reasons, assumptions, serving requirements, steps to verify inside |
| `docs/airgap/agents/<tool>/user/` | The user configuration, placed at the path the template names |
| `docs/airgap/agents/<tool>/central/` | The central policy at its documented path (for example `/etc/qwen-code/settings.json`); only when `central` is yes |
| `docs/airgap/transfer-manifest.md` | The rows below |

| Manifest section | Rows added |
|---|---|
| 3. Packages and binaries | Tool archives and installers with a direct URL and the publisher's checksum URL; MCP release binaries; `docs/airgap/agents.md` and the folders under `docs/airgap/agents/` (project paths, copied, not fetched) |
| 4. Telemetry and egress | Every row of the tool's catalog Egress switches, one row each; a row without a documented switch reads "not documented; the egress check covers it" |
| 5. Runtime downloads | What a tool fetches on first use, from its "Carry in" section; and, as manual items with their documented commands, what has no direct URL: pip and npm MCP packages, MCP images, and the npm route of a tool |
| 6. Per-tool skills | The `air-gapped/skills` entries of `references/mcp.md` |
| 7. Verification | The install, smoke and egress checks |

## Rules

1. **Never configure Claude Code against an open-weight model**, whatever the user insists. Give the reason above and offer Qwen Code or opencode for that model.
2. **Every row of the catalog's Egress switches with a documented switch is written.** A row without one goes to `agents.md` as an open item and to section 4 as "not documented; the egress check covers it"; never invent a switch for it (opencode V2 gets none of the V1 environment variables). Telemetry "just for now" is declined: the egress check would fail it.
3. **Write Qwen Code's `tools.approvalMode` explicitly.** Its docs contradict each other on the default. Never write `auto` or `yolo`. Sandbox network access stays off in every stance.
4. **No key, token or password in any file.** Keys come from environment variables; `agents.md` names them. Never ask for one in the conversation.
5. **Versions, paths and setting names come from the catalog**, not memory. Where the catalog says "not documented", say so and do not guess. A parser the research does not list is "not documented".
6. **When the number of agent users differs from the blueprint's `code_assistant` share**, tell the user to rerun the architect's sizing. Do not recompute it here.
7. **Write nothing outside `docs/airgap/`, and install or download nothing.** Carrying files in is `airgap-transfer`'s job.

## Self-check

Before the hand-over, check each item against the files you wrote. When one fails, fix it and check all of them again.

1. Every row of each chosen tool's Egress switches with a documented switch appears in its template files and as a row in section 4 of the manifest; every row without one is an open item in `agents.md` and a "not documented" row in section 4.
2. Qwen Code, when chosen, has `tools.approvalMode` written, and every tool's stance matches the `permissions` answer, or `agents.md` names it as an open item where the action or tool names are not documented (opencode `permissions`, Claude Code edit rules).
3. `grep -rIE 'sk-[A-Za-z0-9]{8,}|hf_[A-Za-z0-9]{20,}' docs/airgap` finds nothing, and each key is named as an environment variable in `agents.md`.
4. Claude Code appears only with `claude_route` yes and a Claude model; `agents.md` states the reason for any refusal.
5. Each tool has its API, parser (or "not documented"), a context window at or below the engine's `--max-model-len`, and a served model name without `/`.
6. Manifest rows sit in sections 3 to 7 as the table shows, each is marked "(from airgap-agent)", every pinned version equals its catalog entry, and each tool's three checks are in `agents.md`. With Codex CLI chosen, Qwen Code is carried too and `agents.md` names it as the fallback.
7. Every default the interview used is listed as an assumption, and a headcount that differs from the blueprint is flagged.

## Hand-over

Tell the user, in their language:

1. What was written: the tools chosen with the reason for each, and the paths of `agents.md` and the configuration folders.
2. What comes next: run `airgap-transfer`. It bundles the rows marked "(from airgap-agent)" without a blueprint row, and copies `agents.md` and the configuration folders as project files, checksummed like any other file.
3. What the inside does after it unpacks the bundle: follow `docs/airgap/agents.md`: install check, smoke test, egress check. A tool whose egress check shows an unexpected address is not released to developers.
4. What is still open: "not documented" items, assumptions from defaults, and a headcount to re-size.

## Common mistakes

| Mistake | Instead |
|---|---|
| Pointing Claude Code at the local GLM or Qwen model because vLLM documents it | Decline the pairing with Anthropic's statement; offer Qwen Code or opencode |
| Writing the user file only and calling central enforcement done | With `central` yes, write the central file at its documented path too |
| Trusting the settings and skipping the egress check | The check is mandatory: an undocumented connection shows only there |
| Guessing a tool-call parser for a model family the table lacks | Write "not documented" and ask the user to test |
| Installing the newest tool release | Carry the pinned version; the catalog shows when it was verified |
