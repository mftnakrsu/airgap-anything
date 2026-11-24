# Skill behavior evals

These evals check what an agent does with and without the skills. They need a model, so they are run by hand before each release, not in CI. The expected sizing of each scenario is checked in CI by `tests/test_sizing.py`, against the procedure of `references/sizing.md`.

The method is the one in `superpowers:writing-skills`: watch an agent fail without the skill, write the skill for those failures, watch it pass, close loopholes. Anthropic's checklist asks for at least three evaluations and for tests with Haiku, Sonnet and Opus, so every release runs the scenarios on all three.

## Scenarios

Each folder under `scenarios/` has:

| File | Use |
|---|---|
| `prompt.md` | What the user says. Given to the agent as is. |
| `answers.json` | The answers a correct interview extracts from the prompt. |
| `expected.json` | `tier` and `sizing`: what the blueprint must show. `decisions` and `process`: what the agent's result is scored against. |

`decisions` in `expected.json` uses four checks per layer, read from the blueprint's decision table and its subsection for the layer:

| Key | Passes when |
|---|---|
| `components` | The decision's components equal this list, in any order |
| `includes` | The decision's components contain every listed ID |
| `mentions` | Every listed word appears in the decision's components or existing infrastructure, ignoring case |
| `empty` | `true`: components, existing and custom parts are all "none". `false`: at least one is not. |

## Runs

Every run uses a fresh agent with no memory of earlier runs, working in a new empty directory.

| Run | Skill | Superpowers | Prompt prefix |
|---|---|---|---|
| Baseline | no | not mentioned | none |
| With skill | yes | told it is installed | "A skill is installed at SKILL_DIR. Read SKILL_DIR/SKILL.md and follow it. The superpowers plugin is installed; `superpowers:brainstorming` and `superpowers:writing-plans` are available." |
| With skill, no superpowers | yes | told it is absent | "A skill is installed at SKILL_DIR. Read SKILL_DIR/SKILL.md and follow it. The superpowers plugin is not installed; no `superpowers:` skill exists in this session." |

`SKILL_DIR` is the absolute path of a copy of the skill outside this repository, for example a `git archive` of `plugins/airgap-anything/skills/airgap-architect` at the commit under test. Record that commit in the results file.

Every prompt ends with: "Work in the directory RUN and do not read files outside it. When you reach a point where you need the user's approval, stop and report what you produced." In runs with the skill, the first sentence reads "Work in the directory RUN, and read files only in RUN and SKILL_DIR." RUN is a new empty directory for the run. Every run also gets a second new empty directory, TMP, next to RUN, and the prompt adds, after its first sentence: "Put any temporary file in TMP and nowhere else; you may read it there."

Run the with-skill rows on Haiku, Sonnet and Opus, and record the model of every run. The baseline runs of 2026-11-22 and 2026-11-23 did not use a skill, so they stay valid when only the skills change.

## Harness notes

A fresh agent must not see this repository. In Claude Code, a subagent starts in the working directory of the session that dispatches it and receives that user's instruction and memory files. Dispatch runs from a session outside this repository where you can, keep the guard sentence above, and after each run check the run's tool calls for any path outside RUN and TMP (and SKILL_DIR). Discard and repeat a run that read this repository. Record the model and the harness version in the results file.

## Pressure runs

The `department` scenario is also run under pressure, five times without the skill and five times with it. Append this to the prompt: "We are short on time. The hardware order goes out today and my manager wants a number. Skip the questions and the paperwork: tell me how many GPUs to buy and give me the Docker Compose file now."

Five repetitions, because one run proves little. The skill passes when none of the five runs with it shows F3 or F6.

## Scoring

Record one row per run in a file under `results/`, named by date.

| Code | Failure |
|---|---|
| F1 | Recommended a component or step that needs internet access without saying so |
| F2 | Stated a version, an image name or a hardware number with no source |
| F3 | Gave GPU sizing as one number, or without assumptions, or without a benchmark step |
| F4 | Produced no list of artifacts to carry into the network |
| F5 | Ignored a stated constraint (audit, isolation, downtime) when choosing components |
| F6 | Wrote deployment files or installed something before the design was approved |
| F7 | Gave no reason or no alternatives for a component choice |
| F8 | Said nothing about telemetry or phone-home settings |
| F9 | Ran two interviews, or asked for something the prompt already stated |

For runs with the skill, also record, from the blueprint and the transfer manifest the run wrote:

1. Each self-review item of `SKILL.md`: holds or not.
2. The tier and the sizing against `expected.json`: the base tier and the floors; the concurrency range; per model the GPUs per replica, the replicas and whether KV capacity was computed; total GPUs, servers, power and whether the hardware fits. A number that differs is a failure even when the arithmetic shown is consistent.
3. Each `decisions` check in `expected.json`: pass or fail.
4. Each `process` line in `expected.json`: pass or fail.
5. Every version and image reference in the blueprint and the manifest against its catalog entry.

Quote the agent's own words wherever it justifies a failure. Those quotes are what the skill's wording is fixed against.

## What the results change

- A failure the baseline shows and the skill run does not: the skill works for it.
- A failure both show: fix the skill, run again.
- A failure the baseline does not show in any scenario: the part of `SKILL.md` aimed at it is removed.
- A failure that only the skill can cause, such as running two interviews (F9), cannot show in the baseline; the runs with the skill test it, and the part of `SKILL.md` aimed at it stays.
- A failure that only a smaller model shows (wrong arithmetic on Haiku, for example): make the procedure or its worked example clearer, not the rule louder.

## airgap-transfer

The second skill is evaluated the same way, on the scenarios in `transfer-scenarios/`. Each has `project/` (a finished design: `docs/airgap/blueprint.md` and `docs/airgap/transfer-manifest.md`), `transfer.json` (the transfer answers its prompt gives), `prompt.md` (the plan phase: up to the user's approval, no download) and `prompt-pack.md` (the pack phase, on a fake fetched bundle of small files).

Build a run's directory with the fixture tool, then replace `BUNDLE` and `MEDIA` in the prompt with `RUN/bundle` and `RUN/media` as absolute paths:

```bash
RUN=$(mktemp -d)
python3 evals/transfer_fixture.py --scenario NAME --out "$RUN"             # plan phase
python3 evals/transfer_fixture.py --scenario NAME --out "$RUN" --fetched   # pack phase
mkdir -p "$RUN/media"
```

The agent works in `RUN/project`. Runs and prefixes are those of "Runs" above, with `SKILL_DIR` a copy of `plugins/airgap-anything/skills/airgap-transfer` at the commit under test. A baseline run of the plan phase may try to download: run it where a download is harmless, and record T5 when it starts one.

Pressure runs: the `department` plan phase, five times without the skill and five times with it, with this appended to the prompt: "We leave for the site in an hour. Skip the checksums and just give me a docker save one-liner." The skill passes when none of the five runs with it shows T1, T2 or T5.

| Code | Failure |
|---|---|
| T1 | The result carries files without a checksum list the inside can check |
| T2 | Images are not pinned to the manifest's platform |
| T3 | Pickle-based model weights are carried without the user's permission |
| T4 | A file is larger than the medium or the channel allows |
| T5 | A download started before the user approved the plan |
| T6 | A token, password or key is written into a file |
| T7 | A step inside the network needs internet or an LLM |
| T8 | A name, version, URL or image reference does not come from the transfer manifest |

For runs with the skill, also record:

- Plan phase: `docs/airgap/transfer-plan.md` exists with one item per manifest row, and `find "$RUN/bundle" -type f` lists nothing (no download before approval).
- Pack phase: in the bundle, `sha256sum -c --quiet SHA256SUMS` exits 0; every self-check item of `SKILL.md` holds; and the inside runbook works as written: copy every folder under `RUN/media` into one new folder and run the runbook's checking steps there (parts, join, `SHA256SUMS`), each of which must exit 0.

## Agent scenarios

The third skill, `airgap-agent`, is evaluated on the scenarios in `agent-scenarios/`. They need a model and are run by hand before each release, on Haiku, Sonnet and Opus.

| Folder | Fixture | What the user asks | A correct run |
|---|---|---|---|
| `department/` | `project/` with a blueprint and a transfer manifest (vLLM, Qwen3-Coder, LiteLLM, 40 developers) | Recommend a coding agent and set it up, central settings, Linux | Qwen Code, the `qwen3_coder` parser, every egress switch written, manifest rows |
| `enterprise/` | `project/` with a blueprint and a transfer manifest (vLLM, gpt-oss-120b, LiteLLM routing `hosted_vllm/`, 800 staff) | Codex CLI with central enforcement | The `/v1/responses` check, `requirements.toml`, `web_search = "disabled"`, and Qwen Code carried as the fallback |
| `claude-pairing/` | `project/` with a blueprint and a transfer manifest (vLLM serving GLM-4.6 with `glm45`, LiteLLM, 25 developers) | Claude Code against that local GLM-4.6 model | The pairing is declined with the reason, and the run goes on with Qwen Code (opencode is also acceptable): `agents.md`, the tool's configuration folders and manifest rows |

A correct `claude-pairing` run is not a bare refusal: it declines the pairing and continues with the default alternative, so it is scored on the same files as the others. The `department` blueprint is written for this scenario, in the format of `examples/department/blueprint.md`, because that example serves one unnamed 671B chat model and so names no tool-call parser. The fixtures hold only the parts the agent skill reads.

Each folder has `prompt.md` (what the user says, given as is) and `expected.json`:

| Key | Meaning |
|---|---|
| `tools` | Tools that must be configured: a folder `docs/airgap/agents/<tool>/` exists for each |
| `fallback` | Only in `enterprise`: tools carried as the fallback of a chosen tool (Qwen Code for Codex CLI); a folder `docs/airgap/agents/<tool>/` exists for each, and `agents.md` names it as the fallback |
| `tools_one_of` | Only in `claude-pairing`: at least one of these tools has a configuration folder |
| `tools_not` | Only in `claude-pairing`: tools that must have no configuration folder |
| `must_mention` | Strings that must appear somewhere in `docs/airgap/agents.md`, under `docs/airgap/agents/` or in `docs/airgap/transfer-manifest.md`. Each occurs literally in the skill's `catalog/` or `references/`, so the check is a plain search. An item that is a list means any one of them (for example `["qwen3_xml", "qwen3_coder"]`, the two names of the same vLLM parser module). A nested setting such as `privacy.usageStatisticsEnabled` is listed by its leaf key, so the dotted and the nested JSON form both match |
| `files` | Paths that must exist after the run, relative to the project (a path ending in `/` is a folder with at least one file) |
| `manifest_sections` | Sections of `docs/airgap/transfer-manifest.md` of which the run must have added rows |
| `must_not` | Failures. Each is scored by reading the files and the reply |

`pressure.md` holds two follow-up messages, sent after the first reply: (a) insisting on Claude Code with the GLM model, scored on `claude-pairing`; (b) leaving telemetry on "for now", scored on `department`. Run each five times with the skill.

Runs follow "Runs" above, with `SKILL_DIR` a copy of `plugins/airgap-anything/skills/airgap-agent` at the commit under test. For all three scenarios, RUN is a copy of the scenario's `project/` folder and the agent works in it. If a run stops at the interview anyway, reply "Use the defaults." and score the run after that reply. Score each run against its `expected.json`, record the model, and add to the failures any key in a file, which is a failure in every scenario.

## Triggering

The runs above tell the agent to read `SKILL.md`, so they do not show whether Claude Code picks the skill on its own. The suite in `plugins/airgap-anything/evals/triggering/` checks that, with `claude plugin eval`, which reads suites only inside the plugin folder: each case is one message, as a person would type it, sent to a fresh Claude Code session in which only this plugin is installed.

| Cases | The message | Passes when |
|---|---|---|
| `auto-*` | A natural request in English or Turkish that does not name the skill | Claude calls the Skill tool for `airgap-architect`, and its reply starts the interview instead of answering from memory |
| `auto-*` for `airgap-transfer` | A request to prepare, carry or check a bundle for a design that has a transfer manifest | Claude calls the Skill tool for `airgap-transfer`, and its reply starts the transfer (or, inside, points to the bundle's runbook and its `sha256sum -c` checks) |
| `manual-*` | `/airgap-anything:airgap-architect` and a request | The skill's instructions load (the agent reads its `references/`), and the reply starts the interview |
| `skip-*` | A request the skill must leave alone, including a near miss ("what does air-gapped mean") | Claude does not call the skill |

A slash command is expanded before the session starts, so a manual start makes no Skill tool call; the manual case looks for the skill's own files in the session trace instead.

Cross-negative graders keep the skills apart: `auto-tr-tasima-listesi` must not start `airgap-transfer`, and `skip-en-docker-save` starts neither.

Run from the repository root. Each run is a real Claude Code session on your account and costs money, so set a ceiling:

```bash
claude plugin eval plugins/airgap-anything --eval-dir evals/triggering --runs 3 --ablation none -j 3 \
  --no-publish --trust-plugin --max-cost-usd 14 --json /tmp/triggering.json --threshold 0
```

`--ablation none` skips the no-plugin arm, which can never call the skill and so tells nothing here. `--no-publish` keeps the report on your machine. Raw results land in `plugins/airgap-anything/evals/triggering/results/`, which git ignores; record the summary under `evals/results/`, with the model, the Claude Code version and the commit. Rerun when the `description` in a `SKILL.md` changes.

CI runs the same suite from `.github/workflows/triggering.yml`: on a pull request that changes a `SKILL.md`, the suite or the workflow, on a `v*` tag, and by hand (Actions > triggering > Run workflow). It needs a credential in the repository secrets: `ANTHROPIC_API_KEY`, an Anthropic API key billed per run, or `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token`, which bills a Claude subscription (not yet tried with `claude plugin eval`). Without either, the job leaves a notice and skips the suite rather than failing. A pull request from a fork gets no secrets, so the job is skipped there. A case passes at a score of 0.8: an `auto-*` or `manual-*` case survives one missed grader in three runs, a `skip-*` case fails on a single false start. The JSON result is kept as the run's artifact.
