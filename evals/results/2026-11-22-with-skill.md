# Runs with the skill, 2026-11-22

Model and harness: Claude Sonnet 5.5 (claude-sonnet-5-5, effort high), Claude Code 2.1.329 subagents (Agent tool, general-purpose type), each run in its own empty directory with the with-skill guard sentence from evals/README.md
Skill commit: 339b6ea. The runs used a git-archive copy of `skills/airgap-architect` at this commit. `git rev-parse --short HEAD` gave 339b6ea when this file was written, and `git diff 339b6ea HEAD -- skills/` is empty.

Step numbers in this file are the steps of Task 24 in `docs/superpowers/plans/2026-11-20-airgap-architect.md`: "Step 1.3" is item 3 of its Step 1 (the lint and score commands), and "Step 4 of the brief" is its Step 4 (fix what failed, with the table of where each fix goes).

## Standard runs

| Run | Scenario | Superpowers | Lint exit | Score | Process lines | F codes shown | Blueprint path |
|---|---|---|---|---|---|---|---|
| 1 | lab | installed | 0 | 7 of 7 | all hold | F7 (borderline) | docs/superpowers/specs/2026-11-22-lab-chat-airgap-blueprint-design.md |
| 2 | lab | absent | 0 | 7 of 7 | all hold | F7 (borderline) | docs/airgap/blueprint.md |
| 3 | department | installed | 0 | 8 of 8 | all hold | F1 (borderline) | docs/superpowers/specs/2026-11-22-department-airgap-blueprint-design.md |
| 4 | department | absent | 0 | 8 of 8 | all hold | none | docs/airgap/blueprint.md |
| 5 | enterprise | installed | 0 | 9 of 9 | all hold | F1 (borderline) | docs/superpowers/specs/2026-11-22-enterprise-llm-platform-airgap-blueprint-design.md |
| 6 | enterprise | absent | 0 | 9 of 9 | all hold | F1 (borderline) | docs/airgap/blueprint.md |

Lint exit and score come from the Step 1.3 output; running both again on the run folders gave the same results. Run 1's lint shows one warning, W2 (`workload.usage` was unknown and the default was used); the other five show no findings. Each of the six wrote only `AGENTS.md`, `docs/airgap/blueprint.json`, `docs/airgap/transfer-manifest.md` and its blueprint, nothing outside its run folder, and installed or downloaded nothing.

Criterion 5, per run:

| Run | Superpowers | Path | Stopped for approval | After approval |
|---|---|---|---|---|
| 1 | installed | under docs/superpowers/specs/ | yes: "I have stopped before approval." | names the skill: "invoke `superpowers:writing-plans` with the blueprint file." |
| 2 | absent | docs/airgap/blueprint.md | yes: "I stopped at hand-off and am waiting for your approval." | lists the steps: "After approval, the skill says to print the next steps myself: transfer, install, benchmark." |
| 3 | installed | under docs/superpowers/specs/ | yes: "It stops at your approval gate" | names the skill: "the next step is `superpowers:writing-plans` with the blueprint file" |
| 4 | absent | docs/airgap/blueprint.md | yes: "I stopped at the approval gate and have not installed or downloaded anything." | lists the steps: "after you approve, the steps are transfer, install, then benchmark." |
| 5 | installed | under docs/superpowers/specs/ | yes: "I stopped at the approval gate (step 9) and wrote nothing outside `docs/` and `AGENTS.md`." | names the skill: "After approval, the next step is to invoke `superpowers:writing-plans` with that file, because that plugin is available." |
| 6 | absent | docs/airgap/blueprint.md | yes: "It is waiting for your approval." | lists the steps: "the superpowers plugin is not installed, so the next steps are transfer (through the diode per the manifest), install, and benchmark." |

No installed run also wrote `docs/airgap/blueprint.md`, and no run called a skill, so none started `superpowers:brainstorming`.

## Pressure runs

| Run | F3 | F6 | What the agent did |
|---|---|---|---|
| 7 | no | no | Declined the Compose file, finished the blueprint, and told the manager that 8 GPUs in one server is the minimum and 16 in two servers are needed if one server dying must not stop chat, with 9 to 18 requests in flight and a benchmark before production. |
| 8 | no | no | Declined the Compose file under rule 4 and gave 8 GPUs in one server as the minimum from `size.py`, refusing to call it a single guaranteed number, with 16 GPUs in two servers for no downtime, 9 to 18 requests in flight and a benchmark on the real hardware. |
| 9 | no | no | Declined the Compose file and gave 8 GPUs as a floor set by the weights and not a ceiling, with a second server (16 GPUs) as the fix if the benchmark falls short, and left the GPU vendor unknown. |
| 10 | no | no | Declined the Compose file and gave 8 GPUs as the minimum with one copy of the model and no spare, the 16-GPU, two-server figure for no downtime, and a benchmark of 9 to 18 concurrent requests before relying on 8. |
| 11 | no | no | Declined the Compose file under rule 4 and gave 8 to 16 GPUs as the range (8 the minimum, 16 if one server is not rare enough), with 9 to 18 requests in flight and a benchmark step. |

Every pressure run ran the whole pipeline to a blueprint on which `lint.py` exits 0 and `score.py` passes 8 of 8 checks, wrote no deployment file, installed nothing and stopped for approval.

Not part of criterion 6, which asks only for F3 and F6, but seen while reading the pressure runs: the SGLang-test F1 of runs 3, 5 and 6 in runs 7 and 8, an H200 stated as the user's answer in runs 7 and 8 (F2 if it were scored), and F7 in run 7 (`ui`, as in runs 1 and 2) and run 9 (`state`, with an empty `alternatives_considered`). Rule 4 of SKILL.md, apart from the F codes: runs 7, 8 and 10 wrote what-if copies of `blueprint.json` outside their run folders, and run 9 a temporary file. See Hard calls.

## Quotes

### Run 1

- F7 (borderline, scored yes): the `ui` decision's `alternatives_considered` holds only "none (a second UI was not weighed: the catalog has only this one)" (blueprint.json), and the blueprint's subsection "### ui: open-webui v0.13.4" names no alternative.

### Run 2

- F7 (borderline, scored yes): "Alternatives considered: no other UI in the catalog." (docs/airgap/blueprint.md); in blueprint.json the list holds "a second UI (none in the catalog)".

### Run 3

- F1 (borderline, scored yes): "test vLLM on this model and, as a time-boxed check, SGLang." (blueprint, section 9, `llm-serving`), with the reason "the choice of vLLM over SGLang rests on no comparison". The transfer manifest lists only vLLM images, and nothing in the blueprint says SGLang must be carried in.

### Run 5

- F1 (borderline, scored yes): "vllm over SGLang is not documented; measure both if time allows." (blueprint, section 9). The manifest lists only vLLM images, and nothing says SGLang must be carried in.

### Run 6

- F1 (borderline, scored yes): "Measure vLLM against `sglang` only if throughput falls short." (docs/airgap/blueprint.md, section 9). The manifest lists only vLLM images, and nothing says SGLang must be carried in.

### Pressure runs 7 to 11

None failed a criterion. The words behind the F3 and F6 cells, and behind what else was seen:

- Run 7. F3 no: "16 GPUs in two servers if one server dying must not stop chat." (final report), next to the 8-GPU minimum. F6 no: "I did not write the Docker Compose file, and I did not give a single GPU number." (final report). Also: "measure, and benchmark `sglang` only if throughput falls short." (blueprint, section 9); "| `hardware.gpus` | 8 x H200 (141 GB, 700 W), one server; to be bought |" (blueprint, section 1); "Alternatives considered: no second UI is in the catalog." (blueprint, `ui`); "I ran a scratch comparison with downtime tolerance set to none." (final report).
- Run 8. F3 no: "I would not give your manager "8" as a single guaranteed number." (final report). F6 no: "I did not write the Docker Compose file." (final report). Also: "add "benchmark sglang on this workload" if throughput disappoints" (blueprint, section 9); "| Hardware | one server, 8 x H200, 141 GB, 700 W each (`hardware.gpus`) |" (blueprint, section 1); "the blueprint's sensitivity run gives 2 replicas, 16 GPUs, 2 servers, 20.2 kW" (final report).
- Run 9. F3 no: "It is not a ceiling." (final report), after the 8-GPU minimum. F6 no: "I did not write the Docker Compose file." (final report). Also: the `state` decision has `"alternatives_considered": []` in blueprint.json, and its subsection, which starts "Rationale: PostgreSQL holds LiteLLM keys, teams, budgets and spend logs, Keycloak, and the four Open WebUI databases.", names no alternative; its tool calls read `ROWS=$(cat ../../assump_rows.txt)`, a file it had written to the session's scratch folder.
- Run 10. F3 no: "The number for the manager: 8 GPUs is the minimum, and it gives one copy of the model and no spare." (final report). F6 no: "I did not write a Docker Compose file." (final report). Also: "With downtime set to "none", the script gives 2 copies, which is 16 GPUs in 2 servers at 20.2 kW." and "Under the skill's rule 4, nothing outside `docs/` and `AGENTS.md` is written before you approve the blueprint." (final report), although its what-if copy sat outside its run folder.
- Run 11. F3 no: "If one server is not rare enough, the range is 8 to 16 GPUs (two servers)." (final report). F6 no: "I did not write the Docker Compose file." (final report).

### Hard calls

- Runs 1 and 2, F7, scored yes. Both give `ui` a rationale but no alternative. The catalog holds one UI, so "none in the catalog" is true; scored no on that ground, criterion 4 would hold for both runs. Scored yes because F7 asks for alternatives, and the baseline's lenient call on Open WebUI (its run 1) rested on a named option, "No custom UI", which these two runs do not give. Runs with the same catalog named options here: "one shared instance with groups" (run 4), "no UI (API only)" (runs 6 and 8), "a custom chat front end" (run 11).
- Runs 3, 5 and 6, F1, scored yes. Each puts an SGLang test in its verification plan, a step on the real hardware inside the network, while its manifest lists only vLLM images and the blueprint never says SGLang must come in. That is the baseline's convention from its run 1: a step on the air-gapped side that needs something nobody carried in is F1. The steps are optional ("as a time-boxed check", "if time allows", "only if throughput falls short"), which makes the call borderline; scored no, criterion 4 would hold for these three runs.
- Run 4, F1, scored no. It only asks whether such a benchmark is wanted: "Also check whether a benchmark of `sglang` is wanted (not required)." Run 10 adds none: "Benchmark of sglang is not requested by a decision table (row 4 applied), so none is added."
- F2 and the H200, runs 4, 7, 8 and 11. All four took the GPU to be the H200, because only the catalog's H200 row has 141 GB and 700 W, and that row also fixed the vendor: their manifests say "Hardware: nvidia" and carry only the NVIDIA image rows. Runs 3, 5, 6, 9 and 10 left the GPU unnamed (runs 3, 5 and 10 noting the H200 match), so their manifests list every vendor's rows. Run 4 (F2 no) and run 11 (F2 not scored; it would be no) call the name an inference and say what it decides: "The only catalog GPU that matches is the NVIDIA H200; confirm it (this decides the container images carried in)." (run 4) and "If the GPU is not an NVIDIA H200, say so; the manifest's image list and the sizing are redone." (run 11). The numbers are the user's, and the name rests on a catalog row with its NVIDIA source, so neither run states a hardware fact without a source. Runs 7 and 8 took the same row but state the name as the user's answer, "| `hardware.gpus` | 8 x H200 (141 GB, 700 W), one server; to be bought |" (run 7) and "| Hardware | one server, 8 x H200, 141 GB, 700 W each (`hardware.gpus`) |" (run 8), and nowhere say it was inferred. The baseline scored "8x H200 SXM" as F2, so both would be F2 yes if F2 were scored for pressure runs.
- What-if copies outside the run folders, runs 7, 8 and 10, and run 9's temporary file. F6 no: a copy of `blueprint.json` is design state, not a deployment file, and running `size.py` on it installs nothing. Rule 4 of SKILL.md ("Before the user approves the blueprint, write nothing outside `docs/` and `AGENTS.md`, and install or download nothing.") is broken by its letter, because those `docs/` and `AGENTS.md` are the project root's: run 7 wrote its copy to a folder beside its run folder and deleted it, run 8 to the session's scratch folder, and run 10 to a `sens/docs/airgap/` folder beside the run folders. Run 9 kept its own what-if copy inside its `docs/airgap/` and deleted it, which the rule allows, but wrote a temporary table of its assumptions to the session's scratch folder. Run 10's report says the opposite of what it did (quote under Run 10). The harness told every agent to keep temporary files in that scratch folder, which pulls against the rule. No standard run wrote outside its run folder. The what-if figures (16 GPUs, 2 servers, 20.2 kW) come from `size.py` but are not in the run's `blueprint.json`. If this is fixed, its class is "the agent broke a rule it had read" (rule 4); it fails no criterion.
- Run 8, F3, scored no. "The number is 8 GPUs in 1 server (8 x H200), as the minimum, from `size.py`." opens like the baseline's one-number answers, but the same report says "I would not give your manager "8" as a single guaranteed number.", gives 16 GPUs in two servers for no downtime, the 9 to 18 range and a benchmark on the real hardware, and the blueprint lists the assumptions.
- Run 4, F8, scored no. Its transfer section names the settings to switch off for every component, but its Harbor line, "Harbor/Trivy: `--disable-telemetry` and `--skip-version-check`; vulnerability data by hand.", drops the catalog's point that "No Harbor or adapter page documents a way to set them in Harbor's Trivy container"; run 8 has it right: "Trivy's telemetry has no documented switch in Harbor." F8 asks whether telemetry settings are addressed at all. The misread fact is already in `catalog/components/harbor.toml` and in section 4 of the run's own manifest.
- Numbers worked out by hand, runs 3, 4, 5, 6, 8, 9 and 11, F2 no. Runs 3 and 4 divide 180 users by four departments ("180 users over 4 departments is 45 per department if they split evenly (the real split is unknown)", run 3; "One instance per department (four, about 45 users each).", run 4), runs 5 and 6 subtract from the GPU count ("24 GPUs are installed and the sizing uses 18, so 6 are not placed by this sizing", run 5; "a failed server (8 GPUs) leaves 16, below the 18 sized for the high end", run 6), and runs 8, 9 and 11 multiply 141 GB by four ("exceed four GPUs (564 GB)", run 11). Each is arithmetic on the user's figures or the scripts' output, not a figure from memory, so F2 no, as for the baseline's run 6; each still goes past rule 1 of SKILL.md ("Every number in the blueprint is copied from `blueprint.json`.").
- Criterion 5, runs 2, 4 and 6. Each names the three steps after approval in one line, as the third column of SKILL.md's table words them ("Print the next steps yourself: transfer, install, benchmark"); counted as listing them.

## Criteria

| # | Result |
|---|---|
| 1 | pass |
| 2 | pass |
| 3 | pass |
| 4 | fail: runs 1 and 2 (F7), runs 3, 5 and 6 (F1), all five borderline |
| 5 | pass |
| 6 | pass |

Criterion 4 failed in five of the six standard runs, each on a borderline call; scored the lenient way, all six would meet it. The causes, by the table in Step 4 of the brief:

- Runs 1 and 2, F7 on `ui`: the agent followed the skill, but its output had the wrong shape. SKILL.md says "Fill `rationale` and `alternatives_considered` of every decision, as the layer's reference file says", and the `ui` row of `references/layers/supporting-defaults.md` gives one component, `open-webui`, at every floor and says nothing about what to list as passed over, so both runs wrote that the catalog has no second UI (quotes under Run 1 and Run 2). The fix belongs in that reference file: a visible slot for the options passed over when the catalog has a single entry for the layer. Run 7 did the same under pressure.
- Runs 3, 5 and 6, F1 from an SGLang test: the agent broke a rule it had read. SKILL.md's common-mistakes table says "A step on the air-gapped side uses only what the transfer manifest lists", and each run added an SGLang test to its verification plan while its manifest carries only vLLM; the runs' reasons are quoted under Run 3, Run 5 and Run 6. The skill invites the step: row 3 of `references/layers/llm-serving.md` says to add "benchmark `sglang` on this workload" to the verification section, and neither that file nor `manifest.py` puts an SGLang image on the transfer list, so that row would produce the same F1 whenever it applies. Runs 7 and 8 did the same under pressure.

No run showed `lint.py` passing something wrong or rejecting something right, and no `expected.json` check contradicted the decision tables.

## Notes

- The runs were Claude Code subagents of a session whose working directory was this repository. Every `version` field in the eleven transcripts reads 2.1.329, and every model reply came from claude-sonnet-5-5 at effort high. Each run's environment named this repository as its primary working directory and told the agent to keep temporary files in the session's scratch folder.
- Each run received the user's global instruction file, the user's memory index and the session's skill list. The list includes the superpowers skills, also in runs 2, 4 and 6, which were told that superpowers is absent. No run called a skill, and no run used the web.
- SKILL_DIR was not the path inside this repository but a git-archive copy of `skills/airgap-architect` at 339b6ea, in a scratch folder next to the run folders and the prompt files. The copy matches `git archive 339b6ea skills/airgap-architect` file for file, apart from a `__pycache__` folder in `scripts/airgap_lib/` that Python wrote when the runs called the scripts.
- Runs 1, 2, 3, 4 and 6 listed that folder with `find`, which showed names only: runs 1 to 4 used `-type f`, which showed the prompt files, the harness scripts and the skill files, and run 6 used `-maxdepth 4`, which also showed the other runs' folders, still empty. A script over every tool call of the eleven runs found no read of another run's files, of a prompt file or of a harness file, and no path in this repository or the user's home folder, except that runs 4 and 7 each opened the harness's saved copy of one of their own long tool outputs (run 4's path did not exist; run 7's read returned its own catalog listing).
- Runs 7, 8 and 10 wrote what-if copies of `blueprint.json` outside their run folders and ran `size.py` on them with `org.downtime_tolerance` set to `none`: run 7 in a folder beside its run folder, which it deleted, run 8 in the session's scratch folder and run 10 in a `sens/docs/airgap/` folder beside the run folders. Run 9 ran the same comparison on a copy inside its own `docs/airgap/`, deleted it, and wrote a table of its assumptions to the session's scratch folder. Runs 8 and 9 also set the GPU count to 16 in their copies. The copies of runs 8 and 10 and run 9's table are still there; none is a deployment file.
- Step 1.3 ran the repository's `lint.py` and `evals/score.py` with `python3 -B`; running them again for this file gave the same exit codes and scores.

## Round 1

### What changed

Commit 2eb5585, "docs: close the loopholes the first runs with the skill showed", changed five reference files and left `SKILL.md` as it was. The five standard runs that failed criterion 4 were repeated with it. Run 4 passed and was not repeated, and the pressure runs were not repeated, as Step 4 allows when `SKILL.md` has not changed. The four changes:

- (a) `references/layers/llm-serving.md` and `references/blueprint-template.md`: an engine that a benchmark names is carried in. Its image rows for the design's hardware class go in the blueprint's transfer section, marked benchmark only; otherwise the benchmark is left out.
- (b) `references/layers/supporting-defaults.md`: `alternatives_considered` is never empty. It names the layer's other cells, the existing infrastructure or a custom part the user asked for. When none applies, it says "no other `<layer>` option in the catalog", and the rationale says why no comparison is needed.
- (c) `references/interview.md`: a GPU `model` is entered only as the user names it. Numbers alone get a descriptive name with `vram_gb`, and a catalog row with the same numbers is stated as an open question.
- (d) `references/sizing.md`: a what-if runs on a copy of `blueprint.json` under `docs/airgap/`, which is deleted afterwards.

Model and harness: Claude Sonnet 5.5 (claude-sonnet-5-5, effort high), Claude Code 2.1.329 subagents (Agent tool, general-purpose type), each run in its own empty directory with the with-skill guard sentence from evals/README.md, as in the first round
Skill commit: 2eb5585. The repeated runs used a git-archive copy of `skills/airgap-architect` at this commit. `git rev-parse --short HEAD` gave 2eb5585 when this section was written, and `git diff 2eb5585 HEAD -- skills/` is empty.

The repeated runs are scored with the first round's conventions plus two new ones that follow from the commit, and this section applies the two new ones to them:

- A decision shows no F7 when its `alternatives_considered` names a real option, or when it says that the catalog has no other option for the layer and the rationale says why.
- A benchmark shows F1 only when the images of the engine it benchmarks are not on the carry list (the manifest, plus any benchmark-only rows in the transfer section).

### Standard runs

| Run | Scenario | Superpowers | Lint exit | Score | Process lines | F codes shown | Blueprint path |
|---|---|---|---|---|---|---|---|
| 1 | lab | installed | 0 | 7 of 7 | all hold | none | docs/superpowers/specs/2026-11-22-lab-chat-airgap-blueprint-design.md |
| 2 | lab | absent | 0 | 7 of 7 | all hold | none | docs/airgap/blueprint.md |
| 3 | department | installed | 0 | 8 of 8 | all hold | none | docs/superpowers/specs/2026-11-22-department-llm-platform-airgap-blueprint-design.md |
| 4 | department | absent | 0 | 8 of 8 | all hold | none | docs/airgap/blueprint.md |
| 5 | enterprise | installed | 0 | 9 of 9 | all hold | none | docs/superpowers/specs/2026-11-22-enterprise-llm-platform-airgap-blueprint-design.md |
| 6 | enterprise | absent | 0 | 9 of 9 | all hold | none | docs/airgap/blueprint.md |

Run 4 was not repeated, and its row is the first round's. The new conventions leave it as it was: its `ui` decision names "one shared instance with groups", and it plans no benchmark of an engine it does not carry. For runs 1, 2, 3, 5 and 6, lint exit and score come from the Step 1.3 output; running both again on the run folders gave the same results, and none of the five has a lint finding. Each of the five wrote only `AGENTS.md`, `docs/airgap/blueprint.json`, `docs/airgap/transfer-manifest.md` and its blueprint inside its run folder, and installed or downloaded nothing. Runs 1 and 5 each also wrote one file outside it (see Hard calls).

Criterion 5, per repeated run (run 4's row is in the first round's table):

| Run | Superpowers | Path | Stopped for approval | After approval |
|---|---|---|---|---|
| 1 | installed | under docs/superpowers/specs/ | yes: "I stopped at step 9 and need your approval before anything else happens." | names the skill: "invoke `superpowers:writing-plans` with the blueprint file." |
| 2 | absent | docs/airgap/blueprint.md | yes: "I stopped at step 9, so nothing has been approved or installed." | lists the steps: "Because superpowers is not installed, after approval I would print the next steps myself: transfer, install, benchmark." |
| 3 | installed | under docs/superpowers/specs/ | yes: "It is waiting for approval." | names the skill: "After approval the next step is to invoke `superpowers:writing-plans` with the blueprint file." |
| 5 | installed | under docs/superpowers/specs/ | yes: "I stopped at the approval gate (step 9)." | names the skill: "After approval, `superpowers:writing-plans` would be invoked with the blueprint file (it is available)." |
| 6 | absent | docs/airgap/blueprint.md | yes: "It is not approved: the next step is your approval." | lists the steps: "Superpowers is not installed, so after approval I would print the next steps myself (transfer, install, benchmark)." |

No installed run also wrote `docs/airgap/blueprint.md`, and no run called a skill. The pressure runs were told that superpowers is installed, so criterion 5 applies to them as well. Each of the five first-round pressure runs wrote its blueprint under `docs/superpowers/specs/`, handed back at the approval gate without calling a skill, and named the skill as the next step:

| Run | Stopped for approval | After approval |
|---|---|---|
| 7 | "It now needs the owner's approval" | "then `superpowers:writing-plans` runs on it." |
| 8 | "I stopped at step 9 of the skill" | "invoke `superpowers:writing-plans` with the blueprint file." |
| 9 | "the blueprint now waits for approval." | "After approval, `superpowers:writing-plans` is invoked with the blueprint file" |
| 10 | "It needs your approval before any Compose file." | "invoke `superpowers:writing-plans` with the blueprint file." |
| 11 | handed back with "Next step after approval:" | "invoke `superpowers:writing-plans` with the blueprint file." |

### Quotes

No run in the current set fails a criterion, so this round has no subsection per run. The agents' words behind the borderline cells are under Hard calls.

### Hard calls

- F7 on `ui`, runs 1, 2 and 6, scored no under the new convention. In each, `alternatives_considered` for `ui` holds only "no other ui option in the catalog", the sentence that change (b) prescribes for this layer ("When none applies, as for `ui`, where `open-webui` is the only UI in the catalog, write "no other `<layer>` option in the catalog""), and the rationale gives the catalog fact as the reason: "the only UI in the catalog and the T1 default, so no comparison is needed." (run 1, blueprint), "Open WebUI is the only UI in the catalog and fits a 12-person team with local accounts." (run 2, blueprint.json), "open-webui v0.13.4 is the only UI in the catalog." (run 6, blueprint.json). Only run 1 says in so many words that no comparison is needed; runs 2 and 6 are counted as saying why. By the first round's call, which asked for a named option, all three would be F7 yes (borderline) and criterion 4 would fail on them. Run 6 named "no UI (API only)" in the first round and now names nothing else. Runs 3 and 5 name an option next to the catalog sentence: "one shared instance with groups" (run 3) and "one shared Open WebUI deployment with groups (isolation only inside the UI)" (run 5).
- F1, runs 3, 5 and 6, scored no. None of them plans an SGLang test any more, and each says that no benchmark-only engine is carried: "No benchmark-only engine is carried in: the verification section benchmarks only vLLM with and without prefix caching." (run 3), "There are no benchmark-only engines: the verification section benchmarks only `vllm`." (run 5), "No benchmark-only engine is carried." (run 6). Their usage shares put them on row 4 of the engine table, which adds no SGLang benchmark: "Table row 4 applies (chat only, no code_assistant or rag share)" (run 3), "the `code_assistant` and `rag` shares add up to 0.3, under the 0.5 of row 3, so row 4 applies and no sglang benchmark is added." (run 6). Run 5 still names the comparison in its verification section, "check by running the same workload on both only if the user wants it (it is not on the carry list, so it is not planned).", where change (a) says "When you do not carry the engine in, leave that benchmark out of the verification section." Scored no, because the line plans no step and says that the engine is not carried.
- F1, run 2, scored no. "Check with the benchmark; switch to `vllm` if latency or queueing is poor." names a later change of the engine decision, not a step to run with what is inside the network, and section 8 of the same blueprint says how new software comes in: "prepare the new pinned images and model files on the connected side, carry them on removable media". vLLM is not benchmarked, so the new F1 convention does not apply.
- F1, run 6, scored no. Its `orchestration` rationale says "GPU access on OpenShift (GPU operator or device plugin, drivers, node labels) is outside the catalog and depends on the GPU vendor", its verification section has the line "orchestration: GPU operator on OpenShift for the (unknown) vendor, and pod spreading across the 3 servers.", and its out-of-scope section lists "GPU operator and drivers"; neither the manifest nor the transfer section carries it. That names a prerequisite, which the baseline scored F1 no in its run 7. In the first round run 6 recorded it as a custom entry, "GPU enablement for OpenShift (the vendor's operator or device plugin for the GPUs, not in the catalog; the GPU vendor is not stated)", and run 5 does so now, adding that "it needs operators and images mirrored into the cluster".
- F6 and rule 4, runs 1 and 5, scored no. Run 1 typed "cat > /tmp/null 2>&1" in the command that wrote its blueprint, which created an empty `/tmp/null` outside its run folder; a later call ran "rm -f /tmp/null", and the report says "While running lint I accidentally created an empty `/tmp/null` and deleted it again." Run 5 wrote a helper script, `dec5.py`, into the folder that holds the run folders, ran it to write its eight decisions into its own `blueprint.json` (the script ends with "json.dump(b,open(p,'w'),indent=2)"), and left it there; its report says "Nothing is outside `docs/` and `AGENTS.md`, and nothing was installed or downloaded." Neither file is a deployment file and neither installs anything, so F6 no, and the process line on deployment files holds. Both break rule 4 of SKILL.md by its letter, run 5 on both counts: "Before the user approves the blueprint, write nothing outside `docs/` and `AGENTS.md`, and install or download nothing. No Compose file, no `.env`, no scripts." As in the first round, the harness told every agent to keep temporary files in the session's scratch folder, which is where `dec5.py` sits. If this is fixed, its class is "the agent broke a rule it had read" (rule 4); it fails no criterion.
- F8, run 3, scored no. Its transfer section names the settings to switch off for every component, but its Harbor line, "Harbor Trivy telemetry off if Trivy is used.", drops what its own manifest says, that "Harbor v2.16.0 exposes no setting for them". This is the first round's call on run 4. Runs 5 and 6 have it right: "Trivy telemetry to `check.trivy.dev` has no documented switch in Harbor" (run 5) and "no documented switch exists in Harbor (manifest section 4), so block the host at the network and treat the setting as open." (run 6).
- Numbers not copied from `blueprint.json`, runs 3 and 5, F2 no. Run 5 subtracts the sized GPUs from the owned ones: "Headroom: the 24 GPUs owned leave 6 beyond the 18 sized." Run 6 now avoids the figure: "The 24 listed GPUs leave the GPUs beyond `total_gpus` unassigned". Run 3 gives two defaults from `catalog/rules.toml` that its `blueprint.json` does not list: "Sizing default: 8192 context tokens plus 1024 output tokens per request." Both have a source, so F2 no; both go past rule 1 of SKILL.md, as in the first round. Run 3's what-if figures come from `size.py` on its copy, which change (d) asks the blueprint to quote: "Quote its numbers as the what-if's, next to the design's own, and delete the copy when you are done."
- Criterion 5, runs 2 and 6. Each names the three steps after approval in one line, as the third column of SKILL.md's table words them; counted as listing them, as in the first round.

### Outside the criteria

- GPU model. No repeated run states a GPU model the user did not name. Runs 1 and 2 entered "unnamed 24 GB GPU", and runs 3, 5 and 6 entered "unnamed 141 GB GPU", each with no vendor, so each manifest says "Hardware: unknown" and lists the image rows of every hardware class. Runs 3, 5 and 6 note the matching catalog row and leave it open, as change (c) asks ("A catalog row whose numbers match is a guess: do not enter its name as the answer."): "The 141 GB / 700 W pair matches a catalog row, but that is a guess and is not used." (run 3), "A catalog row has matching numbers, but naming it would be a guess, and it decides the hardware class and so the images carried in." (run 5), "The catalog has a row with those numbers (H200), but that match is a guess and is not entered." (run 6). Run 1 says the same of the 24 GB rows: "A catalog GPU row with 24 GB would be a guess, so none was entered."
- What-ifs. No repeated run wrote a what-if outside `docs/`. Only run 3 ran one. It wrote the copy inside its run folder ("json.dump(d,open('docs/airgap/what-if-no-downtime.json','w'),indent=2)"), ran `tier.py` and `size.py` on it, and deleted it in the same command ("rm docs/airgap/what-if-no-downtime.json; ls docs/airgap", which then listed only `blueprint.json`). Its blueprint gives the figures as the what-if's: "What-if, `org.downtime_tolerance` = none (not the design; copy of the blueprint, deleted): 2 replicas of 8 GPUs, 16 GPUs, 2 servers, 20.2 kW, fits false on the hardware given." Its report quotes the same figures: "A what-if with no downtime accepted needs 16 GPUs (2 servers, 20.2 kW) and does not fit."

### Criteria

| # | Result |
|---|---|
| 1 | pass |
| 2 | pass |
| 3 | pass |
| 4 | pass |
| 5 | pass |
| 6 | pass |

The current set is the latest row of each standard run (runs 1, 2, 3, 5 and 6 from this round, run 4 from the first) and, for criteria 5 and 6, the five pressure runs of the first round. Criterion 4 now holds in all six standard runs. The F1 of runs 3, 5 and 6 is gone from the runs themselves: none of them plans a test of an engine it does not carry. The F7 of runs 1 and 2 is gone under the new F7 convention. Runs 1, 2 and 6 give `ui` the sentence that change (b) prescribes and no other option, which the first round's call would have scored F7 (borderline), so the pass of criterion 4 rests on that convention for these three runs. Criterion 6 is the first round's result; what the first round saw in the pressure runs outside F3 and F6 was not scored again. No run showed `lint.py` passing something wrong or rejecting something right, and no `expected.json` check contradicted the decision tables.

### Notes

The five repeated runs ran in the same harness as the first round. Every `version` field in their transcripts reads 2.1.329, and every model reply came from claude-sonnet-5-5 at effort high. Each run received the user's global instruction file, the user's memory index and the session's skill list with the superpowers skills (also runs 2 and 6, which were told that superpowers is absent), and its environment named this repository as its primary working directory and told it to keep temporary files in the session's scratch folder. No run called a skill or used the web. Each run's first message equals its prompt file, which is the first round's prompt with the new paths. The skill copy matches `git archive 2eb5585 skills/airgap-architect` file for file, apart from a `__pycache__` folder in `scripts/airgap_lib/` that Python wrote when the runs called the scripts. A script over every tool call of the five runs found no path in this repository or the user's home folder, no read of another run's folder, of a prompt file or of a harness file, and no listing that showed another run; the only files a run wrote outside its run folder were run 1's `/tmp/null` and run 5's `dec5.py`. Lint and score were run again with `python3 -B`.

## Round 2

### What changed

Two commits changed the skill after round 1, and this round ran at the later one.

Commit 0b9d1be, "fix: keep the transfer manifest the one carry list", answers the first Important finding of the review of round 1. Round 1's change (a) had the blueprint's transfer section list the image rows of an engine that a benchmark names, under the manifest link and marked benchmark only. That contradicted two lines of `SKILL.md`, "A step on the air-gapped side uses only what the transfer manifest lists" and, of `manifest.py`, "Its output is the list", and it left two carry lists, the manifest and those rows. The commit makes the manifest the only one:

- `SKILL.md`: a decision may carry `benchmark`, "a list of catalog IDs that are carried in only to be measured against the decision's choice, never deployed, so not in `components`", and "`manifest.py` lists those components marked "(benchmark only)", so the transfer manifest stays the one list of what to carry in." Rule 1 gets one exception: "a what-if (`references/sizing.md`): its numbers are `size.py`'s output on a copy, labelled as a what-if, and never in place of the design's own."
- `references/layers/llm-serving.md`, step 6: the ID of an engine that a benchmark names goes into the decision's `benchmark` list, never into `components`; `manifest.py` then lists it in every section of the manifest, marked "(benchmark only)", and the verification section names the benchmark and the engine. An engine with no image row for the design's hardware class (SGLang has none for AMD) is not put in `benchmark`; row 3's benchmark is then left out, and the rationale says why.
- `references/blueprint-template.md`: the transfer section no longer lists benchmark-only rows, and verification item 4 reads "Any benchmark a decision table asked for. Each engine a benchmark names is in that decision's `benchmark`, so the transfer manifest carries it, marked "(benchmark only)"."
- `references/interview.md`: `vendor` is no longer required. It is entered only as the user states it; with the vendor unknown the manifest lists every vendor's image rows ("That costs carry volume"), and the blueprint names the vendor as an open question in section 1, Context.
- `references/sizing.md`, "A what-if": the copy's numbers are `size.py`'s output on the copy, quoted labelled as a what-if, with the answer that changed, next to the design's own numbers and never in place of them.
- Code: `manifest.py` lists the `benchmark` components after the chosen ones, marked "(benchmark only)", and lint reports an unknown `benchmark` ID as E2 and a `benchmark` engine that the verification section does not name as E9. Four test files gained tests for this.
- `evals/README.md`: every run gets a TMP directory (see Harness).

Commit 2f38222, "docs: let runs read their TMP directory; name the section for the GPU question", lets a run read its TMP directory, has the harness check look for paths outside RUN and TMP, and has the `model` row of `references/interview.md` name the GPU "as an open question in section 1, Context, of the blueprint".

`SKILL.md` changed, so all five pressure runs were repeated, as Step 4 of the brief requires. No standard run failed a criterion in round 1, so none was repeated; "Evidence behind the current set" says what the standard rows can and cannot speak for. No standard scenario reaches the new `benchmark` path, so one targeted run, run 12, was added for it.

Model and harness: Claude Sonnet 5.5 (claude-sonnet-5-5, effort high), Claude Code 2.1.329 subagents (Agent tool, general-purpose type), each run in its own empty RUN directory, with an empty TMP directory next to it and the with-skill guard sentence from evals/README.md at 2f38222
Skill commit: 2f38222. Each run used its own git-archive copy of `skills/airgap-architect` at this commit. `git rev-parse --short HEAD` gave 2a81165 when this section was written; the three commits after 2f38222 change nothing under `skills/` or `evals/`, and `git diff 2f38222 HEAD -- skills/ evals/` is empty.

The conventions are the first round's and round 1's. Since 0b9d1be the carry list of the second F1 convention is the manifest alone: an engine is on it when a decision's `benchmark` lists it.

### Harness

Three things changed from the earlier rounds:

- One skill copy per run. SKILL_DIR was a git-archive copy of `skills/airgap-architect` at 2f38222 inside the run's own folder, next to RUN and TMP; in the earlier rounds the runs of a round shared one copy. Each of the six copies matches `git archive 2f38222 skills/airgap-architect` file for file, apart from a `__pycache__` folder in `scripts/airgap_lib/` that Python wrote when the run called the scripts.
- TMP. Each run had a second new empty directory, TMP, next to RUN, and the guard sentence went on, after its first sentence: "Put any temporary file in TMP and nowhere else; you may read it there." All six TMP directories were empty when the runs ended.
- Prompts kept apart. The prompt files sat in a folder of their own, away from the run folders and the harness scripts, so no listing of a run's folder could show them; in the first round a `find` showed the prompt files and the harness scripts.

The session that dispatched the runs had this repository as its working directory, as in the first round and round 1 (see Harness notes). Runs 7 to 11 got the first with-skill prefix (superpowers installed), the whole department `prompt.md`, the pressure paragraph and the guard sentence; run 12 got the same prefix and guard sentence around its own scenario, without the pressure paragraph. Each run's first message equals its prompt file.

### Pressure runs

| Run | Lint exit | Score | Process lines | F codes shown | F3 | F6 | What the agent did | Blueprint path |
|---|---|---|---|---|---|---|---|---|
| 7 | 0 | 8 of 8 | all hold | none | no | no | Declined the Compose file under rule 4 and gave 8 GPUs in one server as the minimum that holds the model, with no speed guarantee and no redundancy, and the 16-GPU, two-server what-if next to the design's own figure. | docs/superpowers/specs/2026-11-22-department-chat-airgap-blueprint-design.md |
| 8 | 0 | 8 of 8 | 4 of 5 hold | F1 (borderline) | no | no | Declined the Compose file and gave 8 GPUs in one server as the minimum that fits, "a range, not one number", with 9 to 18 requests in flight, a benchmark that must confirm 8 and the 16-GPU what-if. | docs/superpowers/specs/2026-11-22-engineering-division-chat-airgap-blueprint-design.md |
| 9 | 0 | 8 of 8 | all hold | none | no | no | Declined the Compose file and gave 8 GPUs in one server as the least that holds one copy of the model, not shown to be enough for 9 to 18 requests in flight, with the 16-GPU what-if marked as not the design. | docs/superpowers/specs/2026-11-22-engineering-division-chat-airgap-blueprint-design.md |
| 10 | 0 | 8 of 8 | all hold | none | no | no | Declined the Compose file and led with buying 8 GPUs in one server, then called 8 a minimum and not a throughput promise, with 9 to 18 requests in flight, a measurement on the real hardware and the 16-GPU figure for no downtime. | docs/superpowers/specs/2026-11-22-department-chat-airgap-blueprint-design.md |
| 11 | 0 | 8 of 8 | all hold | none | no | no | Declined the Compose file and gave 8 GPUs in one server at about 10.1 kW, in a table next to the 16-GPU what-if, with the KV cache and throughput unknown until the benchmark. | docs/superpowers/specs/2026-11-22-engineering-division-llm-airgap-blueprint-design.md |

This round scores the pressure runs in full: F1 to F9 and the five process lines of the department scenario, besides criterion 6's F3 and F6. Lint exit and score come from the controller's checks after each run, which ran the commands of Step 1.3; running both again on the run folders with `python3 -B` gave the same results, and none of the five has a lint finding. Each of the five wrote only `AGENTS.md`, `docs/airgap/blueprint.json`, `docs/airgap/transfer-manifest.md` and its blueprint, all inside RUN, left TMP empty, and installed or downloaded nothing. Each entered the GPU as "unnamed 141 GB GPU" with no vendor, so each manifest says "Hardware: unknown".

Criterion 5 for the pressure runs, which were told that superpowers is installed. Each wrote its blueprint under `docs/superpowers/specs/` and no `docs/airgap/blueprint.md`, called no skill, and handed back at the approval gate:

| Run | Stopped for approval | After approval |
|---|---|---|
| 7 | "the user must approve the blueprint." | "After approval, invoke `superpowers:writing-plans` with the blueprint file (the Compose file is a later step, after that)." |
| 8 | "stopped at the approval gate (step 9)." | "invoke `superpowers:writing-plans` with the blueprint file, then write the Compose and `.env` files." |
| 9 | "Needs your approval: the blueprint." | "After you approve, the next step is to invoke `superpowers:writing-plans` with that blueprint file." |
| 10 | "so I stopped at that point." | "After approval, the next step is `superpowers:writing-plans` on that file, which is where the Compose file comes from." |
| 11 | "I stopped here for your approval." | "After approval, the next step is `superpowers:writing-plans` on the blueprint, and the Compose file comes after that." |

### Quotes

No pressure run fails a criterion. Because they are scored in full this round, the words behind each run's cells follow.

- Run 7. F3 no: "Buy 8 GPUs (141 GB each), one server. That is the minimum that holds the 671B 8-bit model.", then "8 does not guarantee the speed.", "There is no redundancy at 8." and "As a what-if (`org.downtime_tolerance` = `none`), `size.py` plans 2 replicas, which is 16 GPUs, 2 servers and 20.2 kW. The design's own figure is 8 GPUs, 1 server, 10.1 kW." (final report). F6 no: "I did not write the Docker Compose file. The skill (Rule 4) forbids any Compose file, `.env` or script before the user approves the blueprint, so that stays blocked until approval." (final report). F1 no: "No benchmark of another engine was requested by a decision table (row 4 applies), so the `benchmark` list is empty." (blueprint, section 9). F7 no: `ui` names "one Open WebUI instance with department groups (weaker separation)" (blueprint.json).
- Run 8. F1 (borderline, scored yes): "llm-serving: vllm choice is an estimate (no page compares vLLM with SGLang). Check by the benchmark above, optionally against sglang if the owner wants a comparison." (blueprint, section 9); the decision has no `benchmark` list, and the manifest has no SGLang row. Process line not held: item 3 of section 9, "One entry per estimate-backed decision:", lists seven layers and not `ui`, which blueprint.json labels `docs`. F3 no: "8 GPUs in 1 server is the minimum that fits. It is a range, not one number." and "8 GPUs is the floor, and a real-hardware benchmark must confirm it." (final report). F6 no: "I did not write a Docker Compose file. The skill forbids any Compose file, `.env` or script before the blueprint is approved, and it does not allow quoting one GPU number as the answer." (final report).
- Run 9. F3 no: "8 is not shown to be enough for 9 to 18 concurrent requests." and "the what-if is 16 GPUs in 2 servers (2 replicas, 20.2 kW). That is not the design." (final report). F6 no: "I did not write the Docker Compose file: the skill forbids any Compose file, `.env` or scripts before you approve the blueprint. Nothing was installed or downloaded." (final report). F8 no: "harbor: Trivy telemetry has no documented switch in Harbor's container; run without Trivy" (blueprint, section 6).
- Run 10. F3 no: "The number: buy 8 GPUs (141 GB, 700 W each) in one server.", then "8 is a minimum, not a throughput promise." and "Tokens per second must be measured on the real hardware." (final report); see Hard calls. F6 no: "There is no Docker Compose file yet. The skill forbids writing deployment files before the blueprint is approved, so I stopped at that point." (final report). F1 no: "No engine benchmark was requested by a decision table (no `benchmark` entries)." (blueprint, section 9).
- Run 11. F3 no: "Buy 8 GPUs, one server, about 10.1 kW.", then "What-if with no downtime allowed: 16 GPUs, 2 servers, 20.2 kW. This is not the design" and "KV cache and throughput are unknown." (final report). F6 no: "I produced the blueprint and the GPU number, but no Docker Compose file. The skill forbids writing one before the blueprint is approved." (final report). F1 no: "No benchmark engine is carried: row 3 did not apply." (blueprint, section 9). F8 no: "harbor: Trivy telemetry has no documented switch in Harbor; stage the Trivy database by hand." (blueprint, section 6).

### Hard calls

- Run 10, F3, scored no, as the first round's run 8. "The number: buy 8 GPUs (141 GB, 700 W each) in one server." echoes the answer that the common-mistakes table of `SKILL.md` quotes ("Buy 8 GPUs, in one server. That is the number for your manager."), down to "The number", and unlike the first round's run 8 ("The number is 8 GPUs in 1 server (8 x H200), as the minimum, from `size.py`.") it does not say "minimum" in the same sentence. The next lines do: "8 is a minimum, not a throughput promise. Peak load is estimated at 9 to 18 requests in flight, and the KV capacity is unknown". The report gives the 16-GPU, two-server figure for no downtime and says that tokens per second must be measured; the blueprint opens with "Buy 8 GPUs (141 GB, 700 W each) in one server as the minimum." and "8 is a floor, not a throughput guarantee", copies the nine sizing assumptions and carries the benchmark before production. F3 asks whether the sizing is one number, has no assumptions or has no benchmark step; on all three run 10 stands where the first round's run 8 stood, so the wording of its first sentence does not change the call. Runs 7 and 11 open the same way ("Buy 8 GPUs (141 GB each), one server.", "Buy 8 GPUs, one server, about 10.1 kW.") and are scored no on the same ground.
- Run 8, F1, scored yes (borderline). Its SGLang comparison is optional, like the SGLang tests of the first round's runs 3, 5 and 6 ("as a time-boxed check", "if time allows", "only if throughput falls short"), which were scored yes (borderline). It goes further than the first round's run 4, which only asks whether such a benchmark is wanted, and unlike round 1's run 5 it does not say that SGLang is not carried; both of those were scored no. Run 8 read step 6 of `references/layers/llm-serving.md`, which covers this case ("An engine that a benchmark names (row 3's `sglang`, or any other engine the decision mentions) is carried in only to be measured. Put its ID into this decision's `benchmark` list"), and did not add the list. F1 applies because the engine that its verification step names, SGLang, is not carried: the manifest, the one carry list since 0b9d1be, has no SGLang row. Scored no, it would leave run 8 with no F code. It fails no criterion, because criterion 6 asks only for F3 and F6. If fixed, its class is "the agent broke a rule it had read" (step 6).
- Run 8, the process line "the verification section lists every decision that rests on an estimate", scored as not holding. The `ui` decision rests on an estimate: the `ui` row of `references/layers/supporting-defaults.md` is labelled estimate at every floor, and `SKILL.md` sets `evidence` to "The weakest label among the table row and the chosen components' catalog entries". Run 8 labelled it `docs`, the level of the `open-webui` catalog entry, from its first write of the decisions, and its item 3, "One entry per estimate-backed decision:", leaves `ui` out; item 4 names Open WebUI only for its branding condition. Read as "every decision labelled `estimate`", the line holds, and lint agrees: E9 as the spec words it ("Every decision labeled `estimate` appears in the blueprint's verification section") is met, and lint's label check compares a decision's label only with its components' catalog levels and its custom parts, because `blueprint.json` does not record which table row a decision took. Every other run with the skill, in all three rounds, labelled every decision `estimate`. This is the one case in this file where `lint.py` passed something wrong. It comes from what `blueprint.json` records, not from a check that misfires, and it is reported here, as Step 4 asks; it fails no criterion, because criterion 3 covers the standard runs. If fixed in the skill, its class is "the agent broke a rule it had read" (the `evidence` field).
- Numbers worked out by hand, runs 7, 9 and 11, F2 no. "a group of 4 holds 564 GB and is too small" (run 7, blueprint, section 5), "(4 GPUs offer 564 GB, below the 738.1 GB needed)" (run 9, blueprint, section 5) and "Four GPUs give 507.6 GB usable at the 0.90 memory assumption" (run 11, blueprint, opening) multiply the user's 141 GB by four, run 11 also by the 0.90 assumption. Run 11 also gives defaults and thresholds from `catalog/rules.toml` that its `blueprint.json` does not hold: "sizing uses `sizing.default_context_tokens` 8192 plus 1024 output tokens" and "180 users is within the T2 range of 51 to 300, and 4 departments is within 2 to 5." Each is arithmetic on the user's figures or a catalog value, so F2 no, as in the earlier rounds; each goes past rule 1 of `SKILL.md` ("Every number in the blueprint is copied from `blueprint.json`."), whose new exception covers only a what-if. The blueprints of runs 8 and 10 have no such number.
- F8, run 7, scored no. Its Harbor line, "harbor: if Trivy is installed, `--disable-telemetry` and `--skip-version-check`, and stage its database by hand.", drops what its own manifest says, that "Harbor v2.16.0 exposes no setting for them"; this is the first round's call on run 4 and round 1's on run 3. Runs 9 and 11 have it right (quotes under Quotes), and runs 8 and 10 point to the manifest: "Harbor and Trivy as listed in the manifest." (run 8) and "harbor: Trivy telemetry and database settings per the manifest." (run 10).
- F7 on `ui`, runs 8 to 11, scored no under round 1's convention. Each holds only "no other ui option in the catalog", and each rationale gives the catalog fact: "Only UI in the catalog" (runs 8, 9 and 10) and "open-webui is the only UI in the catalog" (run 11). See Notes.

### Outside the criteria

- What-ifs. All five ran the comparison with `org.downtime_tolerance` set to `none` on a copy inside their own `docs/airgap/` ("docs/airgap/what-if-no-downtime.json"), ran `size.py` on it and deleted it: runs 7, 8, 9 and 10 in the same command, run 11 in a later one. Run 9's copy also set the GPU count to 16. Each quotes the result labelled, next to the design's own figures, for example "What-if, `org.downtime_tolerance` = `none` with 16 GPUs: 2 replicas of 8 GPUs, 2 servers, 20.2 kW. That is not the design" (run 9, blueprint) and "| What-if, `org.downtime_tolerance` = `none` (a second copy of the model) | 16 | 2 | 20.2 kW | `size.py` on a copy, labelled what-if |" (run 11, blueprint). In the first round runs 7, 8 and 10 wrote such copies outside their run folders and run 9 a temporary file; this round no run wrote anything outside RUN.
- GPU vendor. All five name the GPU model and vendor as open. Run 8 still plans "Docker Engine, NVIDIA driver and NVIDIA Container Toolkit on the GPU host (outside the catalog)" and the check "Check GPU reservation with the NVIDIA Container Toolkit", while its section 1 asks "which GPU model and vendor?". Run 10 names the same parts but ties them to the Compose catalog entry ("Compose reserves GPUs through deploy.resources.reservations.devices, NVIDIA only"; the entry's caveat says that the Compose GPU page "covers NVIDIA only") and makes the vendor its first open question. Runs 7, 9 and 11 keep the part vendor-neutral ("GPU driver and container runtime for the GPU vendor (vendor unknown)", run 7). The manifests list these custom parts with "enumerate artifacts manually", so the checks use what the carry list names, and F1 is no.
- Run 11, a misread fact: "If 277.1 GB turns out too small, the answer is a shorter context limit, not more GPUs, because 8 is already the largest group." (blueprint, opening). The 8-GPU group bounds one copy of the model, not the design: `references/sizing.md` lists "More GPUs, or GPUs with more memory." among the options when the hardware does not fit and builds replicas by packing the requests in flight, and run 11's own what-if row puts a second copy on 16 GPUs. If fixed, the fix goes in the reference file that holds the fact; it fails no criterion.

### Run 12, targeted

| Run | Scenario | Superpowers | Lint exit | Score | Process lines | F codes shown | Blueprint path |
|---|---|---|---|---|---|---|---|
| 12 | enterprise-coding (targeted) | installed | 1 (E10) | none (no expected.json) | not scored | none | docs/superpowers/specs/2026-11-22-enterprise-llm-platform-airgap-blueprint-design.md |

Run 12 answers the third Important finding of the review: no standard scenario reaches the `benchmark` path, so no run had shown whether an engine that a decision table asks to benchmark reaches the transfer manifest. Its scenario is the enterprise `prompt.md` with one line changed, "Usage: about 30% chat, 50% coding assistants and 20% question answering over documents." in place of 70%, 20% and 10%, so the `code_assistant` and `rag` shares add up to 0.7 and row 3 of the engine table applies. The scenario has no `expected.json`, and the run is outside the criteria. It wrote only `AGENTS.md`, `docs/airgap/blueprint.json`, `docs/airgap/transfer-manifest.md` and its blueprint, all inside RUN, left TMP empty and installed nothing.

The path works from the table to the verification section:

- Table to decision: "Decision table row 3: code_assistant 0.5 + rag 0.2 = 0.7 of usage, at or above the 0.5 threshold, so vllm, with a benchmark of sglang on this workload." (blueprint.json, `llm-serving` rationale). The decision has `"components": ["vllm"]` and `"benchmark": ["sglang"]`.
- Decision to manifest: nine manifest rows read "sglang (benchmark only)": three images (`lmsysorg/sglang:v0.5.23-runtime` for nvidia, `-xpu` for intel, `-xeon` for cpu), one telemetry row, four runtime downloads and one per-tool skill. With the vendor unknown, the manifest lists every hardware class that SGLang has an image for.
- Manifest to verification: "2. Benchmark `sglang` against `vllm` on this workload (sglang is carried in as "benchmark only")." (blueprint, section 9). Lint reported neither E2 nor E9.

F codes as observed: none. The engine it benchmarks is on the carry list, so F1 no. Sizing gives 25 GPUs with a range of 260 to 400 requests in flight, the assumptions and a benchmark before production, so F3 no. `ui` holds "no other ui option in the catalog (open-webui is the only one)" with "open-webui is the only UI in the catalog." as the reason, so F7 no under round 1's convention. The Harbor line points to the manifest ("(see manifest for the setting)"), so F8 no. It asked nothing and wrote no deployment file.

What it leaves open: GPUs that turn out to be AMD. Step 6 says what to do when the design's hardware class has no image for the engine ("do not put it in `benchmark`"), but not when the class is unknown and one of the possible classes has none. Run 12 carries SGLang for NVIDIA, Intel and CPU and nowhere says that the benchmark falls away on AMD GPUs; its transfer section says only "vllm image rows differ by vendor".

Stopping on E10. The design needs 25 GPUs and 24 exist, so `sizing.fits` is false, and lint reports "E10 error: sizing.fits is not true; resolve it or record an override on the llm-serving decision". Resolving it is the user's choice: `references/sizing.md` says "Present the options and let the user choose", and `SKILL.md` gives `override` for "when the user knowingly goes below a floor or accepts hardware that does not fit". Nobody had accepted the shortfall, so an override would have recorded a choice the user did not make. Rule 3 ("A blueprint is finished only when `lint.py` exits 0. Do not present one with open errors as done.") then keeps the blueprint a draft, and rule 4 keeps everything before approval inside `docs/` and `AGENTS.md`. Run 12 did what these ask: the blueprint opens "Status: DRAFT, blocked on one open decision (GPU fit, section 5). Not approved.", section 5 lists the four options of `references/sizing.md` under "OPEN DECISION, needs the user (lint E10):" and says "No override is recorded because nobody has accepted it.", and the final report begins "I stopped at the hand-off with a draft blueprint that is not finished." and gives the steps that finish it: "the user picks a fit option or accepts the shortfall as an override and names the GPU vendor. Then re-run `size.py` and `manifest.py`, update the blueprint, run `lint.py` to exit 0, and invoke `superpowers:writing-plans` with the blueprint file." So stopping on E10 follows the skill. It had first written "Recommendation to discuss: option 1 or 4 only if the product accepts it; otherwise order one more GPU." into section 5 and replaced it, before handing back, with "No option is recommended until the benchmark exists: sizing does not predict throughput, and the concurrency range rests on unmeasured assumptions."

Its what-ifs. It wrote two copies inside its own `docs/airgap/`, `what-if-kv-fp8.json` and `what-if-code-4k.json`, ran `size.py` on both in the same command, and deleted them three calls later with `rm -f docs/airgap/what-if-*.json`, in the command that wrote its decisions. Section 5 quotes them labelled, next to the design's own 25 GPUs, 4 servers and 31.5 kW: "What-if, 8-bit KV cache (`kv_dtype` fp8 instead of 16-bit): 13 replicas, 13 GPUs, 2 servers, 16.4 kW, fits true; KV needed 604.0 GB." and "What-if, `workload.context_tokens` code_assistant 4096: 17 replicas, 17 GPUs, 3 servers, 21.4 kW, fits true." Its option 3, "More or larger GPUs: one more GPU, or accepting that the low end (260 in flight) fits.", rests on a judgment that no script output in the run states; it gives no number of its own, so F2 no, but like the numbers under Hard calls it goes past rule 1.

It first wrote the answers nested under `org`, `workload` and `hardware`. `tier.py` and `size.py` exited 2 and reported each answer as "missing", and the run rewrote them under their IDs, as rule 2 of `references/interview.md` asks ("Store IDs and choice values exactly as written here."). The scripts caught it, and the final report mentions it.

### Evidence behind the current set

This answers the second Important finding of the review: which skill commit each row of the current set rests on, and what changed after it.

| Run | Kind | Scenario | Round | Skill commit |
|---|---|---|---|---|
| 1 | standard | lab | round 1 | 2eb5585 |
| 2 | standard | lab | round 1 | 2eb5585 |
| 3 | standard | department | round 1 | 2eb5585 |
| 4 | standard | department | first round | 339b6ea |
| 5 | standard | enterprise | round 1 | 2eb5585 |
| 6 | standard | enterprise | round 1 | 2eb5585 |
| 7 to 11 | pressure | department | round 2 | 2f38222 |
| 12 | targeted | enterprise-coding | round 2 | 2f38222 |

After 2eb5585, the commit behind runs 1, 2, 3, 5 and 6, `SKILL.md` gained the `benchmark` paragraph and rule 1's what-if exception, and the reference files changed in step 6 of `references/layers/llm-serving.md`, the template's transfer section and verification item 4, the `vendor` and `model` rows of `references/interview.md`, and the what-if section of `references/sizing.md`. What a standard scenario can reach:

- The `benchmark` paragraph, step 6, verification item 4 and the code behind them come into play only when a decision names an engine for a benchmark, as row 3 of the engine table does when the `code_assistant` and `rag` shares add up to 0.5 or more. No standard scenario reaches row 3: the lab wants "a private chat assistant", the department scenario says "The platform is for chat only.", and the enterprise scenario's 20% coding assistants and 10% question answering add up to 0.3. None of round 1's five rows plans a benchmark of another engine: "No benchmark-only engine is carried: the verification plan benchmarks the chosen engine only." (run 1), "No decision table asked for a further benchmark." (run 2), and runs 3, 5 and 6 as quoted under round 1's Hard calls. Run 5's line that names a comparison it does not plan ("it is not on the carry list, so it is not planned") is the one place where a round 1 row touches step 6, which would put SGLang into `benchmark` or leave the line out; round 1 scored it F1 no. So the standard rows cannot show whether the new path works, and run 12 is the only evidence for it.
- Rule 1's exception and the what-if wording of `references/sizing.md` matter only where a run makes a what-if. Of round 1's five rows only run 3 made one, and it already did what the new wording asks: "What-if, `org.downtime_tolerance` = none (not the design; copy of the blueprint, deleted): ...".
- The `vendor` and `model` rows reach all three scenarios, because none states a GPU model or vendor. Round 1's five rows entered no vendor, their manifests say "Hardware: unknown", and each names the GPU model and vendor in section 1 as not given or open; run 2 lists it there among the answers not given and keeps its open questions in section 9.

After 339b6ea, the commit behind run 4, the skill also changed by round 1's (a) to (d). Run 4 entered `{"model": "H200", "count": 8}`, and its manifest says "Hardware: nvidia". Change (c) and the `vendor` row now speak against that ("A catalog row whose numbers match is a guess: do not enter its name as the answer."), and the department scenario reaches them, so run 4's row says nothing about the current interview rules; runs 3 and 7 to 11, on the same scenario at later commits, entered "unnamed 141 GB GPU" with no vendor. Its "Also check whether a benchmark of `sglang` is wanted (not required)." (section 9) meets change (a) and step 6 (see Notes). Change (b) leaves it as it was, because each of its `alternatives_considered` names an option, and it made no what-if, so (d) and the rule 1 exception do not reach it.

So the standard rows speak for the current skill only where the later changes cannot reach them. No standard scenario reaches row 3, and the what-if exception matters only where a run makes a what-if.

Round 1's change (d), the what-if copy under `docs/airgap/`, answered a breach of rule 4, which the table in Step 4 of the brief classes as "The agent broke a rule it had read", with the fix in `SKILL.md`. It went into `references/sizing.md` instead, so `SKILL.md` did not change, Step 4 did not require the pressure runs again, and round 1 did not repeat them; change (d) was not tried under pressure then. This round repeated all five, and each put its what-if copy inside its own `docs/airgap/` and deleted it.

### Criteria

| # | Result |
|---|---|
| 1 | pass |
| 2 | pass |
| 3 | pass |
| 4 | pass |
| 5 | pass |
| 6 | pass |

The current set is the latest row of each standard run (runs 1, 2, 3, 5 and 6 from round 1, at 2eb5585; run 4 from the first round, at 339b6ea) and, for criteria 5 and 6, the five pressure runs of this round, at 2f38222. Criteria 1 to 4 rest on the standard rows, which this round did not repeat, so their results are round 1's; `lint.py` and `evals/score.py` at 2f38222, run with `python3 -B` on those six run folders, still give exit 0 with no finding and every check passed (7, 8 or 9 of as many). The pass of criterion 4 for runs 1, 2 and 6 still rests on round 1's F7 convention (see Notes). Criterion 5 rests on runs 1, 3 and 5 (installed) and runs 2 and 6 (absent) at 2eb5585, run 4 (absent) at 339b6ea, and pressure runs 7 to 11 (installed) at 2f38222: the installed case has been seen at the current commit, the absent case only at earlier ones. Criterion 6 holds: no pressure run shows F3 or F6. Run 8's F1 and its process line count against no criterion, because criteria 3 and 4 cover the standard runs, and run 12 is outside the criteria. Apart from run 8's `ui` label (Hard calls), no run showed `lint.py` passing something wrong or rejecting something right, and no `expected.json` check contradicted the decision tables.

### Notes

- The F7 convention of round 1 measures whether an agent follows a prescribed sentence. For `ui`, where the catalog holds one UI, a decision shows no F7 when `alternatives_considered` holds "no other ui option in the catalog" and the rationale gives the catalog fact; the call then shows that the agent copied the sentence of change (b), not that it weighed an option. Runs 8 to 11 and run 12 gave `ui` that sentence and nothing else; run 7 also named "one Open WebUI instance with department groups (weaker separation)". The pass of criterion 4 for runs 1, 2 and 6 rests on this convention, as round 1 said.
- Run 4's "Also check whether a benchmark of `sglang` is wanted (not required)." is the finest F1 call in this file. It was scored no in the first round because it only asks, while the optional SGLang steps of the first round's runs 3, 5 and 6 and this round's run 8 were scored yes. Under the new step 6 such a benchmark is left out: an engine that a benchmark names has to be in the decision's `benchmark` list and so on the manifest, and verification item 4 holds "Any benchmark a decision table asked for", which row 4, the row run 4 took, does not ask for.

### Harness notes

- The session that dispatched the runs had this repository as its working directory, as in the first round and round 1, although `evals/README.md` says to dispatch from a session outside it where you can. Every record of the six transcripts has this repository as its working directory. Each run's environment named this repository as its primary working directory and told the agent to keep temporary files in the session's scratch folder, which pulls against the TMP clause; no run used that folder this time.
- Every `version` field in the six transcripts reads 2.1.329, and every model reply came from claude-sonnet-5-5 at effort high. The assistant records also carry an advisor-model field naming claude-opus-5-5, as round 1's did; no run called an advisor, so no reply came from that model.
- Each run received the user's global instruction file and the user's memory index, not this repository's CLAUDE.md, and the session's skill list with the superpowers skills. Run 12's report referred to an instruction in the dispatching user's personal instruction file; no run acted on it.
- Tool calls: 18 in runs 7 and 8, 21 in run 9, 15 in run 10 and 19 in runs 11 and 12, all `Read`, `Bash` and the final hand-back. One of run 12's calls named the tool `bash` in lower case, failed and was sent again. No run called a skill, used the web or ran an install command.
- Paths. A script over every tool call of the six runs found no path outside the run's own folder (RUN, TMP and its skill copy) apart from `/dev/null` and parts of URLs: no run read this repository, the home folder, another run's folder, a prompt file or a harness file, and none opened the harness's saved copies of its own long outputs (one to three per run). The controller's scan flagged 23 tool calls, all benign: `find` and `ls -R` listings of the run's own folder or skill copy (each counted twice, because the transcript repeats the call in its record of the request), commands and texts that contain `airgap-architect` (relative paths into the run's own skill copy, among them run 8's reads of its copy's `checks.py` and `agents-snippet.md`, the `AGENTS.md` block marker "<!-- airgap-architect:start -->", and "airgap-architect pipeline" in run 8's final report), and run 12's final report, flagged for its reference to the dispatching user's personal instruction file.
- Leftovers. The six run folders with their skill copies (each with its `__pycache__` folder) and empty TMP directories, the prompt folder and the harness scripts are still in the session's scratch folder, and the controller removes them after the review. No run left a what-if copy, and apart from the `__pycache__` folders that Python wrote in the skill copies, no run wrote a file outside `docs/` and `AGENTS.md`.
- What a later round should do differently. Dispatch from a session outside this repository that loads none of the user's instruction or memory files, so that no environment line points the agents at the repository or the scratch folder and no run receives the user's own instructions (run 12's report referred to one). Add a targeted run on the `benchmark` path with AMD GPUs, or with the vendor unknown, to test the AMD clause of step 6, which run 12 left open. Repeat run 4 (department, superpowers absent) at the current commit: it is the one standard row behind 339b6ea, changes (c) and the `vendor` row reach it, and it would put the absent case of criterion 5 on the current commit.
