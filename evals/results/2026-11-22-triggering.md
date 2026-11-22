# Triggering, 2026-11-22

Does Claude Code pick `airgap-architect` by itself, start it from its slash command, and leave other requests alone? Suite: `evals/triggering/`, protocol in `evals/README.md` ("Triggering").

- **Harness:** `claude plugin eval`, Claude Code 2.1.330, model `claude-opus-5-5`. Only this plugin was installed in each session: no user settings, no CLAUDE.md, no other plugins.
- **Skill:** `SKILL.md` as of commit 4667a93 (its `description` unchanged since v0.1).
- **Runs:** 8 cases, 3 runs each, `--ablation none`, `max_turns: 10`, tools `Skill, Read, Glob, Grep`.
- **Cost:** USD 4.34 for this run, plus USD 0.49 for three single runs of the manual case while its grader was settled.

| Case | Message (abridged) | Skill check | Interview starts |
|---|---|---|---|
| `auto-en-offline-platform` | LLM chat service for ~200 engineers, network without internet | called 3/3 | 3/3 |
| `auto-en-gpu-sizing` | GPUs and servers for a 70B model, 500 users, disconnected data center | called 3/3 | 3/3 |
| `auto-tr-internetsiz-platform` | İnternete kapalı ağda üç departmana LLM platformu | called 3/3 | 3/3 |
| `auto-tr-tasima-listesi` | Kapalı ağa vLLM ve Open WebUI; içeri neler taşınacak | called 3/3 | 3/3 |
| `manual-plugin-command` | `/airgap-anything:airgap-architect`, 12-person lab, no internet | skill files read 3/3 | 3/3 |
| `skip-en-cloud-api` | Python function calling a hosted LLM API | not called 3/3 | — |
| `skip-tr-postgres-backup` | Docker Compose Postgres nightly backup | not called 3/3 | — |
| `skip-en-what-is-air-gap` | "What does air-gapped mean", two sentences | not called 3/3 | — |

All 24 runs pass every grader.

What it shows:

- **Automatic start works in English and Turkish.** A request that names no skill made Claude call it in every run, including a bare sizing question and a request for the carry-in list.
- **Manual start works.** The slash command is expanded before the session, so no Skill tool call appears; the first tool call reads `references/interview.md`.
- **No false starts.** Two unrelated requests and a near miss about the term itself never called the skill.

Caveats:

- One model and three runs per case. Weaker models, or a session with many other skills installed, may pick it less reliably.
- The sessions could not write files or run commands (`allowed_tools`), so the runs stop at the first interview question. The behaviour after that is covered by the scenario runs in `2026-11-22-with-skill.md`.
- The near-miss set is small. A request such as "deploy Open WebUI with Docker on my laptop" (on-premises wording, but online) is not tested yet.
