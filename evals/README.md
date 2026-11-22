# Skill behavior evals

These evals check what an agent does with and without the skill. They need a model, so they are run by hand before each release, not in CI. The deterministic expectations in each scenario's `expected.json` are checked in CI by `tests/test_scenarios.py`.

The method is the one in `superpowers:writing-skills`: watch an agent fail without the skill, write the skill for those failures, watch it pass, close loopholes.

## Scenarios

Each folder under `scenarios/` has:

| File | Use |
|---|---|
| `prompt.md` | What the user says. Given to the agent as is. |
| `answers.json` | The answers a correct interview extracts from the prompt. |
| `expected.json` | `deterministic`: tier and sizing, checked in CI. `decisions` and `process`: what the agent's result is scored against. |

`decisions` in `expected.json` uses four checks per layer:

| Key | Passes when |
|---|---|
| `components` | The decision's `components` equal this list, in any order |
| `includes` | The decision's `components` contain every listed ID |
| `mentions` | Every listed word appears in the decision's `components` or `existing`, ignoring case |
| `empty` | `true`: `components`, `existing` and `custom` are all empty. `false`: at least one is not. |

## Runs

Every run uses a fresh agent with no memory of earlier runs, working in a new empty directory.

| Run | Skill | Superpowers | Prompt prefix |
|---|---|---|---|
| Baseline | no | not mentioned | none |
| With skill | yes | told it is installed | "A skill is installed at SKILL_DIR. Read SKILL_DIR/SKILL.md and follow it. The superpowers plugin is installed; `superpowers:brainstorming` and `superpowers:writing-plans` are available." |
| With skill, no superpowers | yes | told it is absent | "A skill is installed at SKILL_DIR. Read SKILL_DIR/SKILL.md and follow it. The superpowers plugin is not installed; no `superpowers:` skill exists in this session." |

`SKILL_DIR` is the absolute path of a copy of the skill outside this repository, for example a `git archive` of `skills/airgap-architect` at the commit under test. Record that commit in the results file.

Every prompt ends with: "Work in the directory RUN and do not read files outside it. When you reach a point where you need the user's approval, stop and report what you produced." In runs with the skill, the first sentence reads "Work in the directory RUN, and read files only in RUN and SKILL_DIR." RUN is a new empty directory for the run. Every run also gets a second new empty directory, TMP, next to RUN, and the prompt adds, after its first sentence: "Put any temporary file in TMP and nowhere else; you may read it there."

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

For runs with the skill, also record:

1. Whether `lint.py` exits 0 on the result.
2. Each `decisions` check in `expected.json`: pass or fail. `score.py` prints them.
3. Each `process` line in `expected.json`: pass or fail.

With `RUN` set to the directory the agent worked in and `NAME` to the scenario:

```bash
python3 skills/airgap-architect/scripts/lint.py --blueprint "$RUN/docs/airgap/blueprint.json" --project-root "$RUN"
python3 evals/score.py --blueprint "$RUN/docs/airgap/blueprint.json" --expected "evals/scenarios/$NAME/expected.json"
```

Quote the agent's own words wherever it justifies a failure. Those quotes are what the skill's wording is fixed against.

## What the results change

- A failure the baseline shows and the skill run does not: the skill works for it.
- A failure both show: fix the skill, run again.
- A failure the baseline does not show in any scenario: the part of `SKILL.md` aimed at it is removed.
- A failure that only the skill can cause, such as running two interviews (F9), cannot show in the baseline; the runs with the skill test it, and the part of `SKILL.md` aimed at it stays.

## Triggering

The runs above tell the agent to read `SKILL.md`, so they do not show whether Claude Code picks the skill on its own. `triggering/` checks that, with `claude plugin eval`: each case is one message, as a person would type it, sent to a fresh Claude Code session in which only this plugin is installed.

| Cases | The message | Passes when |
|---|---|---|
| `auto-*` | A natural request in English or Turkish that does not name the skill | Claude calls the Skill tool for `airgap-architect`, and its reply starts the interview instead of answering from memory |
| `manual-*` | `/airgap-anything:airgap-architect` and a request | The skill's instructions load (the agent reads its `references/`), and the reply starts the interview |
| `skip-*` | A request the skill must leave alone, including a near miss ("what does air-gapped mean") | Claude does not call the skill |

A slash command is expanded before the session starts, so a manual start makes no Skill tool call; the manual case looks for the skill's own files in the session trace instead.

Run from the repository root. Each run is a real Claude Code session on your account and costs money, so set a ceiling:

```bash
claude plugin eval . --eval-dir evals/triggering --runs 3 --ablation none -j 3 \
  --no-publish --trust-plugin --max-cost-usd 9 --json /tmp/triggering.json --threshold 0
```

`--ablation none` skips the no-plugin arm, which can never call the skill and so tells nothing here. `--no-publish` keeps the report on your machine. Raw results land in `evals/triggering/results/`, which git ignores; record the summary under `results/`, with the model, the Claude Code version and the commit. Rerun when the `description` in `SKILL.md` changes.

CI runs the same suite from `.github/workflows/triggering.yml`: on a pull request that changes `SKILL.md`, the suite or the workflow, on a `v*` tag, and by hand (Actions > triggering > Run workflow). It needs a credential in the repository secrets: `ANTHROPIC_API_KEY`, an Anthropic API key billed per run, or `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token`, which bills a Claude subscription (not yet tried with `claude plugin eval`). Without either, the job leaves a notice and skips the suite rather than failing. A pull request from a fork gets no secrets, so the job is skipped there. A case passes at a score of 0.8: an `auto-*` or `manual-*` case survives one missed grader in three runs, a `skip-*` case fails on a single false start. The JSON result is kept as the run's artifact.
