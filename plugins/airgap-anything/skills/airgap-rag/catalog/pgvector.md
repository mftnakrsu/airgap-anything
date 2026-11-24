# pgvector (`pgvector`)

PostgreSQL extension that stores embeddings and searches them with HNSW or IVFFlat indexes. Open WebUI's default choice for the vector store in this skill, in the same database engine as the blueprint's `postgresql`.

| Field | Value |
|---|---|
| Kind | `vector-store` |
| Version | `0.8.7` |
| License | PostgreSQL |
| Install | image `pgvector/pgvector:0.8.7-pg18` (PostgreSQL 18.7, amd64 and arm64) |
| Evidence | docs |
| Last verified | 2026-11-24 |

Released 2026-10-01; 0.9.0 is not released (https://github.com/pgvector/pgvector/blob/master/CHANGELOG.md). The image contains `PG_VERSION=18.7-1.pgdg12+2` (Debian bookworm), which matches the pin in the architect's `postgresql` entry (https://hub.docker.com/v2/repositories/pgvector/pgvector/tags/0.8.7-pg18/images). The variants `0.8.7-pg18-bookworm` and `0.8.7-pg18-trixie` exist, and `pg18` is a moving tag: use the pinned one.

## Choose when

- The default: Open WebUI is the platform, and one PostgreSQL service for application data and vectors is preferred. Open WebUI's docs say only PGVector and ChromaDB are consistently maintained by its team (https://docs.openwebui.com/reference/env-configuration/).
- The corpus fits one database server; the vectors and the HNSW index should fit in memory for speed.

## Avoid when

- The corpus is very large, or a separate vector service is wanted: use `qdrant`.
- The embedding model has more than 4,000 dimensions: HNSW and IVFFlat index halfvec up to 4,000 dimensions, vector up to 2,000.

## Configuration

Open WebUI variables (https://docs.openwebui.com/reference/env-configuration/):

- `VECTOR_DB=pgvector` and `PGVECTOR_DB_URL`, which defaults to `DATABASE_URL`; the database password comes from the environment. The skill's default leaves `PGVECTOR_DB_URL` unset, so the vectors go into the PostgreSQL that Open WebUI already uses, and that service runs on this image instead of `postgres:18.7`. The alternative is a separate database on this image, with `PGVECTOR_DB_URL` set to it.
- `PGVECTOR_INDEX_METHOD=hnsw`, set before the first load. When unset, Open WebUI uses ivfflat for vector columns and hnsw for halfvec. Earlier Open WebUI versions built the IVFFlat index on an empty table, which gave a recall@10 of 0.480; IVFFlat needs data first. If it already happened, run `REINDEX INDEX idx_document_chunk_vector;`.
- `PGVECTOR_USE_HALFVEC=true` is needed above 2,000 dimensions (default False).
- `PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH`, default 1536. The research documents only the default; setting it to the embedding model's dimension when that is larger is inferred from its name, not documented.
- Other documented variables and defaults: `PGVECTOR_CREATE_EXTENSION` true, `PGVECTOR_HNSW_M` 16, `PGVECTOR_HNSW_EF_CONSTRUCTION` 64, `PGVECTOR_IVFFLAT_LISTS` 100, `PGVECTOR_ITERATIVE_SCAN` relaxed_order, `PGVECTOR_POOL_*`.

Index settings (https://github.com/pgvector/pgvector/blob/master/README.md):

- HNSW has better speed-recall than IVFFlat but slower builds and more memory, with no training step; defaults m=16 and ef_construction=64.
- IVFFlat: build after loading data; lists = rows/1000 up to 1M rows, sqrt(rows) above; probes default to 1, start at sqrt(lists).
- Iterative index scans for filtered queries exist since 0.8.0.

Storage per vector (README): vector 4*d+8 bytes, halfvec 2*d+8, bit d/8+8, sparsevec 8*non-zero+16. At 768 dimensions that is 3,080 vs 1,544 bytes; at 1,024 dimensions, 4,104 vs 2,056 (computed). An HNSW size formula is not documented: build it and measure with `SELECT pg_size_pretty(pg_relation_size('index_name'));`.

The PostgreSQL service itself (data volume layout since version 18, licensing) is in the architect's `postgresql` entry; this image replaces `postgres:18.7` for the database that holds the vectors: by default the database of Open WebUI itself, the same PostgreSQL 18.7. The manifest carries it as the section-1 row `pgvector` (from airgap-rag), and `rag.md` records the substitution; the blueprint is not rewritten.

## Egress switches

| Connection | Default | Switch | Source |
|---|---|---|---|
| none documented (no downloads, telemetry or update check in the README) | not applicable | not applicable | https://github.com/pgvector/pgvector/blob/master/README.md |

## Caveats

- HNSW build memory: indexes build significantly faster when the graph fits into `maintenance_work_mem`. When it does not, the server logs a NOTICE ("hnsw graph no longer fits into maintenance_work_mem after 100000 tuples"). The README warns not to set it so high that the server runs out of memory. Parallel workers default to 2.
- An index need not fit in memory but performs better if it does; half-precision indexing or binary quantization shrinks it.
- The 16,000-dimension storage limit is far above the index limits (2,000 for vector, 4,000 for halfvec); the index limits are the ones that matter.
- Changing the embedding model changes the dimension and needs a full reindex in Open WebUI.

## Carry in

### Images

| Image | Hardware | Digest |
|---|---|---|
| `pgvector/pgvector:0.8.7-pg18` | amd64, arm64 | not recorded |

Pushed to Docker Hub on 2026-11-12 (https://hub.docker.com/v2/repositories/pgvector/pgvector/tags?page_size=100&name=pg18).

### Models

None.

### Runtime downloads to stage in advance

None documented.

### Telemetry and egress to switch off before the first start

None documented.

## Evidence

- https://github.com/pgvector/pgvector/blob/master/CHANGELOG.md
- https://github.com/pgvector/pgvector/blob/master/META.json
- https://github.com/pgvector/pgvector/blob/master/README.md
- https://hub.docker.com/v2/repositories/pgvector/pgvector/tags?page_size=100&name=pg18
- https://hub.docker.com/v2/repositories/pgvector/pgvector/tags/0.8.7-pg18/images
- https://docs.openwebui.com/reference/env-configuration/
