# Baseline for `airgap-install` without the skill, 2026-11-25

Why: the fifth skill, `airgap-install`, is not written yet. The design (`plans/2026-11-25-airgap-install-design.md`, section 3, "Evaluation first") asks for runs without the skill before `SKILL.md` exists, so that the "Common mistakes" table comes from what agents actually get wrong. The scorer comes in Task 8; this file was scored by hand against each `expected.json`.

Model: Sonnet, no skill, one fresh subagent per scenario, single turn. Date: 2026-11-25. Five scenarios: `lab-compose`, `department-compose`, `department-k3s`, `enterprise-existing`, `family-custom`. `unapproved` was not run (it needs the skill's refusal to be tested, and a baseline agent has no skill to send the user back to).

Each run's folder RUN was a copy of the scenario's `project/` folder in `evals/install-scenarios/`; the prompt was the scenario's `prompt.md` plus "Work in RUN. You have no internet inside the target network." The outputs are not kept in the repository (they are 60 to 120 KB each); this file quotes at most a line per finding. Paths below are relative to the run folder.

## How the keys were scored

`must_mention` and `files` name paths under `docs/airgap/install/`. No run wrote there (they used `install/`, `deploy/`, `INSIDE.md` or `docs/airgap/runbook.md`), so by the rule of `evals/README.md` every `files` key and every `must_mention` string fails by path. To make the table informative each row has two results:

- **Strict**: as `expected.json` says, searching only under `docs/airgap/install/`.
- **Intent**: the same check on the files the run wrote, wherever they are (`install/`, `deploy/`, `INSIDE.md`, `docs/airgap/runbook.md`).

Strict is therefore `fail` on every path key in every scenario, and is shown once per scenario, not per row. The `must_not` keys do not depend on the path and are scored once.

## Summary

| Scenario | Strict (path keys) | Intent: must_mention | Intent: files | must_not |
|---|---|---|---|---|
| `lab-compose` | all fail | 6 of 6 (1 by accident) | 3 of 4 (no `plan.md`; `INSTALL.md` under another name) | all pass |
| `department-compose` | all fail | 7 of 9 | 2 of 4 (no `plan.md`, no `INSTALL.md`) | all pass |
| `department-k3s` | all fail | 4 of 5 | 1 of 4 | 1 fail (GPU) |
| `enterprise-existing` | all fail | 1 of 2 | 1 of 3 (no `INSTALL.md`, no `AGENTS-INSTALL.md`) | all pass |
| `family-custom` | all fail | 3 of 5 | n/a | all pass |

All five also fail `manifest_marker` where they had to add a row (three of five), and every run that wrote a runbook named it something other than `INSTALL.md`.

## lab-compose

Run folder files: `install/compose.yaml`, `install/registry.compose.yaml`, `install/.env.example`, `install/scripts/` (8 shell scripts), `docs/airgap/runbook.md` (230 lines, 9 steps).

| Key | Result | Evidence |
|---|---|---|
| `orchestration` docker-compose | pass | `install/compose.yaml`, `name: lab-chat` |
| `must_mention` `pull_policy: never` | intent pass | `install/compose.yaml` on `vllm` and `open-webui`; `install/registry.compose.yaml` on `registry` (3 of 3) |
| `must_mention` `HF_HUB_OFFLINE` | intent pass | `install/compose.yaml`: `HF_HUB_OFFLINE: "1"` on both services |
| `must_mention` `Expect` | intent pass by accident | only `install/scripts/verify-bundle.sh`: `# Expects /path/to/bundle/SHA256SUMS`; the runbook has no Expect label ("It must end with `OK: all checksums match`", runbook.md:81) |
| `must_mention` `If not` | intent pass | `docs/airgap/runbook.md:81` "If not, do not import anything"; only one step has an If not |
| `must_mention` `openssl rand` | intent pass | `docs/airgap/runbook.md:95` `WEBUI_SECRET_KEY=$(openssl rand -hex 32)` |
| `must_mention` `chmod 600` | intent pass | `docs/airgap/runbook.md:89` `chmod 600 .env` |
| `files` `plan.md` | fail | no plan file anywhere; files written at once, no approval step |
| `files` `INSTALL.md` | intent pass | `docs/airgap/runbook.md` (wrong name and folder) |
| `files` `compose/compose.yaml` | intent pass | `install/compose.yaml` |
| `files` `compose/.env.example` | intent pass | `install/.env.example` (`WEBUI_SECRET_KEY=CHANGE_ME`) |
| `must_not_files` | pass | no `AGENTS-INSTALL.md`, no `kubernetes/` |
| `manifest_marker` | pass (nothing added) | `docs/airgap/transfer-manifest.md` identical to the fixture |
| `must_not`: latest | pass | no `latest` anywhere; tags `v0.34.0`, `v0.13.4`, `3.1.2` |
| `must_not`: secret value in a file | pass | `.env.example` holds `CHANGE_ME`; `OPENAI_API_KEY: not-needed` is a placeholder |
| `must_not`: service without `pull_policy: never` | pass | 3 of 3 |
| `must_not`: GPU count | pass | `install/compose.yaml`: `count: 1` |

Other findings from this run:

- Eight scripts, among them `install/scripts/verify-bundle.sh` (recomputes `SHA256SUMS`) and `install/scripts/load-and-push.sh` (`docker load` and push), which are what `airgap-transfer`'s `INSIDE.md` does.
- It assumed a bundle layout: `docs/airgap/runbook.md:21-22` "SHA256SUMS ... images/*.tar docker save files".
- Runbook step 4 (copy model, write `.env`, generate the key) has no Expect and no If not.
- Step 7 admits a guess: runbook.md:124 "the stock image **(estimate)** may or may not manage"; the word `unverified` is not used (0 hits).
- The runbook tells the reader to run `docker compose`, the manifest carries the standalone `docker-compose` v5.8.0 binary (runbook.md:71 says both are accepted).

## department-compose

Run folder files: `install/compose.yaml` (406 lines), `install/.env.example`, `install/bin/` (13 shell scripts), `install/config/` (nginx proxy templates, litellm, prometheus, grafana, postgres), `install/keycloak/Dockerfile`, `install/harbor/harbor.yml.settings`, `INSIDE.md` (534 lines, 18 numbered steps).

| Key | Result | Evidence |
|---|---|---|
| `orchestration` docker-compose | pass | `install/compose.yaml` |
| `must_mention` `pull_policy: never` | intent pass | `install/compose.yaml:16`, in the shared anchor `x-common`; every service merges it with `<<: *common` (also `x-open-webui`) |
| `must_mention` `HF_HUB_OFFLINE` | intent pass | `install/compose.yaml` vllm environment and `x-owui-common` |
| `must_mention` `Expect` | intent pass (weak) | `INSIDE.md:321` "Expected: nothing"; the runbook's own form is "You should see" (INSIDE.md:262) |
| `must_mention` `If not` | intent pass | `INSIDE.md:242` "If not: `docker-compose logs keycloak`" |
| `must_mention` `openssl rand` | fail | 0 hits; `install/bin/gen-secrets.sh` uses `head -c 24 /dev/urandom \| od -An -tx1` |
| `must_mention` `chmod 600` | intent pass | `install/bin/gen-secrets.sh` (`chmod 600 .env`); INSIDE.md:145 for `tls.key` |
| `must_mention` `--tensor-parallel-size 8` | intent pass, string fail | `install/compose.yaml:165-166` is a list: `- --tensor-parallel-size` then `- "8"`; a plain search for the string finds nothing |
| `must_mention` `--ipc=host` or `shm_size` | intent pass | `install/compose.yaml:187` `ipc: host` on `vllm`; the only `shm_size` (line 104) is on postgres |
| `must_mention` `count: 8` or `device_ids` | fail | `install/compose.yaml:193` `count: all` |
| `files` `plan.md` | fail | none |
| `files` `INSTALL.md` | fail | `INSIDE.md` at the project root: the name `airgap-transfer` writes |
| `files` `compose/compose.yaml`, `compose/.env.example` | intent pass | `install/compose.yaml`, `install/.env.example` |
| `must_not_files` | pass | none written |
| `manifest_marker` | fail by omission | `docs/airgap/transfer-manifest.md` identical to the fixture, yet `INSIDE.md:21` says the TLS proxy image "has **no row** in the manifest ... must be added", and `install/compose.yaml:135` runs `local/keycloak-optimized:26.8.2`, built on the host by `install/bin/build-keycloak.sh`, not in the manifest |
| `must_not`: latest | pass | none |
| `must_not`: secret value in a file | pass | `.env.example` holds `CHANGE_ME` or `FILL_IN_*` only |
| `must_not`: service without `pull_policy: never` | pass | all services through the anchors |
| `must_not`: GPU count | pass in effect | 8 through `--tensor-parallel-size 8` and `count: all` on an 8-GPU host; not the number of §5 |

Other findings:

- The TLS reverse proxy is in the blueprint (section 3, "TLS reverse proxy", custom, "the product is to be chosen"), so it was not "added". The run still chose a product: `config/proxy/templates/chat.conf.template` is nginx syntax, and `.env.example:30` leaves `PROXY_IMAGE=FILL_IN_PROXY_IMAGE`. The manifest has no row for it.
- `install/compose.yaml:87` runs `${REGISTRY_HOST}/library/postgres:18.7`; the manifest target path is `REGISTRY_HOST/postgres:18.7`. Blueprint line 434 does say "project prefixes for single-name references", so the change is defensible, but the manifest was not updated to match.
- Thirteen scripts, including `install/bin/verify-checksums.sh`, `install/bin/load-images.sh` and `install/bin/harbor-projects.sh`; the bundle layout is assumed (`SHA256SUMS`, `docker save` archives).
- The `unverified` label is used 11 times (as **UNVERIFIED**); each has the test step that checks it.

## department-k3s

Run folder files: `install/00-check-bundle.sh` ... `80-smoke-test.sh` plus `lib.sh`, `backup/` (13 shell scripts), `install/templates/` (14 Kubernetes files with `@@NAME@@` placeholders), `install/config.env.example`, `install/keycloak/Dockerfile`, `INSIDE.md` (293 lines, 20 numbered steps).

| Key | Result | Evidence |
|---|---|---|
| `orchestration` k3s | pass | `install/30-k3s.sh` |
| `must_mention` `INSTALL_K3S_SKIP_DOWNLOAD=true` | intent pass | `install/30-k3s.sh:58`; INSIDE.md step 7 |
| `must_mention` `registries.yaml` | intent pass | `install/30-k3s.sh:40` writes `/etc/rancher/k3s/registries.yaml` from a script heredoc |
| `must_mention` `imagePullPolicy` | fail | 0 hits in all 14 templates; no workload sets a pull policy |
| `must_mention` `Ready` | intent pass | INSIDE.md:121 "the node `Ready`" |
| `must_mention` `harbor.yml` | intent pass | `install/10-harbor.sh:27` `cp -n harbor.yml.tmpl harbor.yml`, then `set_yaml_key` |
| `files` `INSTALL.md` | fail | `INSIDE.md` |
| `files` `kubernetes/` | intent pass | `install/templates/` (placeholders, rendered by `install/40-render.sh`) |
| `files` `kubernetes/cluster/registries.yaml` | fail | no file; the script generates it at install time |
| `files` `compose/` | fail | no folder; Harbor is configured by `install/10-harbor.sh` editing `harbor.yml.tmpl` |
| `must_not_files` | pass | none written |
| `manifest_marker` | fail by omission | manifest identical to the fixture; `install/templates/05-nvidia-device-plugin.yaml:1` "The image is NOT in the transfer manifest", `install/templates/20-keycloak.yaml:30` `keycloak-optimized:26.8.2` is a derived image |
| `must_not`: latest | pass | none |
| `must_not`: secret value in a file | pass | none |
| `must_not`: GPU count | fail | blueprint line 233: "The engine pod requests all 8" through `nvidia.com/gpu`. The default `GPU_MODE=runtime-env` (`install/config.env.example:79`) sets `NVIDIA_VISIBLE_DEVICES=all` and reserves nothing; `nvidia.com/gpu: 8` exists only in lines prefixed `#@dp` (`install/templates/30-vllm.yaml`) that the render script enables on request |

Other findings:

- The run says so openly (INSIDE.md:32 "Known gaps and changes from the blueprint", row 1: the device plugin image is not in the manifest) and chose a fallback that departs from the blueprint, instead of adding the image as a manifest row.
- `install/templates/10-postgres.yaml:52` `.../library/postgres:18.7`, as in `department-compose`.
- Thirteen scripts: `install/00-check-bundle.sh` (checksums), `install/20-push-images.sh` (comment: "Assumption: image archives in the bundle are docker-save files"), and `INSIDE.md:24` lists the assumed bundle layout.
- The runbook is good on honesty: six **UNVERIFIED** labels, each with a test step; expected outputs follow most commands ("Check:").
- The runbook is named `INSIDE.md`, the same file `airgap-transfer` writes.

## enterprise-existing

Run folder files: `install/manifests/` (9 Kubernetes files with `@@NAME@@` placeholders), `install/bin/` (11 shell scripts and `add-model-to-cost-map.py`), `install/install.env.example`, `install/departments.txt`, `docs/airgap/runbook.md` (268 lines, 16 numbered sections).

| Key | Result | Evidence |
|---|---|---|
| `orchestration` existing | pass | runbook step 4 "Prepare the cluster" uses `oc` against OpenShift; no cluster is installed |
| `must_mention` `replicas: 18` | intent fail on the string | `install/manifests/50-vllm.yaml:22` `replicas: @@VLLM_REPLICAS@@`; the 18 sits in `install/install.env.example:31` `VLLM_REPLICAS=18` |
| `must_mention` `nvidia.com/gpu` | intent pass | `install/manifests/50-vllm.yaml:82-83` `nvidia.com/gpu: "1"` in requests and limits |
| `files` `INSTALL.md` | fail | `docs/airgap/runbook.md` |
| `files` `AGENTS-INSTALL.md` | fail | not written; `docs/airgap/runbook.md:254` "the rules for the agent are a separate document and are not part of this runbook" |
| `files` `kubernetes/` | intent pass | `install/manifests/` |
| `must_not_files` `kubernetes/cluster/` | pass | none |
| `manifest_marker` | pass (nothing added) | manifest identical to the fixture |
| `must_not`: latest | pass | none |
| `must_not`: secret value in a file | pass | `install/bin/create-secrets.sh:6` generates with `openssl rand -hex 24` at run time; `install.env.example` holds `CHANGE_ME` |
| `must_not`: GPU count | pass | 18 replicas of 1 GPU (`install.env.example:31`, `50-vllm.yaml:82`) |
| `must_not`: cluster install step | pass | none |

Other findings:

- `people_then_agent` (blueprint line 20) was read and deferred in one sentence; the run is the one that most needs `AGENTS-INSTALL.md`.
- No `imagePullPolicy` on any workload (0 hits under `install/manifests/`); the OpenShift pull secret (`harbor-pull`, runbook step 4) is the only pull control.
- Eleven shell scripts and one Python file, among them `install/bin/push-images.sh` (comment: `*.tar from docker save`).
- Good: nine **unverified** labels (for example the SCC for postgres, runbook.md:85, and `fail_closed_budget_enforcement`), each with a check.

## family-custom

Run folder files: `deploy/compose.yaml`, `deploy/.env.example`, `deploy/qwen-code/settings.json`, `docs/airgap/runbook.md` (147 lines, 12 sections), and an edited `docs/airgap/transfer-manifest.md`. No scripts: the only run of the five with none.

| Key | Result | Evidence |
|---|---|---|
| `orchestration` docker-compose | pass | `deploy/compose.yaml` |
| `must_mention` `unverified` | fail | 0 hits in the run's files; the runbook says "not known", "open item", "none is invented here" (`deploy/compose.yaml:92-93`) instead of the label |
| `must_mention` `ticket-search` | intent pass | `deploy/compose.yaml`, runbook section 8 |
| `must_mention` `docling` | intent pass | `deploy/compose.yaml` `docling-serve` service, image `quay.io/docling-project/docling-serve-cpu:v1.39.0` |
| `must_mention` `arm64` | intent pass | runbook section 7: "each developer's `arm64` Linux machine" |
| `must_mention` `docs/airgap/agents.md` | fail | the runbook points to `deploy/qwen-code/settings.json` and "(from airgap-agent)" but never names `docs/airgap/agents.md` |
| `must_not_files` `AGENTS-INSTALL.md` | pass | none |
| `manifest_marker` | fail | the run added `ticket-search` rows to `docs/airgap/transfer-manifest.md`, ending "(in-house, from the user)" and not "(from airgap-install)" (three rows and two verification steps added) |
| `must_not`: latest | pass | none |
| `must_not`: secret value in a file | pass | `CHANGE_ME` only |
| `must_not`: GPU count | pass | `count: 1` |
| `must_not`: service without `pull_policy: never` | pass | 5 of 5 |
| `must_not`: Qwen Code deployed as a service | pass | runbook section 7 "Developer machines (Qwen Code, from airgap-agent)": installed from the carried archive on arm64 machines |
| `must_not`: Elasticsearch setting presented as sourced | pass | no Elasticsearch service; runbook section 10, item 7 "The Elasticsearch 8 version, address, authentication, and the loader ... : not known" |
| `must_not`: ticket-search health check presented as sourced | pass | `deploy/compose.yaml` has none; runbook section 8 "A guessed health check can mark a working service as broken" |

Other findings:

- The controller's worry that vLLM flags and the Qwen settings came "from memory" is not borne out: the `settings.json` keys are those of `docs/airgap/agents.md:37` and manifest section 4; the tool-call parser flags are listed as an open item (`deploy/compose.yaml:36-37`). Only the settings file location `~/.qwen/settings.json` is from memory, and the runbook hedges it (section 7, step 2: "check that name ... it is not recorded here").
- This run is the best of the five on the family's unknowns, with prose in place of the label, which is why `unverified` still fails the string check.
- Section 5 has seven numbered steps, of which only step 4 states an output ("prints nothing"); "If not" never appears in the form of the template, and the runbook has one troubleshooting table instead (section 9).
- Section 5, step 5 pushes images into the registry service "(optional, useful for re-deploys)" while no service reads from it (`deploy/compose.yaml` names the images directly).

## Patterns across runs

What the baseline already does well, which `SKILL.md` must not break: no key in any file (5 of 5); no `latest` tag (5 of 5); Compose offline switches copied from the manifest's section 4 (`HF_HUB_OFFLINE` in 5 of 5); `pull_policy: never` on every Compose service (3 of 3 Compose runs); no cluster install for the existing cluster; Qwen Code handed off and not deployed; no invented health check for `ticket-search`; open items written down in four of five runs.

What it gets wrong, in the order of how many runs show it:

1. **Wrong place and names (5 of 5).** Nothing under `docs/airgap/install/`. Three runbooks are `docs/airgap/runbook.md`, two are `INSIDE.md` (the name `airgap-transfer` writes, in `department-compose` and `department-k3s`), none is `INSTALL.md`. No `plan.md` in any run, so there was no approval step.
2. **Scripts and an invented bundle layout (4 of 5).** 46 shell scripts and one Python file (lab 8, department-compose 13, department-k3s 13, enterprise 12 and 1 `.py`), including their own checksum check (`verify-bundle.sh`, `verify-checksums.sh`, `00-check-bundle.sh`) and image load and push (`load-and-push.sh`, `load-images.sh`, `20-push-images.sh`, `push-images.sh`). Both are `airgap-transfer`'s job. Three runbooks state the layout they assumed (`SHA256SUMS`, `docker save` archives). The design says the install skill writes no scripts.
3. **Manifest left unchanged when a file needs a new artifact (3 of 5).** `department-compose` (proxy image, `local/keycloak-optimized`), `department-k3s` (NVIDIA device plugin image, `keycloak-optimized`) and the changed postgres path in both, and `family-custom` (rows added, wrong marker). No run added a row ending "(from airgap-install)".
4. **GPU reservation weaker than the blueprint (2 of 5).** `department-compose` `count: all`; `department-k3s` default `NVIDIA_VISIBLE_DEVICES=all` with the `nvidia.com/gpu: 8` request behind a render switch.
5. **Placeholder templates with a render script (2 of 5).** `department-k3s` and `enterprise-existing` write `@@VAR@@` templates, so the numbers of the blueprint (`replicas: 18`, GPU lines) are not in the files an operator reads.
6. **No pull policy on Kubernetes workloads (2 of 2 Kubernetes runs).** 0 `imagePullPolicy` lines.
7. **`people_then_agent` ignored (1 of 1).** `enterprise-existing` wrote no `AGENTS-INSTALL.md` and says so in one sentence.
8. **Runbook steps without Expect and If not in the template's form (5 of 5).** The runs use "You should see", "Check:", "must end with"; literal "If not" appears 0 to 2 times per runbook; steps that only copy files or write `.env` usually state no output (lab step 4, family section 5 steps 1 to 3).
9. **The label `unverified` missing (2 of 5).** `lab-compose` ("(estimate)") and `family-custom` (prose). The other three use it 6 to 11 times.
10. **Secrets generated without `openssl rand` (2 of 5).** `department-compose` and `department-k3s` generate from `/dev/urandom` with `od` inside a script; the files stay clean, but the string check fails.

Not observed: a cluster install for OpenShift; `latest`; a secret in a file; a Compose service without `pull_policy: never`; a wrong replica count.

Not verifiable from the files: the controller reported that two runs briefly wrote outside their folder (a `.env` copy in the parent, `/tmp/h.yml`). Nothing of that remains in `baseline/` or in `/tmp`, so no finding is recorded for it.

Corrections to the first reading of these runs: the TLS proxy of `department-compose` is in the blueprint (the run chose its product, nginx syntax, and left the image open); the `library/` postgres path is supported by blueprint line 434 and the failure is the missing manifest row; `family-custom` wrote no scripts and did not take its Qwen settings from memory.

## Notes for the scorer (Task 8)

- A plain search for `--tensor-parallel-size 8` fails on a correct Compose list written on two lines (`- --tensor-parallel-size` then `- "8"`); either `references/compose.md` shows the command as a single string, or the key becomes `--tensor-parallel-size`.
- `Expect` passes on any word that contains it ("Expects", "Expected"). A key such as `**Expect:**` would test the label.
- `replicas: 18` and `count: 8` fail on placeholders: the templates of the skill must write the blueprint's numbers into the file.

## Rows for SKILL.md

| Mistake | What to do instead |
|---|---|
| Writes the runbook as `docs/airgap/runbook.md` or `INSIDE.md`, and files under `install/` or `deploy/` (5 of 5 runs) | Write only the tree of §7.2: `docs/airgap/install/` with `plan.md`, `INSTALL.md` (`AGENTS-INSTALL.md` when `inside.operator` includes an agent), `compose/` or `kubernetes/`. `INSIDE.md` is `airgap-transfer`'s file (Rule 4) |
| Writes the files at once, with no plan and no approval (5 of 5) | Write `plan.md` first (host, order, files, ports, health checks, GPUs), record the date of the user's approval in it, and stop; write nothing else before the user approves (Rule 4, workflow step 3) |
| Writes 8 to 13 shell scripts that check checksums, load and push images, render templates and write `registries.yaml`, on an assumed bundle layout (4 of 5) | No scripts. Each step is a command in `INSTALL.md`. Checksums and loading belong to `airgap-transfer`'s `INSIDE.md`: step 1 of `INSTALL.md` asks that it is finished, then starts from the registry (Rule 1, Rule 7, self-check 6) |
| Needs an image or a binary the manifest lacks (the TLS proxy, a device plugin, an image built on the host) and only mentions it in the runbook (3 of 5); changes an image path without telling the manifest | Add a row ending "(from airgap-install)" to `docs/airgap/transfer-manifest.md`; every image in the files has the manifest's tag and target path (§6 closing paragraph, self-check 1) |
| Reserves GPUs as `count: all`, or defaults to `NVIDIA_VISIBLE_DEVICES=all` with `nvidia.com/gpu: 8` behind an option (2 of 5) | Copy the blueprint's §5 number: `count: 8` or `device_ids`, `--tensor-parallel-size 8`, `nvidia.com/gpu: 8`; for 18 replicas of 1 GPU, `replicas: 18` and `nvidia.com/gpu: 1` in the file. If a part is missing, report it as a blueprint change (Rule 6, self-check 3) |
| Writes `@@VAR@@` templates and a render step, so `replicas: 18` and the GPU lines are not in the file (2 of 5) | Write final YAML with the blueprint's numbers in it; placeholders only for what nobody on the connected side knows, in capitals, listed at the top of `INSTALL.md` (§8, self-check 3 and 6) |
| Kubernetes workloads with no pull policy (2 of 2) | Name the local registry and set `imagePullPolicy` as the catalog entry documents it, on every container (Rule 2, self-check 2) |
| Reads `people_then_agent` and defers the agent runbook in one sentence (1 of 1) | Write `AGENTS-INSTALL.md` next to `INSTALL.md`: the same steps, and the rules for the agent (§7.2, workflow step 5) |
| Steps with "You should see", "Check:" or nothing, and one "If not" in a whole runbook (5 of 5) | Every step has Why, commands, **Expect** and **If not**, in those words; a step that only copies a file expects the `ls` or `stat` output (§8, self-check 6) |
| Prose such as "not known", "(estimate)" in place of the label (2 of 5); secrets generated with `od` in a script (2 of 5) | Label every value not from the catalog `unverified`, and say what step checks it (§8, self-check 7). Generate each secret in a runbook step with `openssl rand`, into `.env` with `chmod 600`; `.env.example` holds names only (Rule 3, self-check 5) |
