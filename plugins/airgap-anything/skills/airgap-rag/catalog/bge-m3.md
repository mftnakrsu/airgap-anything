# BGE-M3 (`bge-m3`)

Multilingual embedding model from BAAI with dense, sparse and ColBERT outputs and an 8,192-token window. The alternative embedding model when the user's languages are not named for Qwen3.

| Field | Value |
|---|---|
| Kind | `embedding-model` |
| Version | `5617a9f61b028005a4858fdac845db406aefb181` |
| License | MIT |
| Install | `hf download BAAI/bge-m3` on the connected side, then `vllm serve` from the copied directory |
| Evidence | docs |
| Last verified | 2026-11-24 |

The Version is the `sha` of the Hugging Face model record, read 2026-11-24 (https://huggingface.co/api/models/BAAI/bge-m3).

| Property | Value | Source |
|---|---|---|
| Parameters | 568M | https://huggingface.co/Snowflake/snowflake-arctic-embed-l-v2.0/raw/main/README.md (comparison table) |
| Dimensions | 1024 dense, plus sparse and ColBERT outputs; the `dimensions` request field is rejected | https://huggingface.co/BAAI/bge-m3 and https://docs.vllm.ai/en/stable/models/pooling_models/embed/ |
| Max tokens | 8192 | https://huggingface.co/BAAI/bge-m3 |
| Weights on disk | 2.27 GB FP32 | https://huggingface.co/api/models/BAAI/bge-m3?blobs=true |
| Languages | Turkish: yes (MKQA Turkish Recall@100 is 75.6) | https://arxiv.org/html/2402.03216 |

The score is a reason, not a promise: MMTEB (multilingual) mean 59.56, taken from the table on the Qwen3-Embedding-8B card, whose leaderboard figures were read on 2025-05-24 (https://huggingface.co/Qwen/Qwen3-Embedding-8B).

## Choose when

- The user's languages are not named for the Qwen3 base model, and the paper's coverage matters.
- Sparse or ColBERT outputs are wanted next to the dense vector.

## Avoid when

- Shorter vectors are wanted: bge-m3 rejects the `dimensions` request field.
- Disk or download size is tight: 2.27 GB against 1.19 GB for `qwen3-embedding`, and the weights are a single `pytorch_model.bin`.

## Configuration

Serving, on a separate instance of the architect's `vllm` entry (v0.34.0), as a pooling model (https://docs.vllm.ai/en/stable/cli/serve/):

```
vllm serve MODEL_DIR --runner pooling
```

For the sparse or ColBERT outputs vLLM documents `--runner pooling --hf-overrides '{"architectures":["BgeM3EmbeddingModel"]}' --pooler-config.task embed|token_classify|token_embed` (https://docs.vllm.ai/en/stable/models/pooling_models/specific_models/). Whether Open WebUI uses them: not documented.

Open WebUI (https://docs.openwebui.com/reference/env-configuration): `RAG_EMBEDDING_ENGINE=openai`, `RAG_OPENAI_API_BASE_URL`, `RAG_OPENAI_API_KEY` (from the environment) and `RAG_EMBEDDING_MODEL`. 1024 dimensions need no halfvec. Changing the model needs "Reindex Knowledge and Memory Vectors".

## Egress switches

| Connection | Default | Switch | Source |
|---|---|---|---|
| Hugging Face Hub calls from vLLM and its libraries | on | `HF_HUB_OFFLINE=1` | https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables |
| vLLM usage statistics sent to stats.vllm.ai | on | `VLLM_NO_USAGE_STATS=1` (also `DO_NOT_TRACK=1`) | https://docs.vllm.ai/en/stable/usage/usage_stats.html |

## Caveats

- `hf download <repo>` fetches the current main branch. Pinning the download to the revision above is not documented in the research: compare the `sha` on the model record at download time with the Version.
- The repository holds `pytorch_model.bin` only, with no safetensors file; the `onnx/` folder adds another 2.27 GB: carry it only if needed.
- On TEI, bge-m3 and vLLM tie (median 1.08x) in the Runpod benchmark: bge-m3 FP16 with 512-token passages, vLLM on an A40 about 238 texts per second (https://www.runpod.io/blog/gpu-embedding-workloads-benchmark).

## Carry in

### Images

None.

### Models

| Repo | Revision | Size | Source |
|---|---|---|---|
| `BAAI/bge-m3` | `5617a9f61b028005a4858fdac845db406aefb181` | 2.27 GB (`pytorch_model.bin` only; the `onnx/` folder is another 2.27 GB, carry it only if needed) | https://huggingface.co/api/models/BAAI/bge-m3?blobs=true |

The runtime image is the architect's `vllm` entry (`vllm/vllm-openai:v0.34.0`), not carried again here.

### Runtime downloads to stage in advance

None once the model directory is copied and `HF_HUB_OFFLINE=1` is set.

### Telemetry and egress to switch off before the first start

All rows of Egress switches, in the environment of the embedding instance.

## Evidence

- https://huggingface.co/api/models/BAAI/bge-m3
- https://huggingface.co/api/models/BAAI/bge-m3?blobs=true
- https://huggingface.co/BAAI/bge-m3
- https://huggingface.co/Snowflake/snowflake-arctic-embed-l-v2.0/raw/main/README.md
- https://huggingface.co/Qwen/Qwen3-Embedding-8B
- https://arxiv.org/html/2402.03216
- https://docs.vllm.ai/en/stable/cli/serve/
- https://docs.vllm.ai/en/stable/models/pooling_models/embed/
- https://docs.vllm.ai/en/stable/models/pooling_models/specific_models/
- https://docs.vllm.ai/en/stable/models/supported_models/
- https://docs.vllm.ai/en/stable/usage/usage_stats.html
- https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables
- https://docs.openwebui.com/reference/env-configuration
- https://www.runpod.io/blog/gpu-embedding-workloads-benchmark
