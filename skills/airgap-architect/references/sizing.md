# Sizing

Script, catalog and reference paths in this file are relative to the skill root, the folder that holds `SKILL.md`. Run a script by its full path (the skill root joined with `scripts/NAME.py`) from the project root, so that `docs/airgap/blueprint.json` resolves.

Run:

```bash
python3 scripts/size.py --blueprint docs/airgap/blueprint.json
```

It writes `sizing` and `assumptions` into `blueprint.json`. Never type or adjust one of these numbers yourself. To change a result, change the answer and run the script again.

## Reading `sizing`

| Field | Meaning | What you do with it |
|---|---|---|
| `concurrency.low`, `concurrency.high`, `concurrency.by_usage` | Requests in flight at the peak, as a range, and the same split by usage type. Batch work is not included. | Use `high` in the engine decision table. Show the range, never one number. |
| `gpu` | The GPU type sizing used: the one with the most memory. | If the user listed several types, say that the others were ignored. |
| `models[].gpus_per_replica` | GPUs one copy of the model spans: the smallest allowed GPU group that holds the weights and, when KV figures exist, one request of the longest context. `null` means the weights fit no allowed group. | `null` makes `fits` false. |
| `models[].kv.status` | `computed`: KV-cache capacity was calculated. `unknown`: no architecture numbers were given. `insufficient`: the KV cache cannot hold one request of the longest group context on the largest allowed GPU group. `not_applicable`: embedding or rerank model, no GPU, or any model whose weights fit no allowed GPU group (its `gpus_per_replica` is then `null`). | For `unknown`, ask for the `arch` numbers or put a KV-capacity benchmark in the verification section. `insufficient` makes `fits` false, and so does `not_applicable` for a model whose weights fit no group (the `gpus_per_replica` `null` case). |
| `models[].kv` (when `computed` or `insufficient`) | `bytes_per_token`; `cached_tokens`, the tokens one replica's KV cache holds; `tokens_per_request`, the average request (context plus output); `sequences`, how many such requests one replica holds, as a decimal; `demand_tokens` and `demand_gb`, the KV cache needed at peak; `context_by_usage` and `in_flight_by_usage`, the context and the requests in flight of each usage type. | Quote `demand_gb`, `sequences` and `context_by_usage` in the sizing section. |
| `models[].replicas` | Copies of the model. They come from packing the requests in flight into replicas, each replica holding whole requests. At least 2 when no downtime is accepted. Only the status `computed` packs requests; with `unknown`, `not_applicable` or `insufficient` it is that minimum only (1, or 2 when no downtime is accepted). | Quote it in the sizing section. |
| `models[].notes` | Remarks on this model, for example when a larger GPU group would need fewer GPUs in total, or that its KV capacity is unknown. | Copy each into the sizing section. |
| `total_gpus`, `servers`, `power_kw` | Totals. `power_kw` is `null` when the GPU's power draw is unknown. | Quote them with the assumptions. |
| `power_within_budget` | `false` when the estimate exceeds `hardware.power_budget_kw`. | Tell the user; it is a warning, not a lint error. |
| `fits` | Whether every model can be placed (no `null` in `gpus_per_replica`, no `insufficient` KV status) and `total_gpus` does not exceed the count of the GPU type in `gpu`. Without a GPU: whether `hardware.ram_gb` covers `ram_required_gb`. | See below when it is `false`. |
| `warnings` | Plain-language caveats for the whole sizing. | Copy each into the sizing section. |

`size.py` also prints a summary. Per model it prints a KV-cache line (the KV cache needed at peak, and how many requests one replica holds), and when the user groups have different contexts, a context-per-group line. Its `note:` lines are the model's `notes`; its `!` lines are the `warnings`.

## When `fits` is false

Present the options and let the user choose:

1. A lower precision or a quantized build of the same model.
2. A smaller model.
3. More GPUs, or GPUs with more memory.
4. A shorter context for one user group (`workload.context_tokens`).
5. A larger GPU group per replica, when a model's `notes` say that one needs fewer GPUs and that count fits the GPUs given. `size.py` keeps the smallest group, because tensor parallelism adds synchronization overhead, so `fits` stays false: record the choice as the override below, with a reason that quotes the note, and name a throughput benchmark of that group in the verification section.

For options 1 to 4, change the answers accordingly and run `size.py` again. If the user decides to proceed anyway, for example because more hardware is on order, record that on the `llm-serving` decision: `"override": { "reason": "..." }`. Lint error E10 stays until `fits` is true or that override exists.

## A what-if

To compare a variant (for example `org.downtime_tolerance` set to `none`), copy `docs/airgap/blueprint.json` to a file under `docs/airgap/`, for example `docs/airgap/what-if-no-downtime.json`. Change the answer in the copy and run `size.py --blueprint` on the copy. The numbers it writes are `size.py`'s output on the copy, not the design's numbers. Quote them labelled as a what-if, with the answer that changed (for example "What-if, `org.downtime_tolerance` = `none`: ..."), next to the design's own numbers from `docs/airgap/blueprint.json` and never in place of them. Delete the copy when you are done.

## `assumptions`

Every default the script used is listed with its evidence label. Copy the list into the blueprint's sizing section. Each one is a number somebody should replace with a measurement.

## What sizing does not tell you

It does not predict throughput. Tokens per second depend on the model, the hardware and the shape of the requests. Every blueprint therefore carries a "benchmark before production" step in its verification section.

## Exit code 2

The script lists the question IDs that are missing or invalid, for example a GPU that is not in `catalog/gpus.toml` and has no `vram_gb`. Go back to the interview for those, then run it again.
