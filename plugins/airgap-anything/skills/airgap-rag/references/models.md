# Embedding and reranking models

Goal: choose the two models, serve them on the network's vLLM, and wire Open WebUI to them with nothing downloaded at start. The facts per model are in the catalog entries; this file decides and connects.

## Contents

- Choice
- Serving
- Open WebUI settings
- Search settings
- Changing the model

## Choice

| Role | Default | Alternative | Serving |
|---|---|---|---|
| Embedding | `catalog/qwen3-embedding.md`: Apache-2.0, 1024 dimensions, 32K tokens. MMTEB 64.33 per its model card | `catalog/bge-m3.md`: MIT, 8192 tokens, 1024 dimensions, Turkish named in its paper | The architect's vLLM (v0.34.0), a separate instance with `--runner pooling` |
| Reranker | `catalog/qwen3-reranker.md`, with vLLM's documented `--hf_overrides` | `catalog/bge-reranker-v2-m3.md`, which needs no overrides | vLLM `/v1/rerank`, which matches Open WebUI's external reranker format; TEI's `/rerank` does not |

When to switch, by the `languages` answer:

- Every language is named for the Qwen3 base model (https://qwenlm.github.io/blog/qwen3/): keep the default pair. The Qwen3 embedding card says "100+ languages" without naming Turkish; the base model's list does.
- A language is not on that list: embed with bge-m3 and say in `rag.md` why. The reranker follows: bge-reranker-v2-m3 states "multilingual" only, without naming languages, so the retrieval check is the proof.
- The overrides of Qwen3-Reranker cannot be passed, or TEI is already in the network: bge-reranker-v2-m3.
- Sparse or ColBERT outputs: bge-m3 offers them, but whether Open WebUI uses them is not documented.

Scores are reasons, not promises: see "No model ranking" in `references/decisions.md`. Each model is a pinned Hugging Face revision; the revision and the download command are in the catalog entry. When a revision cannot be read, the entry says "revision: record at download".

## Serving

Run each model as its own instance of the architect's `vllm` entry (`vllm/vllm-openai:v0.34.0`, not carried again here), on its own port. Use `--served-model-name` so the name Open WebUI sends is short and has no `/`. Put the key in `VLLM_API_KEY` from the environment of the inside host, never in the file.

```
vllm serve ./qwen3-embedding --runner pooling
vllm serve ./qwen3-reranker --runner pooling --hf_overrides '{"architectures":["Qwen3ForSequenceClassification"],"classifier_from_token":["no","yes"],"is_original_qwen3_reranker":true}'
```

For the alternatives: `vllm serve ./bge-m3 --runner pooling` and `vllm serve ./bge-reranker-v2-m3 --runner pooling`. There is no `--task` flag. The embedding endpoint is `/v1/embeddings`; the reranker endpoint is `/v1/rerank` (also `/rerank` and `/v2/rerank`).

Environment of every model instance (switches from the catalog entries):

```
HF_HUB_OFFLINE=1
VLLM_NO_USAGE_STATS=1
```

`DO_NOT_TRACK=1` also turns off Hugging Face library telemetry. The model folders are copied in with the bundle; with `HF_HUB_OFFLINE=1` nothing is fetched. These are the rows of section 4 of the manifest, marked "(from airgap-rag)".

Sources: https://docs.vllm.ai/en/stable/cli/serve/, https://docs.vllm.ai/en/stable/models/pooling_models.html, https://docs.vllm.ai/en/stable/models/pooling_models/scoring/, https://docs.vllm.ai/en/stable/usage/usage_stats.html.

## Open WebUI settings

Write these to `docs/airgap/rag/` as environment settings (https://docs.openwebui.com/reference/env-configuration). Values in angle brackets come from the user's network; keys are named, never written.

```
OFFLINE_MODE=true
RAG_EMBEDDING_ENGINE=openai
RAG_OPENAI_API_BASE_URL=<embedding instance, the OpenAI-compatible base>
RAG_OPENAI_API_KEY=<from the environment>
RAG_EMBEDDING_MODEL=<served model name of the embedding instance>
ENABLE_RAG_HYBRID_SEARCH=true
RAG_RERANKING_ENGINE=external
RAG_EXTERNAL_RERANKER_URL=<reranker instance, the full URL including /v1/rerank>
RAG_EXTERNAL_RERANKER_API_KEY=<from the environment>
RAG_RERANKING_MODEL=<served model name of the reranker instance>
RAG_EXTERNAL_RERANKER_TIMEOUT=<seconds>
VECTOR_DB=pgvector
PGVECTOR_INDEX_METHOD=hnsw
```

- `OFFLINE_MODE=true` sets `HF_HUB_OFFLINE=1`, turns off the version check and forces the `*_AUTO_UPDATE` settings to false. Without it, the default SentenceTransformers engine (sentence-transformers/all-MiniLM-L6-v2) contacts Hugging Face at every start and downloads a model that is not cached. With the external embedding engine above, no local embedding model is needed.
- `RAG_EXTERNAL_RERANKER_URL` must be the full URL including `/v1/rerank`. `RAG_RERANKING_MODEL` is sent as `model`.
- Whether `RAG_OPENAI_API_BASE_URL` must end in `/v1`, and a sensible `RAG_EXTERNAL_RERANKER_TIMEOUT`: not documented. Check the first with the install check (`references/verification.md`, check 1) and write the timeout after measuring a query.
- Do not use `RAG_RERANKING_MODEL` as a local Hugging Face model: it loads inside Open WebUI, and if it fails to load, hybrid search turns off.
- The environment values only seed the settings at the first start; later changes go through the admin panel (persistent config).

## Search settings

- Hybrid search is on: `ENABLE_RAG_HYBRID_SEARCH=true`, then the reranker. Related documented settings and defaults: `RAG_HYBRID_BM25_WEIGHT` 0.5, `RAG_TOP_K` 10, `RAG_TOP_K_RERANKER` 10, `RAG_RELEVANCE_THRESHOLD` 0.0. Keep the defaults until the retrieval check says otherwise.
- `ENABLE_RAG_HYBRID_SEARCH_ENRICHED_TEXTS`, when on, skips the native hybrid search in pgvector: leave it off.
- Vector size: 1024 dimensions need no `PGVECTOR_USE_HALFVEC`. A model above 2,000 dimensions needs `PGVECTOR_USE_HALFVEC=true`, and `PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH` (default 1536) set to its dimension; the index limits are in `catalog/pgvector.md`. Halfvec also halves the storage per vector (`references/sizing.md`, step 4).

## Changing the model

Changing the embedding model means a full reindex: the dimension and the meaning of every vector change. In Open WebUI that is "Reindex Knowledge and Memory Vectors", and `rag.md` says so next to the model choice. Plan the reload time with the embedding step of `references/sizing.md`. Changing only the reranker needs no reindex: it works on the results of a query. The research does not state this explicitly; it follows from the reranker scoring retrieved passages (inferred, `estimate`).
