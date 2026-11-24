---
title: Searchable documents inside
description: How airgap-rag makes an organization's documents searchable in a network without internet, who chooses the platform, how documents become text, how the first load is sized and the five checks that run inside.
---

Turn on document features in Open WebUI inside a closed network and it tries to download an embedding model on its first start, scanned PDFs come back empty, some extractors send files to hosted services by default (Marker uses datalab.to), and nobody knows how long the first load takes. Inside the network nothing can be downloaded to fix that. `airgap-rag` is the fourth skill: it decides the platform, the extraction, the models and the vector store, sizes the first load and writes the configuration while you still have internet, so that the inside only unpacks, loads and checks. Like the other three it is plain markdown. It downloads nothing and runs nothing; it writes configuration files, a bulk-load runbook and the steps to check them. Its pages are on the [airgap-rag reference](/reference/rag/).

## You choose the platform

After the blueprint exists, ask in your own words, for example "make our documents searchable inside". Unless your message already names a platform, the skill asks which one you want, with three options, and waits for your answer, even when you said "set it up":

1. **Open WebUI knowledge bases** (recommended). Open WebUI is already in the blueprint, and a knowledge base grants Read or Write by group, with groups synced from LDAP or OAuth.
2. **A RAG server**, with RAGFlow as the default. Choose it when scanned or complex PDFs and tables are the core of the corpus and you want a separate server with its own interface and API. Its sharing is only "Only me" or "Team", so there are no group permissions.
3. **Something else**, your own tool. The skill records its name, version and documentation link, labels every value it cannot verify `unverified`, and still applies the air-gap checklist: staged models, telemetry, manifest rows and the egress check.

It never swaps a platform you named. [Decisions](/reference/rag/decisions/) gives the reasons, and why the alternatives are not chosen.

## What it asks

The skill reads the blueprint for `org.isolation`, the GPUs and the `rag` users, then asks, in one message, those of its eight questions that your request and the blueprint leave open, each with its default; only the volume of documents has none. When you asked it to set things up, it states the defaults it takes, lists them as assumptions in `rag.md` and goes on. The questions are: the platform, who searches (chat users, scripts, coding agents), where the documents live and how many pages, what kinds of documents, which languages, how many pages change per week, who may see what, and whether a GPU is available. [Interview](/reference/rag/interview/) lists them. When your answers are short or you ask to go faster, it takes the defaults, records each as an assumption, and shows the sizing as one summary table.

## How documents become text

| Documents | Method |
|---|---|
| Mostly digital PDF and Office | Open WebUI's built-in extractor (pypdf for PDFs) |
| Scanned or table-heavy | docling-serve, with its OCR models carried in and the languages named |
| An LLM wiki for coding agents | The local agent inside, with `pdftotext`, writing markdown into a git repository |

**Documents from inside the network never go to a cloud agent outside it.** "Just send the PDFs to Claude, it's faster" gets a no, with the reason: a copy that has left cannot be taken back. Converting inside is slower, never unsafe. The agent on the connected side may convert only public documents. [Extraction and chunking](/reference/rag/extraction/) has the tiers, the OCR settings and the chunking.

## Sizing the first load

The skill never skips the sizing, because the first load is the part nobody can estimate by feel. It writes it step by step: extraction time, the number of chunks, embedding time and the size of the index, each number with its source or marked `estimate`, plus a line for the small GPU replica that serves the embedding and reranker models. The volume of documents has no default; without it, the sizing goes to the open items. On the fast path the same sizing is one summary table. [Sizing the first load](/reference/rag/sizing/) has the steps and a worked example.

## What it writes

| Path in the project | Holds |
|---|---|
| `docs/airgap/rag.md` | Decisions with reasons and alternatives, every default used as an assumption, the sizing, the folder to knowledge base to group map for you to fill in, the environment variable that holds each key, open items, and the checks to run inside |
| `docs/airgap/rag/` | The configuration of the chosen platform, the bulk-load runbook and the wiki steps |

It also adds rows to the transfer manifest: the images, the embedding and reranker models at their pinned revision, every outbound switch of the chosen components, what each downloads on first use, and the five checks. Every row it adds is marked "(from airgap-rag)", so `airgap-transfer` accepts it without a blueprint row, and carries `rag.md` and `rag/` in as project files, checksummed like everything else ([Carrying it in](/guides/carrying-it-in/)). No key is ever written to a file: keys come from environment variables, and the skill never asks for one in the conversation.

The bulk-load runbook loads a folder into a knowledge base, updates it, grants access and queries it from a script. The Open WebUI API endpoints in it were read from source at v0.13.4, because the docs no longer document them; the steps that need a person are marked MANUAL ([Bulk load, updates and queries](/reference/rag/ingestion/)). Open WebUI has no MCP server, so coding agents get the documents as a wiki instead ([The LLM wiki](/reference/rag/wiki/)).

## The five checks inside

A person runs these, in this order, following `rag.md`. No LLM is needed ([Verification inside](/reference/rag/verification/)).

1. **Install check.** The images and models are the ones carried in, `OFFLINE_MODE` is on and the first start waited on no download, the embedding and reranker endpoints answer, and the vector store has its extension at the pinned version.
2. **Retrieval check.** A question whose answer is in a known document is answered with that document cited, in the interface and through the API.
3. **OCR check.** With docling-serve and the network cut, a scanned page in each named language converts to the right text and nothing tries to download a model.
4. **Access check.** A user outside a group cannot see that group's knowledge base.
5. **Egress check.** Every address the services contact is on the internal network. A service whose egress check shows an unexpected address is not released to users.

## Not in scope

The skill syncs no connector (Confluence, SharePoint, Jira): documents come from a folder or file share, or from uploads in the interface. It builds no custom ingestion pipeline and does no semantic chunking, because Open WebUI has none; chunking follows the document's headings, then size. It ranks no models: a score appears only as the reason for a choice, with its model-card source. For more ideas, see [#12](https://github.com/mftnakrsu/airgap-anything/issues/12).
