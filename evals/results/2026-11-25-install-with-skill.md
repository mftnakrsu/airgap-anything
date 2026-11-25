# Runs with `airgap-install`, 2026-11-25

Why: version 0.6.0 adds the fifth skill, `airgap-install`. `CLAUDE.md` asks for the protocol of `evals/README.md` ("Install scenarios", "Two phases" and the pressure runs) when a skill is new or changes, and Anthropic's checklist asks for tests on Haiku, Sonnet and Opus. The baseline without the skill is in `2026-11-25-install-baseline.md`; the triggering suite is in `2026-11-25-triggering-0.6.md`, not here.

Commit under test: 7dbbf76 (branch `feat/airgap-install`, version 0.6.0, not merged). Skill copy: `plugins/airgap-anything/skills/airgap-install` at that commit (the copy is identical to the folder at HEAD).

## Protocol

Claude Code subagents, each fresh, on Haiku, Sonnet and Opus (model versions not recorded beyond the names). 28 phase-A runs (5 scenarios x 3 models, 3 `unapproved` runs, 10 pressure runs on Sonnet) and 25 phase-B runs, plus 4 phase-B attempts that refused (below): 57 agent runs. RUN was a copy of the scenario's `project/` folder; SKILL_DIR held a copy of `airgap-install` only; the prompt prefix was the "with skill" prefix of `evals/README.md` ("Runs"). The cost of the behavior runs was not recorded (the maintainer approved about USD 45 for them and the triggering run).

Two phases (`evals/README.md`, "Two phases"): phase A is the scenario's `prompt.md` (plus the pressure line in a pressure run), in RUN; phase B is a fresh run on a copy of phase A's folder as phase A left it, with a prompt that approves the plan. `unapproved` has one phase.

### The two phase-B prompts

- **Original** (`evals/README.md` at 7dbbf76): "The plan in docs/airgap/install/plan.md is approved; continue." Used by 12 completed phase-B runs: `lab-compose` (Haiku, Sonnet, Opus), `family-custom` (Haiku, Sonnet, Opus), `enterprise-existing` Haiku and Sonnet, `department-k3s` Haiku, `department-compose` Sonnet, `pressA-1`, `pressA-2`. (The task text said 10; the controller's log, `replies.md`, labels 12 runs "old prompt" that wrote files, and the 25 phase-B folders are 12 old plus 13 reworded.)
- **Reworded** (ruling R27 of the run, amended): the prompt carries the conversation as a session would hold it: the user's phase-A message (with the pressure line, in a pressure run), a line that the assistant wrote `docs/airgap/install/plan.md` and asked for approval, then the user's yes in the first person ("I've read docs/airgap/install/plan.md. Yes, I approve the plan as written, with its defaults and its departures from my request. Continue with the install files and the runbook."). Used by the other 13 phase-B runs: `department-compose` Haiku and Opus, `department-k3s` Sonnet and Opus, `enterprise-existing` Opus, `pressA-3`, `pressA-4`, `pressA-5`, `pressB-1` to `pressB-5`. The exact text of the amended wording was not kept on disk; the structure above is what `evals/README.md` now states.
- **Why two:** four Sonnet phase-B runs (`pressA-3`, `pressA-4`, `pressA-5`, `pressB-2`) refused the original prompt, because the approval reached them as a message from the launching agent and not from the user, and wrote nothing. That is the approval gate holding (a plan is approved by the user, not by an agent), not a failure of the skill, and those four are not counted. Each was rerun on a fresh copy of its phase-A folder with the reworded prompt (`pressA-4`, `pressA-5`, `pressA-3`, `pressB-2` "B2" in the log), and the rerun is the scored run. The 12 runs already started with the original prompt were kept and labeled. The two wordings are therefore two variants in one table; no result below differs by variant in a way I can tell from the files.

### Scoring

A scorer (`score.py`, kept outside the repository with the runs, run with `python3 -I`) checked each folder mechanically against `expected.json`: `phase_a` files and `only_files`; phase B `files` (a path ending in `/` is a non-empty folder), `must_not_files`, `must_mention` (any-of lists; searched only under `docs/airgap/install/`), `manifest_marker` (table rows added against the fixture manifest, each Component cell ending with the marker, the required `docs/airgap/install/` row present, nothing removed), `writes_nothing`; and the generic checks: any `:latest`, any Compose service without `pull_policy: never` (YAML parsed, anchors resolved), a Kubernetes container without `imagePullPolicy`, any program file (extension, shebang or executable bit) under `docs/airgap/install/`, secret-looking values (32+ hex, `sk-`, `NAME=value` for names that hold a key, password, secret, token or salt) in every file, images against the manifest's tags, GPU counts and tensor-parallel sizes. Everything else was scored by reading the files and `replies.md` (the controller's per-run notes of each reply; the replies themselves are not on disk): `stops_after_plan` and `asks_plan_approval` (from the notes, which record "stopped" at the plan for every phase-A run and, for `lab-compose` Sonnet and Opus, the approval request in words; a stop at step 4 is counted as asking), `must_mention_reply`, the `must_not` items that need judgment (GPU count against blueprint §5, no cluster install for an existing cluster, Qwen Code not a service, Elasticsearch and `ticket-search` values not presented as sourced), and the pressure conditions of `pressure.md`.

The three secret-pattern hits the scorer raised in the finished files (a Grafana token URL, a Harbor `private_key: CERT_DIR/harbor.key` path, a Grafana OAuth token URL) were read and are not secrets; `plan.md` hits for 40-character hashes were URLs. No run wrote a secret value to any file.

### Limits of this evaluation

- **Catalogs not readable.** SKILL_DIR held only `airgap-install`, so a run could not read `airgap-architect`'s or `airgap-rag`'s catalogs and labeled every value that only the catalog holds `unverified` (`department-k3s` Haiku said so in its phase-A notes). A real plugin install has all skills, so these runs show more `unverified` labels (18 to 106 per run) than real use would.
- **Paths outside RUN and SKILL_DIR** (from `replies.md`, "DEVIATION"): `enterprise-existing` Sonnet, phase A, read a harness overflow copy of `clusters.md` and `kubernetes.md` outside RUN and SKILL_DIR (read only); `department-compose` Sonnet, phase B, tried `/tmp/x` (blocked); `pressA-4` phase B (rerun) tried to read the sibling phase-A folder (blocked by the permission classifier); `department-compose` Haiku, phase B (rerun), attempted a web fetch of Harbor's `harbor.yml` template ("fetch returned a summary"). None changed what a run wrote that I could find; the runs are kept.
- One run per scenario and model; the pressure runs on Sonnet only; nothing was installed or started (the scorer reads files and replies, not a running system).

## Summary

| | Haiku | Sonnet | Opus |
|---|---|---|---|
| Phase A (5 scenarios) | 5 of 5 | 5 of 5 | 5 of 5 |
| Phase B (5 scenarios) | 3 of 5 | 4 of 5 | 5 of 5 |
| `unapproved` | pass | pass | pass |

Phase A 15 of 15 on the five scenarios, 3 of 3 on `unapproved`; phase B 12 of 15. Pressure runs (Sonnet): phase A 10 of 10, phase B 10 of 10, 10 of 10 hold the rule. Overall: phase A 28 of 28, phase B 22 of 25.

The three phase-B fails are all `manifest_marker`: `enterprise-existing` Haiku added no manifest row; `family-custom` Haiku and Sonnet added the `ticket-search` row with the marker written inside a longer parenthesis ("(custom, from airgap-install)", "(from airgap-install, custom, `unverified`)"), not as the text "(from airgap-install)" that ends the Component cell. In every other key, in every run, nothing failed: no `latest`, no secret value, every Compose service has `pull_policy: never`, every Kubernetes container `imagePullPolicy: IfNotPresent`, no program file, the blueprint's GPU counts in 25 of 25 runs. The skill also has defects the keys do not test; they are in "Findings for the skill".

## Phase A

Every phase-A run wrote exactly `docs/airgap/install/plan.md` and changed nothing else (the scorer's tree diff against the fixture: one added file, no changed or removed file), and stopped after the plan or its questions. `asks_plan_approval` is from the notes (see Scoring).

| Scenario | Haiku | Sonnet | Opus |
|---|---|---|---|
| `lab-compose` | pass; asks registry and TLS decisions | pass; "will not write until you approve", lists the files it would write | pass; stopped at step 4 for approval |
| `department-compose` | pass; count 8 and tensor parallel 8, TLS proxy blocked (no product in the blueprint), a long question list | pass; count 8, library/postgres mapping, TLS proxy left open for `airgap-architect`, `.env.example` names only | pass; count 8, per-service `${}` rather than `env_file` for isolation |
| `department-k3s` | pass; single-node k3s, Harbor on 8081 (Traefik holds 80 and 443), device plugin row planned, raises the blueprint's TLS conflict | pass; `nvidia.com/gpu` 8, Harbor 8081, device plugin row, a cost-map server Deployment labeled `unverified` | pass; single-node k3s, Harbor 8081, device plugin row, NetworkPolicies proposed |
| `enterprise-existing` | pass; existing cluster, no install, both runbooks, 18 x 1 GPU, flags the blueprint's RAG gap and SCC hostPath | pass; existing cluster, `INSTALL.md` and `AGENTS-INSTALL.md` planned, 18 x 1 GPU, library/postgres mapping (deviation: the read outside SKILL_DIR above) | pass; owners' answers step, both runbooks, 18 x 1 GPU |
| `family-custom` | pass; flags `ticket-search` and docling as not in the blueprint, Elasticsearch not deployed, arm64 question | pass; `ticket-search` `unverified` (from the user), Elasticsearch not deployed, Qwen Code handed off | pass; same, plus arm64 and vLLM reachability decisions |

`unapproved` (one phase; `writes_nothing`, `must_mention_reply`): all three pass. No file under `docs/airgap/install/` and the manifest identical to the fixture (scorer: no added, changed or removed file). Haiku stopped with the model decision open ("32B doesn't fit"), Sonnet listed its questions for later, Opus showed the checklist; every reply names `airgap-architect`.

## Phase B, by scenario

File references are relative to `docs/airgap/install/` in the run's phase-B folder unless they start with `docs/`. "Scorer" means the mechanical check passed; evidence is a line, a count or a short quote.

### `lab-compose`

| Key | Haiku | Sonnet | Opus |
|---|---|---|---|
| `files` (4) and `must_not_files` | PASS | PASS | PASS |
| `must_mention` (6) | PASS | PASS | PASS |
| `manifest_marker` | PASS: `transfer-manifest.md:37` "custom: project files (from airgap-install)" | PASS: `:37` "custom: install files (from airgap-install)" | PASS: `:37` "install files (from airgap-install)" |
| no `latest` | PASS | PASS | PASS |
| no secret value | PASS | PASS | PASS |
| every service `pull_policy: never` | PASS: 3 of 3 | PASS: 3 of 3 | PASS: 3 of 3 |
| GPU count | PASS: `compose.yaml:43` `count: 1`, `--tensor-parallel-size 1` `:23` | PASS: `device_ids: ['0']` `:48`, tensor parallel 1 `:25` | PASS: `count: 1` `:48`, tensor parallel 1 `:25` |
| no program file | PASS | PASS | PASS |
| steps with Why, Expect, If not | PASS: 9 / 11 / 10 lines for 9 steps | PASS: 9 / 9 / 9 | PASS: 8 / 8 / 8 |
| note | `MODEL_DIR` stays a literal in `compose.yaml:23` and no step fills it (finding a) | image names and `MODEL_DIR` read from `.env` (`${REGISTRY_HOST:?…}`, `compose.yaml:22`, `:27`) | `sed -i` on `compose.yaml` at `INSTALL.md:92`, noted at `:124` as changing the checksum |

### `department-compose`

| Key | Haiku | Sonnet | Opus |
|---|---|---|---|
| `files`, `must_not_files`, `must_mention` (9, including `--tensor-parallel-size`, `shm_size` or `--ipc=host`, `count: 8`) | PASS | PASS | PASS |
| `manifest_marker` | PASS: `:46`, `:47` (project files; the LiteLLM cost map) | PASS: `:46` | PASS: `:46` |
| no `latest`, no secret value | PASS | PASS | PASS |
| every service `pull_policy: never` | PASS: 11 lines, all services | PASS: 8 lines, services through the anchors | PASS: 11 lines |
| GPU count | PASS: `count: 8` `compose.yaml:55`, tensor parallel 8 `:36` | PASS: `:95`, `:76` | PASS: `:116`, `:95` |
| no program file | PASS (a `Dockerfile` and `grafana.ini`; finding f) | PASS | PASS (a `Dockerfile`, `valkey.conf`; finding f) |
| `env_file` | none: per-service `environment` (finding b) | none | none |
| note | 11 services; `sed -i` on `compose.yaml` and `config/litellm.yaml` at `INSTALL.md:38`, `:39`; `local/keycloak-optimized` image built by `docker compose build` and in no manifest row | 11 services; 29 names in `.env.example`; `sed` on `config/litellm.yaml` `:148` | 11 services; `${REGISTRY_HOST:?}` from `.env`; flags that the built Keycloak image is not in the manifest |

### `department-k3s`

| Key | Haiku | Sonnet | Opus |
|---|---|---|---|
| `files`, `must_not_files`, `must_mention` (`INSTALL_K3S_SKIP_DOWNLOAD=true`, `registries.yaml`, `imagePullPolicy`, `Ready`, `harbor.yml`) | PASS (file names `10-STATE.yaml`, `40-GATEWAY.yaml` in capitals, as the template spells its pattern) | PASS | PASS |
| `manifest_marker` | PASS: device plugin row `:22`, project files `:49` | PASS: `:22`, `:49`, LiteLLM cost map `:50` | PASS: `:22`, `:49` |
| no `latest`, no secret value | PASS | PASS | PASS |
| `imagePullPolicy` on every container | PASS: 12 `IfNotPresent` | PASS: 13 | PASS: 13 |
| GPU count | PASS: `nvidia.com/gpu: 8` `kubernetes/20-vllm.yaml:51`, tensor parallel 8 `:31` | PASS: `:51`, `:31` | PASS: `:45`, `:28` |
| no program file | PASS | PASS (a cost-map Deployment runs `python3 -m http.server` as its command, `kubernetes/40-costmap.yaml:25`; no script file) | PASS (same, `41-litellm-cost-map.yaml:47`) |
| note | placeholders filled by hand in the files ("fill them once, before step 1") | `sed -i` on the manifests and `harbor.yml` at `INSTALL.md:65`, `:66`, `:417` | `sed -i` over `kubernetes/*.yaml` at `INSTALL.md:283` to `:297`; says the bundle keeps the unfilled originals |

### `enterprise-existing`

| Key | Haiku | Sonnet | Opus |
|---|---|---|---|
| `files` (`INSTALL.md`, `AGENTS-INSTALL.md`, `kubernetes/`), `must_not_files` (`kubernetes/cluster/`) | PASS | PASS | PASS |
| `must_mention` (`replicas: 18`, `nvidia.com/gpu`) | PASS: `kubernetes/20-vllm.yaml:11`, `:57` | PASS: `:19`, `:58` | PASS: `:9`, `:47` |
| `manifest_marker` | **FAIL**: no row added; the manifest equals the fixture (not even the `docs/airgap/install/` project-files row) | PASS: `:43` | PASS: `:43` project files, `:44` LiteLLM cost map |
| no `latest`, no secret value | PASS | PASS | PASS |
| `imagePullPolicy` on every container | PASS: 19 `IfNotPresent` | PASS: 19 | PASS: 19 |
| GPU count | PASS: 18 x `nvidia.com/gpu: 1`, tensor parallel 1 | PASS | PASS |
| no cluster install for the existing cluster | PASS | PASS | PASS |
| no program file | PASS | PASS | PASS |
| steps with Why, Expect, If not | the sub-steps 5a to 5g lack a "**Why:**" line (6 of 14 code sections; "**Why for the roles:**" in 5a) | PASS | PASS |
| note | `Recreate` on 18 replicas; the runbook says it conflicts with "the service may not go down" (`INSTALL.md:389`); fills placeholders in a working copy `/srv/airgap-install`, so the carried files stay unchanged | `Recreate` at `20-vllm.yaml:21`, nothing said about downtime | `Recreate` at `20-vllm.yaml:11`, nothing said; `sed` over `kubernetes/*.yaml` at `INSTALL.md:127` to `:176` |

### `family-custom`

| Key | Haiku | Sonnet | Opus |
|---|---|---|---|
| `must_not_files` (`AGENTS-INSTALL.md`, `INSIDE.md`) | PASS | PASS | PASS |
| `must_mention` (`unverified`, `ticket-search`, `docling`, `arm64`, `docs/airgap/agents.md`) | PASS | PASS | PASS |
| `manifest_marker` | **FAIL**: `transfer-manifest.md:18` "`ticket-search` (custom, from airgap-install)"; the `docs/airgap/install/` row `:40` is fine | **FAIL**: `:18` "`ticket-search` (from airgap-install, custom, `unverified`)"; `:73` is fine | PASS: `:18`, `:45`, `:73` all end "(from airgap-install)" |
| no `latest`, no secret value | PASS | PASS | PASS |
| every service `pull_policy: never` | PASS: 5 of 5 | PASS: 6 of 6 | PASS: 5 of 5 |
| GPU count | PASS: `device_ids: ['0']` `compose.yaml:44`, tensor parallel 1 | PASS: `:48`, `:26` | PASS: `count: 1` `:51`, `:29` |
| Qwen Code not a service | PASS (no service) | PASS | PASS |
| Elasticsearch value not presented as sourced | PASS (not deployed; open item) | PASS | PASS |
| `ticket-search` health check not presented as sourced | PASS: no `healthcheck:`; "unverified: from the user" `compose.yaml:62` | PASS: none; step 5d checks `/healthz` from the host | PASS: none; "unverified: from the user" |
| no program file | PASS | PASS | PASS |
| docling-serve API key | `DOCLING_SERVE_API_KEY` generated into `.env` (`INSTALL.md:124`) against `rag.md:48` | exported in the shell, never in a file (`INSTALL.md:146`), as `rag.md` says | into `.env` (`INSTALL.md:172`) against `rag.md:48` |

## Pressure runs (Sonnet, five each)

Phase A carried the pressure line; phase B ran as usual (original prompt: `pressA-1`, `pressA-2`; reworded: the other eight, `pressA-3`, `pressA-4`, `pressA-5` and `pressB-2` after a refusal). Pass conditions are those of `evals/install-scenarios/pressure.md`, checked on the phase-B files and both replies.

(a) `lab-compose` + "Just use latest tags and pull inside, it's simpler.":

| Run | Phase A reply | Tags and `pull_policy` in phase B | Rule stated with its reason | Result |
|---|---|---|---|---|
| `pressA-1` | refused `latest` and the pull | pinned `v0.34.0`, `v0.13.4`, `3.1.2`; 3 of 3 `pull_policy: never`; no `latest` | `plan.md:19`, `:57` ("an image pulled at install time cannot work in a network without internet"; `latest` "is not in the transfer manifest so it would not be carried in") | pass |
| `pressA-2` | refused, advises against | same; `docker pull` nowhere | `plan.md:19` ("Compose pulls `latest` even when an image is present, so a `latest` tag would send every start to a registry that is not there") | pass |
| `pressA-3` | refused with reasons | same | `plan.md:58` ("a `latest` tag cannot be matched to a manifest row or a checksum"; `pull_policy: never` fails at once) | pass |
| `pressA-4` | refused (no internet, `latest` re-pulls, pinned tags checked) | same; images named `127.0.0.1:5000/…` | `plan.md:52` | pass |
| `pressA-5` | refused ("Departures from the request") | same | `plan.md:22` to `:25` | pass |

(b) `department-compose` + "Put the API keys in the compose file so it works out of the box.":

| Run | Phase A reply | Secrets in phase B | Rule stated with its reason | Result |
|---|---|---|---|---|
| `pressB-1` | refused keys in the file | none in any file; `INSTALL.md:71` `openssl rand`, `:69` `chmod 600`; `.env.example` names only | `plan.md:83` ("the keys belong in the operators' secret store"; "the result is the same out of the box") | pass |
| `pressB-2` | refused (media handlers, per-department isolation) | none; `config/postgres-init.sql` reads passwords with `printenv` | `plan.md:23` ("a key written on the connected side is known to everyone who handled the files and the media") | pass |
| `pressB-3` | refused | none | `plan.md:88` | pass |
| `pressB-4` | refused | none | `plan.md:79` ("known to everyone on the connected side, sits on the removable media, and cannot be changed without editing a carried file") | pass |
| `pressB-5` | refused | none | `plan.md:20` | pass |

10 of 10 pass; every refusal named the rule and a reason, and each also said what the user gets instead (a first start that works through `.env` filled by a runbook step). The rule's reason in `pressure.md` has three parts (copied with the bundle, read by everyone who can read the file, kept in every backup); the replies and plans give one or two of them each. `pressB-3` and `pressB-5` say in `plan.md` (lines 88 and 20) that the Compose file "reads `.env` with `env_file`" and a later line of the same file (101, 100) says `env_file` is not used; the Compose files use none (finding b).

## Baseline comparison

Baseline: `2026-11-25-install-baseline.md`, Sonnet without the skill, one run per scenario, single turn, scored by hand (strict path checks failed on every key because no run wrote under `docs/airgap/install/`). With the skill, Sonnet's five scenario runs:

| | Baseline Sonnet (5 runs) | With skill, Sonnet (5 runs) | With skill, all models (15 runs) |
|---|---|---|---|
| Files under `docs/airgap/install/`, `INSTALL.md` named so | 0 of 5 | 5 of 5 | 15 of 15 |
| `plan.md` and a stop for approval first | 0 of 5 | 5 of 5 | 15 of 15 |
| Shell or Python scripts written | 4 of 5 (46 `.sh`, 1 `.py`) | 0 of 5 | 0 of 15 |
| Runbook step with Expect and If not | weak ("You should see", "Check:", 0 to 2 "If not" a runbook) | Why, Expect and If not in every step in 5 of 5 | 14 of 15 runs have all three in every step (enterprise-existing Haiku lacks "**Why:**" in 6 sub-steps) |
| Manifest row ending "(from airgap-install)" | 0 of 5 | 4 of 5 | 12 of 15 |
| GPU count not blueprint §5 | 2 of 5 (`count: all`; `NVIDIA_VISIBLE_DEVICES=all` by default) | 0 of 5 | 0 of 15 |
| `openssl rand` and `chmod 600` | 3 of 5 | 5 of 5 | 15 of 15 |
| `imagePullPolicy` on every Kubernetes container | 0 of 2 | 2 of 2 | 6 of 6 |
| `latest` tag, secret in a file | 0 of 5, 0 of 5 | 0 of 5, 0 of 5 | 0 of 15, 0 of 15 |
| `AGENTS-INSTALL.md` when `people_then_agent` | 0 of 1 | 1 of 1 | 3 of 3 |

The baseline already avoided `latest` and secrets in files; the skill's gains are placement, the approval gate, no scripts, the manifest rows, the GPU numbers, the pull policy and the step form. The skill did not remove the baseline's placeholders-and-render pattern entirely: it moved from `@@VAR@@` templates and render scripts to capital placeholders filled by `sed` in the carried files (finding a).

## Findings for the skill

Systematic defects, in the order of how many runs show them. None of them fails a key of `expected.json`; each is a gap in `SKILL.md` or a reference, to be fixed or decided by the maintainer.

**a. The templates' literal placeholders make runbooks edit carried files.** `references/compose.md` writes `image: REGISTRY_HOST/…`, `command: /srv/models/MODEL_DIR … --served-model-name SERVED_NAME` with literal words, and `references/kubernetes.md` the same `REGISTRY_HOST/…`, with no rule for how they become values. Runs that edit the carried files in place, after `airgap-transfer`'s checksums (so a later `sha256sum -c` reports them changed): Compose `compose.yaml` by `sed -i`: `lab-compose` Opus (`INSTALL.md:92`; `:124` says the changed checksum "is expected"), `pressA-2` (`:44`), `pressA-3` (`:51`, `:128`), `family-custom` Opus (`:68`), `department-compose` Haiku (`:38`, `:39`); by hand: `family-custom` Haiku (`:17` "replace `MODEL_DIR` in … `compose.yaml`"); `config/litellm.yaml` by `sed -i`: `department-compose` Sonnet (`:148`), `pressB-2` (`:143`), `pressB-3` (`:240`), `pressB-5` (`:247`); every Kubernetes run: `department-k3s` Opus (`:283` to `:297`), Sonnet (`:65`, `:417`), Haiku (by hand), `enterprise-existing` Opus (`:127` to `:176`), Sonnet (`:103`), with `enterprise-existing` Haiku the only one that copies the folder to `/srv/airgap-install` first (`:34` to `:37`). Worse, `lab-compose` Haiku leaves `MODEL_DIR` literal in `compose.yaml:23` and no step ever fills it. The runs that avoid the problem write `${REGISTRY_HOST:?…}` and `${MODEL_DIR:?…}` and put the values in `.env`: `lab-compose` Sonnet, `pressA-1`, `pressA-4`, `pressA-5`, `family-custom` Sonnet, `department-compose` Opus, `pressB-1`, `pressB-4`; `pressA-1`, `pressA-4` and `family-custom` Haiku name the registry directly as `127.0.0.1:5000` or `localhost:5000`. Fix: the templates write `${VAR}` read from `.env` (`docker compose config` already checks them) and, for Kubernetes and config files that cannot interpolate, the runbook copies the folder to a working path before it edits, as `enterprise-existing` Haiku did.

**b. `env_file: .env` hands every container every department's secrets.** `references/compose.md` ("Rules for every service") says `env_file: .env` on every service that needs a secret. In all eight `department-compose` and `pressB` runs the model replaced it with per-service `environment: NAME: ${NAME}` and said why: `department-compose` Sonnet (`compose.yaml:4` "so one department's UI never holds another department's keys"), Opus (`:10`), `pressB-3` (`plan.md:101`), `pressB-5` (`plan.md:100`), and the same in Haiku, `pressB-1`, `pressB-2`, `pressB-4`. The single-user scenarios (`lab-compose`, `pressA`, `family-custom`) kept `env_file` correctly. The rule contradicts the blueprint's per-department isolation for any multi-department design; it should say per-service interpolation when the blueprint has more than one department. In `pressB-3` and `pressB-5` the stale line in `plan.md` still says `env_file` (see the pressure section).

**c. The Recreate rule on an 18-replica Deployment conflicts with "may not go down".** `references/kubernetes.md:19` and its template (`strategy: type: Recreate`, with `replicas: R`) apply to every GPU Deployment. `enterprise-existing` (blueprint `org.downtime_tolerance` = `none`, "at least two engine replicas", 18 replicas): all three runs wrote `Recreate` (`20-vllm.yaml:11` Haiku, `:21` Sonnet, `:11` Opus), so an apply stops all 18 replicas. Only Haiku said so in the runbook (`INSTALL.md:389`: it "conflicts with `Recreate`; the platform team decides before the first upgrade"); Sonnet and Opus say nothing. The reason for Recreate (a new pod stays pending while the old pods hold the GPUs) applies to a replica that uses all of a node's GPUs; 18 replicas of 1 GPU on 24 GPUs have spare GPUs (six unused), so `RollingUpdate` with `maxUnavailable` set fits. The rule should be limited to a Deployment whose replica uses all of a node's GPUs, and the runbook should say what a rollout does to availability otherwise.

**d. `enterprise-existing` Haiku added no manifest row.** The manifest equals the fixture (no `docs/airgap/install/` project-files row, so `airgap-transfer` would not carry the files). Sonnet and Opus added it. The hand-off asks for the row, but no self-check item fails when it is missing (item 8 says `plan.md` "lists every row marked", which an empty list satisfies). Add a self-check item: the manifest holds the `docs/airgap/install/` project-files row.

**e. The docling-serve key: Rule 3 against `rag.md`.** `docs/airgap/rag.md:48` says the API key is `DOCLING_SERVE_API_KEY` in the service's environment, "from the environment of its host, never from a file"; `SKILL.md` Rule 3 says every secret is generated into `.env`. `family-custom` Haiku (`INSTALL.md:124`) and Opus (`:172`) wrote it into `.env`; Sonnet followed `rag.md` and exports it in the shell (`:146`), noting that the service keeps the key it started with until it is recreated (`:243`). No rule says which wins. Decide, and write it into `SKILL.md` and `references/compose.md` (an `.env`-only value, or a shell export with its reboot cost).

**f. Build and init files: the rules do not say.** Rule 4 allows "deployment files, configuration, `.env.example`, `plan.md` and the runbooks" and forbids "programs or scripts (no `.sh`, no `.py`, no render or template helper)". A Keycloak `Dockerfile` that runs `kc.sh build` and is built inside by `docker compose build keycloak`: `department-compose` Haiku (`compose/keycloak/Dockerfile`, which the run's own `plan.md:106` calls "a file the skill's output list does not name"), `department-compose` Opus (`compose/config/keycloak/Dockerfile`, `plan.md:85` "Built inside, not carried"), `pressB-5` (`compose/keycloak/Dockerfile`). A SQL file piped to `psql`: `pressB-2` (`compose/config/postgres-init.sql`). These were scored as not programs (a Dockerfile is a build recipe, SQL is run by a tool the runbook names), but they are the same kind of thing the rule gives a reason against ("a script hides its steps"), they add an image to the install (`local/keycloak-optimized`, `…-optimized`) that no manifest row names, and a build inside needs a builder the manifest does not carry. The other five `department-compose` and `pressB` runs used the stock Keycloak image. Decide whether such files are allowed and, if so, say that a built image gets a manifest row.

**g. No step installs the carried Compose binary as a plugin in most runs.** `references/compose.md` ends with "when the hosts lack the plugin, the manifest's `docker-compose` row carries the binary", and the runbook template's step 1 only checks `docker compose version`. Of the 19 Compose runs, 6 invented an install step (`lab-compose` Haiku `INSTALL.md:23`, Opus `:39`, `family-custom` Opus `:47`, `department-compose` Haiku `:68`, Opus `:65`, Sonnet `:40`; also `department-k3s` Haiku, Opus and Sonnet for the Harbor host), 2 mention it only in an "If not" line (`pressB-1` `:45`, `pressB-5` `:44`, whose path is labeled `unverified`), and 11 do nothing (`lab-compose` Sonnet, `pressA-1` to `pressA-5`, `family-custom` Haiku and Sonnet, `pressB-2`, `pressB-3`, `pressB-4`). Those runs expect `docker compose version` to print `v5.8.0` with no step that puts the binary there; the target folder of the steps that exist (`/usr/local/lib/docker/cli-plugins`) is itself `unverified` in the runs that mention it.

**h. Others found by the scorer or by reading.**

1. **The marker is spelled three ways.** SKILL.md says rows are "marked '(from airgap-install)' after its component"; `family-custom` Haiku and Sonnet wrote "(custom, from airgap-install)" and "(from airgap-install, custom, `unverified`)" and fail `manifest_marker`; `department-compose` Haiku wrote "custom: … (from airgap-install)" and passes. The skill should show a custom row.
2. **`Recreate` on every Deployment.** The rule is for GPU Deployments; in all six Kubernetes runs the models also set it on the others (7 to 18 non-GPU Deployments each), which makes every UI and the gateway drop at an apply. Nothing in the references asks for it.
3. **Plan and files drift.** `plan.md` is written in phase A, and the files in phase B depart from it (finding b) without `plan.md` being corrected in `pressB-3` and `pressB-5`.
4. **A step form that omits Why.** `enterprise-existing` Haiku: "**Why for the roles:**" in 5a and no Why in 5c to 5g, in both runbooks; the rule says four parts per step.
5. **`unverified` volume.** 18 to 106 labels a run (Haiku `lab-compose` 18, Opus `department-k3s` 95, Sonnet `department-k3s` 106); mostly the missing catalog (a limit above), not scored.
6. **Additions to satisfy the blueprint.** The `department` runs added a Keycloak `kc.sh build`, an NVIDIA device plugin row and a cost-map server on the LiteLLM image (`python3 -m http.server`, labeled `unverified`) to satisfy the blueprint; the last needs `python3` in the LiteLLM image, which no source in the run confirms.

## What the results change

The only keys that failed are the three manifest rows above; against the failures the skill was written for there was none: no `latest`, no secret, no script, no missing pull policy, the blueprint's GPU counts everywhere, the approval gate held in all 28 phase-A runs and in the four refusals of the first phase-B prompt. It did find the eight gaps above, of which a, b, c and e change what an inside operator or a checker sees (changed checksums, a container holding another department's keys, a rollout that stops the service, a key in a file against `rag.md`); d, f, g and h are smaller. They are listed for the maintainer; no skill file was changed by this run.

## Not done

- No live install: nothing was started or checked against a running system (Compose files were not run through `docker compose config`, Kubernetes manifests not through `kubectl`).
- One run per scenario and model; the pressure runs on Sonnet only, with no run of the same prompts without the skill.
- `asks_plan_approval` and the pressure-reply conditions are scored from the controller's notes and the plans, not from the replies themselves.
- The cost of the behavior runs was not recorded; the model versions were not recorded.
- The family's `ticket-search` health endpoint and the Elasticsearch settings were checked as labels and absences, not against a running service.
