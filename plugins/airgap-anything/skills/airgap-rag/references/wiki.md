# The LLM wiki for coding agents

Goal: give coding agents the organization's documents as plain markdown files in a git repository, read with the tools they already have. Open WebUI has no MCP server, so this is the supported path for agents (`references/ingestion.md`, "Large loads and MCP").

## How it works

1. The local agent inside the network converts each document with `pdftotext`, which is in poppler-utils. poppler-utils is an OS package: take it from the internal mirror, or carry it in as a row in section 3 of the transfer manifest, marked "(from airgap-rag)". Its version and download address are not documented in the research: record the version the mirror provides.
2. The agent writes one markdown file per document into a git repository, keeping the folder structure of the source. Each file starts with a heading holding the document's name and a line naming the source path, then the text. A short index file per folder lists the documents with one line each.
3. The repository is committed, so a change in a document is a diff and a reviewable change.
4. Coding agents read it with grep and read, the tools a coding agent already has. Or they reach it through the `mcp-server-git` in airgap-agent's MCP reference (none of its tools fetches, pulls or clones), or the folder is simply opened as a workspace.

Search by grep finds words, not meaning. Say so in `rag.md`: the wiki is the path for agents, the knowledge bases are the path for people and scripts.

## Limits

- `pdftotext` reads the text layer of a PDF. A scanned PDF has none, so the result is empty or short (inferred from how the tool works; confirm on a sample). For scanned documents use docling-serve inside and save its markdown instead (`catalog/docling-serve.md`, `references/extraction.md`).
- Layout and tables are not preserved the way Docling preserves them: not tested here.
- Office files need another converter. The research documents none for the wiki: list them in the open items rather than guess a tool.

## The cloud rule

Never send documents from inside the network to a cloud agent outside it to convert them. The connected-side agent may convert only public documents; the conversion of internal documents is done by the local agent inside (`references/extraction.md`, "The cloud rule").

## What goes in `rag.md`

The repository path, the conversion command the agent runs, how often it runs (the `updates` answer), the list of documents it could not convert, and who may read the repository (it is as sensitive as the documents: give it the same access as the `access` answer says for the knowledge bases).
