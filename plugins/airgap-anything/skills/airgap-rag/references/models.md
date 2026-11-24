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
- bge-m3's weights are a single pickle file (`pytorch_model.bin`, no safetensors), and `airgap-transfer` leaves pickle files out and fails the model folder unless its plan says "Pickle files allowed: yes" for that model. A pickle file can run code when it is loaded, so only the user's scanning rules can allow it. Choosing bge-m3 therefore puts that answer in the open items of `rag.md`. Keep the Qwen3 pair unless a language requires bge-m3.
- The overrides of Qwen3-Reranker cannot be passed, or TEI is already in the network: bge-reranker-v2-m3.
- Sparse or ColBERT outputs: bge-m3 offers them, but whether Open WebUI uses them is not documented.

Scores are reasons, not promises: see "No model ranking" in `references/decisions.md`. Each model is a pinned Hugging Face revision; the revision and the download command are in the catalog entry. When a revision cannot be read, the entry says "revision: record at download".

## Serving

Run each model as its own instance of the architect's `vllm` entry (v0.34.0), on its own port. The image follows the hardware:

- With a GPU: `vllm/vllm-openai:v0.34.0`, already in the manifest from the architect.
- With no GPU (`hardware.gpus` empty): `vllm/vllm-openai-cpu:v0.34.0-x86_64` (`v0.34.0-arm64` on arm64), which this skill adds as a section-1 row, `vllm` (from airgap-rag). These are the tags vLLM's CPU installation page names (https://github.com/vllm-project/vllm/blob/v0.34.0/docs/getting_started/installation/cpu.x86.inc.md, and the architect's `vllm` entry); the x86_64 image is 1.8 GB (https://hub.docker.com/v2/repositories/vllm/vllm-openai-cpu/tags/v0.34.0-x86_64). Pooling models on CPU are `unverified`: the supported-models page for CPU lists no embedding or reranker model, and the CPU benchmark cases for embeddings name only `jinaai/jina-embeddings-v3` (https://github.com/vllm-project/vllm/blob/v0.34.0/docs/models/hardware_supported_models/cpu.md, https://github.com/vllm-project/vllm/blob/v0.34.0/.buildkite/performance-benchmarks/tests/serving-tests-cpu-embed.json). The install check proves it inside (`references/verification.md`, check 1).

Inside, `airgap-transfer` copies each model folder to `/srv/models/<MODEL>`, where `<MODEL>` is the model's folder under `models/` in the bundle (airgap-transfer's inside reference; the bundle's `INSIDE.md` uses the same path). The commands below use `qwen3-embedding` and `qwen3-reranker`, the folder names of the catalog entries' download form; use the names the bundle has, and in a container mount `/srv/models` at the same path.

`--served-model-name` sets the name Open WebUI sends, short and without `/`. `--port` defaults to 8000, which the chat model's instance may already use, so each instance gets its own; 8001 and 8002 are this skill's choice. `--api-key` takes the key from `VLLM_API_KEY` in the environment of the inside host, never from a file (https://docs.vllm.ai/en/stable/cli/serve/).

```
vllm serve /srv/models/qwen3-embedding --runner pooling --served-model-name qwen3-embedding --port 8001 --api-key "$VLLM_API_KEY"
vllm serve /srv/models/qwen3-reranker --runner pooling --served-model-name qwen3-reranker --port 8002 --api-key "$VLLM_API_KEY" --hf_overrides '{"architectures":["Qwen3ForSequenceClassification"],"classifier_from_token":["no","yes"],"is_original_qwen3_reranker":true}'
```

For the alternatives, the same flags with `/srv/models/bge-m3` and `/srv/models/bge-reranker-v2-m3`, without overrides. There is no `--task` flag. The embedding endpoint is `/v1/embeddings`; the reranker endpoint is `/v1/rerank` (also `/rerank` and `/v2/rerank`).

Sharing a GPU with the chat model: `--gpu-memory-utilization` is the fraction of GPU memory one instance uses, a per-instance limit, so two instances on one GPU can each take 0.5. Unset, an instance takes 0.92, or 1.0 with the extensible KV cache (https://docs.vllm.ai/en/stable/cli/serve/, https://github.com/vllm-project/vllm/blob/v0.34.0/vllm/config/cache.py). The chat instance would have to give memory up, which changes the architect's sizing, and the fraction these two models need is not documented: run them on a separate GPU, or measure and rerun the architect's sizing.

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

- `PGVECTOR_DB_URL` stays unset, so it defaults to `DATABASE_URL`: the vectors live in the PostgreSQL that Open WebUI already uses. That service therefore runs on `pgvector/pgvector:0.8.7-pg18` instead of the plain `postgres:18.7` image (the same PostgreSQL 18.7; `catalog/pgvector.md`), carried as the section-1 row `pgvector` (from airgap-rag). `rag.md` records the substitution; the blueprint is not rewritten. The alternative is a separate database on the pgvector image, with `PGVECTOR_DB_URL` set to it and its password from the environment.

- `OFFLINE_MODE=true` sets `HF_HUB_OFFLINE=1`, turns off the version check and forces the `*_AUTO_UPDATE` settings to false. Without it, the default SentenceTransformers engine (sentence-transformers/all-MiniLM-L6-v2) contacts Hugging Face at every start and downloads a model that is not cached. With the external embedding engine above, no local embedding model is needed.
- `RAG_EXTERNAL_RERANKER_URL` must be the full URL including `/v1/rerank`. `RAG_RERANKING_MODEL` is sent as `model`.
- Whether `RAG_OPENAI_API_BASE_URL` must end in `/v1`, and a sensible `RAG_EXTERNAL_RERANKER_TIMEOUT`: not documented. Check the first with the install check (`references/verification.md`, check 1) and write the timeout after measuring a query.
- Do not use `RAG_RERANKING_MODEL` as a local Hugging Face model: it loads inside Open WebUI, and if it fails to load, hybrid search turns off.
- The environment values only seed the settings at the first start; later changes go through the admin panel (persistent config).

## Search settings

- Hybrid search is on: `ENABLE_RAG_HYBRID_SEARCH=true`, then the reranker. Related documented settings and defaults: `RAG_HYBRID_BM25_WEIGHT` 0.5, `RAG_TOP_K` 10, `RAG_TOP_K_RERANKER` 10, `RAG_RELEVANCE_THRESHOLD` 0.0. Keep the defaults until the retrieval check says otherwise.
- `ENABLE_RAG_HYBRID_SEARCH_ENRICHED_TEXTS`, when on, skips the native hybrid search in pgvector: leave it off.
- Vector size: 1024 dimensions need no `PGVECTOR_USE_HALFVEC`. A model above 2,000 dimensions needs `PGVECTOR_USE_HALFVEC=true`. `PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH` defaults to 1536; setting it to the model's dimension when that is larger is inferred from its name and default, not documented. The index limits are in `catalog/pgvector.md`. Halfvec also halves the storage per vector (`references/sizing.md`, step 4).

## Changing the model

Changing the embedding model means a full reindex: the dimension and the meaning of every vector change. In Open WebUI that is "Reindex Knowledge and Memory Vectors", and `rag.md` says so next to the model choice. Plan the reload time with the embedding step of `references/sizing.md`. Changing only the reranker needs no reindex: it works on the results of a query. The research does not state this explicitly; it follows from the reranker scoring retrieved passages (inferred, `estimate`).
