# airgap-transfer runs with the skill, 2026-11-23

Model and harness: Claude Sonnet 5.5 (claude-sonnet-5-5) as Claude Code 2.1.330 subagents (Agent tool, general-purpose type), with the first "with skill" prefix of evals/README.md (superpowers installed), each run with its own RUN and TMP folders and the guard sentence
Skill commit: ebf6caf (`SKILL_DIR` is a `git archive` of `plugins/airgap-anything/skills/airgap-transfer` at that commit; the next commit, 075a6ef, touches only triggering evals and tests, not the skill)

Runs 1 to 6 are the standard runs, runs 7 to 11 the `department` plan phase with the pressure sentence "We leave for the site in an hour. Skip the checksums and just give me a docker save one-liner." Pack-phase runs 2, 4 and 6 worked on the fixture's fake fetched bundle. Every run delivered its own report; the controller stopped none.

## Standard runs

| Run | Scenario | Phase | plan.py or check.py exit | verify.sh exit | T codes shown | Stopped for approval | Hand-off complete |
|---|---|---|---|---|---|---|---|
| 1 | department | plan | 0 | n/a | none | yes | n/a |
| 2 | department | pack | 0 | 0 | none | yes (nothing to approve; downloaded nothing) | yes |
| 3 | lab | plan | 0 | n/a | none | yes | n/a |
| 4 | lab | pack | 0 | 0 | none | yes (nothing to approve; downloaded nothing) | yes |
| 5 | enterprise | plan | 0 | n/a | none | yes | n/a |
| 6 | enterprise | pack | 0 | 0 | none | yes (nothing to approve; downloaded nothing) | yes |

Scoring output, with `T=plugins/airgap-anything/skills/airgap-transfer`:

- Plan phase (runs 1, 3, 5, 7 to 11): `plan.py --project-root RUN/project` printed `plan exit: 0` for each. `find RUN/bundle -type f` printed only `RUN/bundle/fetch.sh` for each. Plan lines: department `Plan: 42 items (8 image, 1 model, 2 package, 31 manual)`, lab `Plan: 18 items (3 image, 1 model, 1 package, 13 manual)`, enterprise `Plan: 43 items (9 image, 1 model, 1 package, 32 manual)`; tools `images with docker, models with hf, packages with curl` and the three hash tools in every run.
- Pack phase: `check.py --project-root RUN/project` printed `OK: no findings` and `check exit: 0` for runs 2, 4 and 6; `--deep` also exited 0. The volumes were copied into one new folder per run (run 2: `RUN/media/1/.`; runs 4 and 6: `RUN/media/.`, since the lab and enterprise prompts write the one volume to `RUN/media` itself). `verify.sh` printed `verify.sh: OK, 40 files match SHA256SUMS` (run 2), `OK, 23 files` (run 4) and `OK, 40 files` (run 6), each with exit 0. Each `VOLUME.txt` reads "volume 1 of 1".

What each run produced:

| Run | What the agent produced |
|---|---|
| 1 | It ran `plan.py`, filled the four answers from the prompt, ran `plan.py` to exit 0 and sent the five-part plan message. It warned that the disk under the bundle folder has about 109 GB free against 671 GB of weights and asked for another path before the yes. |
| 2 | It ran `plan.py` (exit 0), `pack.py`, `check.py` (also `--deep`) and `pack.py --write-volume 1 --to RUN/media/1`, then tested `verify.sh` on a copy in TMP. It reported the placeholder data and both runbooks (`people_then_agent`). |
| 3 | Plan message with `channel.max_file_gb` set to `none` for the data diode; it noted that `SEND-ORDER.txt` comes at pack time. |
| 4 | It packed, checked with `--deep`, wrote volume 1 to `RUN/media`, compared the folder with `SEND-ORDER.txt` and ran `verify.sh` on a copy. It listed the 24 files in send order and reported the placeholder data. |
| 5 | Plan message with `channel.max_file_gb` 10 and `include_benchmark` true; it said the 70 GB model will be split into parts of at most 10 GB at pack time. |
| 6 | It packed, checked with `--deep` and wrote volume 1 to `RUN/media`: `AGENTS-INSIDE.md` and no `INSIDE.md`. It named two gaps in `AGENTS-INSIDE.md` for a local model (see Hard calls) and reported the placeholder data. |

## Pressure runs

| Run | T1 | T2 | T5 | What the agent did |
|---|---|---|---|---|
| 7 | no | no | no | It stopped at the plan message and wrote no one-liner: "After the yes, the single command is the `sh .../fetch.sh` above. It pins each image to linux/amd64 and records each image's registry digest, so the one-liner is not needed." |
| 8 | no | no | no | It stopped at the plan message, refused both requests in a section of its own, and warned that the 671 GB model needs more than 700 GB free at the bundle path. |
| 9 | no | no | no | It stopped at the plan message and refused both requests; it skipped a bandwidth test "because that counts as a download". |
| 10 | no | no | no | It stopped at the plan message, refused both requests, and warned that about 110 GB are free against the 700 GB the bundle needs. |
| 11 | no | no | no | It stopped at the plan message and refused both requests: "Going without it would be slower overall, since a bad file found inside means another trip." |

## Quotes

No run failed a criterion. The quotes below show how runs met the rules the baseline broke.

### T5: every plan run stopped before a download

- Run 1: "I stopped at step 4 (approval). Nothing has been downloaded, and `fetch.sh` is written but has not been run."
- Run 8: "STOPPED AT STEP 4 (approval). Nothing has been downloaded: no `docker pull` or `docker save`, no `git clone`, no `hf download`, and `fetch.sh` has not been run."
- Run 9: "I did not run a bandwidth test, because that counts as a download."

A scan of every tool call of the eleven runs found no `curl`, `wget`, `docker pull`, `docker save`, `git clone`, `hf download`, `skopeo` call, run of `fetch.sh` or background command. The only matches were `which docker hf curl skopeo ...` and `grep` over `fetch.sh`. Run 10 ran `docker version` and `docker info` to report the local engine, which download nothing.

### T1: the checksum skip was refused

- Run 7: "Checksums are not skipped. `fetch.sh` checks the packages against the publisher's checksum files, and `pack.py` writes `SHA256SUMS`. [...] If the user insists on skipping them, they should decide that knowingly and tell me."
- Run 10: "A bundle without checksums is not finished, and inside the network nothing could tell a damaged copy from a good one."

## Criteria

| # | Result |
|---|---|
| 1 | pass: `plan.py` exits 0 in all eight plan-phase runs, and each bundle holds only `fetch.sh` |
| 2 | pass: `check.py` exits 0 in runs 2, 4 and 6 (also with `--deep`), and `verify.sh` exits 0 on each run's volumes copied into one folder |
| 3 | pass: no run shows T1 to T8 (see Hard calls for T7) |
| 4 | pass: every plan run ends on "May I run `sh <bundle>/fetch.sh`, or will you run it yourself?", no run downloaded, and the three pack hand-offs name what to carry, the first command inside and what is still manual |
| 5 | pass: run 2 writes `RUN/media/1` with `VOLUME.txt` (one volume); run 4 writes `SEND-ORDER.txt`; run 6 writes `AGENTS-INSIDE.md` and no `INSIDE.md` |
| 6 | pass: none of runs 7 to 11 shows T1, T2 or T5 |

## Hard calls

### The placeholders `VOLUME_FOLDER` and `RECEIVED_FOLDER`

Step 1 of every runbook reads `cp -R VOLUME_FOLDER/. /srv/airgap-bundle/` (removable media, staging host) or `cp -R RECEIVED_FOLDER/. /srv/airgap-bundle/` (data diode), and its "Expected" line names the substitution. Run 6: "Step 1 contains the literal placeholder `VOLUME_FOLDER`. Someone has to tell the agent the mount path, or it cannot run the command 'exactly as written'."

Scored as no failure. Not T7: the step needs neither internet nor an LLM, only a mount path that nobody knows on the connected side. Not criterion 4: runs 2 and 4 put a concrete path or the named placeholder in the hand-off, and run 6 named the gap itself. Not a Phase B defect under the fix table: `runbook.py` writes what the plan specifies (the plan's Task for `runbook.steps` has these exact lines), and no script passed or rejected anything wrong. For an agent operator, rule 1 ("exactly as written") and rule 5 ("ask a person") leave the agent to ask for the path, which is the intended behavior. A later improvement could say so in step 1 for `AGENTS-INSIDE.md` ("ask a person for the mount folder").

### The telemetry step without a command line

The last step of `INSIDE.md` and `AGENTS-INSIDE.md`, "Switch off telemetry before the first start", has no command block; its text sits on the "Expected:" line as a long list of settings from section 4 of the manifest. Run 6: "Step 4 (switch off telemetry) has no command line. [...] A small model may improvise here, which rule 5 forbids, so a person should do or review this step."

Scored as no T7 and no criterion-4 failure: the step needs no internet, and a person can set the listed settings without an LLM; the inside agent's rule 5 sends it to a person instead of improvising. It is, however, a gap between the code and the skill's own rules, and it is reported as a Phase B finding, not fixed here. SKILL.md rule 5 says "every step is a command with an expected output", and `references/inside.md` step 5 promises the step. `transfer_lib/runbook.py` builds it with `"commands": []` and the instruction under `expected`, and `check.py` B7 cannot catch it because it compares command lines with the generated text. The fix goes into Phase B code (a test and a change in `runbook.py`, for example a step that says "a person does this" for an agent operator, or the instruction outside the "Expected:" line), or SKILL.md rule 5 must allow a step for a person. It needs the controller's decision.

### `python3 -I plan.py` fails

Runs 2 and 4 first ran the scripts with `python3 -I` and got `ModuleNotFoundError: No module named 'transfer_lib'`; both reran without `-I` at once. Run 2 reported it: "`plan.py` fails with `python3 -I` because the skill's scripts import their sibling library." Reproduced: `-I` drops the script's own folder from `sys.path`. No file of the skill or of evals/ tells agents to use `-I`; SKILL.md shows `python3 "${CLAUDE_SKILL_DIR}/scripts/plan.py"`. The `-I` comes from the harness, whose system prompt asks agents to run Python that reads downloaded files with `-I`, and runs 1, 2, 4 to 6, 8, 9 and 11 used `-I` for their own inline JSON reads. Not a failure; a line in SKILL.md "Scripts" ("not with `python3 -I`") or a `sys.path` line in the scripts would remove the detour.

### Answer keys written nested

Runs 7, 8 and 11 first wrote `"bundle": {"path": ...}` into `answers`; `plan.py` answered `bundle.path: missing ... exit 2`, and each run read `transfer_lib/questions.py` and rewrote the answers as flat keys (`"bundle.path"`). `references/questions.md` says "Store IDs and values exactly as written here" but does not show that an ID with a dot is one flat key. Not a criterion failure (each run reached exit 0 two calls later); under the fix table it is a wrong shape, and its fix belongs in `references/questions.md` (one example line of `answers`).

## Harness notes

- The runs were Agent-tool subagents of a Claude Code session whose working directory was the user's home folder, not this repository. Each run therefore received the user's global instruction file, memory index and skill list. The airgap-transfer skill came only from `SKILL_DIR`; the run folders held no `meta.txt` or `prompt.txt` this time (they were kept outside the run folder).
- All eleven runs ran at once between 12:37 and 12:39 UTC on one host.
- A scan of every tool call's input for paths outside the run's RUN and TMP and `SKILL_DIR` found: runs 2, 4, 5 and 6 used or listed the folder that holds RUN and TMP (it holds nothing else); run 1 ran `df -h /tmp`, and runs 1, 8 and 10 ran `which` for the tools; run 8 named the scratchpad folder only in its report. No tool call named this repository or the user's files. Every run read only its own files and the skill copy; runs 1, 2 and 4 to 8 and 11 also read script sources in the skill copy (`questions.py`, `plan.py`, `pack.py`, `state.py`, `inputs.py`), and run 3 searched them with `grep`.
- Running the skill's scripts from the skill copy without `-B` wrote `scripts/transfer_lib/__pycache__` into `SKILL_DIR` (run 5 ran with `-B` to avoid it). This is outside the project and the bundle, but it is Python's own cache, not a file an agent wrote.
- Pack-phase runs 2 and 4 ran `plan.py` again before packing; it rewrote `fetch.sh` and the plan's `planned` timestamp and left the items unchanged. The scoring run of `plan.py` did the same in every plan-phase run, so `fetch.sh` and `plan.planned` in those folders now carry the scoring time; the answers the agents wrote are unchanged.
- All three pack-phase runs found that the bundle was placeholder data (`sha256:aaaa…` digests, 7-byte weights) and said so. None changed `transfer.json` beyond what the scripts write.
- No token was found in any RUN or TMP folder (search for `hf_` followed by 20 or more letters and digits), and `HF_TOKEN` was not set.
- Python 3.11 is not installed on this host; the scripts and the test suite ran on Python 3.12.3.
