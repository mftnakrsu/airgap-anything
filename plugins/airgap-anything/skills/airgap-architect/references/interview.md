# Interview

Goal: fill `answers` in `docs/airgap/blueprint.json`. Ask only what you cannot find out yourself.

Paths such as `catalog/rules.toml` and `catalog/gpus.toml` are relative to the skill root, the folder that holds `SKILL.md`.

## Before the first question

1. Read what the user points you to (README, architecture notes, hardware inventory). Fill every answer those files already give.
2. If `docs/airgap/blueprint.json` does not exist, create it with this content, replacing the three values in capitals:

   ```json
   {
     "schema_version": 1,
     "project": "PROJECT NAME",
     "created": "TODAY AS YYYY-MM-DD",
     "language": "LANGUAGE CODE OF THE CONVERSATION, FOR EXAMPLE en",
     "blueprint_path": "",
     "answers": {},
     "assumptions": [],
     "tier": {},
     "sizing": {},
     "decisions": []
   }
   ```

3. Tell the user in one message which answers you already have and how many questions remain.

## Rules

1. One question per message. Offer the choices from the table.
2. Ask in the user's language. Store IDs and choice values exactly as written here.
3. "I don't know" is an answer: store the string `"unknown"`. The scripts apply the default from `catalog/rules.toml` (`defaults.` followed by the question ID) and record it as an assumption. An optional question without a default (for example `workload.context_tokens`) counts as not answered.
4. Four questions have no default and must be answered: `org.users_total`, `org.departments`, `workload.models`, `hardware.gpus`.
5. Write each answer to `blueprint.json` before you ask the next question, so an interrupted interview can resume.
6. Skip every question that the files or the conversation already answered.

## Questions, in order

| # | ID | Ask | Store |
|---|---|---|---|
| 1 | `org.users_total` | How many people will use the platform? | whole number, 1 or more |
| 2 | `org.departments` | How many departments or teams need their own budget or data boundary? | whole number, 1 or more |
| 3 | `org.isolation` | May departments see each other's prompts and data? | `none` (they may), `per_department` (they may not), `multi_level` (they may not, and data also has classification levels) |
| 4 | `org.audit_required` | Must every request be attributable to a person and retained? | `true` or `false` |
| 5 | `org.downtime_tolerance` | How much downtime is acceptable? | `accepted`, `planned_only`, `none` |
| 6 | `org.ops_capacity` | Who will operate the system? | `part_time_one`, `small_team`, `platform_team` |
| 7 | `org.kubernetes_experience` | Does the operating team run Kubernetes today? | `true` or `false` |
| 8 | `workload.usage` | What will people use it for, in rough shares? | map of `chat`, `code_assistant`, `rag`, `batch` to shares that sum to 1 |
| 9 | `workload.models` | Which model or models will be served? | list, see below |
| 10 | `workload.context_tokens` | How long is a typical request of each group, prompt and history together, in tokens? Ask it when the groups differ. Optional. | map of `chat`, `code_assistant`, `rag` to a whole number of tokens, see below |
| 11 | `hardware.gpus` | Which GPUs exist or will be bought? | list, see below; `[]` when there is no GPU |
| 12 | `hardware.ram_gb` | How much system RAM does the server have? Ask only when there is no GPU. | number |
| 13 | `hardware.power_budget_kw` | How much power is available for this system? Optional. | number |
| 14 | `existing.identity` | Is there an identity provider already? | `none`, `ad_ldap`, `oidc` |
| 15 | `existing.api_gateway` | Is there an API gateway already? | `none`, `kong`, `other` |
| 16 | `existing.kubernetes` | Is there a cluster platform already? | `none`, `kubernetes`, `openshift` |
| 17 | `existing.registry` | Is there an artifact registry already? Optional. | `none`, `harbor`, `nexus`, `artifactory`, `other` |
| 18 | `transfer.channel` | How do files enter the network? | `removable_media`, `data_diode`, `staging_host`, `other` |
| 19 | `transfer.cadence` | How often can updates be carried in? Optional. | `ad_hoc`, `monthly`, `quarterly` |

Usage types: `chat` is conversation in a chat window. `code_assistant` covers agentic coding tools, which keep a request in flight most of the time; people who only use inline completion in an editor are counted under `chat`. That is a deliberate overestimate, not a sourced placement: the notes of `sizing.code_assistant.duty_low` and `sizing.code_assistant.duty_high` in `catalog/rules.toml` show that inline completion keeps a request in flight only a few percent of the time, far below `code_assistant` and far below the duty of `chat`. `rag` is question answering over documents. `batch` is unattended jobs.

## `workload.models`

One object per model.

| Field | Required | Meaning |
|---|---|---|
| `role` | yes | `chat`, `code`, `embedding` or `rerank` |
| `params_b` | one of three | Parameters in billions. Needs `precision`. |
| `weights_gb` | one of three | Size of the weight files in GB. Use it when the user knows it; it overrides arithmetic. |
| `size_class` | one of three | For a user who does not know the model yet: `S` up to 15B, `M` 16B to 80B, `L` 81B to 300B, `XL` above 300B |
| `precision` | with `params_b` | `fp32`, `bf16`, `fp16`, `fp8`, `int8` or `int4`. With `size_class` it is optional: sizing then uses `sizing.default_precision`. |
| `name` | no | Free text |
| `context_tokens` | no | Typical prompt plus history length in tokens. Sizing uses it for every user group that has no entry in `workload.context_tokens`. |
| `arch` | no | `layers`, `kv_heads`, `head_dim` and optionally `kv_dtype` (one of the precision values; the default is `sizing.default_kv_dtype`). With these, sizing computes KV-cache capacity; without them it reports the capacity as unknown. |

Give exactly one of `params_b`, `weights_gb` and `size_class`.

The `arch` numbers come from the model's configuration file: the number of hidden layers (`num_hidden_layers`), the number of key-value heads (`num_key_value_heads`; when the field is absent, `num_attention_heads`), and the head dimension (`head_dim`; when the field is absent, `hidden_size` divided by `num_attention_heads`). Read `head_dim` from the file when it is there: it can differ from that division.

Example:

```json
[
  {
    "name": "main chat model",
    "role": "chat",
    "params_b": 70,
    "precision": "fp8",
    "arch": { "layers": 80, "kv_heads": 8, "head_dim": 128 }
  },
  { "role": "embedding", "weights_gb": 2.5 },
  { "role": "code", "size_class": "M" }
]
```

## `workload.context_tokens`

Optional. A map of `chat`, `code_assistant` and `rag` to the context of one request of that group, as a whole number of tokens above 0. `batch` is rejected: it has no interactive context.

The context of a group's request is its entry here; without one, the model's `context_tokens`; without that, `sizing.default_context_tokens`. Sizing adds `sizing.default_output_tokens` to every request. A key for a group that has no share in `workload.usage` has no effect.

Give it when the groups differ. Example, coding assistants 32k and chat 8k:

```json
{ "code_assistant": 32768, "chat": 8192 }
```

## `hardware.gpus`

One object per GPU model.

| Field | Required | Meaning |
|---|---|---|
| `model` | yes | GPU model name, entered only as the user names it. When the user gives memory (and power) but no model, enter a descriptive name such as "unnamed 141 GB GPU" with `vram_gb` (and `tdp_w`), and `vendor` only if the user states it. A catalog row whose numbers match is a guess: do not enter its name as the answer. Name it as an open question in section 1, Context, of the blueprint, because it would also decide the manifest's hardware class and so the images carried in. |
| `count` | yes | How many, 1 or more. A planned purchase counts: enter the number the user intends to buy. |
| `vram_gb` | when the model is not in `catalog/gpus.toml` | Memory per GPU in GB |
| `vendor` | no | `nvidia`, `amd` or `intel`, entered only as the user states it. The transfer manifest lists the container images for the blueprint's hardware class, taken from the vendor of the primary GPU (`cpu` when `hardware.gpus` is `[]`); a model in `catalog/gpus.toml` supplies its own vendor. When the vendor is unknown, the manifest's `Hardware:` line says unknown and it lists every vendor's image rows, each naming its hardware in the `For` column. That costs carry volume. Name the vendor as an open question in section 1, Context, of the blueprint, which asks the user for it. |
| `tdp_w` | no | Power per GPU in watts, for the power estimate |

A GPU name that fits several variants with different memory (for example `H100` or `A100`) matches no row of the GPU table, on purpose. Ask which variant it is, or ask for `vram_gb` and `vendor`.

Example: `[{ "model": "example-gpu", "count": 8, "vram_gb": 48, "vendor": "nvidia" }]`. With no GPU, store `[]` and ask `hardware.ram_gb`.

## After the last question

Run `tier.py`, then `size.py`. Exit code 2 lists the question IDs to go back to.
