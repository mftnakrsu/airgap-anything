# Sizing

Sizing turns the answers into GPU memory, GPU count, servers and power. It sizes memory by arithmetic, because published throughput numbers for inference engines conflict. It does not predict tokens per second; that is why every blueprint carries a benchmark step.

Show your work. Write every step's inputs and result into the blueprint's sizing section, so that a reader can check each number with a calculator. Do the arithmetic step by step, keep the units, and round only where a step says so.

## Contents

- Constants
- The procedure, steps 1 to 9
- Worked examples: department (KV unknown), enterprise (KV known), mixed contexts, CPU only
- When the hardware does not fit
- A what-if

## Constants

Every value is `estimate` unless it says otherwise. List the ones a design used in its assumptions table, so that somebody can replace them with measurements.

| Constant | Value | Basis |
|---|---|---|
| Chat and rag: share of users active in the peak hour | 0.20 | Unmeasured; only active × duty is anchored (next rows). |
| Chat and rag: share of time an active user has a request in flight | 0.25 low, 0.50 high | Set so that active × duty is 5 % to 10 % of users in flight. NVIDIA's RAG sizing guide: "a good estimate of peak usage for the Chat service is 10% of total users", 5 % its lowest sensitivity row (https://docs.nvidia.com/enterprise-reference-architectures/enterprise-rag-retrieval-scaling-and-sizing-guide/latest/rag-sizing-guidelines.html). |
| Code assistant: active in the peak hour | 0.30 | Unsourced. |
| Code assistant: in flight | 0.70 low, 1.00 high | Models agentic coding tools, which keep a request in flight most of the time; unsourced. Inline completion is far lower: GitHub telemetry gives 158 completion opportunities per active hour, a duty of a few percent (https://arxiv.org/pdf/2205.06537). |
| Bytes per parameter | fp32 4, bf16 2, fp16 2, fp8 1, int8 1, int4 0.5 | Arithmetic; int4 ignores quantization metadata. |
| Memory overhead on top of the weights | 10 % | Starting value of the design. |
| Share of GPU memory the engine may use | 0.90 | Starting value of the design, below what engines document: vLLM v0.34.0 documents 1.0 on CUDA and ROCm and 0.92 elsewhere (https://github.com/vllm-project/vllm/blob/v0.34.0/docs/configuration/optimization.md). It is a sizing assumption, not an engine default; never present it as one. |
| GPUs one replica may span | 1, 2, 4 or 8 | Common server sizes. vLLM accepts any tensor-parallel size (https://github.com/vllm-project/vllm/blob/v0.34.0/docs/serving/parallelism_scaling.md). |
| Context per request when nothing else is known | 8,192 tokens | Chosen by the design, not measured. |
| Output tokens per request | 1,024 | Chosen by the design, not measured. |
| KV-cache element type when the model does not state one | fp16 (2 bytes) | |
| Parameters of a size class, in billions | S 8, M 32, L 120, XL 671 | Representative values; precision bf16 when none is given. |
| Minimum replicas when `org.downtime_tolerance` is `none` | 2 | |
| GPUs per server | 8 | |
| Whole-system power ÷ GPU power | 1.8 | |

## The procedure

Do the steps for every model in `workload.models`.

### 1. Concurrency

For each interactive group (`chat`, `code_assistant`, `rag`) with a share in `workload.usage`:

- low = users × share × active × in-flight low
- high = users × share × active × in-flight high

`batch` is unattended work: leave it out of concurrency.

`concurrency.low` = the sum of the lows, rounded up to a whole number, at least 1. `concurrency.high` the same with the highs. Always present the range, never one number.

### 2. Which GPU

The GPU type with the most memory per GPU (on a tie, the larger count). Take its memory and power from `references/gpus.md`, or from the user's answer when it is not there. When the user listed several types, say that sizing used only this one.

### 3. Weights

- `weights_gb` given: use it.
- `params_b` given: params_b × bytes per parameter of its `precision`.
- `size_class` given: the class's parameters × bytes per parameter (bf16 unless a precision is given).

Required memory = weights × 1.10.

### 4. Smallest GPU group

Usable memory of a group = GPUs in the group × memory per GPU × 0.90. Take the smallest group of 1, 2, 4 or 8 whose usable memory is at least the required memory. When even 8 is too small, the model does not fit: go to "When the hardware does not fit".

### 5. KV cache

This step needs the model's architecture (`arch`: `layers`, `kv_heads`, `head_dim`, optionally `kv_dtype`) and applies only to generative models (`role` `chat` or `code`). An embedding or rerank model skips to step 6 with the minimum replicas.

Without `arch`, KV capacity is unknown. Write that in the sizing section, use the minimum replicas in step 6, and put a KV-capacity benchmark in the verification section. You may add, labelled as arithmetic, the largest KV cost per token the remaining memory allows at the peak (usable − required, divided by the peak requests × their tokens), and list the constants it uses. Ask for the numbers when the user can get them: they are in the model's `config.json` (`num_hidden_layers`, `num_key_value_heads`, else `num_attention_heads`, and `head_dim`, else `hidden_size` ÷ `num_attention_heads`).

With `arch`:

- bytes per token = 2 × layers × kv_heads × head_dim × bytes of `kv_dtype`
- cached tokens per replica = (usable − required) × 10^9 ÷ bytes per token, rounded down
- tokens per request of each group = its context + 1,024. The context of a group is its entry in `workload.context_tokens`, else the model's `context_tokens`, else 8,192.

When the cached tokens cannot hold one request of the longest group, take the next larger group (back to step 4) until they can. If none of 1, 2, 4, 8 can, the KV cache is insufficient: the model does not fit.

### 6. Replicas

- Minimum = 2 when `org.downtime_tolerance` is `none`, otherwise 1.
- With KV computed, a replica holds whole requests. For each group: in flight = its high from step 1, rounded up; requests per replica = cached tokens ÷ its tokens per request, rounded down.
- replicas = the larger of the minimum and (the sum over the groups of in flight ÷ requests per replica, rounded up at the end).
- Without KV figures: replicas = the minimum.

KV cache needed at peak, for the sizing section = sum over the groups of in flight × tokens per request × bytes per token ÷ 10^9 GB.

### 7. A larger group per replica

With KV computed, repeat steps 5 and 6 for each larger group size that still fits. When one needs fewer GPUs in total (replicas × group), keep the smallest group in the design and add a note, for example: "with 4-GPU replicas the memory model needs 8 GPUs instead of 18; tensor parallelism adds synchronization overhead, so benchmark throughput before choosing it". The user may choose it as an override (see below).

### 8. Totals

- GPUs of a model = replicas × group. Total GPUs = the sum over the models.
- Servers = total GPUs ÷ 8, rounded up, at least 1.
- Whole-system power = total GPUs × power per GPU × 1.8 ÷ 1000 kW, rounded to one decimal: the factor 1.8 already covers the rest of the server. Unknown GPU power: say power is unknown. Compare it with `hardware.power_budget_kw` when given, and warn when it is above.

### 9. Fits

The hardware fits when every model was placed (no model failed step 4 or step 5) and the total GPUs are no more than the count of the GPU type from step 2.

### Without a GPU

`hardware.gpus` is `[]`. Required RAM = the sum of every model's required memory (step 3). It fits when `hardware.ram_gb` covers it. Servers 1; power unknown. Warn that CPU inference suits only a few concurrent users and needs a benchmark. The engine decision (`references/layers/llm-serving.md`) reads this case.

## Worked examples

### Department: KV unknown

180 users, chat only, downtime `planned_only`; one 671B model at fp8, no `arch`; eight GPUs of 141 GB and 700 W.

1. Concurrency: low 180 × 1.0 × 0.20 × 0.25 = 9; high 180 × 1.0 × 0.20 × 0.50 = 18. Range 9 to 18.
2. GPU: 141 GB, 700 W.
3. Weights 671 × 1 = 671 GB; required 671 × 1.10 = 738.1 GB.
4. Usable: 1 GPU 126.9, 2 GPUs 253.8, 4 GPUs 507.6, 8 GPUs 1,015.2 GB. Smallest that holds 738.1: 8 GPUs.
5. No `arch`: KV capacity unknown; benchmark it.
6. Replicas: minimum 1.
8. GPUs 1 × 8 = 8; servers 1; power 8 × 700 × 1.8 ÷ 1000 = 10.08, so 10.1 kW.
9. 8 needed, 8 available: fits.

### Enterprise: KV known

2,000 users, 70 % chat, 20 % code assistant, 10 % rag, downtime `none`; one 70B model at fp8, `arch` 80 layers, 8 KV heads, head dim 128, fp16 KV, context 8,192; 24 GPUs of 141 GB and 700 W.

1. Concurrency: chat 2,000 × 0.7 × 0.20 × 0.25 = 70 to × 0.50 = 140; code 2,000 × 0.2 × 0.30 × 0.70 = 84 to × 1.00 = 120; rag 2,000 × 0.1 × 0.20 × 0.25 = 10 to 20. Range 164 to 280.
3. Weights 70 GB; required 77.0 GB.
4. 1 GPU: usable 126.9 GB, enough.
5. Bytes per token 2 × 80 × 8 × 128 × 2 = 327,680. Cached tokens (126.9 − 77.0) × 10^9 ÷ 327,680 = 152,282. Tokens per request 8,192 + 1,024 = 9,216 for every group; 152,282 holds one.
6. Requests per replica 152,282 ÷ 9,216 = 16 (rounded down). In flight 140 + 120 + 20 = 280. Replicas 280 ÷ 16 = 17.5, rounded up 18; the minimum is 2, so 18. KV needed at peak 280 × 9,216 × 327,680 ÷ 10^9 = 845.6 GB.
7. 2 GPUs: cached 539,550, 58 per replica, 5 replicas, 10 GPUs. 4 GPUs: cached 1,314,086, 142 per replica, 2 replicas, 8 GPUs. 8 GPUs: 2 replicas (the minimum), 16 GPUs. Note: "with 4-GPU replicas the memory model needs 8 GPUs instead of 18; tensor parallelism adds synchronization overhead, so benchmark throughput before choosing it".
8. GPUs 18; servers 18 ÷ 8 = 2.25, so 3; power 18 × 700 × 1.8 ÷ 1000 = 22.68, so 22.7 kW.
9. 18 needed, 24 available: fits.

### Mixed contexts

The enterprise example with `workload.context_tokens` = `{"code_assistant": 32768, "chat": 8192}`. Code requests are 32,768 + 1,024 = 33,792 tokens, chat and rag 9,216 (rag takes the model's 8,192). Per 1-GPU replica: chat 16, code 152,282 ÷ 33,792 = 4, rag 16. Replicas 140 ÷ 16 + 120 ÷ 4 + 20 ÷ 16 = 8.75 + 30 + 1.25 = 40. That is 40 GPUs, more than 24: it does not fit. Step 7 finds 8-GPU replicas at 2 × 8 = 16 GPUs, which would fit as an override after a throughput benchmark.

### CPU only

12 users, one 8B model at fp8, no GPU, 64 GB RAM. Required 8 × 1.10 = 8.8 GB, below 64 GB: fits. Concurrency 12 × 0.20 × 0.25 = 0.6, so 1, to 12 × 0.20 × 0.50 = 1.2, so 2. Warn that CPU inference suits only a few concurrent users.

## When the hardware does not fit

Present the options and let the user choose:

1. A lower precision or a quantized build of the same model.
2. A smaller model.
3. More GPUs, or GPUs with more memory.
4. A shorter context for one user group (`workload.context_tokens`).
5. A larger group per replica, when step 7 found one whose total fits. It trades GPUs for tensor-parallel overhead, so it needs a throughput benchmark in the verification section.

For 1 to 4, change the answer and size again. When the user goes ahead anyway (option 5, or more hardware is on order), record an override on the `llm-serving` decision with the user's reason, and say in the sizing section that the hardware does not fit without it.

## A what-if

To compare a variant, for example `org.downtime_tolerance` = `none`, or a recommendation that changes the numbers (running spare GPUs as more replicas, say), size it next to the design and label it: "What-if, `org.downtime_tolerance` = `none`: …". A what-if never replaces the design's own numbers.
