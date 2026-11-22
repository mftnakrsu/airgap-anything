# Inference engine (`llm-serving`)

Read `sizing.cpu_only`, `sizing.concurrency.high`, `answers` and `tier.floors["llm-serving"]` from `blueprint.json`. Take the first row that matches. Skip a row when the `tiers` list in the component's catalog entry does not include the floor.

| # | Condition | Choose | Evidence | Basis |
|---|---|---|---|---|
| 1 | `sizing.cpu_only` is true | `ollama` | estimate | Ollama's Docker page gives a CPU-only run command, but vLLM also has a CPU build (FP32, FP16 and BF16, basic serving) and SGLang is documented on CPUs only for Intel Xeon with AMX, so the other two engines do not strictly need a GPU, and no documentation ranks Ollama first on a CPU host: https://github.com/ollama/ollama/blob/v0.40.17/docs/docker.mdx https://github.com/vllm-project/vllm/blob/v0.34.0/docs/getting_started/installation/cpu.x86.inc.md https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/hardware-platforms/cpu_server.mdx |
| 2 | `sizing.concurrency.high` is 4 or less and `org.ops_capacity` is `part_time_one` | `ollama` | estimate | Ollama documents parallel requests per loaded model (`OLLAMA_NUM_PARALLEL`, 1 on the backends other than MLX on Metal) and a request queue (`OLLAMA_MAX_QUEUE`, 512, then HTTP 503) but no continuous batching, so a handful of requests at once needs that setting raised; the limit of 4 and the part-time operations condition are the spec's thresholds, not documented: https://github.com/ollama/ollama/blob/v0.40.17/docs/faq.mdx |
| 3 | The `code_assistant` and `rag` shares in `workload.usage` add up to 0.5 or more | `vllm`, and add "benchmark `sglang` on this workload" to the verification section | estimate | vLLM lists continuous batching, chunked prefill and prefix caching, and SGLang lists RadixAttention and prefix caching, but neither page benchmarks one engine against the other, so which engine is faster on shared-prefix work is not documented, and the 0.5 share is a spec threshold: https://github.com/vllm-project/vllm/blob/v0.34.0/README.md https://github.com/sgl-project/sglang/blob/v0.5.23/docs/index.mdx |
| 4 | Otherwise | `vllm` | estimate | vLLM's README lists continuous batching of incoming requests, but no page compares vLLM with SGLang for general serving, so vLLM as the default over SGLang is not documented: https://github.com/vllm-project/vllm/blob/v0.34.0/README.md |

Choose `sglang` directly only when its catalog entry carries `field` evidence for this kind of workload, or the user supplies their own measurements. Say so in the rationale.

A `sizing.cpu_only` design at a T3 floor skips rows 1 and 2, because the `ollama` entry's tiers exclude T3, and lands on `vllm` through row 3 or 4. It uses vLLM's CPU build (the `vllm/vllm-openai-cpu` image, which the transfer manifest lists for hardware class `cpu`). The rationale states the limits of that build from `choose.avoid_when` in `catalog/components/vllm.toml` (x86 CPU: FP32, FP16 and BF16, basic serving, AVX512 recommended). Stop and tell the user only if those limits do not meet the need.

When no row leaves a usable component, stop and tell the user. The way forward is different hardware or an override.

## Writing the decision

1. Read the chosen component's catalog entry, `catalog/components/` followed by the ID and `.toml`: `choose.when`, `choose.avoid_when`, `choose.caveats` and `airgap`. A caveat that applies goes into the rationale.
2. List the other engines in `alternatives_considered`.
3. Say what the entry says about concurrency and nothing beyond it:
   - `vllm`: continuous batching, with the queue settings `--max-num-seqs`, `--max-num-batched-tokens`, `--max-num-queued-reqs` and `--max-num-queued-tokens`.
   - `sglang`: the entry found a continuous-batching statement only in the SGLang Model Gateway section of its RL guide, about rollout serving, and none for the server in general. Its scheduler settings are `--max-running-requests` and `--max-queued-requests`, both unset by default. Do not call SGLang a continuous-batching engine in a general sense, and do not call it faster or slower than `vllm` without a measurement.
   - `ollama`: parallel requests per loaded model (`OLLAMA_NUM_PARALLEL`) and a request queue (`OLLAMA_MAX_QUEUE`), with no mention of continuous batching.
4. `sizing.gpu_memory_utilization` is the sizing assumption of `catalog/rules.toml` (the design spec's starting value), not an engine default. Do not describe it as one. If the decision states a GPU memory setting, say it comes from sizing. For `vllm`, the note of `[sizing.gpu_memory_utilization]` in `catalog/rules.toml` gives the default vLLM v0.34.0 documents (1.0 on CUDA and ROCm with the extensible KV cache, 0.92 elsewhere); take it from there. The `sglang` and `ollama` entries state no such default, so the decision records "not documented in the catalog" for them. Do not fill it from memory.
5. Set `evidence` to the weakest of this row's label and the `evidence.level` of the chosen component. The order from weakest to strongest is `estimate`, `docs`, `field`.

6. An engine that a benchmark names (row 3's `sglang`, or any other engine the decision mentions) is carried in only to be measured. Put its ID into this decision's `benchmark` list, never into `components`, and run `manifest.py` again: the transfer manifest then lists it in every section, marked "(benchmark only)". Name the benchmark and the engine in the verification section; lint reports a `benchmark` engine that section does not name (E9). If the engine has no image row for the design's hardware class (`catalog/components/sglang.toml` has none for AMD), do not put it in `benchmark`: leave row 3's benchmark out of the verification section, and say in the rationale that the engine has no image for this hardware, so row 3's benchmark is not carried.

Components used in this file: `ollama`, `vllm`, `sglang`.
