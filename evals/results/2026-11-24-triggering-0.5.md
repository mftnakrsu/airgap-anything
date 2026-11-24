# Triggering, 2026-11-24 (0.5)

Does Claude Code pick the new `airgap-rag` by itself for a request to make internal documents searchable inside an air-gapped network, still pick `airgap-architect`, `airgap-transfer` and `airgap-agent` for their requests, and leave other requests alone, now that the plugin holds four skills? Suite: `evals/triggering/` in the plugin folder (18 cases: the 15 of the 0.4 run plus `auto-en-searchable-docs`, `auto-tr-belge-arama` and `skip-en-cloud-search`), protocol in `evals/README.md` ("Triggering"). The results of the 0.4 descriptions are in `2026-11-24-triggering-0.4.md`; that file is unchanged.

- **Harness:** `claude plugin eval`, Claude Code 2.1.331. Model: not recorded; the JSON result has no model field and the command passed no `--model` flag, so the harness default applied.
- **Skills:** the `plugins/airgap-anything` folder on branch `feat/airgap-rag` at 301bf75 (version 0.5.0, not merged). The later commit 2a76739 (the skill writes no programs into the project) changed no `description` and no suite file, so the result holds for it too.
- **Runs:** 18 cases, 3 runs each (54 runs, none errored, `partial: false`), `--ablation none`, `max_turns: 10`, tools `Skill, Read, Glob, Grep`. Command, from the repository root: `claude plugin eval plugins/airgap-anything --eval-dir evals/triggering --runs 3 --ablation none -j 3 --no-publish --trust-plugin --max-cost-usd 16 --json <file> --threshold 0`. Duration 497 s.
- **Cost:** USD 9.47 for the 54 agent runs (the JSON's `costUsd`, 9.4698). The judge calls cost a further USD 0.04 and are not in that figure.
- **Pass rule** (`evals/README.md`): every `auto-*` and `manual-*` case scores at least 0.8, every `skip-*` case 1.0.

| Case | Skill check | Starts | Score | Pass | Cost (USD) |
|---|---|---|---|---|---|
| `auto-en-offline-platform` | architect called 3/3, agent not called 3/3, rag not called 3/3 | interview 3/3 | 1.00 | yes | 0.52 |
| `auto-en-gpu-sizing` | architect called 3/3 | interview 3/3 | 1.00 | yes | 0.83 |
| `auto-tr-internetsiz-platform` | architect called 3/3 | interview 3/3 | 1.00 | yes | 0.50 |
| `auto-tr-tasima-listesi` | architect called 3/3, transfer not called 3/3 | interview 3/3 | 1.00 | yes | 0.53 |
| `manual-plugin-command` | skill files read 3/3 | interview 3/3 | 1.00 | yes | 0.62 |
| `auto-en-coding-agent` | agent called 3/3, architect not called 3/3, rag not called 3/3 | agent interview 2/3 | 0.92 | yes | 1.51 |
| `auto-tr-kodlama-ajani` | agent called 3/3 | agent interview 3/3 | 1.00 | yes | 0.52 |
| `auto-en-searchable-docs` | rag called 3/3, architect not called 3/3 | rag interview 3/3 | 1.00 | yes | 0.48 |
| `auto-tr-belge-arama` | rag called 3/3 | rag interview 3/3 | 1.00 | yes | 0.51 |
| `auto-en-build-bundle` | transfer called 3/3 | transfer 3/3 | 1.00 | yes | 0.34 |
| `auto-en-verify-inside` | transfer called 3/3 | transfer 3/3 | 1.00 | yes | 0.38 |
| `auto-tr-usb-hazirla` | transfer called 3/3 | transfer 3/3 | 1.00 | yes | 0.33 |
| `skip-en-cloud-api` | not called 3/3 | none | 1.00 | yes | 1.43 |
| `skip-tr-postgres-backup` | not called 3/3 | none | 1.00 | yes | 0.21 |
| `skip-en-what-is-air-gap` | not called 3/3 | none | 1.00 | yes | 0.15 |
| `skip-en-docker-save` | neither architect nor transfer called 3/3 | none | 1.00 | yes | 0.20 |
| `skip-en-cloud-copilot` | neither architect nor agent called 3/3 | none | 1.00 | yes | 0.21 |
| `skip-en-cloud-search` | neither architect nor rag called 3/3 | none | 1.00 | yes | 0.21 |

Overall score 0.995, overall pass rate 0.981. 53 of 54 runs pass every grader; all 18 cases meet the pass rule (18 of 18). Every skill check passed in every run: the two document-search requests (English and Turkish, neither names a platform) called `airgap-rag` and not the architect, the coding-agent requests called `airgap-agent` and neither the architect nor `airgap-rag`, the offline-platform request called only the architect, the carry-in request without a manifest stayed with the architect, and no unrelated request or near miss ("add Google Drive search to ChatGPT Enterprise", "enable GitHub Copilot for my team") called any skill. In all six runs of the two `airgap-rag` cases the judge passed the reply on all three votes: each asked the platform question with its three options.

The one failed grader: `auto-en-coding-agent`, run 3, `starts-the-agent-interview` (judge votes PASS, FAIL, FAIL). The skill was called, and the cross-negative graders passed. The reply said that writing files was turned off in the session, assumed defaults for the open questions (Linux amd64, edits need approval, central settings, git only, no Claude route), listed them under "Assumptions" and gave the full setup for Qwen Code instead of asking the interview questions. The case still passes the rule (0.92, above 0.8: one missed grader in three runs). The other two runs of the case passed all four graders.

Compared with `2026-11-24-triggering-0.4.md` (0.4, 15 cases, 1.000): the one case below 1.00 here (`auto-en-coding-agent`, 1.00 there) is the one with a single judge vote that failed; the `description` lines of `airgap-architect`, `airgap-transfer` and `airgap-agent` are the same as on the 0.4 run, and the changes to the 15 old cases are the added "rag not called" graders on `auto-en-offline-platform` and `auto-en-coding-agent`. Whether the difference is the judge's spread or an effect of the fourth description was not tested.

Caveats:

- One model (unrecorded) and three runs per case.
- Two prompts (`auto-en-build-bundle`, `auto-tr-usb-hazirla`) still name `docs/airgap/transfer-manifest.json`, the 0.2 file name; the skill was called in all six of their runs anyway. They are left as measured.
- Double fires were not measured beyond the cross-negative graders named in the table.
- The costs per case are the agent runs only (the sum of the three runs' `costUsd`, rounded); the cost of `auto-en-coding-agent` (USD 1.51) and `skip-en-cloud-api` (USD 1.43) is higher than the rest, as in the 0.4 run, and the JSON does not say why.
- The command passed `--max-cost-usd 16`; `evals/README.md` shows 14 as its example ceiling. The run cost USD 9.47, below both.
