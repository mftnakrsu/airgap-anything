# Sizing the first load

Goal: how long the first load takes and how much space the index needs. Every number is sourced or labeled `estimate`.

## Contents

- Inputs
- The five steps
- Worked example
- The fast path
- The GPU line

## Inputs

Documents, average pages per document, scanned share, languages, new or changed pages per day or week, hardware (CPU or GPU). They come from the interview (`references/interview.md`); the volume has no default.

## The five steps

| Step | Calculation | Sourced reference |
|---|---|---|
| 1. Extraction time | scanned pages × s/page + digital pages × s/page | Docling with EasyOCR, 4,008 pages: 8-vCPU EPYC 3.1 s/page, L4 GPU 0.49 s/page, M3 Max 1.27 s/page (https://arxiv.org/html/2501.17887). Without OCR, 0.92 to 1.34 pages/s at 16 threads: Xeon E5-2690 0.92, M3 Max 1.34 (https://arxiv.org/html/2408.09869). pypdf: no sourced rate, so "measure on a 100-page sample" |
| 2. Chunks | total characters ÷ (chunk size − overlap) | Open WebUI defaults are 1024 and 100, so the stride is 924. Characters per page is an `estimate`: use 3,000 until a sample says otherwise |
| 3. Embedding time | chunks ÷ texts per second | TEI with bge-m3 (FP16, 512-token passages): L40S about 277/s, H100 SXM about 1,240/s (https://www.runpod.io/blog/gpu-embedding-workloads-benchmark). For Qwen3-Embedding-0.6B only the vLLM-to-TEI ratio (2.6×) is published, so measure it |
| 4. Index size | chunks × (4 × dimensions + 8) bytes, plus text | pgvector storage formula for `vector`; `halfvec` is 2 × dimensions + 8 (https://github.com/pgvector/pgvector/blob/master/README.md). No HNSW size formula is documented: measure with `pg_relation_size` after the load |
| 5. GPU line | embedding and reranker models (each about 1.2 GB of weights) as a small separate replica in the architect's sizing | Query load comes from the architect's `rag` group |

Notes on each step:

- Step 1: take the row for the user's hardware. When the digital pages also go through docling-serve, the "without OCR" rates apply to them; when they go through pypdf, sample first. Add the time of the update batches (`updates` answer) as pages per batch at the same rates.
- Step 2: the 1024-character chunk is about 256 tokens at the roughly 4 characters per token that Open WebUI's own config comment assumes, so the Runpod passages (512 tokens) are heavier than ours and the time of step 3 is likely an upper bound (`estimate`).
- Step 4: the text of the chunks is stored too: about chunks × 1,024 characters at most (`estimate`). Qdrant has its own parts and a 20 % headroom rule: `catalog/qdrant.md`.
- Step 5: the research documents no memory beyond the weights (Qwen3 pair 1.19 GB each, bge pair 2.27 GB each). Measure the activation memory with a load test and write it as an open item.

## Worked example

50,000 pages, 30 % scanned, 1024-dimension vectors, GPU class L4 for extraction. The 3,000 characters per page is an `estimate`.

| Step | Result |
|---|---|
| 1. Extraction | 15,000 scanned pages × 0.49 s = 7,350 s, about 2 h on an L4; × 3.1 s = 46,500 s, about 13 h on 8 vCPU. The 35,000 digital pages: through pypdf, measure; through docling-serve without OCR at 0.92 to 1.34 pages/s that is about 7 to 11 h on CPUs of that class |
| 2. Chunks | 50,000 × 3,000 = 150,000,000 characters ÷ 924 = about 162,000 chunks |
| 3. Embedding | 162,000 ÷ 277/s = about 590 s (10 min) on an L40S with bge-m3; ÷ 1,240/s = about 130 s on an H100 SXM |
| 4. Index | 4 × 1,024 + 8 = 4,104 bytes per vector × 162,000 = about 0.67 GB of vectors (`vector`), 0.33 GB as `halfvec`; text about 0.17 GB; measure the HNSW index with `pg_relation_size` after the load |
| 5. GPU line | two models, about 2.4 GB of weights for the Qwen3 pair |

Extraction dominates. The embedding step is minutes, which is why the retrieval check (`references/verification.md`) can be repeated after a model change.

## The fast path

When the user is in a hurry, or the answers were short, show the same calculation as one summary table, record the defaults as assumptions, and skip the explanation. Every cell still carries its source or `estimate` mark, and `rag.md` keeps the step-by-step version. Template:

| Item | Value | Basis |
|---|---|---|
| Documents and pages | (user) | `sources` |
| Scanned share | (user, or default mostly digital) | `doc_types` |
| Extraction time | (hours, for the hardware) | step 1: 3.1 s/page CPU, 0.49 s/page L4; pypdf measured |
| Chunks | (count) | step 2, `estimate` for characters per page |
| Embedding time | (minutes) | step 3 |
| Vectors on disk | (GB) | step 4; measure the HNSW index with `pg_relation_size` after the load |
| GPU line | (models, GB of weights) | step 5 |
| Update batch | (pages per week and hours) | `updates`, step 1 rates |
| Assumptions | (every default used) | `references/interview.md` |

"Skip the sizing" is not an option: the fast path shows this table and nothing else.

## The GPU line

Read the `rag` group in the architect's sizing (`docs/airgap/blueprint.md`, and the sizing reference of airgap-architect): it holds the concurrency of question answering. This skill adds a small separate replica for the two models of step 5, next to the chat model, and does not rewrite the blueprint. If the `rag` user count differs from the blueprint, tell the user to rerun the architect's sizing. With no GPU the models run on CPU: the research has no CPU rate, so measure it and say so in the open items.
