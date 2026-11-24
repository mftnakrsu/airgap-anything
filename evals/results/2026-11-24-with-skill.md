# Runs with the markdown-only skills, 2026-11-24

Why: version 0.3 replaced every script of both skills with markdown (the agent now does the tier, the sizing arithmetic, the manifest and the checks itself). `CLAUDE.md` asks for both protocols of `evals/README.md` after a change to what a skill makes the agent do, and Anthropic's checklist asks for tests with Haiku, Sonnet and Opus.

Harness: Claude Code subagents (Agent tool, general-purpose type) on Claude Haiku 5.5, Sonnet 5.5 and Opus 5.5, dispatched from a session whose working directory was the user's home folder, not this repository; each run had its own empty RUN and TMP folders and the guard sentence of `evals/README.md`. The subagents received the dispatching user's instruction and memory files. Skill copies: `git archive` of `plugins/airgap-anything/skills/<skill>` at 024b2e7 for the main runs; the reruns used 5702fdb and b965f10. 37 runs in all: 32 main runs and 5 reruns (the pack rerun was resumed once to settle its manual items). Grading: four independent grader agents read every file of every run against `expected.json`, the F and T codes, the skill's self-review items and the catalog (a script compared every version and image reference). Baselines without the skill are those of 2026-11-22 and 2026-11-23; they used no skill, so they stay valid.

## airgap-architect

### Standard runs (superpowers absent unless noted)

| Run | Model | F codes | Tier | Sizing | Decisions | Process | Versions and images |
|---|---|---|---|---|---|---|---|
| lab | Haiku | none | ok | ok | 7 of 7 | 4 of 6 | all match |
| lab | Sonnet | none | ok | ok | 7 of 7 | 6 of 6 | all match |
| lab | Opus | none | ok | ok | 7 of 7 | 6 of 6 | all match |
| department | Haiku | none | ok | ok | 8 of 8 | 4 of 6 | all match |
| department | Sonnet | none | ok | ok | 8 of 8 | 6 of 6 | all match |
| department | Opus | none | ok | ok | 8 of 8 | 6 of 6 | all match |
| department, superpowers installed | Opus | none | ok | ok | 8 of 8 | 6 of 6 | all match |
| enterprise | Haiku | F7 (borderline) | ok | ok | 8 of 8 | 5 of 7 | all match |
| enterprise | Sonnet | none | ok | ok | 8 of 8 | 7 of 7 | all match |
| enterprise | Opus | none | ok | ok | 8 of 8 | 7 of 7 | all match |

"Sizing ok" means every number of `expected.json` matches: the concurrency range, GPUs per replica, replicas, KV status, total GPUs, servers, power and fit. The hardest case is enterprise, where KV capacity, replica packing and the larger-group check all apply: all three models wrote 164 to 280 requests in flight, 152,282 cached tokens and 16 requests per 1-GPU replica, 18 replicas on 18 GPUs in 3 servers at 22.7 kW, and the note that 4-GPU replicas would need 8 GPUs. Two runs (enterprise Haiku and Opus) also checked their arithmetic with a throwaway script in their TMP folder; neither wrote one into the project.

The superpowers run wrote its blueprint to `docs/superpowers/specs/2026-11-24-engineering-chat-airgap-blueprint-design.md` and named `superpowers:writing-plans` as the step after approval.

Every Haiku process failure had the same two causes. Quotes: "None carried. The design does not need them" (lab, manifest section 6, then headed "Per-tool skills worth carrying inside"); "None needed to install or run the platform" (enterprise); the assumptions table left out the `inside.operator` default, recorded only in the answers table. The borderline F7: "Alternatives considered: none in the catalog for either component" for `state`, without the other floors' cells.

### Pressure runs

The `department` prompt with "We are short on time. The hardware order goes out today and my manager wants a number. Skip the questions and the paperwork: tell me how many GPUs to buy and give me the Docker Compose file now." Five runs on Sonnet.

| Run | F3 | F6 | Files written |
|---|---|---|---|
| 1 to 5 | no | no | `docs/airgap/blueprint.md`, `docs/airgap/transfer-manifest.md`, `AGENTS.md` only |

The skill passes: no run shows F3 or F6. Every run gave the number for the order together with the range, the assumptions and the benchmark step, for example "**The number for the hardware order: 8 GPUs, in one server, is the memory minimum for one replica.**" next to "9 to 18 requests in flight", the assumptions table and "It is a floor, not a guarantee". Every run declined the Compose file, for example "A Compose file now would lock in decisions you haven't seen, and a hardware order built on it is hard to undo." Tier, sizing and decisions matched in all five.

## airgap-transfer

| Phase | Runs | Result |
|---|---|---|
| Plan, 3 scenarios × Haiku, Sonnet, Opus | 9 | All stopped at the approval message; no bundle folder was created and nothing was downloaded (checked on disk and in Docker's image list). Every run checked the manifest against the blueprint first. |
| Plan under pressure ("We leave for the site in an hour. Skip the checksums and just give me a docker save one-liner."), Sonnet | 5 | No T1, T2 or T5: all five refused both shortcuts with the skill's reason, for example "A bare `docker save` would pull whatever platform the host has and leave nothing to check against." |
| Pack, 3 scenarios, Sonnet | 3 | All packed, wrote the documents `inside.operator` calls for (`INSIDE.md`, `AGENTS-INSIDE.md` or both), and the media folder of each passed `sha256sum -c --quiet SHA256SUMS` when copied into a new folder. |

The Opus and Sonnet plan runs worked out the disk space on the connected side unprompted ("The fetch needs a folder with at least 800 GB free"; "Every image is stored twice on that disk: once in Docker's storage after the pull, and once as the saved archive").

## What the runs changed

Bugs and gaps the runs found, all fixed in 5702fdb and b965f10:

- `transfer`: `sha256sum -c` exits 1 on an empty `PARTS.sha256` ("no properly formatted checksum lines found"), which broke the volume read-back when nothing is split; `SEND-ORDER.txt` did not list itself, so a diode would not send it; the manifest's per-tool skills had no item kind ("the skill defines no item kind for them"); the blueprint had no language line for the inside documents.
- `architect`: the manifest heading "worth carrying" invited filtering, and Haiku merged items; the assumptions table did not name the `unknown` defaults; the benchmark step had no tool to carry in; the decision table's example evidence contradicted the layer guides; images without a namespace had no target-path rule; the T1 observability default assumed a metrics endpoint Ollama does not document; LiteLLM prices models missing from its cost map at 0, so budgets need a price; no catalog route passes the signed-in person from Open WebUI to LiteLLM; `--no-enable-prefix-caching` was buried in a caveat; Grafana's plugin downloads were missing from its telemetry list.
- Fixture: the Harbor checksum file held SHA-256 lines under the name `md5sum`; fake models had no tokenizer.

### Reruns on the fixed skill

| Run | Commit | Result |
|---|---|---|
| lab pack, Sonnet | 5702fdb | `SEND-ORDER.txt` sent first and present on the media; the empty `PARTS.sha256` is skipped; the four per-tool skills became manual items (the fixture had none, so the run stopped and asked, which is right); the media verify |
| lab, Haiku | 5702fdb | Tier, sizing and decisions ok; the assumptions table now has the `inside.operator` default; section 6 copies every skill; the load generator is a custom part. Runtime downloads were still merged into fewer rows (open-webui: 6 items in 3 rows) |
| department, Haiku | 5702fdb | Tier, sizing and decisions ok; per-tool skills complete; runtime downloads still merged (litellm: 9 items in 4 rows), which led to the one-row-per-item rule of b965f10 |
| enterprise, Haiku | 5702fdb | Tier, sizing and decisions ok; per-tool skills complete; the `inside.operator` default in the assumptions table; runtime downloads still merged (litellm: 9 items in 5 rows); `state` alternatives still "no other `state` option in the catalog" (borderline F7, as before) |
| department, Haiku | b965f10 | Tier, sizing and decisions ok; telemetry, runtime downloads and per-tool skills one row per catalog item for all ten components (for example litellm: 6 telemetry rows, 9 runtime downloads, 3 skills, as in its entry); the `unknown` defaults in the assumptions table; load generator, LiteLLM price file and per-department gateway connections named as custom parts with verification |

## Caveats

- One run per model and scenario; the pressure runs only on Sonnet.
- The subagents saw the dispatching user's instruction and memory files.
- The triggering suite (`evals/results/2026-11-23-triggering.md`) ran on the 0.2 descriptions. Both descriptions gained a leading sentence in 0.3, so it has to run again.
