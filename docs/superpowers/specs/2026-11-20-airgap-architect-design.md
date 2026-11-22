# airgap-anything — Design Spec for the airgap-architect skill

- **Date:** 2026-11-20
- **Status:** Approved by the maintainer on 2026-11-20
- **Names:** repository and plugin `airgap-anything`; skill `airgap-architect` (see §18)
- **Revised:** 2026-11-21, after research: T1 user threshold 25 → 50 and chat/RAG duty 0.15-0.30 → 0.25-0.50 (sources in rules.toml). 2026-11-21 and 2026-11-22, during implementation: a context per user group and a KV cache counted in tokens and packed in whole requests, with a note on larger GPU groups (§7, §10.2, §16); a GPU vendor, image rows per hardware class and a manifest digest over decisions, models and GPUs (§7, §10.5, §11.1, §14.2); GPU names that stay unique after normalization (§10.5); source code at the release tag as `docs` evidence (§11.2). 2026-11-22, after the final review: the E8 and E9 rows, exit 3 and the `manifest.py` row in §12, the decision's `benchmark` list (§13, §14.2), and the vLLM links of §10.2 pinned to v0.34.0
- **Covers:** sub-project 1 — the core pipeline plus the LLM platform layer

## 1. Summary

`airgap-architect` is an open-source Agent Skill, published in the `airgap-anything` repository (tagline: "Design any system for air-gapped environments"). It interviews a person about their organization — people, departments, privacy rules, hardware, operations capacity — and produces an end-to-end design blueprint for a system that must run in an air-gapped or on-premises environment.

The blueprint names a component for every layer, sizes the GPUs, explains each choice, and lists everything that has to be carried into the network. It is written so that `superpowers:writing-plans` can turn it into an implementation plan, and so that an agent working inside the air-gapped network can follow it without internet access.

The skill is a decision layer. It does not explain how to operate each tool; it points to existing per-tool skills for that.

## 2. Problem and prior art

Two groups of skills exist today, checked on GitHub on 2026-11-20:

| Group | Examples | What they do | What is missing |
|---|---|---|---|
| General architecture skills | `yonatangross/orchestkit` (`scope-appropriate-architecture`), `davila7/claude-code-templates` (`architecture`), `bmad-code-org/BMAD-METHOD`, `navraj007in/architecture-cowork-plugin` | Classify a project by scale and recommend patterns or stacks | They recommend SaaS (Clerk, Vercel, Supabase) and assume the agent can search the web. Neither holds in an air-gapped network. |
| LLM and air-gapped skills | `ScaleDockHQ/llm-skills` (208 skills), `air-gapped/skills` (78 skills), `agentsope/SkillAlchemy`, `anubhavg-icpl/vibe` (`gateway-picker`) | Per-tool operator references and single-point decisions (hosting, engine, gateway) | No single interview that yields one whole-stack blueprint. Inputs are engineering parameters (RPS, concurrent users), not the shape of an organization. |

Gaps this project fills:

1. One interview produces one blueprint across all layers.
2. Scale tiers are combined with air-gapped constraints.
3. Organization language (departments, headcount) is translated into engineering parameters (concurrency, GPUs, servers, power).
4. The catalog is self-contained, so it works when the agent has no web access.

GitHub code search is not exhaustive. "Missing" here means "not found on 2026-11-20".

## 3. Users and where the skill runs

| Role | Where | What they do |
|---|---|---|
| Designer | Connected workstation, strong-model coding agent (Claude Code first, any agent that supports the Agent Skills format) | Runs the interview and produces the blueprint |
| Implementer | Inside the air-gapped network, possibly with a local-model agent | Builds the system by following the blueprint; has no web access |
| Contributor | GitHub | Adds or verifies catalog entries through pull requests |

The design happens outside; the result is applied inside. The interview and the scripts run on the connected workstation. Only static files (blueprint, state file, transfer manifest, agent instructions) travel inside with the project repository.

## 4. Decisions already made

| Topic | Decision |
|---|---|
| Direction | Air-gapped and on-prem system design, all layers over time; v1 starts with the LLM platform layer |
| Audience | Open source on GitHub, MIT license, repository in English |
| Output | One blueprint with decision records, integrated with superpowers |
| Evidence | Field experience plus research; every catalog value carries an evidence label |
| Internal structure | Hybrid: the model decides from Markdown decision tables; Python scripts compute and verify; the catalog is structured data |
| Tier versus hardware | Two separate axes. The tier measures organizational complexity. GPU count is computed by sizing and is independent of the tier. |

## 5. Scope

In scope for v1:

1. Core pipeline: interview, tier computation, decisions, sizing, blueprint, lint, hand-off.
2. Two decision tables: inference engine and LLM gateway.
3. Fixed per-tier defaults for six supporting layers: UI, identity, observability, orchestration, state stores, artifact registry.
4. A catalog of about 16 components, a GPU table and a rules file.
5. Four scripts with unit tests, three scenario fixtures, CI.
6. Distribution as a Claude Code plugin and through `npx skills add`.

Out of scope for v1:

1. Generating deployment files (Docker Compose, Helm).
2. Recommending which LLM to run. Sizing takes the model as an input.
3. Decision tables for the supporting layers and for data, CI/CD and security layers.
4. Compliance packs (KVKK, ISO 27001 and similar).
5. Running the interview with a weak local model.

## 6. Architecture

### 6.1 Repository layout

```
airgap-anything/
├── README.md
├── LICENSE
├── CONTRIBUTING.md                     how to add or verify a catalog entry
├── .claude-plugin/
│   └── marketplace.json                lists the plugin folder below
├── plugins/airgap-anything/            the plugin folder: all that an install gets
│   ├── .claude-plugin/
│   │   ├── plugin.json
│   │   └── icon.png
│   └── skills/airgap-architect/
│       ├── SKILL.md                    process, about 150 lines
│       ├── references/
│       │   ├── interview.md            questions, order, defaults
│       │   ├── tiers.md                tier model explained for the model
│       │   ├── sizing.md               how to read size.py output
│       │   ├── layers/
│       │   │   ├── llm-serving.md      decision table
│       │   │   ├── llm-gateway.md      decision table
│       │   │   └── supporting-defaults.md  fixed defaults per tier
│       │   ├── blueprint-template.md
│       │   └── agents-snippet.md
│       ├── catalog/
│       │   ├── rules.toml              thresholds, escalators, sizing defaults
│       │   ├── gpus.toml               GPU table
│       │   └── components/*.toml       one file per component
│       └── scripts/
│           ├── tier.py
│           ├── size.py
│           ├── manifest.py
│           ├── lint.py
│           └── airgap_lib/             shared code: catalog loading, schema, rules, math
├── tests/                              unittest suites and fixtures
├── evals/scenarios/                    lab, department, enterprise
├── docs/superpowers/specs/             this spec
└── .github/workflows/ci.yml
```

Everything an installed skill needs lives under `plugins/airgap-anything/skills/airgap-architect/`, because skill installers copy only that folder. The plugin folder `plugins/airgap-anything/` holds only the manifest, the icon, the skill and the triggering suite: a plugin install gets that folder alone, and Anthropic's directory checks every file in it (moved there from the repository root on 2026-11-22).

### 6.2 Pipeline

| Step | Who | Input | Output |
|---|---|---|---|
| 1. Interview | Model | Conversation, project files | `answers` in `blueprint.json` |
| 2. Tier | `tier.py` | `answers`, `rules.toml` | `tier` in `blueprint.json` |
| 3. Sizing | `size.py` | `answers`, `rules.toml`, `gpus.toml` | `sizing` and `assumptions` in `blueprint.json` |
| 4. Decisions | Model | `tier`, `sizing`, decision tables, catalog | `decisions` in `blueprint.json` |
| 5. Transfer manifest | `manifest.py` | `decisions`, catalog | `transfer-manifest.md` |
| 6. Blueprint | Model | Everything above, template | Blueprint Markdown file |
| 7. Lint | `lint.py` | All outputs, catalog | Errors and warnings |
| 8. Hand-off | Model | Lint-clean blueprint, user approval | `superpowers:writing-plans`, or printed next steps |

Scripts write their results directly into `blueprint.json`. The model never copies a computed number by hand.

### 6.3 Principles

1. **The skill is itself air-gap friendly.** Scripts use only the Python standard library (Python 3.11 or newer). No `pip install`, no web search, no network calls.
2. **The model decides; scripts compute and verify.** Trade-offs are judged by the model. Arithmetic, lists and consistency checks are done by scripts.
3. **Point, do not copy.** Tool-level detail stays in existing per-tool skills. Catalog entries link to them.
4. **Nothing from memory.** No catalog value or rule is written from the implementing agent's memory. Each one has a source fetched at authoring time or a field note; otherwise it is labeled `estimate`.

## 7. Interview

Rules:

1. Look before asking. Read project files the user points to and skip questions they already answer.
2. Ask one question at a time, multiple choice where possible, in the user's language.
3. Accept "unknown". Use the documented default, record it in `assumptions`, continue.
4. Save `answers` to `blueprint.json` after every answer, so an interrupted interview can resume.

Questions:

| ID | Asks | Type | Required |
|---|---|---|---|
| `org.users_total` | How many people will use the platform | integer | yes |
| `org.departments` | How many departments or teams need separate budgets or data boundaries | integer | yes |
| `org.isolation` | Whether departments may see each other's prompts and data | `none`, `per_department`, `multi_level` | yes |
| `org.audit_required` | Whether every request must be attributable to a person and retained | boolean | yes |
| `org.downtime_tolerance` | How much downtime is acceptable | `accepted`, `planned_only`, `none` | yes |
| `org.ops_capacity` | Who operates the system | `part_time_one`, `small_team`, `platform_team` | yes |
| `org.kubernetes_experience` | Whether the operating team runs Kubernetes today | boolean | yes |
| `workload.usage` | Share of each usage type: `chat`, `code_assistant`, `rag`, `batch` | map of shares summing to 1 | yes |
| `workload.models` | Models to serve: role, parameter count and precision, or weight size; optional context length and architecture numbers | list | yes |
| `workload.context_tokens` | Typical context length per user group: `chat`, `code_assistant`, `rag` | map of group to tokens | no |
| `hardware.gpus` | GPUs that exist or will be bought: model, count, optional VRAM and vendor (`nvidia`, `amd`, `intel`) | list, may be empty | yes |
| `hardware.ram_gb` | System RAM, asked only when there is no GPU | number | conditional |
| `hardware.power_budget_kw` | Power available for the system | number | no |
| `existing.identity` | Existing identity provider | `none`, `ad_ldap`, `oidc` | yes |
| `existing.api_gateway` | Existing API gateway | `none`, `kong`, `other` | yes |
| `existing.kubernetes` | Existing cluster platform | `none`, `kubernetes`, `openshift` | yes |
| `existing.registry` | Existing artifact registry | `none`, `harbor`, `nexus`, `artifactory`, `other` | no |
| `transfer.channel` | How artifacts enter the network | `removable_media`, `data_diode`, `staging_host`, `other` | yes |
| `transfer.cadence` | How often updates can be carried in | `ad_hoc`, `monthly`, `quarterly` | no |

When the user does not know the model, they pick a size class. `rules.toml` maps each class to a representative parameter count, labeled `estimate`: S (up to 15B), M (16B–80B), L (81B–300B), XL (above 300B).

## 8. Tier model

### 8.1 Base tier

Two answers determine the base tier:

| | T1 Single team | T2 Department | T3 Enterprise |
|---|---|---|---|
| Users | up to 50 | 51–300 | above 300 |
| Departments | 1 | 2–5 | 6 or more |

Base tier = the higher of the tier implied by users and the tier implied by departments.

The thresholds (50, 300, 1, 5) live in `rules.toml`. The user thresholds have documentary anchors recorded there; the department thresholds are a heuristic labeled `estimate` until field data replaces them.

What a tier typically looks like — Docker Compose at T1, Compose or lightweight Kubernetes at T2, Kubernetes at T3 — follows from the defaults in §9.3. Downtime tolerance is not part of the base tier; it raises individual layers (§8.2). GPU count is independent of the tier and comes from sizing (§10).

### 8.2 Per-layer floors

The base tier is a floor for every layer. Some answers raise the floor of individual layers:

| Answer | Effect |
|---|---|
| `org.audit_required = true` | `llm-gateway` floor at least T2; the gateway may not be empty |
| `org.isolation = per_department` | `llm-gateway` and `identity` floors at least T2; the gateway may not be empty |
| `org.isolation = multi_level` | `llm-gateway` and `identity` floors T3; the blueprint must contain an "Isolation design" subsection |
| `org.downtime_tolerance = none` | `orchestration`, `llm-serving` and `state` floors T3; at least two engine replicas |

A floor does two things for its layer: it selects the column of the supporting-defaults table (§9.3), and it restricts choices to components whose `tiers` include it. `tier.py` computes the base tier and the floors. The model may raise a layer above its floor, or go below it by recording an override with a reason; `lint.py` reports every override.

When the `orchestration` floor is T3 and `org.kubernetes_experience` is false, the blueprint lists this as a risk in its verification section.

Example: a 15-person team with mandatory audit logging has base tier T1 and an `llm-gateway` floor of T2. It gets a gateway, but no Kubernetes.

## 9. Layers in v1

Every row in this section is starting content. Each row ships with an evidence label. A row without a source or field note at implementation time ships as `estimate`. In the decision tables, a row is skipped when its component does not allow the layer's floor tier.

### 9.1 Inference engine (`llm-serving`)

First matching row wins.

| Condition | Engine |
|---|---|
| No GPU | `ollama` |
| Peak concurrency (high estimate) at most 4 and `org.ops_capacity = part_time_one` | `ollama` |
| `code_assistant` plus `rag` share at least 0.5 | `vllm`, and add "benchmark `sglang` on this workload" to the verification list |
| Otherwise | `vllm` |

`sglang` is chosen directly only when a catalog entry or the user provides field evidence for the workload.

### 9.2 LLM gateway (`llm-gateway`)

First matching row wins.

| Condition | Gateway |
|---|---|
| `existing.api_gateway = kong` and (two or more departments, or audit required) | `kong` at the edge with `litellm` behind it |
| `existing.api_gateway = kong`, single team, no audit | `kong` |
| Audit required, or isolation other than `none`, or two or more departments, or more than one served model | `litellm` |
| Otherwise | none |

The catalog entries for `kong` and `litellm` must state which features need a paid license and whether any license check needs connectivity. Both points decide whether a gateway is usable in an air-gapped network.

### 9.3 Supporting layers (fixed defaults)

| Layer | T1 | T2 | T3 |
|---|---|---|---|
| `ui` | `open-webui` | `open-webui` | `open-webui`, more than one replica |
| `identity` | Local accounts in the UI | `keycloak` federated to the existing directory, or the existing OIDC provider | Same as T2, with department-scoped groups |
| `observability` | Engine metrics endpoint | `prometheus` and `grafana` | `prometheus` and `grafana` |
| `orchestration` | `docker-compose` | `docker-compose`, or `k3s` when the team runs Kubernetes today | Existing Kubernetes or OpenShift, otherwise `rke2` |
| `state` | `postgresql` when a chosen component needs it | `postgresql` and `valkey` | `postgresql` (highly available) and `valkey` |
| `registry` | `distribution-registry` | `harbor`, or the existing registry | `harbor`, or the existing registry |

### 9.4 Catalog components in v1

`ollama`, `vllm`, `sglang`, `litellm`, `kong`, `open-webui`, `keycloak`, `prometheus`, `grafana`, `postgresql`, `valkey`, `docker-compose`, `k3s`, `rke2`, `harbor`, `distribution-registry`.

## 10. Sizing model

`size.py` turns organization answers into hardware numbers. All defaults live in `rules.toml` with evidence labels.

### 10.1 Concurrency

For each usage type `u`: `concurrency_u = users × share_u × active_u × duty_u`.

- `active_u`: share of users active in the peak hour.
- `duty_u`: share of time an active user has a request in flight.
- Each default has a low and a high value, so the result is a range.
- `batch` is excluded from interactive concurrency; its concurrency is a job setting.
- Low and high results are rounded up to whole requests, with a minimum of 1.

The chat and RAG duty is set so that `active × duty` matches NVIDIA's documented 5–10 % of users with a request in flight (sources in `rules.toml`). All factors stay labeled `estimate`.

| Usage | `active` | `duty` low–high |
|---|---|---|
| `chat` | 0.20 | 0.25–0.50 |
| `rag` | 0.20 | 0.25–0.50 |
| `code_assistant` | 0.30 | 0.70–1.00 |

### 10.2 Memory per model

1. `weights_gb = params_b × bytes_per_param(precision)`. A weight size given by the user overrides this arithmetic. Bytes per parameter: fp32 4, bf16 and fp16 2, fp8 and int8 1, int4 0.5.
2. `usable_gb(g) = g × vram_gb × gpu_memory_utilization`, default utilization 0.90.
3. `gpus_per_replica` = the smallest `g` in the allowed group sizes (default 1, 2, 4, 8) with `usable_gb(g) ≥ weights_gb × (1 + overhead)`, default overhead 0.10. Step 5 may raise it.
4. `kv_headroom_gb = usable_gb(g) − weights_gb × (1 + overhead)`.
5. When architecture numbers are given, the KV cache is counted in tokens and packed in whole requests:
   - `kv_bytes_per_token = 2 × layers × kv_heads × head_dim × bytes(dtype)`. A paged KV cache allocates blocks to a request only as its tokens fill them, so it wastes at most one block per request (vLLM's PagedAttention, https://arxiv.org/abs/2309.06180, §4.3); the cache is therefore counted in tokens, not in reserved full-length sequences.
   - The context of a request from user group `u` is `workload.context_tokens[u]` when given, else the model's `context_tokens`, else `default_context_tokens`. Tokens per request of the group: that context plus `default_output_tokens`. With only `batch` there is one implicit group of all requests, with the model's context or the default.
   - The integer `concurrency_high` is split across the interactive groups in proportion to their unrounded peak values (`users × share × active × duty_high`) by the largest-remainder method: floor each quota, give the remaining units to the largest fractional parts, ties in the order `chat`, `code_assistant`, `rag`. A group can get 0 requests.
   - `longest` = the largest tokens per request of any group with a peak value above 0, including a group that got 0 requests. `gpus_per_replica` is the smallest allowed group size that holds the weights and whose `cached_tokens = floor(kv_headroom_gb × 10^9 / kv_bytes_per_token)` is at least `longest`; this can be larger than the size of step 3. When none is, the status is `insufficient`: the KV cache cannot hold one request of the longest context on the largest allowed GPU group.
   - `replicas` = the larger of the minimum (step 7) and the number of replicas that first-fit decreasing needs: requests are taken longest first and each goes into the first replica whose remaining `cached_tokens` holds it, else a new replica is opened. The reasoning: a request's KV cache lives in one replica, because data parallelism "replicates the entire model across multiple GPU sets and processes different batches of requests in parallel" (vLLM optimization guide, https://docs.vllm.ai/en/v0.34.0/configuration/optimization/), so the cache of one replica cannot serve another's requests and tokens are not pooled across replicas. With one context for everyone this equals `ceil(concurrency_high / floor(cached_tokens / tokens_per_request))`.
   - KV cache needed at peak: `demand_tokens` = the sum over groups of in-flight requests × tokens per request; `demand_gb = demand_tokens × kv_bytes_per_token / 10⁹` (1 decimal). `tokens_per_request = demand_tokens / concurrency_high` (rounded to a whole number) and `sequences = cached_tokens / (demand_tokens / concurrency_high)` (2 decimals). `size.py` prints these.
   - A larger group size can need fewer GPUs, because tensor parallelism shards the weights so each GPU has more memory for the KV cache (vLLM optimization guide, https://docs.vllm.ai/en/v0.34.0/configuration/optimization/). The rule keeps the smallest group that holds the weights and the longest request, since tensor parallelism adds synchronization overhead; when a larger group needs fewer GPUs by the memory model, the model gets a note. The note names the larger group with the fewest GPUs (ties go to the smaller group); the comparison is strict, so an equal GPU count gives no note; the GPU counts of the comparison apply step 7's minimum of replicas. The throughput benchmark decides.
6. When architecture numbers are missing: `replicas = 1` and the output states that KV capacity is unknown and must be measured.
7. With `org.downtime_tolerance = none`, `replicas` is at least 2.

Without a GPU, `weights_gb × (1 + overhead)` is compared with `hardware.ram_gb`, and the output warns that CPU inference suits only a few concurrent users.

### 10.3 Totals

- `total_gpus` = sum over models of `replicas × gpus_per_replica`.
- `servers = ceil(total_gpus / gpus_per_server)`, default 8.
- `power_kw = total_gpus × gpu_tdp_w × system_factor / 1000`, default factor 1.8, compared with `hardware.power_budget_kw` when given.
- `fits`: whether `total_gpus` is covered by `hardware.gpus`.

### 10.4 What sizing does not do

It does not predict throughput. Tokens per second depend on the model, the hardware and the shape of the requests. Every blueprint therefore contains a mandatory "benchmark before production" step, and every default used is copied into `assumptions`.

### 10.5 `gpus.toml`

A table of common datacenter and workstation GPUs: model, vendor, VRAM, TDP, source URL, evidence label. The vendor tells the transfer manifest which image variant a GPU needs. A GPU that is not in the table is accepted when the user supplies its VRAM; the power estimate is omitted when TDP is unknown. A GPU is looked up by its model or an alias, ignoring case and punctuation; no two GPU rows share a model or alias after that normalization, and lint reports `C1` when they do, so a name never sizes a design with the wrong memory.

## 11. Catalog

### 11.1 Component entry

One TOML file per component, named after its `id`:

```toml
schema_version = 1
id = "vllm"
name = "vLLM"
layer = "llm-serving"
summary = "OpenAI-compatible inference server for multi-user GPU serving."
tiers = ["T1", "T2", "T3"]
requires = []                   # IDs of components this one needs, e.g. ["postgresql"]
version = "<exact version>"
license = "Apache-2.0"
last_verified = 2026-11-20

[evidence]
level = "docs"                  # field | docs | estimate
sources = ["<URL>"]
verified_by = ""
notes = ""

[airgap]
images = [{ ref = "<registry/repository:tag>", digest = "", hardware = ["nvidia"] }]
packages = []
runtime_downloads = ["model weights"]
telemetry = [{ what = "usage statistics", disable = "<setting>" }]
license_server = false
notes = ""

[choose]
when = ["<condition>"]
avoid_when = ["<condition>"]
alternatives = ["sglang", "ollama"]
caveats = ["<paid-license limits and similar>"]

[[deeper_skills]]
repo = "air-gapped/skills"
skill = "vllm-deployment"
```

`airgap.images` rows are `{ ref, digest, hardware }`. `hardware` names the hardware classes an image is for (`nvidia`, `amd`, `intel`, `cpu`); without it the image is for any hardware. There is one image row per hardware class the project's installation documentation names; aliases of the same image are not listed. Angle-bracket values are filled per component during implementation. `version` is always an exact version, never `latest`, and it is the highest stable version, which is not always the release GitHub marks as latest (a project that patches an older line can publish that patch after a newer release). `airgap.packages` names the files for linux/amd64 (x86_64) hosts exactly as the release names them, and `airgap.notes` gives the files for other architectures; the transfer manifest lists each `airgap.packages` string as a carry item. `requires` drives the `state` layer: PostgreSQL or Valkey is chosen when a chosen component requires it. When other entries list a component in `requires` and their documentation names the versions they support, `version` is the newest release that all of them support, and `airgap.notes` says why.

### 11.2 Evidence policy

| Label | Meaning | Required fields |
|---|---|---|
| `field` | Verified in a real deployment by a named person | `verified_by`, `notes` with hardware and context |
| `docs` | Taken from official project or vendor documentation, or, where the documentation is silent, from the project's source code at the release tag; a statement taken from source code says so | at least one URL in `sources` |
| `estimate` | Reasoned, or taken from community sources | `notes` stating the basis |

The same labels apply to every constant in `rules.toml`, every row in `gpus.toml`, and every row of a decision table.

A decision in a blueprint carries the weakest label among the items it relied on, in the order `estimate`, `docs`, `field`. Decisions that carry `estimate` are listed in the blueprint's verification section.

### 11.3 Freshness

`last_verified` records when an entry was last checked. Lint warns when an entry is older than 180 days.

## 12. Scripts

All scripts require Python 3.11 or newer, import only standard-library modules, and take `--blueprint <path>` and `--catalog <dir>` (default: the skill's own catalog).

| Script | Reads | Writes | Exit codes |
|---|---|---|---|
| `tier.py` | `answers` | `tier` | 0 ok, 2 missing or invalid answers (listed by ID), 3 environment |
| `size.py` | `answers` | `sizing`, `assumptions` | 0 ok, 2 missing or invalid answers, 3 environment |
| `manifest.py` | `decisions`, `workload.models` and `hardware.gpus` from `answers`, catalog | `transfer-manifest.md` | 0 ok, 2 unknown component or no `answers` object, 3 environment |
| `lint.py` | Everything | Report as text or JSON | 0 clean, 1 errors found, 3 environment |

Every script also exits 2 when `blueprint.json` cannot be read, holds a value the scripts cannot use, or, for a script that writes, cannot be written. Exit 3, environment, means that Python is older than 3.11 or that the catalog cannot be read or fails validation; the skill then stops and tells the user.

`lint.py --catalog-only` validates the catalog alone and is used in CI. It reports catalog problems as findings with exit 1; its exit 3 means that Python is too old or that the catalog folder cannot be read.

Lint errors:

| Code | Check |
|---|---|
| E1 | `blueprint.json` matches the schema |
| E2 | Every component ID in `decisions` exists in the catalog |
| E3 | Every chosen component allows the layer's floor tier, or the decision has an override with a reason |
| E4 | Every v1 layer has a decision with a rationale |
| E5 | No escalator is violated without an override |
| E6 | `tier` and `sizing` equal a fresh computation from `answers` |
| E7 | The blueprint file has all template sections, names every chosen component with its version, and has an "Isolation design" subsection when `org.isolation = multi_level` |
| E8 | The transfer manifest exists and its recorded digest matches the current `decisions`, `workload.models` and `hardware.gpus` |
| E9 | Every decision labeled `estimate` appears in the blueprint's verification section, and so does every component in a decision's `benchmark` list |
| E10 | `sizing.fits` is true, or an override explains how the gap is closed |
| E11 | Everything listed in a chosen component's `requires` is itself chosen or named in `existing` |

Lint warnings:

| Code | Check |
|---|---|
| W1 | A catalog entry used by the blueprint was last verified more than 180 days ago |
| W2 | A required answer is "unknown" and a default was used |
| W3 | The agent instruction block is missing from `AGENTS.md` |

Lint notes:

| Code | Check |
|---|---|
| N1 | A decision has an override in effect; the report repeats its reason |

## 13. `blueprint.json`

The single state file, at `docs/airgap/blueprint.json` in the target project. An abbreviated example:

```json
{
  "schema_version": 1,
  "project": "example",
  "created": "2026-11-20",
  "language": "tr",
  "blueprint_path": "docs/superpowers/specs/2026-11-20-example-airgap-blueprint-design.md",
  "answers": { "org.users_total": 180, "org.departments": 4 },
  "assumptions": [
    { "id": "sizing.chat.active", "value": 0.2, "evidence": "estimate", "note": "default" }
  ],
  "tier": {
    "base": "T2",
    "floors": { "llm-gateway": "T2", "identity": "T2" },
    "reasons": ["org.audit_required raises llm-gateway to T2"]
  },
  "sizing": { "concurrency": { "low": 9, "high": 18 }, "total_gpus": 8, "servers": 1, "power_kw": 10.1, "fits": true },
  "decisions": [
    {
      "layer": "llm-gateway",
      "components": ["litellm"],
      "existing": [],
      "custom": [],
      "rationale": "Four departments need separate keys and budgets; audit logging is mandatory.",
      "alternatives_considered": ["kong"],
      "evidence": "docs",
      "override": null
    }
  ]
}
```

- `components` holds catalog IDs to deploy; it may be empty.
- `existing` names infrastructure that is reused and not carried in.
- `custom` names components the user insists on that are not in the catalog. They are labeled `estimate` and appear in the transfer manifest as "enumerate artifacts manually".
- `benchmark` is optional: catalog IDs that are carried in only to be measured against the decision's choice and are never deployed, so they are not in `components`. `references/layers/llm-serving.md` says when an engine goes there. Lint reports a list that is not a list of strings, repeats an ID or repeats one of `components` as E1, an unknown ID as E2, and an ID that the verification section does not name as E9.
- `override` is `null` or `{ "reason": "..." }`.

## 14. Outputs in the target project

```
<project>/
├── docs/superpowers/specs/<date>-<project>-airgap-blueprint-design.md
├── docs/airgap/blueprint.json
├── docs/airgap/transfer-manifest.md
└── AGENTS.md                      one delimited block added
```

When superpowers is not installed, the blueprint is written to `docs/airgap/blueprint.md` instead. `blueprint_path` records which location was used.

### 14.1 Blueprint sections

1. Context: organization shape and constraints.
2. Tier, floors and overrides.
3. Architecture overview with a component diagram.
4. Layer decisions: choice, version, rationale, alternatives, evidence, caveats.
5. Sizing: inputs, concurrency range, GPUs, servers, power, assumptions.
6. Air-gap transfer plan.
7. Data flow: request path and authentication path.
8. Failure modes and operations, including offline upgrades.
9. Verification plan: benchmarks to run and the list of `estimate` decisions.
10. Out of scope and later layers.

The blueprint is written in the language of the interview. Keys and component IDs stay in English.

### 14.2 Transfer manifest

Generated by `manifest.py` from the chosen components:

1. Container images: reference, a `For` column with the hardware classes the image is for, version, digest and size columns to fill at pull time, target registry path. Only the images for the blueprint's hardware are listed: the class is `cpu` without GPUs, otherwise the vendor of the primary GPU (the answer's `vendor`, else its GPU-table row). When the class is unknown every image is listed and the header says so. A chosen component with images but none for the class gets a line after the table that says to check the entry's notes.
2. Model artifacts for every entry in `workload.models`.
3. Packages and binaries.
4. Telemetry and egress settings to switch off before first start.
5. Runtime downloads to stage in advance.
6. Per-tool skills worth carrying inside, from `deeper_skills`.
7. Verification steps: SHA-256 checksums, signature checks where available.

The components in a decision's `benchmark` list follow the chosen ones in sections 1, 3, 4, 5 and 6, each row marked "(benchmark only)", so the manifest stays the one list of what to carry in.

The header records the generation date, a digest of `decisions`, `workload.models` and `hardware.gpus`, which lint uses to detect a stale manifest, and a `Hardware` line with the class the image list was filtered for.

### 14.3 Agent instruction block

A block between `<!-- airgap-architect:start -->` and `<!-- airgap-architect:end -->` in `AGENTS.md`. It tells the implementing agent to follow the blueprint, to use the pinned versions, to assume there is no internet, and to propose any new dependency as a blueprint change instead of adding it. Re-running the skill replaces the block. If the project has a `CLAUDE.md`, the skill asks before adding an `@AGENTS.md` import to it.

## 15. Superpowers integration

Superpowers is a soft dependency.

| Situation | Behavior |
|---|---|
| `superpowers:writing-plans` is available | The blueprint is written to the superpowers spec path. After lint passes and the user approves, the skill invokes `superpowers:writing-plans`. |
| Superpowers is not installed | The blueprint is written to `docs/airgap/blueprint.md`. After approval, the skill prints the next steps itself. |
| `superpowers:brainstorming` is also triggered | One interview only. Brainstorming owns the rhythm and the approval gates; this skill supplies the questions, the decision tables, the scripts and the template. Lint runs as part of the spec self-review. |

In all three cases the skill takes no implementation action before the user approves the blueprint.

## 16. Error handling

| Situation | Handling |
|---|---|
| Required answer missing | `tier.py` or `size.py` exits 2 and lists the IDs; the skill returns to the interview for those questions |
| Answer is "unknown" | Default used, recorded in `assumptions`, lint warning W2 |
| GPU not in `gpus.toml` | The user supplies VRAM; the power estimate is omitted when TDP is unknown |
| Weights do not fit the available hardware | `sizing.fits = false`; the skill presents the options (lower precision, smaller model, a shorter context for a user group, a larger GPU group per replica, more or larger GPUs); lint error E10 until resolved or overridden |
| User wants a component below the floor or outside the catalog | Allowed through `override` or `custom`; shown in the blueprint's overrides list |
| Lint errors | The skill fixes them and re-runs lint; a blueprint with lint errors is never presented as finished |
| Python older than 3.11, or missing | The skill stops and states the requirement |

## 17. Testing

1. **Unit tests** (`unittest`, no extra dependencies) for tier rules, sizing math, catalog loading, manifest generation and every lint rule. Each lint rule has a failing fixture.
2. **Fixed test vectors.** Tier: (50 users, 1 department) is T1; (51, 1) is T2; (20, 2) is T2; (300, 5) is T2; (301, 1) is T3; (50, 6) is T3; (12, 1, audit) is base T1 with an `llm-gateway` floor of T2. Sizing on 141 GB GPUs with defaults: 70B fp8 needs 1 GPU; 70B bf16 needs 2; 235B fp8 needs 4; 671B fp8 needs 8. On a 24 GB GPU, 30B int4 needs 1. With 2,000 users (0.7 chat, 0.2 code_assistant, 0.1 rag; peak 140, 120 and 20 requests in flight) and a 70B fp8 model with 80 layers, 8 KV heads, head dimension 128 and fp16 cache on 141 GB GPUs: contexts of 8192 for every group need 18 replicas of one GPU; chat 8192, code_assistant 32768 and rag 16384 need 40.
3. **Standard-library check.** A test parses every script and fails on any import outside the standard library.
4. **Catalog check in CI.** `lint.py --catalog-only` on every pull request: schema, pinned versions, evidence fields, freshness warnings.
5. **Scenario fixtures**, each with `answers.json` and `expected.json`:
   - `lab`: 12 users, one team, one 24 GB GPU. Expect T1, and an empty gateway is allowed.
   - `department`: 180 users, 4 departments, audit required, eight 141 GB GPUs. Expect T2, a non-empty gateway, identity not local.
   - `enterprise`: 2,000 users, 12 departments, no downtime accepted, existing Kong, OpenShift and directory. Expect T3, a gateway that includes `kong`, at least two engine replicas.
   The deterministic part (tier and sizing) runs in CI without a model.
6. **Skill behavior evals**, run manually before each release following `superpowers:writing-skills`: each scenario is run once without the skill as a baseline and once with it, and once each with and without superpowers installed. Results are recorded under `evals/results/`. A section of the skill that the baseline already gets right is removed.

CI runs on Python 3.11 and on the newest stable Python.

## 18. Distribution and naming

- Claude Code: `/plugin marketplace add <owner>/airgap-anything`, then `/plugin install airgap-anything@airgap-anything-marketplace`.
- Other agents: `npx skills add <owner>/airgap-anything`.
- Offline: the README documents copying `plugins/airgap-anything/skills/airgap-architect/` from a release archive with a SHA-256 checksum.
- Versioning: semantic versioning for the plugin; integer `schema_version` for the catalog and for `blueprint.json`.
- Manifests name the repository owner by GitHub handle. An email address is included only if the owner chooses to.

Naming: the repository and the plugin are named `airgap-anything`, following the "<capability> Anything" pattern, because the long-term scope is every layer. The skill keeps the functional name `airgap-architect`, because agents trigger a skill by its name and description. Skills for later layers join the same repository.

`airgap-anything` and `airgapped-anything` were free on GitHub on 2026-11-20. `architect-anything` is taken by an unrelated agent skill, and `bstrauss84/openshift-airgap-architect` is an OpenShift install wizard; the two-level naming avoids both.

## 19. Risks

| Risk | Mitigation |
|---|---|
| Catalog goes stale | Small catalog, `last_verified`, freshness warnings, pinned versions |
| Thresholds and defaults are guesses | Labeled `estimate`, kept in `rules.toml`, replaced by field data over time |
| The model skips the scripts or ignores a table | Lint as a hard gate; skill behavior evals with baselines |
| Two skills (this one and brainstorming) run two interviews | Explicit rule in `SKILL.md`; an eval scenario with superpowers installed |
| Small and quiet audience | Accepted. The two closest projects had 0 and 6 stars on 2026-11-20. |
| Implementing agent's knowledge of inference tooling is unreliable | Principle 4: every value needs a source or a field note |

## 20. Later sub-projects

Each gets its own spec and plan.

1. Identity and access decision tables.
2. Data layer: database high availability, object storage.
3. CI/CD and the artifact transfer pipeline: Git forge, registry and package mirrors.
4. Observability and audit.
5. Security hardening and compliance packs.
6. Deployment file generation.
7. An interview mode for weak local models.
