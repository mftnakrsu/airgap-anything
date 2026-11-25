# Research lab chat assistant: document search (`airgap-rag`)

Status: written by `airgap-rag` for the install evals; only the parts the install skill reads are filled in. Date: 2026-11-25. Language: en.

## Decisions

| Decision | Choice | Reason | Alternatives |
|---|---|---|---|
| Platform | custom: Elasticsearch 8, run by the user's own team inside the network | The user named it ("we already run Elasticsearch 8 inside"). Never swapped for Open WebUI knowledge bases without the user's consent. | Open WebUI knowledge bases (recommended default), RAGFlow |
| Extraction | `docling-serve` `v1.39.0`, image `quay.io/docling-project/docling-serve-cpu:v1.39.0` | The documents are scanned PDFs; the host is `arm64`, and the `-cu128` image is amd64 only, so the multi-architecture `-cpu` image is used | The built-in extractor of Open WebUI (not used: Open WebUI is not the platform) |
| OCR languages | `ocr_lang`: `["en"]`, EasyOCR (`latin_g2` is baked into the image) | The documents are in English | none |

Custom platform record:

| Field | Value |
|---|---|
| Name | Elasticsearch 8 |
| Version | `unverified` (the user said "8"; the minor version was not given) |
| Documentation link | not given |
| Who runs it | the user's own team, already inside the network |
| How extraction reaches it | `docling-serve` converts a document to markdown; what writes the result into Elasticsearch is an open item |
| Settings, ports, image names, egress behavior | `unverified`: none is in this skill's catalog and none is written here |

## Cloud rule

Internal documents never go to a cloud agent or to any service outside the network: a copy that has left the network cannot be taken back. Conversion runs inside, with `docling-serve`, slower but never unsafe. Conversion on the connected side handles public documents only.

## Assumptions

| Assumption | Value | Evidence |
|---|---|---|
| Document type | scanned PDFs, English | the defaults of the interview, `estimate` |
| Corpus size | not given: open item | none |
| Embedding and reranker models | none carried: whether Elasticsearch embeds the text itself is `unverified` | open item |
| Updates | weekly batch | default |

## Sizing

| Line | Value | Source |
|---|---|---|
| Extraction time per page on CPU with OCR | 3.1 s on an 8-vCPU EPYC (the host's CPU was not named) | the Docling paper, https://arxiv.org/html/2501.17887 |
| Memory for `docling-serve` | about 6.2 GB at 4 threads | https://arxiv.org/html/2408.09869 |
| Volume | not given: open item | none |

## Serving requirements

- `docling-serve` listens on port 5001 as UID 1001, with `UVICORN_WORKERS=1` and `DOCLING_SERVE_MAX_SYNC_WAIT` raised above its 120 s default.
- The API key of `docling-serve` is `DOCLING_SERVE_API_KEY` in the service's environment, from the environment of its host, never from a file.
- The Elasticsearch connection settings (address, credentials) are `unverified`: the user's team provides them, the credentials as environment variables on the host that runs the loader.

## Open items

1. The exact Elasticsearch version, its documentation, its address and its authentication: `unverified`.
2. Who writes the loader that puts the converted markdown into Elasticsearch, and who owns it. This skill writes no program for it.
3. The corpus size and the update volume.
4. Whether Elasticsearch embeds the text itself, or an embedding model has to be added (and staged).
5. Elasticsearch's own telemetry and update checks: not documented here; the egress check covers it.

## Components added to the manifest

`docling-serve`, `custom: Elasticsearch 8 platform`, `airgap-rag`.

## Checks to run inside

The five checks of `references/verification.md`: install, retrieval, OCR, access and egress. They are in section 7 of `docs/airgap/transfer-manifest.md`, each marked "(from airgap-rag)".
