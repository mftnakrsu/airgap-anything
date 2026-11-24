# Bulk load, updates and queries over the API

Goal: the runbook that a person inside follows to load a folder into an Open WebUI knowledge base, update it, grant access and query it from a script. Written to `docs/airgap/rag.md`. Manual steps are marked MANUAL.

## Contents

- Where these facts come from
- MANUAL: before the first call
- Load
- Access
- Periodic updates
- CLI queries
- Large loads and MCP

## Where these facts come from

Read from source at tag v0.13.4; the docs no longer document these endpoints. The Open WebUI docs say its endpoints "are not documented any more" (https://docs.openwebui.com/reference/api-endpoints), and knowledge create, list and access-update are not on the docs pages that were read. Everything below comes from the v0.13.4 backend (`routers/knowledge.py`, `routers/files.py`, `routers/retrieval.py`, `utils/auth.py`), read on 2026-11-24 and not run. Say this in `rag.md`, and recheck it when the Open WebUI pin moves. Swagger (`/docs`, `/openapi.json`) exists only with `ENV=dev`; the container image sets `ENV=prod`, so do not rely on it.

## MANUAL: before the first call

1. An admin turns on `ENABLE_API_KEYS` (Settings, Authentication, API Keys). It defaults to False, and without it the API answers 403 even for admins and for keys that already exist.
2. Non-admin script users need the `features.api_keys` group permission (admin panel: Users, Groups, Permissions, Features, API Keys). Creating a knowledge base needs the admin role or the `workspace.knowledge` permission.
3. Each user creates their own key (Settings, Account, API keys). The key goes in an environment variable on the machine that runs the commands, never in a file of the repository or of `rag.md`.
4. If `ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS` is on, `API_KEYS_ALLOWED_ENDPOINTS` must list `/api/v1/files`, `/api/v1/knowledge` and `/api/v1/retrieval`, or the calls return 403.
5. The user fills in the map in `rag.md`: folder, knowledge base name, groups with Read or Write. Group ids: how to list groups by API is not documented (the router was not read); take the ids from the admin side and keep them in the map.

## Load

Set the variables once. `OWUI_URL` is the internal base address of Open WebUI, and `OWUI_KEY` holds the user's key.

```
OWUI_URL=<internal base address of Open WebUI>
# OWUI_KEY: export it in the shell from the user's own key; never write it to a file
```

Create the knowledge base: `POST /api/v1/knowledge/create`. The body needs `name` and `description`, both strings; the answer holds the knowledge base `id`.

```
curl -X POST -H "Authorization: Bearer $OWUI_KEY" -H "Content-Type: application/json" -d '{"name": "NAME", "description": "DESCRIPTION"}' "$OWUI_URL/api/v1/knowledge/create"
```

Upload each file with `POST /api/v1/files/` (multipart field `file`) and the form field `metadata` holding `knowledge_id`, so the server links and indexes the file itself:

```
KB_ID=<id from the create answer>
META="{\"knowledge_id\": \"$KB_ID\"}"
for f in FOLDER/*.pdf; do
  curl -X POST -H "Authorization: Bearer $OWUI_KEY" -H "Accept: application/json" -F "file=@$f" --form-string "metadata=$META" "$OWUI_URL/api/v1/files/?process_in_background=false"
done
```

- `process_in_background=false` makes each upload block until processing is done, so no polling is needed. The default is asynchronous: the answer returns at once with `data.status` `pending` and the file id, and you poll `GET /api/v1/files/{id}/process/status` until `completed` (the other values are `pending`, `processing` and `failed`, with an `error` string).
- The alternative path is two steps: upload without `knowledge_id`, then `POST /api/v1/knowledge/{id}/file/add` with `{"file_id": "<id>"}`, or the batch form `POST /api/v1/knowledge/{id}/files/batch/add` with a list. Adding a file before it is processed fails with 400 "content provided is empty" (`FILE_NOT_PROCESSED`); duplicate extracted text fails with 400 "Duplicate content detected".
- Upload limits: `rag.file.max_size` gives 413 and `rag.file.allowed_extensions` gives 400. A knowledge base has its own file limits (`KNOWLEDGE_MAX_FILE_SIZE`, `KNOWLEDGE_MAX_FILE_COUNT`, `KNOWLEDGE_MAX_UPLOAD_COUNT`).
- Throttle bulk loads: uploads linked to a knowledge base share a semaphore of about half the thread pool. Load in batches and watch the extraction service (`catalog/docling-serve.md`). A file stuck in Processing after a restart is not re-uploaded by sync for an hour.
- The loop runs one file at a time on purpose. A failed file shows `failed` with its `error`: collect those, fix the cause (often a missing OCR model), and upload them again.

## Access

`POST /api/v1/knowledge/{id}/access/update` with a body of the form `{"access_grants": [{"principal_type": "group", "principal_id": "GROUP_ID", "permission": "read"}]}`.

- `principal_type` is `user`, `group` or `anyone`; `permission` is `read` or `write`. `anyone` is valid only as `principal_id` `*` with `read`, which is public read for every signed-in user.
- The call replaces the whole list: send every grant that should remain. Invalid entries are silently dropped, so read the knowledge base back after the call.
- The caller must be the owner, a `write` grantee or an admin. An empty or absent list means private to the owner (inferred from the source, not stated).
- The same `access_grants` list can be passed at create time; non-admins are filtered by their sharing permissions.
- Each knowledge base's groups come from the user's map in `rag.md`. Admins see private bases while `BYPASS_ADMIN_ACCESS_CONTROL` is on, which is the default: `references/verification.md`, check 4.

```
curl -X POST -H "Authorization: Bearer $OWUI_KEY" -H "Content-Type: application/json" -d '{"access_grants": [{"principal_type": "group", "principal_id": "GROUP_ID", "permission": "read"}]}' "$OWUI_URL/api/v1/knowledge/$KB_ID/access/update"
```

## Periodic updates

Match the rate of the `updates` answer. A weekly batch is one run of the loop above on the changed files.

- New files: upload as in Load.
- Changed files: `POST /api/v1/knowledge/{id}/sync/diff` takes a manifest `[{path, filename, checksum}]` with SHA-256 checksums and returns what to add, modify and delete (documented at https://docs.openwebui.com/features/workspace/knowledge). How a modified file replaces its old version is not documented in the research. The safe order, inferred and untested: remove the old file, then upload the new one.
- Deleted files: `POST /api/v1/knowledge/{id}/sync/cleanup` with `{"file_ids": [...], "dir_ids": [...]}` removes them (same page). A per-file delete endpoint was not read: not documented.
- Chunk and model settings: after changing the embedding model or the chunking settings, reindex (`references/models.md`, `references/extraction.md`).

## CLI queries

`POST /api/v1/retrieval/query/collection` returns the matching chunks of a knowledge base, with the same key and the same access rules. The body is `{"collection_names": ["<kb id>"], "query": "...", "k": 5}`; `hybrid` is an optional field. The knowledge base id is the vector collection name.

```
curl -X POST -H "Authorization: Bearer $OWUI_KEY" -H "Content-Type: application/json" -d '{"collection_names": ["KB_ID"], "query": "QUESTION", "k": 5}' "$OWUI_URL/api/v1/retrieval/query/collection"
```

Listing: `GET /api/v1/knowledge/?page=1` returns `{"items": [...], "total": N}`; each item has `write_access`. The page size (`PAGE_ITEM_COUNT`) was not read.

## Large loads and MCP

- **`oikb`**: the official sync tool (`pip install oikb`, Python 3.11 and later, Open WebUI 0.9.6 and later, `oikb sync ./docs --kb-id <id>`, environment `OPEN_WEBUI_URL` and `OPEN_WEBUI_API_KEY`) drives the sync endpoints, and the docs call it the way to load tens of thousands of files (https://docs.openwebui.com/ecosystem/knowledge-base-sync). It is a pip package, so it would have to be staged as a wheel. Its license, source and offline install were not checked: an open point. It is not recommended here until they are; plain API calls work without it.
- **MCP:** the official docs cover Open WebUI only as an MCP client, and the v0.13.4 source has no MCP server route. The one retrieval-focused community server is RonasIT/open-webui-mcp-server (MIT, v0.2.0, Node 22, npm package `open-webui-knowledge-mcp-server`): unverified, untested offline, and its README states support for Open WebUI 0.7.2 and later (https://github.com/RonasIT/open-webui-mcp-server). The supported path for agents is the LLM wiki (`references/wiki.md`).
