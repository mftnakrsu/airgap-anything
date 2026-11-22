# Blueprint template

Write the blueprint to the path stored in `blueprint_path`. Copy everything below the line, then fill each section.

Rules:

1. Keep every `<!-- airgap:section ... -->` marker exactly as written and in this order. Lint finds the sections by these markers, so headings and text may be in the user's language.
2. Component IDs, question IDs and versions stay as they are in `blueprint.json` and the catalog.
3. Every number comes from `blueprint.json`. Copy; do not recompute.
4. In section 4, each chosen component gets one table row that contains both its ID and its version.
5. Add the "Isolation design" subsection, with its marker, only when `tier.requirements.isolation_design_section` is true.

---

<!-- airgap:section context -->
## 1. Context

Who the system is for and what constrains it: users, departments, isolation, audit, downtime tolerance, who operates it, what already exists, how files enter the network. State each as a fact from `answers`. List every answer that was "unknown" and the default that was used.

<!-- airgap:section tier -->
## 2. Tier, floors and overrides

Base tier and what it means. The floor of each layer as a table. Every entry of `tier.reasons`. Every decision that carries an override, with its reason, and every custom component.

<!-- airgap:section architecture -->
## 3. Architecture overview

One paragraph, then a component diagram (Mermaid or plain text) that shows users, UI, gateway, engine, identity, state, observability and registry, with the chosen component named in each box.

<!-- airgap:section decisions -->
## 4. Layer decisions

One subsection per layer, in the order of `decisions`. Start with this table, one row per chosen component:

| Layer | Component | Version | Evidence |
|---|---|---|---|

Then, for each layer: the rationale, the alternatives considered, the caveats from the catalog entry that apply, and what is reused from existing infrastructure. A layer with nothing to deploy still gets its rationale.

<!-- airgap:section isolation-design -->
### Isolation design

Only when required. How classification levels are kept apart: which engine instances, keys, networks and stores are separate per level, and who may cross a boundary.

<!-- airgap:section sizing -->
## 5. Sizing

Inputs (users, usage shares, the context per group when `workload.context_tokens` was given, models, GPUs). The concurrency range. Per model: GPUs per replica, replicas, KV-cache status, the KV cache needed at peak (`kv.demand_gb`), how many requests one replica holds (`kv.sequences`) and the context per group (`kv.context_by_usage`). Totals: GPUs, servers, power. Whether the hardware fits. Every entry of `sizing.warnings` and of each model's `notes`. The full `assumptions` list as a table with ID, value and evidence.

<!-- airgap:section transfer -->
## 6. Air-gap transfer plan

How artifacts enter the network (`transfer.channel`, `transfer.cadence`), who carries them, where they land first, and how they are checked. Link to `docs/airgap/transfer-manifest.md` for the list itself. The manifest's `Hardware:` line must match the design's GPUs; when it says unknown, carry only the image rows for the hardware. Package files are for linux/amd64 hosts: on arm64 hosts, carry the files that the entries' notes name instead. Name the telemetry settings that must be off before first start.

<!-- airgap:section data-flow -->
## 7. Data flow

The path of one request from the user to the model and back, naming each component it crosses. The authentication path: where identity is checked, how a request is tied to a person and a department, and where that is logged.

<!-- airgap:section operations -->
## 8. Failure modes and operations

What happens when each component fails and how it is noticed. Backups of state. How upgrades are carried in and applied without internet access.

<!-- airgap:section verification -->
## 9. Verification plan

1. Benchmark before production: measure tokens per second and time to first token at `concurrency.high` on the real hardware, and KV-cache capacity when sizing reported it as unknown.
2. One entry per decision whose evidence is `estimate`: write the layer ID, what the estimate is, and how to check it.
3. `org.kubernetes_experience`, as a risk, when `tier.requirements.kubernetes_risk_note` is true.
4. Any benchmark a decision table asked for. Each engine a benchmark names is in that decision's `benchmark`, so the transfer manifest carries it, marked "(benchmark only)".

<!-- airgap:section out-of-scope -->
## 10. Out of scope and later layers

What this blueprint does not decide: deployment files, the choice of model, data, CI/CD and security layers, compliance mapping.
