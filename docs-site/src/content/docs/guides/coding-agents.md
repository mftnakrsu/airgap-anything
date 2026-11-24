---
title: Coding agents inside
description: How airgap-agent sets up Qwen Code, Codex CLI, opencode or Claude Code for a network without internet, why Claude Code is never paired with an open-weight model, and the three checks that run inside.
---

A coding agent installed as-is tries to reach a model catalog, telemetry, update servers and web search on its first start, and it may not speak the API that the internal model server offers. Inside the network nothing can be downloaded to fix that. `airgap-agent` is the third skill: it decides the tool and writes its configuration while you still have internet, so that the inside only unpacks, installs and checks. Like the other two it is plain markdown. It downloads nothing and runs nothing; it writes configuration files and the steps to check them. Its pages are on the [airgap-agent reference](/reference/agent/).

## What it decides

After the blueprint exists, ask in your own words, for example "set up a coding agent for the developers inside". The skill reads the blueprint for the engine, the model, the gateway and how many people use a coding assistant, then asks, in one message, those of its eight questions that your request and the blueprint leave open, each with a default. When you asked it to set things up, it states the defaults it takes instead and goes on. The questions are: who uses agents, which tools, which models, whether you can reach Claude models through a private route, which internal systems agents should reach, how much an agent may do without asking, which operating systems, and whether settings are enforced centrally. [Interview](/reference/agent/interview/) lists them.

Then it chooses the tool, using [Decisions](/reference/agent/decisions/):

| Situation | Tool |
|---|---|
| Default, open-weight model | Qwen Code |
| Strongest sandbox or central enforcement wanted, and the server's `/v1/responses` passes the smoke test | Codex CLI, with Qwen Code carried as the fallback in case that test fails inside |
| The team already uses it | opencode, pinned to version 2.4.1 (the V2 line: GitHub's "latest" still returns V1 1.19.6) |
| A private Claude route | Claude Code |

For each tool it writes the API the tool speaks, the parsers the engine needs, a context window at or below the engine's limit, a served model name without a slash, and the gateway route ([Serving requirements](/reference/agent/serving/)). It picks MCP servers for the internal systems that work offline, and it leaves `fetch` and web search off ([MCP servers and skills](/reference/agent/mcp/)).

## Claude Code, and why only on a Claude route

The skill never configures Claude Code against an open-weight model, even when a model server documents such an integration and even when you ask. Anthropic's [LLM gateway documentation](https://code.claude.com/docs/en/llm-gateway) says it "doesn't support routing Claude Code to non-Claude models through any gateway". Claude Code is offered only when you can reach Claude models through a private route, for example a private Bedrock or Agent Platform endpoint, and hold a Claude account. For an open-weight model the skill offers Qwen Code or opencode and says why.

The same goes for telemetry "just for now". Every outbound switch in a tool's catalog entry is written, and the egress check below proves it; a setting left on would fail that check.

## What it writes

| Path in the project | Holds |
|---|---|
| `docs/airgap/agents.md` | Decisions with reasons and alternatives, every default used as an assumption, the serving requirements, the environment variable that holds each key, and the steps to verify inside |
| `docs/airgap/agents/<tool>/user/` | The user configuration, with every outbound switch off |
| `docs/airgap/agents/<tool>/central/` | The central policy, at the path the tool documents, when you want settings enforced |

It also adds rows to the transfer manifest: the tool archives with their checksum URLs, the MCP packages, every outbound switch, what each tool downloads on first use, and the three checks. Every row it adds is marked "(from airgap-agent)", so `airgap-transfer` accepts it without a blueprint row. `airgap-transfer` then carries `agents.md` and the configuration folders in as project files, checksummed like everything else ([Carrying it in](/guides/carrying-it-in/)). No key is ever written to a file: keys come from environment variables, and the skill never asks for one in the conversation. Qwen Code's `tools.approvalMode` is always written explicitly, because its documentation contradicts itself on the default.

## The three checks inside

A person runs these, in this order, on a developer machine or a jump host, following `agents.md`. No LLM is needed ([Verification inside](/reference/agent/verification/)).

1. **Install check.** The archive's checksum matches the publisher's checksum file where the release publishes one; otherwise (Codex CLI) it matches the SHA-256 recorded when it was carried in. The tool prints the version pinned in its catalog entry. A file that fails is not installed.
2. **Smoke test.** One non-interactive prompt that forces a tool call ("List the files in this folder using your tool") runs against the internal model. A plain text answer with no tool call usually means a missing or wrong parser on the engine.
3. **Egress check.** The same command runs under `strace` on Linux, or with the firewall's deny log read on macOS and Windows. Every address must be the gateway, the engine, the internal DNS resolver (port 53), loopback or a local socket. A tool that shows any other address is not released to developers. opencode in particular has no documented switch for its model-catalog fetch, so for it this check is what proves the configuration.

## Not in scope

The skill ranks no models for agents: card scores are self-reported, and the one cross-model board found is flagged "Flawed" by its publisher. The model comes from the blueprint or from you. It configures no editor extension or other command-line agent beyond a single line each in [Decisions](/reference/agent/decisions/), and it does not operate the tools day to day: catalog entries name per-tool skills for that.
