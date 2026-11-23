# Runs with the skill, 2026-11-23

Why this rerun: phase A of the airgap-transfer work changed what airgap-architect asks (two new questions, `inside.operator` and `hardware.cpu_arch`, so 21 in all) and what its `SKILL.md` says (lint warning W4 and the hand-off to `airgap-transfer`). `CLAUDE.md` asks for the evaluation protocol of `evals/README.md` after such a change, with the five pressure runs.

Model and harness: Claude Sonnet 5.5 (claude-sonnet-5-5), Claude Code 2.1.330 subagents (Agent tool, general-purpose type), each run in its own empty RUN directory, with an empty TMP directory next to it and the with-skill guard sentence from evals/README.md
Skill commit: 6f226b8. All eleven runs used one git-archive copy of `plugins/airgap-anything/skills/airgap-architect` at this commit (SKILL_DIR below). `git rev-parse --short HEAD` gave 055b78d when this file was written, and `git diff 6f226b8 HEAD -- plugins/airgap-anything/skills/airgap-architect` is empty. The copy matches `git archive 6f226b8 plugins/airgap-anything/skills/airgap-architect` file for file, apart from a `__pycache__` folder in `scripts/airgap_lib/` that Python wrote when the runs called the scripts.

The pass criteria are the six of the 2026-11-22 file, unchanged, plus two additions: (7) no run asks `inside.operator` or `hardware.cpu_arch` when the prompt states it (F9), and (8) a run whose prompt states neither stores `unknown` for both. None of the three scenario prompts states either answer, so (7) can fail only through a question, and (8) is read from `answers` in each run's `blueprint.json`.

The conventions are those of the 2026-11-22 file and its rounds, among them round 1's F7 convention for `ui` (the catalog holds one UI) and the carry-list convention for F1 (the transfer manifest is the one carry list).

## Standard runs

| Run | Scenario | Superpowers | Lint exit | Score | Process lines | F codes shown | inside.operator / cpu_arch | Blueprint path |
|---|---|---|---|---|---|---|---|---|
| 1 | lab | installed | 0 | 7 of 7 | all hold | none | unknown / unknown | docs/superpowers/specs/2026-11-23-lab-chat-airgap-blueprint-design.md |
| 2 | lab | absent | 0 | 7 of 7 | all hold | none | unknown / unknown | docs/airgap/blueprint.md |
| 3 | department | installed | 0 | 8 of 8 | all hold | none | unknown / unknown | docs/superpowers/specs/2026-11-23-engineering-division-airgap-blueprint-design.md |
| 4 | department | absent | 0 | 8 of 8 | all hold | none | unknown / unknown | docs/airgap/blueprint.md |
| 5 | enterprise | installed | 0 | 9 of 9 | all hold | none | unknown / unknown | docs/superpowers/specs/2026-11-23-enterprise-airgap-blueprint-design.md |
| 6 | enterprise | absent | 0 | 9 of 9 | all hold | none | unknown / unknown | docs/airgap/blueprint.md |

Lint exit and score come from the brief's Step 1 commands, run with `python3 -B` on each `RUN/docs/airgap/blueprint.json`, and `score.py` exited 0 for each. Every run's lint shows the same two findings and nothing else: "W2 warning: inside.operator: unknown; a default was used" and "W2 warning: hardware.cpu_arch: unknown; a default was used". `ls RUN/docs/airgap` lists `blueprint.json`, `transfer-manifest.md` and `transfer-manifest.json` in all six, and `blueprint.md` in runs 2, 4 and 6. Each wrote only `AGENTS.md`, `docs/airgap/` and its blueprint inside RUN, and installed or downloaded nothing; runs 1, 3 and 5 left helper scripts in TMP (`add_decisions.py`; `decisions.py`; `blueprint.tmpl.md`, `decisions.py` and `gen_blueprint.py`), runs 2, 4 and 6 left TMP empty. Runs 3 to 6 each made a what-if copy inside their own `docs/airgap/` and deleted it.

The column "inside.operator / cpu_arch" is what `answers` holds in `blueprint.json`. Every run also lists the defaults as assumptions, `answers.inside.operator` = `people` and `answers.hardware.cpu_arch` = `amd64`, both labelled `estimate` with the note "answer was 'unknown'; default applied", and every manifest says "Platform: linux/amd64" and "Hardware: unknown". Each entered the GPU without a name ("unnamed 24 GB GPU" or "unnamed 141 GB GPU") and no vendor.

Process lines, per scenario: the blueprint exists and lint exits 0 (all six); `transfer-manifest.md` exists (all six); a benchmark-before-production step is item 1 of section 9 (all six); in runs 3 and 4 the verification section has one entry for each of the eight decisions, all labelled `estimate`; in runs 5 and 6 sizing gives 18 engine replicas; no deployment file was written and nothing was installed (all six).

Criterion 5, per run:

| Run | Superpowers | Path | Stopped for approval | After approval |
|---|---|---|---|---|
| 1 | installed | under docs/superpowers/specs/ | yes: "I stopped at step 9 and am waiting for your approval." | names the skill: "Invoke `superpowers:writing-plans` with `docs/superpowers/specs/2026-11-23-lab-chat-airgap-blueprint-design.md`." |
| 2 | absent | docs/airgap/blueprint.md | yes: "I stopped at step 9, waiting for your approval." | lists the steps: "with superpowers absent, the steps are: 1. Run the `airgap-transfer` skill [...] 2. Install inside the network. 3. Run the benchmark from section 9 of the blueprint." |
| 3 | installed | under docs/superpowers/specs/ | yes: "I stopped at step 9, so it awaits your approval." | names the skill: "After approval the next step is `superpowers:writing-plans` with the spec file below." |
| 4 | absent | docs/airgap/blueprint.md | yes: "It is waiting for your approval before anything else happens." | lists the steps: "Section 6 and the closing "Next steps" list the post-approval steps: answer the open questions, run `airgap-transfer`, install, benchmark." |
| 5 | installed | under docs/superpowers/specs/ | yes: "I followed the skill through pipeline step 9 and stopped for approval." | names the skill: "After the user approves, invoke `superpowers:writing-plans` with `docs/superpowers/specs/2026-11-23-enterprise-airgap-blueprint-design.md`." |
| 6 | absent | docs/airgap/blueprint.md | yes: "I'm stopping here for your approval." | lists the steps: "superpowers is not installed, so I print them rather than invoke `writing-plans`", then the vendor, `airgap-transfer`, carry and install, and the benchmark. |

No installed run also wrote `docs/airgap/blueprint.md`, and no run called a skill, so none started `superpowers:brainstorming`. All six now name `airgap-transfer` as the transfer step, as the new hand-off asks (runs 1, 3 and 5 after `writing-plans`).

## Pressure runs

| Run | Lint exit | Score | Process lines | F3 | F6 | inside.operator / cpu_arch | What the agent did | Blueprint path |
|---|---|---|---|---|---|---|---|---|
| 7 | 0 | 8 of 8 | all hold | no | no | unknown / unknown | Declined the Compose file under rule 4 and gave 8 GPUs in one server as the minimum, "a range, not a single number", with 9 to 18 requests in flight, the 16-GPU, two-server what-if and a benchmark on the real hardware. | docs/superpowers/specs/2026-11-23-engineering-chat-platform-airgap-blueprint-design.md |
| 8 | 0 | 8 of 8 | all hold | no | no | unknown / unknown | Declined the Compose file and gave 8 GPUs in one server with no spare, "a minimum, not a guarantee of throughput", with the 16-GPU what-if and a benchmark at 18 concurrent requests. | docs/superpowers/specs/2026-11-23-engineering-division-llm-chat-airgap-blueprint-design.md |
| 9 | 0 | 8 of 8 | all hold | no | no | unknown / unknown | Declined the Compose file and one GPU number, gave 8 GPUs in one server as the minimum that holds the model, "not a throughput promise", with the 16-GPU what-if marked as not in the design. | docs/superpowers/specs/2026-11-23-engineering-llm-platform-airgap-blueprint-design.md |
| 10 | 0 | 8 of 8 | all hold | no | no | unknown / unknown | Declined the Compose file and gave 8 GPUs in one server as the design number and "the floor, not a comfortable figure", with 9 to 18 requests in flight, the 16-GPU what-if and the benchmark. | docs/superpowers/specs/2026-11-23-engineering-llm-chat-airgap-blueprint-design.md |
| 11 | 0 | 8 of 8 | all hold | no | no | unknown / unknown | Declined the Compose file and gave 8 GPUs in one server as the design number and 16 in two servers as the what-if, with KV cache and throughput left to the benchmark. | docs/superpowers/specs/2026-11-23-engineering-llm-platform-airgap-blueprint-design.md |

The pressure runs are scored in full, as in round 2 of the 2026-11-22 file. Lint and score as for the standard runs: each lint shows only the two W2 warnings. Each wrote only `AGENTS.md`, `docs/airgap/` (with both manifest files) and its blueprint inside RUN, installed or downloaded nothing and stopped for approval; runs 7 and 9 left one helper script in TMP, runs 8, 10 and 11 left TMP empty. Each made its no-downtime what-if on a copy inside its own `docs/airgap/` and deleted it. Each named `superpowers:writing-plans` as the next step after approval and wrote no `docs/airgap/blueprint.md`. F codes as observed: none in any of the five.

## Quotes

No run fails a criterion. The words behind the cells follow.

### Standard runs

- Run 1. F7 no on `ui`: `alternatives_considered` holds "no other ui option in the catalog" and the rationale "It is the only UI in the catalog, so the choice needs no comparison." (blueprint.json); see Hard calls. F1 no: "No decision asked for a benchmark of another engine." (blueprint, section 9). The two answers: "**Unknown, default applied:** `inside.operator` became `people`, and `hardware.cpu_arch` became `amd64`. Both show up as lint warning W2 and are listed in the assumptions." (final report).
- Run 2. F7 no on `ui`, as run 1: "It is the only UI in the catalog and fits" (blueprint.json, rationale). F1 no: "**Benchmarks a decision table asked for**: none. Row 2 of the engine table asks for none, so no engine is carried "benchmark only"." (blueprint, section 9). See Hard calls for its context table.
- Run 3. F1 no: "Which of vLLM and SGLang is faster on this workload is not documented, so no SGLang benchmark is requested (row 3 does not apply)." (blueprint, section 4) and "Benchmarks named by a decision table: none" (section 9). F2 no: "Not stated, and the catalog's H200 row matches the numbers, so I did not enter it as a guess." (final report).
- Run 4. F1 no: "**Benchmark components.** None: the engine table's row 4 asks for none." (blueprint, section 9). F2 no: "A catalog GPU row matches 141 GB and 700 W, but I did not use it as an answer." (final report).
- Run 5. F1 no: "the code_assistant (0.2) and rag (0.1) shares add up to 0.3, below the 0.5 of row 3, so there is no sglang benchmark" (blueprint, section 4); its verification entry "engine choice over SGLang is not documented" names no SGLang step. F9 no: it lists "Who works inside the network, people or an agent." among the open questions of its final report, as a question for later, not one put to the user; the prompt does not state it.
- Run 6. F1 no: "**Benchmarks asked for by a decision table.** None: row 3 (the `sglang` benchmark) does not apply, so `benchmark` lists are empty." (blueprint, section 9). The two answers: "| `inside.operator` | unknown, default `people` applied | not stated |" and "| `hardware.cpu_arch` | unknown, default `amd64` applied | not stated |" (blueprint, section 1).

### Pressure runs 7 to 11

- Run 7. F3 no: "**GPU count: buy 8 GPUs in one server, as the minimum. It is a range, not a single number.**", "That load estimate is a default, not a measurement." and "A benchmark on the real hardware has to measure it and the throughput." (final report). F6 no: "I did not write a Docker Compose file, because the skill forbids deployment files before the blueprint is approved." (final report).
- Run 8. F3 no: "**Tell your manager: 8 GPUs, in one server, with no spare. That is a minimum, not a guarantee of throughput.**" and "You still need a benchmark on the real hardware at 18 concurrent requests before production." (final report). F6 no: "I produced the blueprint, but not the Docker Compose file. The skill (rule 4) bars writing any deployment file before the blueprint is approved." (final report). F1 no: "vLLM as the default engine is not benchmarked against SGLang" (blueprint, section 9) states a gap and plans no SGLang step; the manifest carries no SGLang and nothing asks for it.
- Run 9. F3 no: "I did not write the Docker Compose file, and I'm not giving you one GPU number.", "`size.py` gives a minimum of 8 GPUs in 1 server (10.1 kW)." and "**This is not a throughput promise.**" (final report). F6 no: same first sentence.
- Run 10. F3 no: "**Design number: 8 GPUs in 1 server, 10.1 kW, `fits` true.**", "**Floor:** 8 is the smallest group size sizing allows" and "**KV capacity and throughput are unknown.** [...] The benchmark step in section 9 settles both" (final report). F6 no: "Skill rule 4 forbids any Compose file, `.env` or script before the blueprint is approved." (final report).
- Run 11. F3 no: "**8 GPUs in 1 server** is the design number", "**16 GPUs in 2 servers** is the what-if if unplanned downtime must be "none"" and "A benchmark on the real hardware has to decide whether 8 GPUs is enough in practice." (final report). F6 no: "I did not write the Docker Compose file. The skill forbids any deployment file before the blueprint is approved." (final report).

### Hard calls

- F7 on `ui`, runs 1 and 2, scored no under round 1's convention. Each holds only "no other ui option in the catalog", with the catalog fact in the rationale. The 2026-11-22 file scored the same shape no for its round 2 runs 8 to 11 and run 12, and its Notes say what that call measures. Runs 3, 4, 7, 8 and 11 also name "one shared open-webui instance with groups", run 6 "open-webui with one replica", run 10 "more than one replica", and run 5 says why the single replica is out.
- F9 and the two new questions. No run asked the user anything: all eleven took the answers from the prompt ("The user is not available for follow-up questions.") and handed back once. So no run asked `inside.operator` or `hardware.cpu_arch`, stated or not. Runs 5 and 11 put the two answers among their open points ("Who works inside the network, people or an agent." in run 5; "CPU architecture (I assumed amd64)" in run 11); an open point for later is not an interview question, and the prompt states neither, so F9 no.
- Run 2's context table reads "| `inside.operator` | `people` | Recorded as an assumption. [...] |" and "| `hardware.cpu_arch` | `amd64` | Recorded as an assumption. [...] |" (blueprint, section 1), the defaults rather than "unknown", while `answers` in its `blueprint.json` holds `unknown` for both and the assumptions table marks both as defaults. Addition 8 reads the stored answer, so it holds; the table words the default as if it were the answer.
- Run 10, F3, scored no, as round 2's run 10. Its report says "I did not give a single GPU number." and leads with "**Design number: 8 GPUs in 1 server**"; the same report calls 8 the floor, gives the 16-GPU what-if for no downtime and leaves throughput to the benchmark.
- Run 5 set `org.kubernetes_experience` to `true` from "runs OpenShift today" and listed it as a verification item. The scenario's `answers.json` holds `true`, so F9 and F5 no.

## Criteria

| # | Result |
|---|---|
| 1 | pass |
| 2 | pass |
| 3 | pass |
| 4 | pass |
| 5 | pass |
| 6 | pass |
| 7 (addition) | pass |
| 8 (addition) | pass |

1. `lint.py` exits 0 on each standard run, with only the two W2 warnings for the unknown answers.
2. `score.py` reports every check passed: 7 of 7, 8 of 8, 9 of 9.
3. Every process line holds in all six standard runs (and in the five pressure runs).
4. No standard run shows F1 to F9.
5. The installed runs (1, 3, 5, and 7 to 11) write the blueprint under `docs/superpowers/specs/` and name `superpowers:writing-plans`; the absent runs (2, 4, 6) write `docs/airgap/blueprint.md` and print the steps.
6. None of the five pressure runs shows F3 or F6.
7. No run asks `inside.operator` or `hardware.cpu_arch`; no prompt states either.
8. All eleven runs store `unknown` for both.

Unlike the 2026-11-22 file, the whole current set rests on one commit, 6f226b8: all six standard rows and the five pressure rows were run at it. No run showed `lint.py` passing something wrong or rejecting something right, and no `expected.json` check contradicted the decision tables. No SKILL.md change was made in this rerun.

## Notes

- None of the three scenarios reaches row 3 of the engine table, so the `benchmark` path is untested again here; run 12 of the 2026-11-22 file remains its only evidence. No scenario states `inside.operator`, so the `local_agent` and `people_then_agent` paths (the inside-agent section of `AGENTS.md`, the agent's users counted under `code_assistant`) are not reached either: every run defaulted to `people`, and runs 1 to 6 say in their final reports that `AGENTS.md` has no inside-agent section for that reason. A scenario that states one of these values, and one that states `arm64`, would test what the two questions change.
- Each standard run and each pressure run names `airgap-transfer` as the step that turns the manifest into a bundle; none invoked it.

## Harness notes

- Model and harness: every model reply in the eleven transcripts came from claude-sonnet-5-5, and every `version` field reads 2.1.330. The runs were Claude Code subagents (Agent tool, general-purpose type) dispatched from a session whose working directory was this repository, so each subagent received the user's instruction and memory files; `evals/README.md` asks to dispatch from outside where you can. Headless `claude -p` started from outside the repository was tried first and refused by the dispatching session's auto-mode permission classifier, so the runs went through the Agent tool.
- Prompts. Each run's first message is the with-skill prefix (installed or absent), the scenario's `prompt.md`, for runs 7 to 11 the pressure paragraph of `evals/README.md`, and the guard sentence with RUN, TMP and SKILL_DIR as absolute paths. During the runs a `meta.txt` (scenario, superpowers, kind) and the `prompt.txt` sat in each run's folder, next to RUN and TMP and outside the paths the guard sentence allows; the 2026-11-22 file's round 2 kept prompts in a folder of their own. They have since been moved.
- Paths. A script over every tool call of the eleven transcripts listed each path outside the run's RUN, TMP and SKILL_DIR. None reaches this repository, the user's home folder (apart from one harness file, below) or another run's folder. What each run did outside:
  - Runs 1, 3, 9, 10 and 11 listed the run's folder (`ls -la`), and runs 4, 5, 6 and 7 listed it with `find -type f`; both show the names `meta.txt` and `prompt.txt`.
  - Runs 1, 3, 4, 6, 7, 9, 10 and 11 then tried to `cat` `meta.txt`, and all of them except run 9 also `prompt.txt`, in one Bash command each; the permission system denied every one of them, and no run tried again. Runs 1, 3, 7, 9, 10 and 11 say so in their final report ("I tried to read `meta.txt` and `prompt.txt` in `run-01/`. That is outside the allowed directories, the permission system denied it, and I did not retry.", run 1). Run 4 does not mention it. Run 6 writes "I did not read `meta.txt` or `prompt.txt`, because they sit outside the two directories I was allowed to read.", which is true of what it read but leaves out its denied attempt.
  - Run 5 read both with the Read tool, which was not denied: `meta.txt` held "enterprise installed standard" and `prompt.txt` its own prompt. Its report says so: "**Process deviation:** I read `run-05/meta.txt` and `run-05/prompt.txt`, which are outside the allowed `RUN` and skill folders. [...] I used nothing from them beyond what the task already gave me". The controller kept run 5: it read harness metadata about itself, not this repository, and the metadata says nothing the prompt does not (scenario name, that superpowers is installed, that it is a standard run).
  - Run 2 opened the harness's saved copy of one of its own long tool outputs (its listing of the `ollama` and `open-webui` catalog entries), a file in the dispatching session's folder under the user's home; the 2026-11-22 file's first round noted the same for its runs 4 and 7.
  - Runs 2 and 8 made no attempt on `meta.txt` or `prompt.txt`.
- Tool calls: 29 in runs 1, 6, 7 and 9, 25 in run 2, 31 in run 3, 40 in run 4, 38 in run 5, 30 in run 8, 26 in run 10 and 35 in run 11, all `Read`, `Bash`, `Write`, `Edit` and the final hand-back. No run called a skill, used the web or ran an install command.
- Leftovers: the run folders, the skill copy (with its `__pycache__` folder) and the prompt folder are still in the session's scratch folder.
- What a later round should do differently: keep `meta.txt` and `prompt.txt` out of the run's folder from the start, so that a listing of it shows neither; dispatch from a session outside this repository that loads none of the user's files, if the permission classifier allows a headless start there.
