# Triggering, 2026-11-23

Does Claude Code pick `airgap-architect` and `airgap-transfer` by itself, start `airgap-architect` from its slash command, and leave other requests alone, now that both skills are installed together? Suite: `evals/triggering/`, protocol in `evals/README.md` ("Triggering").

- **Harness:** `claude plugin eval`, Claude Code 2.1.330. Model: not recorded. The JSON result and the raw report have no model field, and the command passed no `--model` flag, so the harness default applied (the 2026-11-22 run reported `claude-opus-5-5`). The JSON lists one plugin, `airgap-anything` 0.1.0, with both skills.
- **Skills:** the `plugins/airgap-anything` folder at commit 9fcdefb when the run started (2026-11-23, 356 s). The `description` of `airgap-transfer` is unchanged since 22cce98 and that of `airgap-architect` since `main`.
- **Runs:** 12 cases, 3 runs each (36 runs, none errored, `partial: false`), `--ablation none`, `max_turns: 10`, tools `Skill, Read, Glob, Grep`. Command, from the repository root: `claude plugin eval plugins/airgap-anything --eval-dir evals/triggering --runs 3 --ablation none -j 3 --no-publish --trust-plugin --max-cost-usd 14 --json <file> --threshold 0`.
- **Cost:** USD 6.50 for the 36 agent runs (the JSON's `costUsd`, 6.4957), plus about USD 0.02 for the LLM judge, which the JSON lists per run but does not add to that total.
- **Pass rule** (`evals/README.md`): every `auto-*` and `manual-*` case scores at least 0.8, every `skip-*` case 1.0. A case's score is the mean of its three runs; a run's score is the weighted share of its graders that passed. The tool's own `casesPassed` (12 of 12) means nothing here because `--threshold 0` lets every case through, so the rule was applied by hand.

| Case | Message (abridged) | Skill check | Starts | Score | Pass | Cost (USD) | Notes |
|---|---|---|---|---|---|---|---|
| `auto-en-offline-platform` | LLM chat service for ~200 engineers, network without internet | architect called 3/3 | interview 3/3 | 1.00 | yes | 0.66 | |
| `auto-en-gpu-sizing` | GPUs and servers for a 70B model, 500 users, disconnected data center | architect called 3/3 | interview 3/3 | 1.00 | yes | 0.82 | |
| `auto-tr-internetsiz-platform` | İnternete kapalı ağda üç departmana LLM platformu | architect called 3/3 | interview 3/3 | 1.00 | yes | 0.54 | |
| `auto-tr-tasima-listesi` | vLLM ve Open WebUI için kapalı ağa taşınacaklar listesi | architect called 3/3, transfer not called 3/3 | interview 2/3 | 0.89 | yes | 0.72 | one run 0.67, see below |
| `manual-plugin-command` | `/airgap-anything:airgap-architect`, 12-person lab, no internet | skill files read 3/3 | interview 3/3 | 1.00 | yes | 0.51 | |
| `auto-en-build-bundle` | Design approved, `transfer-manifest.json` written, everything on it must go onto USB disks, how do we start | transfer called 3/3 | transfer 2/3 | 0.83 | yes | 0.50 | one run 0.50, see below |
| `auto-en-verify-inside` | Inside the isolated network with the bundle on three USB disks, how to check nothing is missing or damaged | transfer called 3/3 | transfer 3/3 | 1.00 | yes | 0.34 | |
| `auto-tr-usb-hazirla` | Tasarım onaylandı, manifest yazıldı, listedeki her şeyi USB disklere hazırlamak, nereden başlayalım | transfer called 3/3 | transfer 3/3 | 1.00 | yes | 0.44 | |
| `skip-en-cloud-api` | Python function calling a hosted LLM API | not called 3/3 | none | 1.00 | yes | 1.43 | |
| `skip-tr-postgres-backup` | Docker Compose Postgres nightly backup | not called 3/3 | none | 1.00 | yes | 0.20 | |
| `skip-en-what-is-air-gap` | "What does air-gapped mean", two sentences | not called 3/3 | none | 1.00 | yes | 0.14 | |
| `skip-en-docker-save` | Save a Docker image to a tar and load it on another machine on the office network | neither skill called 3/3 | none | 1.00 | yes | 0.19 | |

Overall score 0.977. 34 of 36 runs pass every grader; the two others each missed one grader. All 12 cases meet the pass rule.

Below 1.0:

- **`auto-en-build-bundle`, run 1 (score 0.50, judge, `starts-the-transfer`).** The skill was called (`fires-transfer` passed), but the judge voted FAIL, FAIL, PASS on the reply. The reply said `docs/airgap/transfer-manifest.json` is not in the project (the eval session's folder is empty), asked for its path or for a rerun of `airgap-architect`, and then listed the steps it would take once the manifest exists (`plan.py`, the questions, approval, pack and check). It did not read a manifest or ask a transfer question yet. Runs 2 and 3 passed.
- **`auto-tr-tasima-listesi`, run 2 (score 0.67, judge, `starts-the-interview`).** `fires` and `does-not-fire-transfer` passed; the judge voted FAIL three times. The run used all 10 turns. The reply opened with a provisional carry-in list (image tags and versions, model files, telemetry settings) taken from the component catalog, said that it could not write files or run the scripts in this session, and ended with the first interview question ("Platformu kaç kişi kullanacak?"). The grader fails a reply that presents component versions before asking. Runs 1 and 3 passed.

Compared with `2026-11-22-triggering.md` (the 8 cases that existed then):

- Seven of them are unchanged: every run passes every grader (21 of 21 runs).
- `auto-tr-tasima-listesi` was 3 of 3 clean on 2026-11-22 and is 2 of 3 now (above). It also gained a grader since then, `does-not-fire-transfer`, so it now has three graders; that grader passed 3 of 3.
- What else differs: this run had both skills installed (the earlier one had only `airgap-architect`), and the `airgap-architect` body changed in 77eace3 (hand-off to `airgap-transfer`), though its `description` did not. The model of this run is not known, so a model change cannot be ruled out. Claude Code is 2.1.330 in both.

What it shows:

- **Two skills side by side do not steal each other's requests.** Every `airgap-architect` request still called `airgap-architect` (15 of 15 runs across five cases, counting the manual one by its files), and none called `airgap-transfer`. Every transfer request (`auto-en-build-bundle`, `auto-en-verify-inside`, `auto-tr-usb-hazirla`, 9 of 9 runs) called `airgap-transfer`, including the Turkish one and the one that starts inside the network.
- **The carry-in list stays with the architect.** `auto-tr-tasima-listesi` asks for the list of things to carry in before any manifest exists. All three runs called `airgap-architect`, none called `airgap-transfer`.
- **No false starts.** The two unrelated requests, the near miss about the term, and the new near miss (`docker save` between two machines on one network) never called either skill, in 12 of 12 runs.
- **Manual start works.** The slash command is expanded before the session, so no Skill tool call appears; the first tool call reads the skill's `references/` files.

Caveats:

- One model (unrecorded) and three runs per case. A case passes at 0.8 by design, so a single missed grader in three runs does not fail it; both misses above are of that kind and both are judge verdicts on the wording of the first reply, not missed or wrong skill calls.
- The sessions could not write files or run commands (`allowed_tools`), and the eval folder is empty, so the manifest that three transfer prompts mention does not exist. The runs stop at the first reply. What the skills do after that is covered by the scenario runs in `2026-11-22-with-skill.md`, `2026-11-23-with-skill.md`, `2026-11-23-transfer-baseline.md` and `2026-11-23-transfer-with-skill.md`.
- The LLM judge is the only thing that failed a run. Its three votes agreed in one case (3 FAIL) and split 2 to 1 in the other.
- Nothing here tests a session with many other skills installed, or an `airgap-transfer` request in Turkish that starts inside the network.
