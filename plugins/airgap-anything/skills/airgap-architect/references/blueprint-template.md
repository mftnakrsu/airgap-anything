# Blueprint template

Copy everything below the line into the blueprint file and fill each section. Headings and prose may be in the user's language; question IDs, choice values, component IDs and versions stay exactly as the interview and the catalog write them.

---

# PROJECT NAME: air-gapped blueprint

Status: draft. Date: YYYY-MM-DD. Language: the code of the conversation's language, for example en. Oldest catalog entry used: YYYY-MM-DD (component ID).

## 1. Context and answers

Who the system is for and what constrains it, in a short paragraph.

| Question | Answer | From |
|---|---|---|
| `org.users_total` | 180 | the user |
| `org.isolation` | `per_department` | `unknown`, default |

One row per question of `references/interview.md` that has an answer. "From" is the user, a file (name it), or "`unknown`, default".

Open questions: the GPU model or vendor when it was not named, and anything else the user should still answer.

## 2. Tier, floors and overrides

The base tier and why. A table of the eight layers and their floors. Every raised floor with the answer that raised it, every obligation, every override with the user's reason, and every custom part.

## 3. Architecture overview

One paragraph, then a component diagram (Mermaid or plain text): users, UI, gateway, engine, identity, state, observability, registry, with the chosen component in each box.

## 4. Layer decisions

| Layer | Component | Version | Evidence |
|---|---|---|---|
| `llm-serving` | `vllm` | `v0.34.0` | estimate |
| `llm-serving` | `sglang` (benchmark only) | `v0.5.23` | estimate |

One row per component, versions copied from the catalog. Evidence is the decision's label (the weakest of its guide's case and its components), not the catalog entry's own. Then one subsection per layer, in this order: `llm-serving`, `llm-gateway`, `ui`, `identity`, `observability`, `orchestration`, `state`, `registry`.

### `llm-serving`

- Components: catalog IDs with versions, or none
- Existing: infrastructure that already runs and is reused, or none
- Custom: parts with no catalog entry, or none
- Benchmark only: engines carried in only to be measured, or none
- Rationale: why this choice, with the caveats from the catalog entry that apply
- Alternatives considered: each option weighed, with why it lost
- Evidence: `estimate`, `docs` or `field`
- Override: none, or the user's reason for going below a floor or accepting hardware that does not fit

### Isolation design

Only when `org.isolation` is `multi_level`: which engine instances, keys, networks and stores are separate per classification level, and who may cross a boundary.

## 5. Sizing

Inputs: users, usage shares, contexts per group, models, GPUs. Then every step of `references/sizing.md` with its numbers, so that a reader can check each one. Then:

| Model | GPUs per replica | Replicas | GPUs | KV cache |
|---|---|---|---|---|

Concurrency as a range; total GPUs, servers, whole-system power; whether the hardware fits; every note and warning. Last, the assumptions table, with its value and evidence label for each row: one row per interview answer that was `unknown` (with the default used), and one per constant the steps used, the GPU group sizes and the KV type included.

## 6. Air-gap transfer

How files enter the network (`transfer.channel`, `transfer.cadence`), who carries them, where they land first and how they are checked. Link `docs/airgap/transfer-manifest.md`, the list of everything to carry in. The telemetry and egress settings to switch off before first start, copied from its section 4. Who works inside (`inside.operator`) and what they receive: a runbook for people, rules for an agent, or both. The next step is `airgap-transfer`, which turns the manifest into a checked bundle.

## 7. Data flow

The path of one request from the user to the model and back, naming every component it crosses. Where identity is checked, how a request is tied to a person and a department, and where that is logged.

## 8. Failure modes and operations

What happens when each component fails and how it is noticed. Backups of state. How upgrades are carried in and applied without internet, and by whom.

## 9. Verification plan

1. Benchmark before production: tokens per second and time to first token at `concurrency.high` on the real hardware, and KV-cache capacity where sizing could not compute it, with the load generator the transfer manifest lists.
2. One entry per decision whose evidence is `estimate`: the layer ID, what the estimate is, and how to check it.
3. `org.kubernetes_experience` as a risk, when the orchestration floor is T3 and the team does not run Kubernetes.
4. Every benchmark a layer guide asked for, naming the engine.
5. Every chosen catalog entry last verified more than 180 days before the blueprint's date: re-check its sources before relying on it.

## 10. Out of scope

What this blueprint does not decide: deployment files, the choice of model, data, CI/CD, security layers, compliance mapping.
