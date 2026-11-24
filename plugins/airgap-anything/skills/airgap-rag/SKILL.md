---
name: airgap-rag
description: Makes an organization's documents searchable inside an air-gapped or offline network - asks which platform to use (Open WebUI knowledge bases, a RAG server such as RAGFlow, or the user's own choice), chooses document extraction and OCR, embedding and reranker models and the vector store, sizes the first load, writes the configuration and a bulk-load runbook, and adds everything to the transfer manifest. Use when someone wants document search, question answering over internal documents, a knowledge base or RAG to work without internet access, or asks how to load and search their files on a local model
---

# Airgap RAG

## Overview

Turn a short interview into the files that make the organization's documents searchable inside a network with no internet: the platform, the extraction and OCR, the embedding and reranker models, the vector store, a sizing of the first load, the configuration, a runbook for the bulk load, and rows in the transfer manifest so that `airgap-transfer` carries it all in.

Why the skill exists: turn on document features inside a closed network and Open WebUI tries to download an embedding model on its first start, scanned PDFs come back empty, some extractors send files to hosted services by default (Marker uses datalab.to), and nobody knows how long the first load takes. Nothing can be downloaded inside to fix that. So every switch, version and path here comes from `catalog/`, and every setting is proved inside by checks that a person runs.

Paths in this skill are relative to the folder that holds this file. `docs/` is in the user's project.

## When to use

- Someone wants document search, question answering over internal documents, a knowledge base or RAG to work without internet, on a model the organization serves itself.
- Someone asks how to load their files and search them on a local model, or which RAG platform to use in a closed network.

Not for designing the platform or sizing the chat model: that is `airgap-architect`. Not for packing and carrying files: that is `airgap-transfer`. Not for a coding agent: that is `airgap-agent`.

## What it does not do

- It syncs no connector (Confluence, SharePoint, Jira). Documents come from a folder or file share, or from uploads in the interface.
- It does no semantic chunking and builds no custom ingestion pipeline: Open WebUI has none. Chunking follows the document's headings, then size (`references/extraction.md`).
- It ranks no models. A score appears only as the reason for a choice, with its model-card source.
- It never sends documents from inside the network to a cloud agent, whatever the user says about speed. The connected-side agent may convert only public documents. Why: a copy that has left cannot be taken back.
- It runs and downloads nothing. It writes files and checks; a person runs them inside.

## Workflow

Copy this checklist into your reply and tick it off as you go:

```
Air-gap RAG:
- [ ] 1. Blueprint read
- [ ] 2. Interview
- [ ] 3. Platform and vector store chosen
- [ ] 4. Extraction and OCR
- [ ] 5. Models
- [ ] 6. Sizing
- [ ] 7. Configuration files
- [ ] 8. Bulk-load runbook and LLM wiki
- [ ] 9. docs/airgap/rag.md
- [ ] 10. Manifest rows
- [ ] 11. Verification steps
- [ ] 12. Self-check, until every item holds
- [ ] 13. Hand-over to airgap-transfer
```

1. **Blueprint.** Read `docs/airgap/blueprint.md` (or the path `AGENTS.md` names) and `docs/airgap/transfer-manifest.md`. Take the vLLM and Open WebUI versions, `org.isolation`, `hardware.gpus` and the `rag` group from them. With no blueprint, ask for them in the interview.
2. **Interview.** Read `references/interview.md`. Ask only the questions the user's message and the blueprint leave open. When the user has not named a platform, ask the platform question with its three options (Open WebUI knowledge bases, recommended; a RAG server, RAGFlow; something else) and wait for the answer, even when they said "set it up", with the other open questions and their defaults in the same message so one reply settles everything. Continue without asking when they named a platform or said to take the recommended option or the defaults; for the other open questions, state the defaults, list them as assumptions in `rag.md` and continue. When the user's answers are short or they ask to go faster, take the fast path: offer the defaults and show the sizing as one summary table.
3. **Platform and store.** Read `references/decisions.md` and the catalog entry of each choice. Open WebUI knowledge bases is the default and the recommendation; a standalone RAG server is RAGFlow; something else is recorded as custom, with its version and docs link, every value not in the catalog labeled `unverified`, and the air-gap checklist applied in full.
4. **Extraction.** Read `references/extraction.md` and `catalog/docling-serve.md`. Pick the tier by document type, write the OCR languages, and state the cloud rule with its reason in `rag.md`.
5. **Models.** Read `references/models.md` and the entries of the embedding and reranker models. Write the vLLM commands, the Open WebUI settings with `OFFLINE_MODE`, and the model revisions.
6. **Sizing.** Read `references/sizing.md`. Step by step, every number sourced or marked `estimate`; on the fast path, one summary table. Never skip it. The volume has no default: without it, put it in the open items.
7. **Configuration.** Write `docs/airgap/rag/`: the Open WebUI settings, the vLLM commands, the docling-serve settings when chosen, the chunking settings, or RAGFlow's `.env` with its egress settings. When the platform is Open WebUI, the PostgreSQL it already uses runs on `pgvector/pgvector:0.8.7-pg18` instead of the plain postgres image (the same PostgreSQL 18.7), and `PGVECTOR_DB_URL` stays unset, so it defaults to `DATABASE_URL`; the alternative is a separate pgvector database with `PGVECTOR_DB_URL` set (`catalog/pgvector.md`).
8. **Runbook and wiki.** Read `references/ingestion.md` and write the bulk load, the periodic update and the CLI queries to `docs/airgap/rag/ingestion.md`, with the manual steps marked MANUAL. Read `references/wiki.md` when `consumers` includes coding agents.
9. **rag.md.** Write `docs/airgap/rag.md`: decisions with reasons and alternatives, assumptions (every default used), the sizing, the folder to knowledge base to group map for the user to fill in, serving requirements, the environment variable that holds each key, whether `BYPASS_ADMIN_ACCESS_CONTROL` stays on, the pgvector image that replaces the plain postgres image (step 7), open items (with bge-m3, "Pickle files allowed: yes" in `airgap-transfer`: `catalog/bge-m3.md`), the components added to the manifest, and the checks to run inside. The component list holds the catalog ids (or `custom: NAME`) of the rows of sections 1 and 3 to 5; for section 2, the Model names exactly as written in the rows; and `airgap-rag` for the project-file rows. Say that the Open WebUI API values were read from source at tag v0.13.4.
10. **Manifest.** Add rows to `docs/airgap/transfer-manifest.md` as the table below shows. Do not rewrite the blueprint. Mark every row you add by writing "(from airgap-rag)" after the component in its Component cell, for example `docling-serve` (from airgap-rag). Section 7 has no Component column, so append the marker to the step text there. `airgap-transfer` accepts rows so marked, without a blueprint row, when `rag.md` lists their component (for section 2, the name in the Model cell).
    - Section 2: the Model cell holds the Hugging Face repo id followed by the marker, for example `Qwen/Qwen3-Embedding-0.6B` (from airgap-rag); Role is `embedding` or `reranker`; Files to carry holds the pinned revision and the entry's `hf download REPO --revision REVISION --local-dir DIR` form, so that the transfer's `models` question is answered from the manifest.
    - Section 3: Component is the catalog id, Version the pinned version, File the file name, Arch `amd64`, `arm64` or `any`, URL the direct download URL from the entry's Packages table (only `catalog/ragflow.md` has one, for its source archive) or the project path for a project file, and Publisher checksums the checksum file URL (empty when none).
    - No fetchable URL: poppler-utils and every image or file of a custom platform take the architect's `custom: NAME` row in section 3 (File "enumerate the artifacts by hand"; Version and URL "not documented" for poppler-utils, `unverified` values for a custom platform), which the transfer turns into a manual item. Docling's OCR models that are not baked in go to section 5 instead, as a manual item with the documented command `docling-tools models download --output-dir DIR` (`catalog/docling-serve.md`).
11. **Verification.** Read `references/verification.md`. Put the five checks into `rag.md` and into section 7 of the manifest.
12. **Self-check.** Check every item below; fix what fails and check again.
13. **Hand-over.** Below.

## The catalog

One file per component. Read an entry before you write about its component; it holds the pinned version, the install, the egress switches with their sources and what to carry in. The architect's catalog already holds `open-webui`, `vllm` and `postgresql`; point to those entries, do not copy them.

| Component | Entry | Kind | Pinned | Pick when |
|---|---|---|---|---|
| docling-serve | `catalog/docling-serve.md` | extractor | v1.39.0 | Scanned or table-heavy documents; `-cpu` image, or `-cu128` with a GPU |
| pgvector | `catalog/pgvector.md` | vector-store | 0.8.7 (`pgvector/pgvector:0.8.7-pg18`) | Default store |
| Qdrant | `catalog/qdrant.md` | vector-store | v1.20.2 | Very large corpora, or a separate service wanted |
| RAGFlow | `catalog/ragflow.md` | rag-platform | v1.0.0 | Scanned and complex PDFs are the core and a separate server is wanted; no group permissions |
| Qwen3-Embedding-0.6B | `catalog/qwen3-embedding.md` | embedding-model | revision in the entry | Default embedding when every language is named for Qwen3 |
| bge-m3 | `catalog/bge-m3.md` | embedding-model | revision in the entry | A language Qwen3 does not name |
| Qwen3-Reranker-0.6B | `catalog/qwen3-reranker.md` | reranker-model | revision in the entry | Default reranker; needs vLLM's `--hf_overrides` |
| bge-reranker-v2-m3 | `catalog/bge-reranker-v2-m3.md` | reranker-model | revision in the entry | No overrides wanted, or bge-m3 chosen |

Last verified: 2026-11-24. Carry the pinned version, not a newer one.

## Outputs

| Path in the project | Holds |
|---|---|
| `docs/airgap/rag.md` | Decisions with reasons, assumptions, sizing, the group map, open items, the checks inside |
| `docs/airgap/rag/` | The configuration of the chosen platform, the runbook (`ingestion.md`) and the wiki steps |
| `docs/airgap/transfer-manifest.md` | The rows below |

| Manifest section | Rows added |
|---|---|
| 1. Images | docling-serve, the RAGFlow stack, `pgvector` (`pgvector/pgvector:0.8.7-pg18`), Qdrant; when `hardware.gpus` is empty, `vllm` with `vllm/vllm-openai-cpu:v0.34.0-x86_64` (`-arm64` on arm64) for the model instances (`references/models.md`) |
| 2. Models | The embedding and reranker models: repo id in the Model cell, pinned revision and download form in Files to carry |
| 3. Packages and binaries | The RAGFlow source archive; `custom: poppler-utils` for the wiki; `custom: NAME` for a custom platform's parts; `docs/airgap/rag.md` and `docs/airgap/rag/` (project paths, copied, not fetched) |
| 4. Telemetry and egress | Every row of the chosen entries' Egress switches, one row each; a row without a documented switch reads "not documented; the egress check covers it" |
| 5. Runtime downloads | What a component fetches on first use, from its "Carry in" section; Docling's OCR models when not baked in, as manual items |
| 7. Verification | The five checks, each step text ending "(from airgap-rag)" |

## Rules

1. **Internal documents never go to a cloud agent.** "Just send the PDFs to Claude, it's faster" gets a no with the reason, and the slower local tier. Converting inside is slower, never unsafe.
2. **The platform is the user's choice.** When it is unnamed, ask it and wait, even when the user said "set it up"; never decide it silently, and never swap one the user named without their consent. A custom choice gets its record, `unverified` labels and the full air-gap checklist.
3. **Ask only open questions, one message.** Except the platform (Rule 2), when the user asked you to set it up, state defaults, list them as assumptions and continue.
4. **The fast path still sizes.** "Skip the sizing" shows the summary table, nothing less.
5. **Every manifest row is marked "(from airgap-rag)"** after its component, or in the step text of section 7.
6. **No key, token or password in any file.** Keys come from environment variables; `rag.md` names them. Never ask for one in the conversation. In command lines, put the URL in a variable on its own line, so that no line holds a download command together with a URL or a pipe.
7. **Versions, paths and setting names come from the catalog and references**, not memory. Where they say "not documented", say so. For a custom platform invent no values; write `unverified`.
8. **When the number of `rag` users differs from the blueprint,** tell the user to rerun the architect's sizing. Do not recompute it here.
9. **Write nothing outside `docs/airgap/`, and install or download nothing.**

## Self-check

Before the hand-over, check each item against the files you wrote. When one fails, fix it and check all of them again.

1. `rag.md` records the platform with its reason and alternatives; a custom platform has its version, docs link and `unverified` labels, and the staged-models, telemetry, manifest and egress items.
2. The cloud rule appears in `rag.md` with its reason, and no step sends internal documents outside.
3. Every Egress switches row of each chosen entry with a documented switch is in `docs/airgap/rag/` and in section 4; each row without one is an open item and a "not documented" row.
4. When the platform is Open WebUI: `OFFLINE_MODE`, the embedding and reranker endpoints, `VECTOR_DB=pgvector` and `PGVECTOR_INDEX_METHOD=hnsw` are written; its PostgreSQL runs on `pgvector/pgvector:0.8.7-pg18` with `PGVECTOR_DB_URL` unset (or a separate pgvector database with it set), and `rag.md` records the substitution. Every model has its pinned revision, or "revision: record at download".
5. The sizing is in `rag.md` with a source or `estimate` on every number, or the summary table on the fast path.
6. `grep -rIE 'sk-[A-Za-z0-9]{8,}|hf_[A-Za-z0-9]{20,}' docs/airgap` finds nothing, and no runbook line holds a download command together with a URL or a pipe.
7. Manifest rows sit in sections 1 to 5 and 7 as the table shows, each is marked "(from airgap-rag)", every pinned version equals its catalog entry, `docs/airgap/rag.md` and `docs/airgap/rag/` are in section 3, and `rag.md` lists the component of every marked row (the Model cell's name for section 2).
8. The folder to knowledge base to group map is in `rag.md` for the user to fill in, manual steps are marked MANUAL, and the five checks are in `rag.md` and section 7.
9. Every default the interview used is an assumption, and a differing `rag` headcount is flagged.

## Hand-over

Tell the user, in their language:

1. What was written: the platform chosen with the reason, and the paths of `rag.md` and `docs/airgap/rag/`.
2. What comes next: run `airgap-transfer`. It bundles the rows marked "(from airgap-rag)" without a blueprint row, and copies `rag.md` and `rag/` as project files, checksummed like any other file.
3. What the inside does after it unpacks the bundle: follow `docs/airgap/rag.md`: install check, bulk load, retrieval, OCR, access and egress checks. A service whose egress check shows an unexpected address is not released to users.
4. What is still open: the group map to fill in, the manual steps, "not documented" and `unverified` items, assumptions from defaults, and a headcount to re-size.

## Common mistakes

| Mistake | Instead |
|---|---|
| Sending the scanned PDFs to a cloud agent to convert them | Convert inside with docling-serve; slower, never unsafe |
| Leaving Open WebUI on its defaults | `OFFLINE_MODE`, an external embedding endpoint and `VECTOR_DB=pgvector` before the first start |
| Loading before `PGVECTOR_INDEX_METHOD=hnsw` is set | Set it first; the `REINDEX` fix is in `catalog/pgvector.md` |
| Skipping the sizing because the user is in a hurry | Show the fast-path summary table |
| Choosing the platform for the user because they said "set it up" | Ask it with the three options, recommend Open WebUI, and wait; defaults apply to the other questions, and a named platform is never swapped |
| Treating a custom tool's behavior as known | Label it `unverified` and run the egress check |
| Writing an API key into the runbook | The key stays in an environment variable |
