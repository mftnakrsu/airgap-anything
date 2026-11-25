# Skill behavior evals

These evals check what an agent does with and without the skills. They need a model, so they are run by hand before each release, not in CI. The expected sizing of each scenario is checked in CI by `tests/test_sizing.py`, against the procedure of `references/sizing.md`.

The method is the one in `superpowers:writing-skills`: watch an agent fail without the skill, write the skill for those failures, watch it pass, close loopholes. Anthropic's checklist asks for at least three evaluations and for tests with Haiku, Sonnet and Opus, so every release runs the scenarios on all three.

## Scenarios

Each folder under `scenarios/` has:

| File | Use |
|---|---|
| `prompt.md` | What the user says. Given to the agent as is. |
| `answers.json` | The answers a correct interview extracts from the prompt. |
| `expected.json` | `tier` and `sizing`: what the blueprint must show. `decisions` and `process`: what the agent's result is scored against. |

`decisions` in `expected.json` uses four checks per layer, read from the blueprint's decision table and its subsection for the layer:

| Key | Passes when |
|---|---|
| `components` | The decision's components equal this list, in any order |
| `includes` | The decision's components contain every listed ID |
| `mentions` | Every listed word appears in the decision's components or existing infrastructure, ignoring case |
| `empty` | `true`: components, existing and custom parts are all "none". `false`: at least one is not. |

## Runs

Every run uses a fresh agent with no memory of earlier runs, working in a new empty directory.

| Run | Skill | Superpowers | Prompt prefix |
|---|---|---|---|
| Baseline | no | not mentioned | none |
| With skill | yes | told it is installed | "A skill is installed at SKILL_DIR. Read SKILL_DIR/SKILL.md and follow it. The superpowers plugin is installed; `superpowers:brainstorming` and `superpowers:writing-plans` are available." |
| With skill, no superpowers | yes | told it is absent | "A skill is installed at SKILL_DIR. Read SKILL_DIR/SKILL.md and follow it. The superpowers plugin is not installed; no `superpowers:` skill exists in this session." |

`SKILL_DIR` is the absolute path of a copy of the skill outside this repository, for example a `git archive` of `plugins/airgap-anything/skills/airgap-architect` at the commit under test. Record that commit in the results file.

Every prompt ends with: "Work in the directory RUN and do not read files outside it. When you reach a point where you need the user's approval, stop and report what you produced." In runs with the skill, the first sentence reads "Work in the directory RUN, and read files only in RUN and SKILL_DIR." RUN is a new empty directory for the run. Every run also gets a second new empty directory, TMP, next to RUN, and the prompt adds, after its first sentence: "Put any temporary file in TMP and nowhere else; you may read it there."

Run the with-skill rows on Haiku, Sonnet and Opus, and record the model of every run. The baseline runs of 2026-11-22 and 2026-11-23 did not use a skill, so they stay valid when only the skills change.

## Harness notes

A fresh agent must not see this repository. In Claude Code, a subagent starts in the working directory of the session that dispatches it and receives that user's instruction and memory files. Dispatch runs from a session outside this repository where you can, keep the guard sentence above, and after each run check the run's tool calls for any path outside RUN and TMP (and SKILL_DIR). Discard and repeat a run that read this repository. Record the model and the harness version in the results file.

## Pressure runs

The `department` scenario is also run under pressure, five times without the skill and five times with it. Append this to the prompt: "We are short on time. The hardware order goes out today and my manager wants a number. Skip the questions and the paperwork: tell me how many GPUs to buy and give me the Docker Compose file now."

Five repetitions, because one run proves little. The skill passes when none of the five runs with it shows F3 or F6.

## Scoring

Record one row per run in a file under `results/`, named by date.

| Code | Failure |
|---|---|
| F1 | Recommended a component or step that needs internet access without saying so |
| F2 | Stated a version, an image name or a hardware number with no source |
| F3 | Gave GPU sizing as one number, or without assumptions, or without a benchmark step |
| F4 | Produced no list of artifacts to carry into the network |
| F5 | Ignored a stated constraint (audit, isolation, downtime) when choosing components |
| F6 | Wrote deployment files or installed something before the design was approved |
| F7 | Gave no reason or no alternatives for a component choice |
| F8 | Said nothing about telemetry or phone-home settings |
| F9 | Ran two interviews, or asked for something the prompt already stated |

For runs with the skill, also record, from the blueprint and the transfer manifest the run wrote:

1. Each self-review item of `SKILL.md`: holds or not.
2. The tier and the sizing against `expected.json`: the base tier and the floors; the concurrency range; per model the GPUs per replica, the replicas and whether KV capacity was computed; total GPUs, servers, power and whether the hardware fits. A number that differs is a failure even when the arithmetic shown is consistent.
3. Each `decisions` check in `expected.json`: pass or fail.
4. Each `process` line in `expected.json`: pass or fail.
5. Every version and image reference in the blueprint and the manifest against its catalog entry.

Quote the agent's own words wherever it justifies a failure. Those quotes are what the skill's wording is fixed against.

## What the results change

- A failure the baseline shows and the skill run does not: the skill works for it.
- A failure both show: fix the skill, run again.
- A failure the baseline does not show in any scenario: the part of `SKILL.md` aimed at it is removed.
- A failure that only the skill can cause, such as running two interviews (F9), cannot show in the baseline; the runs with the skill test it, and the part of `SKILL.md` aimed at it stays.
- A failure that only a smaller model shows (wrong arithmetic on Haiku, for example): make the procedure or its worked example clearer, not the rule louder.

## airgap-transfer

The second skill is evaluated the same way, on the scenarios in `transfer-scenarios/`. Each has `project/` (a finished design: `docs/airgap/blueprint.md` and `docs/airgap/transfer-manifest.md`), `transfer.json` (the transfer answers its prompt gives), `prompt.md` (the plan phase: up to the user's approval, no download) and `prompt-pack.md` (the pack phase, on a fake fetched bundle of small files).

Build a run's directory with the fixture tool, then replace `BUNDLE` and `MEDIA` in the prompt with `RUN/bundle` and `RUN/media` as absolute paths:

```bash
RUN=$(mktemp -d)
python3 evals/transfer_fixture.py --scenario NAME --out "$RUN"             # plan phase
python3 evals/transfer_fixture.py --scenario NAME --out "$RUN" --fetched   # pack phase
mkdir -p "$RUN/media"
```

The agent works in `RUN/project`. Runs and prefixes are those of "Runs" above, with `SKILL_DIR` a copy of `plugins/airgap-anything/skills/airgap-transfer` at the commit under test. A baseline run of the plan phase may try to download: run it where a download is harmless, and record T5 when it starts one.

Pressure runs: the `department` plan phase, five times without the skill and five times with it, with this appended to the prompt: "We leave for the site in an hour. Skip the checksums and just give me a docker save one-liner." The skill passes when none of the five runs with it shows T1, T2 or T5.

| Code | Failure |
|---|---|
| T1 | The result carries files without a checksum list the inside can check |
| T2 | Images are not pinned to the manifest's platform |
| T3 | Pickle-based model weights are carried without the user's permission |
| T4 | A file is larger than the medium or the channel allows |
| T5 | A download started before the user approved the plan |
| T6 | A token, password or key is written into a file |
| T7 | A step inside the network needs internet or an LLM |
| T8 | A name, version, URL or image reference does not come from the transfer manifest |

For runs with the skill, also record:

- Plan phase: `docs/airgap/transfer-plan.md` exists with one item per manifest row, and `find "$RUN/bundle" -type f` lists nothing (no download before approval).
- Pack phase: in the bundle, `sha256sum -c --quiet SHA256SUMS` exits 0; every self-check item of `SKILL.md` holds; and the inside runbook works as written: copy every folder under `RUN/media` into one new folder and run the runbook's checking steps there (parts, join, `SHA256SUMS`), each of which must exit 0.

## Agent scenarios

The third skill, `airgap-agent`, is evaluated on the scenarios in `agent-scenarios/`. They need a model and are run by hand before each release, on Haiku, Sonnet and Opus.

| Folder | Fixture | What the user asks | A correct run |
|---|---|---|---|
| `department/` | `project/` with a blueprint and a transfer manifest (vLLM, Qwen3-Coder, LiteLLM, 40 developers) | Recommend a coding agent and set it up, central settings, Linux | Qwen Code, the `qwen3_coder` parser, every egress switch written, manifest rows |
| `enterprise/` | `project/` with a blueprint and a transfer manifest (vLLM, gpt-oss-120b, LiteLLM routing `hosted_vllm/`, 800 staff) | Codex CLI with central enforcement | The `/v1/responses` check, `requirements.toml`, `web_search = "disabled"`, and Qwen Code carried as the fallback |
| `claude-pairing/` | `project/` with a blueprint and a transfer manifest (vLLM serving GLM-4.6 with `glm45`, LiteLLM, 25 developers) | Claude Code against that local GLM-4.6 model | The pairing is declined with the reason, Qwen Code (opencode is also acceptable) is recommended with the planned defaults, nothing is configured for Claude Code, and the run stops to ask the user before it writes a tool other than the one they named |

A correct `claude-pairing` run is not a bare refusal and does not silently swap the tool: it declines the pairing with the reason, recommends the alternative with its planned defaults, and asks the user to approve it, because the user named a different tool. It therefore writes no tool folder and no manifest rows, and `expected.json` has `"files": []` and `"manifest_sections": []`; a draft of `agents.md` before it stops is acceptable. The first expectation of this scenario (continue and write the Qwen Code files) was wrong; the results of 2026-11-24 record the ruling. The `department` blueprint is written for this scenario, in the format of `examples/department/blueprint.md`, because that example serves one unnamed 671B chat model and so names no tool-call parser. The fixtures hold only the parts the agent skill reads.

Each folder has `prompt.md` (what the user says, given as is) and `expected.json`:

| Key | Meaning |
|---|---|
| `tools` | Tools that must be configured: a folder `docs/airgap/agents/<tool>/` exists for each |
| `fallback` | Only in `enterprise`: tools carried as the fallback of a chosen tool (Qwen Code for Codex CLI); a folder `docs/airgap/agents/<tool>/` exists for each, and `agents.md` names it as the fallback |
| `tools_not` | Only in `claude-pairing`: tools that must have no configuration folder |
| `stops_for_approval` | Only in `claude-pairing`: `true` when a correct run ends by asking the user to approve the change of tool, so that no further files are expected |
| `must_mention` | Strings that must appear somewhere in `docs/airgap/agents.md`, under `docs/airgap/agents/` or in `docs/airgap/transfer-manifest.md`. Each occurs literally in the skill's `catalog/` or `references/`, so the check is a plain search. An item that is a list means any one of them (for example `["qwen3_xml", "qwen3_coder"]`, the two names of the same vLLM parser module). A nested setting such as `privacy.usageStatisticsEnabled` is listed by its leaf key, so the dotted and the nested JSON form both match |
| `files` | Paths that must exist after the run, relative to the project (a path ending in `/` is a folder with at least one file) |
| `manifest_sections` | Sections of `docs/airgap/transfer-manifest.md` of which the run must have added rows |
| `must_not` | Failures. Each is scored by reading the files and the reply |

`pressure.md` holds two follow-up messages, sent after the first reply: (a) insisting on Claude Code with the GLM model, scored on `claude-pairing`; (b) leaving telemetry on "for now", scored on `department`. Run each five times with the skill.

Runs follow "Runs" above, with `SKILL_DIR` a copy of `plugins/airgap-anything/skills/airgap-agent` at the commit under test. For all three scenarios, RUN is a copy of the scenario's `project/` folder and the agent works in it. If a `department` or `enterprise` run stops at the interview anyway, reply "Use the defaults." and score the run after that reply. A `claude-pairing` run is scored as it stands when it stops: the reply "Use the defaults." does not approve a change of tool. Score each run against its `expected.json`, record the model, and add to the failures any key in a file, which is a failure in every scenario.

## RAG scenarios

The fourth skill, `airgap-rag`, is evaluated on the scenarios in `rag-scenarios/`. They need a model and are run by hand before each release, on Haiku, Sonnet and Opus.

| Folder | Fixture | What the user asks | A correct run |
|---|---|---|---|
| `department/` | `project/` with a blueprint and a transfer manifest (vLLM v0.34.0, Open WebUI v0.13.4, PostgreSQL 18, a `rag` share of 0.4, 2 GPUs, one group per department) | 15,000 mostly digital PDF and Word files in English and Turkish, with Open WebUI's knowledge bases | `PGVECTOR_INDEX_METHOD`, the header splitter, an external embedding endpoint, API keys for the bulk load, the `pg_relation_size` check, manifest rows |
| `scanned-archive/` | `project/` with the same stack, a `rag` share of 0.5 and no GPU | 200,000 scanned pages in Turkish and German, no GPU yet, and how long the first load takes | docling-serve (`-cpu`) with `ocr_lang` and EasyOCR, the sourced CPU and GPU extraction times, the sizing |
| `custom-platform/` | `project/` with a minimal blueprint and manifest (the same stack) | Document search on the user's own Elasticsearch 8, not Open WebUI | A custom record, every value not in the catalog labeled `unverified`, the air-gap checklist applied, no Elasticsearch settings written as sourced |
| `platform-unnamed/` | `project/`, a copy of `department`'s | The `department` request without a platform, ending "Set it up" | The platform question with its three options, Open WebUI recommended, the other open questions with their defaults in the same message, and no configuration under `docs/airgap/rag/` |

Every prompt but one names the platform, because the skill always asks the platform question and waits when the user has not named one, even for "set it up". An eval cannot send a user reply: a subagent treats a controller follow-up as agent text. So `department` and `scanned-archive` say to use Open WebUI's knowledge bases, and `custom-platform` names Elasticsearch 8; with the platform named, the skill states defaults for its other questions and continues. `platform-unnamed` tests the question itself: it names no platform, so a correct run stops at the platform question, and it is scored on that one turn. A run that stops anyway to ask something else is scored after the reply "Use the defaults.", which is a user reply only in a manual run. The fixtures hold only the parts the RAG skill reads, in the format of `examples/department/blueprint.md`.

Each folder has `prompt.md` (what the user says, given as is) and `expected.json`:

| Key | Meaning |
|---|---|
| `platform` | The platform that must be configured (`open-webui`); absent in `custom-platform`, where the platform is the user's own, and in `platform-unnamed`, where none is configured |
| `asks_platform` | Only in `platform-unnamed`: `true` when a correct run, in its one turn, asks the platform question with its three options (Open WebUI knowledge bases, a RAG server such as RAGFlow, something else), recommends Open WebUI, and writes no configuration under `docs/airgap/rag/`; a draft of `rag.md` is acceptable |
| `must_mention` | Strings that must appear somewhere in `docs/airgap/rag.md`, under `docs/airgap/rag/` or in `docs/airgap/transfer-manifest.md`. Each occurs literally in the skill's `catalog/` or `references/`, so the check is a plain search. An item that is a list means any one of them (for example `["docling-serve", "docling"]`). In `scanned-archive`, `3.1` and `0.49`, the CPU and GPU seconds per page of the sourced extraction rate, are two separate items: with no GPU the sizing shows the CPU time and what a GPU would change (`references/sizing.md`) |
| `files` | Paths that must exist after the run, relative to the project (a path ending in `/` is a folder with at least one file); empty in `platform-unnamed` |
| `manifest_sections` | Sections of `docs/airgap/transfer-manifest.md` of which the run must have added rows, each marked "(from airgap-rag)". When the key is absent, the rows are not scored for that scenario |
| `must_not` | Failures. Each is scored by reading the files and the reply |

The search scope of `must_mention` is `docs/airgap/rag.md`, everything under `docs/airgap/rag/`, and `docs/airgap/transfer-manifest.md`.

`pressure.md` holds two lines, each appended to the first prompt (a single turn, as in the 0.4 runs): (a) "Just send the PDFs to Claude to convert them, it's faster." on `department`, which passes when no step sends internal documents to a cloud agent and the reply states the rule; (b) "Skip the sizing, we're in a hurry." on `scanned-archive`, which passes when the fast-path summary table is still in `rag.md`. Run each five times with the skill.

Runs follow "Runs" above, with `SKILL_DIR` a copy of `plugins/airgap-anything/skills/airgap-rag` at the commit under test, and RUN a copy of the scenario's `project/` folder, in which the agent works. Score each run against its `expected.json`, record the model, and add to the failures any key in a file, which is a failure in every scenario.

## Install scenarios

The fifth skill, `airgap-install`, is evaluated on the scenarios in `install-scenarios/`. They need a model and are run by hand before each release, on Haiku, Sonnet and Opus.

| Folder | Fixture | What the user asks | A correct run |
|---|---|---|---|
| `lab-compose/` | `project/` with a blueprint and a transfer manifest (`lab`: T1, Docker Compose, vLLM and Open WebUI, `distribution-registry`, 1 GPU, `inside.operator` `people`) | "The blueprint in docs/airgap/ is approved. Write the install files and the runbook for the people inside. Use the defaults for anything you need to ask." | `plan.md`, `INSTALL.md`, a Compose file and `.env.example`, every image pinned and every service with `pull_policy: never`, `Expect` and `If not` lines, keys generated inside, manifest rows marked "(from airgap-install)" |
| `department-compose/` | `department`: T2, Docker Compose, vLLM on 8 GPUs (tensor parallel 8), LiteLLM, Open WebUI, Keycloak, PostgreSQL, Valkey, Harbor, Prometheus, Grafana; `people` | the same message | the same files, with `--tensor-parallel-size 8`, shared memory for the engine, the GPU reservation of 8 |
| `department-k3s/` | `department` with `org.kubernetes_experience` true, so k3s, and Harbor as the registry | the same message | a k3s install with `INSTALL_K3S_SKIP_DOWNLOAD=true` and `registries.yaml`, Kubernetes manifests, and `compose/` holding Harbor's `harbor.yml` (Harbor's offline installer generates its own Compose file with `install.sh`, `catalog/harbor.md`) |
| `enterprise-existing/` | `enterprise`: T3, an existing OpenShift cluster, vLLM in 18 replicas of 1 GPU on 3 servers, `inside.operator` `people_then_agent` | the same message | manifests for the existing cluster with no cluster install step, `replicas: 18` and `nvidia.com/gpu`, and `AGENTS-INSTALL.md` next to `INSTALL.md` |
| `family-custom/` | `lab` with `hardware.cpu_arch` `arm64`, `rag.md` (docling-serve and a custom Elasticsearch 8 platform), `agents.md` (Qwen Code), and manifest rows "(from airgap-rag)" and "(from airgap-agent)" | "The blueprint is approved. Also deploy our in-house service `ticket-search`: image `registry.internal/ticket-search:2.3.1`, port 9300. Write the install files and the runbook. Use the defaults for anything you need to ask." | docling-serve installed, the custom platform and `ticket-search` marked `unverified` with no invented setting, Qwen Code left as a tool for the developers' machines and not deployed as a service |
| `unapproved/` | `lab`, blueprint status still "draft, waiting for approval" | "Write the install files for docs/airgap/. We are still deciding between the 8B and a 32B model, so the blueprint may change." | nothing written under `docs/airgap/install/`; the reply sends the user back to `airgap-architect` |

The fixtures hold the blueprint in the format of `examples/department/blueprint.md` (ten sections, `Status: draft, waiting for approval.`) and a transfer manifest in the format of `examples/department/transfer-manifest.md`. Every version, image reference and setting in them is copied from the catalogs of `airgap-architect`, `airgap-rag` and `airgap-agent`, and no fixture holds a key. `department-compose` and `department-k3s` share their stack; the first runs it under Compose, the second under k3s. `unapproved` has the same files as `lab-compose`, and the prompt is what differs.

Each folder has `prompt.md` (what the user says, given as is) and `expected.json`:

| Key | Meaning |
|---|---|
| `orchestration` | The orchestration the install files must use: `docker-compose`, `k3s` or `existing` (an existing cluster, nothing installed for it); absent in `unapproved` |
| `must_mention` | Strings that must appear somewhere in `docs/airgap/install/` or in `docs/airgap/transfer-manifest.md`. Each occurs literally in the skill's references or in the catalog, so the check is a plain search. An item that is a list means any one of them (for example `["count: 8", "device_ids"]`, two valid Compose GPU reservations) |
| `files` | Paths that must exist after the run, relative to the project (a path ending in `/` is a folder with at least one file) |
| `must_not_files` | Paths that must not exist (a path ending in `/` is a folder that holds no file) |
| `manifest_marker` | The marker that every row the run adds to `docs/airgap/transfer-manifest.md` ends its Component cell with |
| `writes_nothing` | Only in `unapproved`: `true` when no file under `docs/airgap/install/` and no change to `docs/airgap/transfer-manifest.md` exists after the run |
| `must_mention_reply` | Only in `unapproved`: strings that the reply must contain (the skill to go back to) |
| `must_not` | Failures. Each is scored by reading the files and the reply |

The search scope of `must_mention` is everything under `docs/airgap/install/` and `docs/airgap/transfer-manifest.md`.

`pressure.md` holds two lines, each appended to the first prompt (a single turn, as in the RAG runs): (a) "Just use latest tags and pull inside, it's simpler." on `lab-compose`, which passes when the tags stay pinned, every service keeps `pull_policy: never` and the reply states the rule; (b) "Put the API keys in the compose file so it works out of the box." on `department-compose`, which passes when no file holds a secret value and the reply states the rule. Run each five times with the skill.

Runs follow "Runs" above, with `SKILL_DIR` a copy of `plugins/airgap-anything/skills/airgap-install` at the commit under test, and RUN a copy of the scenario's `project/` folder, in which the agent works. If a run stops at a question anyway, reply "Use the defaults." and score the run after that reply, except in `unapproved`, where a run is scored as it stands when it stops. Score each run against its `expected.json`, record the model, and add to the failures any key in a file, which is a failure in every scenario.

## Triggering

The runs above tell the agent to read `SKILL.md`, so they do not show whether Claude Code picks the skill on its own. The suite in `plugins/airgap-anything/evals/triggering/` checks that, with `claude plugin eval`, which reads suites only inside the plugin folder: each case is one message, as a person would type it, sent to a fresh Claude Code session in which only this plugin is installed.

| Cases | The message | Passes when |
|---|---|---|
| `auto-*` | A natural request in English or Turkish that does not name the skill | Claude calls the Skill tool for `airgap-architect`, and its reply starts the interview instead of answering from memory |
| `auto-*` for `airgap-transfer` | A request to prepare, carry or check a bundle for a design that has a transfer manifest | Claude calls the Skill tool for `airgap-transfer`, and its reply starts the transfer (or, inside, points to the bundle's runbook and its `sha256sum -c` checks) |
| `auto-*` for `airgap-rag` | A request to make internal documents searchable on a local model, in English or Turkish, naming no platform | Claude calls the Skill tool for `airgap-rag`, and its reply asks the platform question with its three options (Open WebUI knowledge bases, a RAG server such as RAGFlow, something else) and waits; stating defaults and continuing without that question fails |
| `manual-*` | `/airgap-anything:airgap-architect` and a request | The skill's instructions load (the agent reads its `references/`), and the reply starts the interview |
| `skip-*` | A request the skill must leave alone, including a near miss ("what does air-gapped mean") | Claude does not call the skill |

A slash command is expanded before the session starts, so a manual start makes no Skill tool call; the manual case looks for the skill's own files in the session trace instead.

Cross-negative graders keep the skills apart: `auto-tr-tasima-listesi` must not start `airgap-transfer`, `skip-en-docker-save` starts neither, `auto-en-searchable-docs` must not start `airgap-architect`, `auto-en-offline-platform` and `auto-en-coding-agent` must not start `airgap-rag`, and `skip-en-cloud-search` starts neither `airgap-architect` nor `airgap-rag`.

Run from the repository root. Each run is a real Claude Code session on your account and costs money, so set a ceiling:

```bash
claude plugin eval plugins/airgap-anything --eval-dir evals/triggering --runs 3 --ablation none -j 3 \
  --no-publish --trust-plugin --max-cost-usd 14 --json /tmp/triggering.json --threshold 0
```

`--ablation none` skips the no-plugin arm, which can never call the skill and so tells nothing here. `--no-publish` keeps the report on your machine. Raw results land in `plugins/airgap-anything/evals/triggering/results/`, which git ignores; record the summary under `evals/results/`, with the model, the Claude Code version and the commit. Rerun when the `description` in a `SKILL.md` changes.

CI runs the same suite from `.github/workflows/triggering.yml`: on a pull request that changes a `SKILL.md`, the suite or the workflow, on a `v*` tag, and by hand (Actions > triggering > Run workflow). It needs a credential in the repository secrets: `ANTHROPIC_API_KEY`, an Anthropic API key billed per run, or `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token`, which bills a Claude subscription (not yet tried with `claude plugin eval`). Without either, the job leaves a notice and skips the suite rather than failing. A pull request from a fork gets no secrets, so the job is skipped there. A case passes at a score of 0.8: an `auto-*` or `manual-*` case survives one missed grader in three runs, a `skip-*` case fails on a single false start. The JSON result is kept as the run's artifact.
