# BGE Reranker v2 M3 (`bge-reranker-v2-m3`)

Multilingual reranker from BAAI that vLLM serves without overrides. The alternative to Qwen3-Reranker, and the one that also runs on TEI.

| Field | Value |
|---|---|
| Kind | `reranker-model` |
| Version | `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` |
| License | Apache-2.0 |
| Install | `hf download BAAI/bge-reranker-v2-m3` on the connected side, then `vllm serve` from the copied directory |
| Evidence | docs |
| Last verified | 2026-11-24 |

The Version is the `sha` of the Hugging Face model record, read 2026-11-24 (https://huggingface.co/api/models/BAAI/bge-reranker-v2-m3).

| Property | Value | Source |
|---|---|---|
| Parameters | 568M | https://huggingface.co/api/models/BAAI/bge-reranker-v2-m3?blobs=true |
| Max tokens | not stated on the card (its examples use 512) | https://huggingface.co/BAAI/bge-reranker-v2-m3 |
| Weights on disk | 2.27 GB FP32 | https://huggingface.co/api/models/BAAI/bge-reranker-v2-m3?blobs=true |
| Languages | multilingual; the card does not name Turkish | https://huggingface.co/BAAI/bge-reranker-v2-m3 |

The score is a reason, not a promise: MMTEB-R 58.36, against 66.36 for Qwen3-Reranker-0.6B. These are Qwen's own runs, reranking the top 100 results of Qwen3-Embedding-0.6B (https://huggingface.co/Qwen/Qwen3-Reranker-8B).

## Choose when

- The overrides of Qwen3-Reranker cannot be used, or the reranker should be served the plain way.
- TEI is already in the network: this model runs on TEI as well as vLLM.

## Avoid when

- Quality matters most and a vLLM instance is available: `qwen3-reranker` scores higher in Qwen's runs.
- Passages longer than 512 tokens are common: the card states no maximum length.

## Configuration

Serving, on an instance of the architect's `vllm` entry (v0.34.0). The XLMRobertaForSequenceClassification architecture needs no overrides (https://docs.vllm.ai/en/stable/models/pooling_models/scoring/):

```
vllm serve MODEL_DIR --runner pooling
```

vLLM's `/v1/rerank` matches Open WebUI's external reranker format. TEI's `/rerank` does not: it takes `{query, texts}` and returns `[{index, score}]`, while Open WebUI sends `{model, query, documents, top_n}` and expects `results[].index/relevance_score` (https://docs.openwebui.com/reference/env-configuration). With TEI, a translation layer in front is needed (inferred from the two formats, not run).

Open WebUI: `ENABLE_RAG_HYBRID_SEARCH=true`, `RAG_RERANKING_ENGINE=external`, `RAG_EXTERNAL_RERANKER_URL` (the full URL including `/v1/rerank`), `RAG_EXTERNAL_RERANKER_API_KEY` (from the environment), `RAG_RERANKING_MODEL` (sent as `model`) and `RAG_EXTERNAL_RERANKER_TIMEOUT`.

## Egress switches

| Connection | Default | Switch | Source |
|---|---|---|---|
| Hugging Face Hub calls from vLLM and its libraries | on | `HF_HUB_OFFLINE=1` | https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables |
| vLLM usage statistics sent to stats.vllm.ai | on | `VLLM_NO_USAGE_STATS=1` (also `DO_NOT_TRACK=1`) | https://docs.vllm.ai/en/stable/usage/usage_stats.html |

## Caveats

- `hf download <repo>` fetches the current main branch. Pinning the download to the revision above is not documented in the research: compare the `sha` on the model record at download time with the Version.
- TEI, if used instead of vLLM, fetches the model from the Hub at start; the documented air-gapped procedure is to clone the repository on a connected machine and start with `--model-id /data/<dir>` (https://raw.githubusercontent.com/huggingface/text-embeddings-inference/main/README.md). Whether `HF_HUB_OFFLINE` is honored by TEI: not documented.

## Carry in

### Images

None.

### Models

| Repo | Revision | Size | Source |
|---|---|---|---|
| `BAAI/bge-reranker-v2-m3` | `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` | 2.27 GB | https://huggingface.co/api/models/BAAI/bge-reranker-v2-m3?blobs=true |

The runtime image is the architect's `vllm` entry (`vllm/vllm-openai:v0.34.0`), not carried again here.

### Runtime downloads to stage in advance

None once the model directory is copied and `HF_HUB_OFFLINE=1` is set.

### Telemetry and egress to switch off before the first start

All rows of Egress switches, in the environment of the reranker instance.

## Evidence

- https://huggingface.co/api/models/BAAI/bge-reranker-v2-m3
- https://huggingface.co/api/models/BAAI/bge-reranker-v2-m3?blobs=true
- https://huggingface.co/BAAI/bge-reranker-v2-m3
- https://huggingface.co/Qwen/Qwen3-Reranker-8B
- https://docs.vllm.ai/en/stable/models/pooling_models/scoring/
- https://docs.vllm.ai/en/stable/models/supported_models/
- https://docs.vllm.ai/en/stable/usage/usage_stats.html
- https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables
- https://raw.githubusercontent.com/huggingface/text-embeddings-inference/main/README.md
- https://docs.openwebui.com/reference/env-configuration
