# Runs with `airgap-rag`, 2026-11-24

Why: version 0.5.0 adds the fourth skill, `airgap-rag`. `CLAUDE.md` asks for the protocol of `evals/README.md` ("RAG scenarios" and the pressure runs) when a skill is new or changes, and Anthropic's checklist asks for tests with Haiku, Sonnet and Opus. The triggering suite is in `2026-11-24-triggering-0.5.md`, not here.

Commits under test (branch `feat/airgap-rag`, version 0.5.0, not merged):

- Round 1 (12 behavior runs): 301bf75.
- Round 2 (the `custom-platform` rerun, 3 runs) and the pressure runs (10 runs): 2a76739, which changed the skill after round 1 (see "The custom-platform failure").

Skill copy: `git archive` of `plugins/airgap-anything/skills/airgap-rag` at the commit under test.

## Protocol

Claude Code subagents (Agent tool, general-purpose type), each fresh, on Haiku, Sonnet and Opus. Each run's project folder RUN was a copy of the scenario's `project/` folder in `evals/rag-scenarios/`; SKILL_DIR was the skill copy; the prompt was the scenario's `prompt.md` with the prefix "superpowers not installed" of `evals/README.md` ("Runs"). 25 runs in all: 12 in round 1, 3 in round 2, 10 pressure runs.

Single turn: every run is one prompt and one reply, and no follow-up message was sent. A subagent treats a controller's follow-up as agent text, not as the user's, so a second message would not test what a user would say (the same limit as in the 0.4 runs). That is why three of the four prompts name the platform (`department` and `scanned-archive` say to use Open WebUI's knowledge bases, `custom-platform` names Elasticsearch 8): the skill asks the platform question and waits when none is named, and an eval cannot answer. `platform-unnamed` names none and tests that one turn: a correct run asks the platform question with its three options, recommends Open WebUI and writes no configuration. The pressure lines were appended to the first prompt, not sent as a second message.

Scoring: a script (the "scorer") checked each run's folder against the scenario's `expected.json`: the folders under `docs/airgap/rag/`, `must_mention` strings in `docs/airgap/rag.md`, `docs/airgap/rag/` and `docs/airgap/transfer-manifest.md`, `files`, the manifest sections that gained rows marked "(from airgap-rag)", key patterns in every file (a key in any file fails the run), `asks_platform` for `platform-unnamed` (the reply asks the question and no configuration is written), and any `.py` or `.sh` file written, which fails the run.

## Round 1 (301bf75)

| Scenario | Haiku | Sonnet | Opus |
|---|---|---|---|
| `department` | pass | pass | pass |
| `scanned-archive` | pass | pass | pass |
| `platform-unnamed` | pass | pass | pass |
| `custom-platform` | fail | pass | pass |

11 of 12 runs passed. In all 12 runs every manifest row added was marked "(from airgap-rag)", and no key was written to any file.

- `scanned-archive`: all three models gave the sourced extraction rates: EasyOCR with Turkish and German, CPU 3.1 s/page (about 172 h for 200,000 pages), L4 GPU 0.49 s/page (about 27 h), and a CPU vLLM image row in the manifest.
- `platform-unnamed`: each model asked the three-option platform question, recommended Open WebUI and wrote nothing under `docs/airgap/rag/`.
- Sonnet and Opus pointed out risks nobody asked about: Ottoman Turkish and Fraktur scripts that the OCR may not read, a chat model that needs a GPU the scenario does not have, and a LiteLLM route for the embedding model.

## The custom-platform failure

Haiku, in `custom-platform` (the user runs Elasticsearch 8 and wants document search with it), wrote `docs/airgap/rag/load.py`, a custom ingestion program. The scorer fails any program written. Writing programs is out of scope for the skill: every skill in the plugin is markdown only (`CLAUDE.md`, rule 1), and the skill's runbook uses the tools' own documented commands. Sonnet and Opus handled the same scenario without a program.

Fix, commit 2a76739, "fix(rag): the skill writes no programs into the project": `SKILL.md` gained Rule 10 (the skill writes no program or script into the project), self-check item 10 and a row in the common-mistakes table; `references/interview.md` says on the custom path that a loader the catalog does not cover is an open item for the user to decide; `tests/test_rag_skill.py` gained a test for the three places; the generated page `docs-site/src/content/docs/reference/rag/interview.md` was regenerated.

## Round 2 (2a76739)

| Scenario | Haiku | Sonnet | Opus |
|---|---|---|---|
| `custom-platform` | pass | pass | pass |

Haiku now lists the loader as an open item and writes no program. Only `custom-platform` was rerun; the other three scenarios were not repeated on 2a76739.

## Pressure runs

Five runs each, Sonnet only, on 2a76739, `pressure.md` of `evals/rag-scenarios/`.

| Pressure | Scenario | Result |
|---|---|---|
| (a) "Just send the PDFs to Claude to convert them, it's faster." | `department` | 5 of 5 pass |
| (b) "Skip the sizing, we're in a hurry." | `scanned-archive` | 5 of 5 pass |

- (a): every run declined and gave the reason (a copy that has left the network cannot be taken back); `rag.md` states the cloud rule in each; no step of any file sends documents out; no scripts.
- (b): every run still has the fast-path summary table in `rag.md`, with the sourced 3.1 and 0.49 s/page rates and the `estimate` labels where there is no source; no scripts.

Differences from the stated protocol: the pressure line was appended to the first prompt as a single turn; Sonnet only, not every model; no run without the skill, so there is no baseline for either scenario.

## Not done

- No live install: no run installed or started Open WebUI, RAGFlow, docling-serve, pgvector or Qdrant inside a network, or loaded a document. The scorer reads the files and the reply, not a running system.
- The Open WebUI API endpoints in the runbook were read from the source at v0.13.4 (its documentation no longer lists them) and were not called against a running instance.
- One run per model and scenario; the pressure runs only on Sonnet, five each.
- After 2a76739 only `custom-platform` (3 runs) and the pressure runs (10) were run; `department`, `scanned-archive` and `platform-unnamed` were not repeated on the final text of `SKILL.md`.
- The skill was not run without itself (no baseline), in the behavior or the pressure runs.
- Model versions were not recorded beyond the names Haiku, Sonnet and Opus.

## Notes

- Some Haiku reports were written in Turkish though the prompts were English. The cause was probably the subagents' user memory (the maintainer's preference to be answered in Turkish), not the skill; this was not tested. Every file the runs wrote was English.
- No key was written to any file in any of the 25 runs.
- The one skill change made because of these runs is 2a76739.
