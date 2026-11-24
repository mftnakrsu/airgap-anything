# Triggering, 2026-11-24

Does Claude Code still pick `airgap-architect` and `airgap-transfer` by itself, start the architect from its slash command, and leave other requests alone, now that version 0.3 gave both descriptions a leading sentence ("Designs systems for air-gapped, offline and on-premises networks from a sourced catalog instead of memory." and "Packs the transfer manifest of an air-gapped design into a bundle that checks itself inside the network.") and both skills are markdown only? Suite: `evals/triggering/`, protocol in `evals/README.md` ("Triggering").

- **Harness:** `claude plugin eval`, Claude Code 2.1.331. Model: not recorded; the JSON result has no model field and the command passed no `--model` flag, so the harness default applied.
- **Skills:** the `plugins/airgap-anything` folder on `main` at 2fec21b (0.3, merged in pull request #18).
- **Runs:** 12 cases, 3 runs each (36 runs, none errored, `partial: false`), `--ablation none`, `max_turns: 10`, tools `Skill, Read, Glob, Grep`. Command, from the repository root: `claude plugin eval plugins/airgap-anything --eval-dir evals/triggering --runs 3 --ablation none -j 3 --no-publish --trust-plugin --max-cost-usd 14 --json <file> --threshold 0`. Duration 278 s.
- **Cost:** USD 5.65 for the 36 agent runs (the JSON's `costUsd`, 5.6470).
- **Pass rule** (`evals/README.md`): every `auto-*` and `manual-*` case scores at least 0.8, every `skip-*` case 1.0.

| Case | Skill check | Starts | Score | Pass | Cost (USD) |
|---|---|---|---|---|---|
| `auto-en-offline-platform` | architect called 3/3 | interview 2/3 | 0.83 | yes | 0.51 |
| `auto-en-gpu-sizing` | architect called 3/3 | interview 3/3 | 1.00 | yes | 0.58 |
| `auto-tr-internetsiz-platform` | architect called 3/3 | interview 3/3 | 1.00 | yes | 0.52 |
| `auto-tr-tasima-listesi` | architect called 3/3, transfer not called 3/3 | interview 3/3 | 1.00 | yes | 0.53 |
| `manual-plugin-command` | skill files read 3/3 | interview 3/3 | 1.00 | yes | 0.50 |
| `auto-en-build-bundle` | transfer called 3/3 | transfer 2/3 | 0.83 | yes | 0.33 |
| `auto-en-verify-inside` | transfer called 3/3 | transfer 3/3 | 1.00 | yes | 0.40 |
| `auto-tr-usb-hazirla` | transfer called 3/3 | transfer 3/3 | 1.00 | yes | 0.31 |
| `skip-en-cloud-api` | not called 3/3 | none | 1.00 | yes | 1.44 |
| `skip-tr-postgres-backup` | not called 3/3 | none | 1.00 | yes | 0.20 |
| `skip-en-what-is-air-gap` | not called 3/3 | none | 1.00 | yes | 0.15 |
| `skip-en-docker-save` | neither skill called 3/3 | none | 1.00 | yes | 0.18 |

Overall score 0.972. 34 of 36 runs pass every grader; all 12 cases meet the pass rule. Every skill check passed in every run: each request called the skill it was meant for, the carry-in request without a manifest (`auto-tr-tasima-listesi`) stayed with the architect, and no unrelated request or near miss called either skill.

Below 1.0, both judge verdicts on the first reply, not missed or wrong skill calls:

- **`auto-en-build-bundle`, run 1 (`starts-the-transfer`).** The skill was called and its checklist shown, stopped at step 1: "I can't start yet because there's no manifest here. The project directory … is empty." The eval folder is empty by design, so stopping at the inputs check is what the skill says to do; the judge wanted the transfer to start. The same case missed the same grader for the same reason on 2026-11-23.
- **`auto-en-offline-platform`, run 1 (`starts-the-interview`).** The skill was called and its checklist shown, then: "A limitation first: file writing is turned off in this session, so I couldn't create `docs/airgap/blueprint.md` to track the design." The judge wanted the first question sooner.

Compared with `2026-11-23-triggering.md` (0.2 descriptions): the same 12 cases pass; the overall score moved from 0.977 to 0.972, within one judge vote; every skill check passed in both runs.

Caveats:

- One model (unrecorded) and three runs per case.
- Two prompts (`auto-en-build-bundle`, `auto-tr-usb-hazirla`) still name `docs/airgap/transfer-manifest.json`, the 0.2 file name; the skill was called in all six of their runs anyway. They are left as measured.
- Double fires were not measured beyond `auto-tr-tasima-listesi` and `skip-en-docker-save`, as on 2026-11-23.
