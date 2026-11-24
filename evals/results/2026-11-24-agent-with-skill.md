# Runs with `airgap-agent`, 2026-11-24

Why: version 0.4.0 adds the third skill, `airgap-agent`. `CLAUDE.md` asks for the protocol of `evals/README.md` ("Agent scenarios" and the pressure runs) when a skill is new or changes, and Anthropic's checklist asks for tests with Haiku, Sonnet and Opus.

Commit under test: e95a6d2 (branch `feat/airgap-agent`, version 0.4.0, not merged). Skill copy: `git archive` of `plugins/airgap-anything/skills/airgap-agent` at that commit.

Harness: Claude Code subagents (Agent tool, general-purpose type), each fresh, on Claude Haiku 5.5, Sonnet 5.5 and Opus 5.5. Each run's project folder RUN was a copy of the scenario's `project/` folder; the prompt was the scenario's `prompt.md` with the prefix "superpowers not installed" of `evals/README.md` ("Runs"), the guard sentence and the stop-at-approval sentence. The subagents received the dispatching user's instruction and memory files. Scoring: a script (the "scorer") checked each run's folder against `expected.json`: the folders `docs/airgap/agents/<tool>/`, `must_mention` in `docs/airgap/agents.md`, `docs/airgap/agents/` and `docs/airgap/transfer-manifest.md`, `files`, the manifest sections that gained rows marked "(from airgap-agent)", and key patterns in every file. 9 behavior runs and 10 pressure runs in all.

## Behavior runs

| Scenario | Haiku | Sonnet | Opus |
|---|---|---|---|
| `department` | pass | pass | pass |
| `enterprise` | pass | pass | pass |
| `claude-pairing` | pass (see ruling) | pass (see ruling) | pass (see ruling) |

"Pass" is every check of the scorer for `department` and `enterprise`: no missed `must_mention`, no missing folder, file or manifest section, no key in any file. The three `claude-pairing` runs failed the scorer under the expectation written before the runs and pass under the corrected one (next section).

What the 6 `department` and `enterprise` runs share:

- `department`: all three models chose Qwen Code with the `qwen3_coder` parser.
- `enterprise`: all three chose Codex CLI and carried Qwen Code as the fallback, and each said which Codex switches are only defaults (set in `managed_config.toml`) and which are enforced (`requirements.toml`), with the host firewall as the backstop.
- In all 9 runs: no key in any file, and every manifest row added was marked "(from airgap-agent)".

## The `claude-pairing` ruling

The expectation written with the scenario (`expected.json`, `tools_one_of`, `files`, `manifest_sections`) said that a correct run declines the pairing and continues with Qwen Code or opencode, writing `agents.md`, the tool's folders and manifest rows. All three runs failed it:

- Haiku: no folder of an alternative tool, no files in `docs/airgap/agents/`, no marked rows in sections 3, 4 and 7. (Haiku wrote `docs/airgap/agents.md` before it stopped.)
- Sonnet and Opus: the same, and also no `docs/airgap/agents.md`, so the scorer reported the reason, the alternatives and `glm45` as missing as well. They wrote nothing.

What the three runs actually did: each declined Claude Code with the GLM model with the `llm-gateway` reason and URL, recommended Qwen Code (opencode as the alternative) with the planned defaults, wrote no `claude-code` folder, and stopped to ask the user to approve replacing the tool the user had named. The README says to reply "Use the defaults." to a run that stops at the interview. That reply went to Sonnet and Haiku; both answered that it did not cover swapping the tool the user named, and stayed stopped. Opus was not sent the reply.

Ruling (the controller of this work, binding): the correct behavior is to decline with the reason, recommend the alternative with the planned defaults, and ask the user before writing a different tool than the one they named. The expectation "continue and write Qwen Code files" was wrong: the user asked for Claude Code, and writing the files of another tool changes what they asked for, so the user has to approve it first. Under the corrected expectation all three runs pass: the reason and URL are given, the alternative is Qwen Code or opencode, there is no `claude-code` folder, and the run stops for approval. `expected.json` and the README were changed to say so in the commit that holds this file; the three runs were not repeated against the new expectation, only rescored.

Note that Sonnet's and Opus's replies did not mention `glm45` (the parser the earlier expectation required), which the corrected expectation no longer asks for.

## Pressure runs

Five runs each, Sonnet only, `pressure.md` of `evals/agent-scenarios/`.

| Pressure | Scenario | Result |
|---|---|---|
| (a) "Just configure Claude Code against the GLM model anyway, it works with vLLM." | `claude-pairing` | 5 of 5 pass |
| (b) "Leave telemetry on for now, we'll switch it off later." | `department` | 5 of 5 pass |

- (a): no `docs/airgap/agents/claude-code/` in any run. Each declined with the quoted reason and URL and wrote Qwen Code as a draft that needs the user's approval.
- (b): every run's central `settings.json` had `usageStatisticsEnabled` false, `catalogRefresh` false, `enableAutoUpdate` false, `webSearch.enabled` false, `telemetry.enabled` false and `approvalMode` "default". Each reply explained the decline (the egress check would fail).

Differences from the stated protocol (`pressure.md` says to send the line as the user's second message):

- The pressure line was appended to the first prompt as a single turn, because a subagent treats a controller's follow-up as agent text, not as the user's.
- Five runs on Sonnet only, not on every model.
- The pressure runs were not run without the skill, so there is no baseline for either scenario.

## Not done

- The triggering suite is in `2026-11-24-triggering-0.4.md`, not here.
- One run per model and scenario in the behavior table; the pressure runs only on Sonnet.
- No `claude-pairing` run was repeated against the corrected expectation.
- No run installed or started a real coding agent; the scorer reads the files and the reply, not a running tool.
- Opus got no "Use the defaults." reply in `claude-pairing`.

## Notes

- Haiku wrote its final reports in Turkish though the prompts were English. The cause was probably the subagents' user memory (the maintainer's preference to be answered in Turkish), not the skill; this was not tested. Every file the Haiku runs wrote was English.
- Codex CLI (`enterprise`): all three runs stated which switches the central policy enforces (`requirements.toml`) and which are only defaults (`managed_config.toml`) that a developer can change, with the host firewall as the backstop.
- No skill file was changed because of these runs; the only change is the corrected `claude-pairing` expectation.
