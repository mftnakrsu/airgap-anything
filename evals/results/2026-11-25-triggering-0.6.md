# Triggering, 2026-11-25 (0.6)

Does Claude Code pick the new `airgap-install` by itself for a request to install an approved air-gapped design inside the network, still pick `airgap-architect`, `airgap-transfer`, `airgap-agent` and `airgap-rag` for their requests, and leave other requests alone, now that the plugin holds five skills? Suite: `evals/triggering/` in the plugin folder (21 cases: the 18 of the 0.5 run plus `auto-en-install-inside`, `auto-tr-kurulum-adimlari` and `skip-en-install-docker-ubuntu`, and `does-not-fire-install` graders on `auto-en-build-bundle` and `auto-en-verify-inside`), protocol in `evals/README.md` ("Triggering"). The results of the 0.5 descriptions are in `2026-11-24-triggering-0.5.md`; that file is unchanged.

- **Harness:** `claude plugin eval`, Claude Code 2.1.332. Model: not recorded; the JSON result has no model field and the command passed no `--model` flag, so the harness default applied.
- **Skills:** the `plugins/airgap-anything` folder on branch `feat/airgap-install` at 7dbbf76 (version 0.6.0, not merged). The `description` lines of `airgap-architect`, `airgap-transfer`, `airgap-agent` and `airgap-rag` are the same as in the 0.5 run (`git diff 301bf75 HEAD` shows no change to them).
- **Runs:** 21 cases, 3 runs each (63 runs, none errored, `partial: false`), `--ablation none`, `max_turns: 10`. Command, from the repository root, as in `evals/README.md`: `claude plugin eval plugins/airgap-anything --eval-dir evals/triggering --runs 3 --ablation none -j 3 --no-publish --trust-plugin --max-cost-usd <ceiling> --json <file> --threshold 0` (the ceiling used was not kept). Duration 570 s.
- **Cost:** USD 11.06 for the 63 agent runs (the JSON's `costUsd`, 11.0610). The judge calls cost a further USD 0.05 and are not in that figure.
- **Pass rule** (`evals/README.md`): every `auto-*` and `manual-*` case scores at least 0.8, every `skip-*` case 1.0.

| Case | Skill check | Starts | Score | Pass | Cost (USD) |
|---|---|---|---|---|---|
| `auto-en-offline-platform` | architect called 3/3, agent not called 3/3, rag not called 3/3 | interview 2/3 | 0.92 | yes | 0.53 |
| `auto-en-gpu-sizing` | architect called 3/3 | interview 3/3 | 1.00 | yes | 0.60 |
| `auto-tr-internetsiz-platform` | architect called 3/3 | interview 3/3 | 1.00 | yes | 0.51 |
| `auto-tr-tasima-listesi` | architect called 3/3, transfer not called 3/3 | interview 3/3 | 1.00 | yes | 0.54 |
| `manual-plugin-command` | skill files read 3/3 | interview 2/3 | 0.83 | yes | 0.53 |
| `auto-en-coding-agent` | agent called 3/3, architect not called 3/3, rag not called 3/3 | agent interview 2/3 | 0.92 | yes | 2.12 |
| `auto-tr-kodlama-ajani` | agent called 3/3 | agent interview 3/3 | 1.00 | yes | 0.50 |
| `auto-en-searchable-docs` | rag called 3/3, architect not called 3/3 | rag interview 3/3 | 1.00 | yes | 0.49 |
| `auto-tr-belge-arama` | rag called 3/3 | rag interview 3/3 | 1.00 | yes | 0.54 |
| `auto-en-build-bundle` | transfer called 3/3, install not called 3/3 | transfer 3/3 | 1.00 | yes | 0.35 |
| `auto-en-verify-inside` | transfer called 3/3, install not called 3/3 | transfer 3/3 | 1.00 | yes | 0.40 |
| `auto-tr-usb-hazirla` | transfer called 3/3 | transfer 2/3 | 0.83 | yes | 0.35 |
| `auto-en-install-inside` | install called 3/3, architect not called 3/3 | install plan 3/3 | 1.00 | yes | 0.48 |
| `auto-tr-kurulum-adimlari` | install called 3/3 | install plan 3/3 | 1.00 | yes | 0.46 |
| `skip-en-cloud-api` | not called 3/3 | none | 1.00 | yes | 1.45 |
| `skip-tr-postgres-backup` | not called 3/3 | none | 1.00 | yes | 0.21 |
| `skip-en-what-is-air-gap` | not called 3/3 | none | 1.00 | yes | 0.16 |
| `skip-en-docker-save` | neither architect nor transfer called 3/3 | none | 1.00 | yes | 0.20 |
| `skip-en-cloud-copilot` | neither architect nor agent called 3/3 | none | 1.00 | yes | 0.22 |
| `skip-en-cloud-search` | neither architect nor rag called 3/3 | none | 1.00 | yes | 0.21 |
| `skip-en-install-docker-ubuntu` | neither architect nor install called 3/3 | none | 1.00 | yes | 0.20 |

Overall score 0.976, overall pass rate 0.937 (the JSON's `overallScore` 0.9762 and `overallPassRate` 0.9365). 59 of 63 runs pass every grader; all 21 cases meet the pass rule (21 of 21). Every tool-use ("skill check") grader passed in every run: the three `airgap-install` cases passed 3/3 on both the skill check and the judge (the English and Turkish install requests called `airgap-install`, the English one without calling `airgap-architect`, and each reply started the install plan; "How do I install Docker Engine on Ubuntu 24.04?" called neither `airgap-architect` nor `airgap-install`), the two transfer requests that used to be the nearest neighbors (`auto-en-build-bundle`, `auto-en-verify-inside`) did not call `airgap-install`, and the five other skills' requests called the skills of the 0.5 run.

The four failed graders are all single runs of the judge-scored "starts-the-*" graders of cases for other skills, not of an install case, and none is a skill check:

- `auto-en-coding-agent`, run 3, `starts-the-agent-interview` (judge votes FAIL, FAIL, FAIL). The skill was called. The reply said it could not save files because writing was turned off, chose Qwen Code and gave the vLLM flags and the setup as text, instead of asking the interview questions. The same case missed one run in the 0.5 run (0.92 there too).
- `auto-en-offline-platform`, run 2, `starts-the-interview` (FAIL, FAIL, FAIL). The architect was called and its checklist shown; the reply says file writing is off, lists the one answer it has (200 users), and asks question 2 ("How many departments or teams need their own budget or data boundary?"). All three judges still failed it; why was not investigated (the reply reads like an interview start).
- `auto-tr-usb-hazirla`, run 3, `starts-the-transfer` (FAIL, PASS, FAIL). The skill was called; the reply, in Turkish, found no `docs/airgap/` folder and no manifest file in its working directory, said it would not write a plan without one and asked for the file's path. Its prompt still names `docs/airgap/transfer-manifest.json`, the 0.2 file name (see caveats).
- `manual-plugin-command`, run 1, `starts-the-interview` (FAIL, FAIL, FAIL). The skill's references were read (`loads-the-skill` 3/3); the reply says the Write tool is turned off, keeps the answers in chat and asks question 2, as in the second miss.

Three of the four replies say that writing files was turned off in the session. In the 0.5 run the one miss also said so. Whether the judge penalizes that note, or the interview start after it, is a question for the grader text and was not tested.

Compared with `2026-11-24-triggering-0.5.md` (0.5, 18 cases, 0.995, pass rate 0.981): the overall score is lower by 0.019 and 59 of 63 runs pass every grader against 53 of 54. Of the 18 old cases, four now score below 1.00 (`auto-en-offline-platform`, `manual-plugin-command`, `auto-en-coding-agent`, `auto-tr-usb-hazirla`), against one in 0.5. Their `description` lines did not change, and every miss is a judge-scored start, so the likeliest cause is the spread of one-run judge votes (three runs per case) and not the fifth description; the three new cases and the two new `does-not-fire-install` graders have no misses. This was not tested (no repeat of the 0.5 descriptions in the same session).

Caveats:

- One model (unrecorded) and three runs per case.
- Two prompts (`auto-en-build-bundle`, `auto-tr-usb-hazirla`) still name `docs/airgap/transfer-manifest.json`, the 0.2 file name; the skill was called in all six of their runs anyway, and the one `usb-hazirla` miss is a reply that looked for that file. They are left as measured.
- Double fires were not measured beyond the cross-negative graders named in the table.
- The costs per case are the agent runs only (the sum of the three runs' `costUsd`, rounded); `auto-en-coding-agent` (USD 2.12, one run costlier than the others) and `skip-en-cloud-api` (USD 1.45) cost more than the rest, as before, and the JSON does not say why.
- The judge's text is in the JSON's `evidence` field and the full report is in `plugins/airgap-anything/evals/triggering/results/2026-11-25T09-06-52-521Z/report.html`, which git ignores.
