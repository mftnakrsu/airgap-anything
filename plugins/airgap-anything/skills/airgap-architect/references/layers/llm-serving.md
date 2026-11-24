# Inference engine (`llm-serving`)

**Default: `vllm`.** Change it only for one of the cases below, and skip any engine whose catalog `Tiers` row does not include the `llm-serving` floor.

| Case | Choose | Evidence | Why |
|---|---|---|---|
| No GPU (sizing is CPU only) | `ollama` | estimate | Ollama's Docker page gives a CPU-only run command (https://github.com/ollama/ollama/blob/v0.40.17/docs/docker.mdx). vLLM also has a CPU build (FP32, FP16 and BF16, basic serving) and SGLang runs on CPUs only for Intel Xeon with AMX, so no documentation ranks Ollama first; it is the simpler one to run (https://github.com/vllm-project/vllm/blob/v0.34.0/docs/getting_started/installation/cpu.x86.inc.md, https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/hardware-platforms/cpu_server.mdx). |
| A handful of requests at once (`concurrency.high` 4 or less) and one part-time operator (`org.ops_capacity` = `part_time_one`) | `ollama` | estimate | Ollama documents parallel requests per loaded model (`OLLAMA_NUM_PARALLEL`) and a queue (`OLLAMA_MAX_QUEUE`, 512, then HTTP 503) but no continuous batching, so it suits a few requests; the limit of 4 and the operator condition are the design's thresholds (https://github.com/ollama/ollama/blob/v0.40.17/docs/faq.mdx). |
| Shared-prefix work: the `code_assistant` and `rag` shares add up to 0.5 or more | `vllm`, and benchmark `sglang` on this workload | estimate | vLLM lists continuous batching, chunked prefill and prefix caching; SGLang lists RadixAttention and prefix caching; neither benchmarks one against the other, so which is faster here is not documented, and 0.5 is the design's threshold (https://github.com/vllm-project/vllm/blob/v0.34.0/README.md, https://github.com/sgl-project/sglang/blob/v0.5.23/docs/index.mdx). |
| Anything else | `vllm` | estimate | vLLM batches incoming requests continuously; no page compares it with SGLang for general serving, so the default itself is the design's choice (https://github.com/vllm-project/vllm/blob/v0.34.0/README.md). |

Choose `sglang` as the engine itself only when its catalog entry carries `field` evidence for this kind of workload or the user brings their own measurements, and say so in the rationale.

A CPU-only design at a T3 floor cannot take `ollama` (its tiers exclude T3). It takes `vllm` with the CPU build (`vllm/vllm-openai-cpu`, the image for hardware `cpu`) and states the limits from the `vllm` entry's "Avoid when" (x86: FP32, FP16 and BF16, basic serving, AVX512 recommended). Stop and tell the user only if those limits do not meet the need.

When no engine is left, stop and tell the user: the way forward is different hardware or an override.

## Writing the decision

1. Read the chosen engine's catalog entry: "Choose when", "Avoid when", "Caveats" and "Carry in". Every caveat that applies goes into the rationale.
2. Alternatives considered: the other engines, each with the reason it lost.
3. Say what the entry says about concurrency and nothing beyond it:
   - `vllm`: continuous batching, with the queue settings `--max-num-seqs`, `--max-num-batched-tokens`, `--max-num-queued-reqs` and `--max-num-queued-tokens`.
   - `sglang`: the entry found a continuous-batching statement only for rollout serving in its RL guide, not for the server in general. Its scheduler settings are `--max-running-requests` and `--max-queued-requests`, both unset by default. Do not call it faster or slower than `vllm` without a measurement.
   - `ollama`: parallel requests per loaded model (`OLLAMA_NUM_PARALLEL`) and a queue (`OLLAMA_MAX_QUEUE`), no continuous batching.
4. The 0.90 share of GPU memory is a sizing assumption, not an engine default. vLLM v0.34.0 documents 1.0 on CUDA and ROCm and 0.92 elsewhere; the `sglang` and `ollama` entries state no default, so write "not documented in the catalog" for them.
5. An engine carried in only to be measured (the `sglang` benchmark above, or any engine the decision wants to compare) goes under "Benchmark only", never under "Components". The transfer manifest lists it marked "(benchmark only)", and the verification section names the benchmark and the engine. When that engine has no image for the design's hardware (the `sglang` entry has none for AMD), leave the benchmark out and say why in the rationale.
6. Departments that must not see each other (`org.isolation` other than `none`) and share one engine: read the engine entry's caveat on its prefix cache (`vllm`, `sglang`) and say in the rationale which separation the design uses: an instance per department, prefix caching off (`--no-enable-prefix-caching` for `vllm`, `--disable-radix-cache` for `sglang`), or a gateway that sets a secret per-department `cache_salt` on every request. No gateway entry in the catalog documents setting that salt. Keeping departments apart only in the UI does not isolate their cached prompts.
7. Evidence: the weakest of the case's label and the chosen components' labels (`estimate` < `docs` < `field`).

Components used in this file: `ollama`, `vllm`, `sglang`.
