# Research lab chat assistant: coding agent (`airgap-agent`)

Status: written by `airgap-agent` for the install evals; only the parts the install skill reads are filled in. Date: 2026-11-25. Language: en.

## Decisions

| Decision | Choice | Reason | Alternatives |
|---|---|---|---|
| Tool | Qwen Code `v0.28.4` | Open-weight model served by vLLM; the default tool for it | Codex CLI, opencode |
| Where it runs | on the developers' machines inside the network, from the checked archive `qwen-code-linux-arm64.tar.gz` | Qwen Code is a terminal tool, not a service | none |
| Stance | `tools.approvalMode`: `default` (edit with approval) | `auto` and `yolo` are never written | none |

## Assumptions

| Assumption | Value | Evidence |
|---|---|---|
| Developers | 5 of the 12 users | default, `estimate` |
| Central policy | no | default |
| Platform of the machines | `linux/arm64` | `hardware.cpu_arch` of the blueprint |

## Serving requirements

For `lab-8b` on the vLLM `v0.34.0` engine of the blueprint:

- API: Chat Completions (`/v1/chat/completions`).
- vLLM needs `--enable-auto-tool-choice`, a `--tool-call-parser` for the model family and the matching `--reasoning-parser`. The parser for this model family is not documented: the model's name was not given (open item).
- Served model name: `lab-8b` (no `/`); `model.name` in the settings is the same value.
- Context window: 8192 tokens, not above the engine's `--max-model-len`.
- No gateway: Qwen Code calls the engine's address directly.

## Keys

The key for the engine is read from the environment variable `OPENAI_API_KEY` of the developer's session, with `OPENAI_BASE_URL` and `OPENAI_MODEL`; no key is written in a file.

## Egress switches

Written in the user settings: `privacy.usageStatisticsEnabled: false`, `model.catalogRefresh: false`, `general.enableAutoUpdate: false`, `tools.webSearch.enabled: false`, `"WebFetch"` in `permissions.deny`, `telemetry.enabled: false`.

## Open items

1. The tool-call parser for the model family (not documented).
2. The sandbox image `ghcr.io/qwenlm/qwen-code:<version>`: not used; the tag form was not settled.
3. The number of developers, to be compared with the blueprint's `code_assistant` share (none: re-run the architect's sizing if the lab adds coding assistants).

## Components added to the manifest

`qwen-code`, `airgap-agent`.

## Checks to run inside

The install check, the smoke test and the egress check of `references/verification.md`, in section 7 of `docs/airgap/transfer-manifest.md`, each marked "(from airgap-agent)".
