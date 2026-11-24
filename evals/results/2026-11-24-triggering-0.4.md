# Triggering, 2026-11-24 (0.4)

Does Claude Code still pick `airgap-architect` and `airgap-transfer` by itself, now pick the new `airgap-agent` for a request to set up a coding agent inside an air-gapped network, and leave other requests alone, now that the plugin holds three skills? Suite: `evals/triggering/` in the plugin folder (15 cases: the 12 of the 0.3 run plus `auto-en-coding-agent`, `auto-tr-kodlama-ajani` and `skip-en-cloud-copilot`), protocol in `evals/README.md` ("Triggering"). The results of the 0.3 descriptions are in `2026-11-24-triggering.md`; that file is unchanged.

- **Harness:** `claude plugin eval`, Claude Code 2.1.331. Model: not recorded; the JSON result has no model field and the command passed no `--model` flag, so the harness default applied.
- **Skills:** the `plugins/airgap-anything` folder on branch `feat/airgap-agent` at e95a6d2 (version 0.4.0, not merged).
- **Runs:** 15 cases, 3 runs each (45 runs, none errored, `partial: false`), `--ablation none`, `max_turns: 10`, tools `Skill, Read, Glob, Grep`. Command, from the repository root: `claude plugin eval plugins/airgap-anything --eval-dir evals/triggering --runs 3 --ablation none -j 3 --no-publish --trust-plugin --max-cost-usd 16 --json <file> --threshold 0`. Duration 417 s.
- **Cost:** USD 7.96 for the 45 agent runs (the JSON's `costUsd`, 7.9563). The judge calls cost a further USD 0.03 and are not in that figure.
- **Pass rule** (`evals/README.md`): every `auto-*` and `manual-*` case scores at least 0.8, every `skip-*` case 1.0.

| Case | Skill check | Starts | Score | Pass | Cost (USD) |
|---|---|---|---|---|---|
| `auto-en-offline-platform` | architect called 3/3, agent not called 3/3 | interview 3/3 | 1.00 | yes | 0.51 |
| `auto-en-gpu-sizing` | architect called 3/3 | interview 3/3 | 1.00 | yes | 0.57 |
| `auto-tr-internetsiz-platform` | architect called 3/3 | interview 3/3 | 1.00 | yes | 0.51 |
| `auto-tr-tasima-listesi` | architect called 3/3, transfer not called 3/3 | interview 3/3 | 1.00 | yes | 0.54 |
| `manual-plugin-command` | skill files read 3/3 | interview 3/3 | 1.00 | yes | 0.51 |
| `auto-en-coding-agent` | agent called 3/3, architect not called 3/3 | agent interview 3/3 | 1.00 | yes | 1.49 |
| `auto-tr-kodlama-ajani` | agent called 3/3 | agent interview 3/3 | 1.00 | yes | 0.55 |
| `auto-en-build-bundle` | transfer called 3/3 | transfer 3/3 | 1.00 | yes | 0.33 |
| `auto-en-verify-inside` | transfer called 3/3 | transfer 3/3 | 1.00 | yes | 0.40 |
| `auto-tr-usb-hazirla` | transfer called 3/3 | transfer 3/3 | 1.00 | yes | 0.35 |
| `skip-en-cloud-api` | not called 3/3 | none | 1.00 | yes | 1.44 |
| `skip-tr-postgres-backup` | not called 3/3 | none | 1.00 | yes | 0.21 |
| `skip-en-what-is-air-gap` | not called 3/3 | none | 1.00 | yes | 0.15 |
| `skip-en-docker-save` | neither architect nor transfer called 3/3 | none | 1.00 | yes | 0.19 |
| `skip-en-cloud-copilot` | neither architect nor agent called 3/3 | none | 1.00 | yes | 0.20 |

Overall score 1.000, overall pass rate 1.000. 45 of 45 runs pass every grader; all 15 cases meet the pass rule (15 of 15). Every skill check passed in every run: each request called the skill it was meant for, the coding-agent requests (English and Turkish) called `airgap-agent` and not the architect, the offline-platform request did not call the agent, the carry-in request without a manifest stayed with the architect, and no unrelated request or near miss ("enable GitHub Copilot for my team") called any skill.

Compared with `2026-11-24-triggering.md` (0.3, 12 cases, 0.972): the two cases that scored 0.83 there (`auto-en-offline-platform` and `auto-en-build-bundle`, each one first reply the judge found late or stopped at the inputs check) scored 1.00 here. That is within the spread of the judge's verdicts across runs, not a change of those skills: the `description` lines of `airgap-architect` and `airgap-transfer` are the same as on the 0.3 run, and the only change to the 12 old cases is the added "agent not called" grader on `auto-en-offline-platform`.

Caveats:

- One model (unrecorded) and three runs per case.
- Two prompts (`auto-en-build-bundle`, `auto-tr-usb-hazirla`) still name `docs/airgap/transfer-manifest.json`, the 0.2 file name; the skill was called in all six of their runs anyway. They are left as measured.
- Double fires were not measured beyond the cross-negative graders named in the table.
- The costs per case are the agent runs only; the cost of `auto-en-coding-agent` (USD 1.49) and `skip-en-cloud-api` (USD 1.44) is higher than the rest, and the JSON does not say why.
