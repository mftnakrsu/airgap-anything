# Bulk load, updates and queries over the API

Goal: the runbook that a person inside follows to load a folder into an Open WebUI knowledge base, update it, grant access and query it from a script. Written to `docs/airgap/rag.md`. Manual steps are marked MANUAL.

## Contents

- Where these facts come from
- MANUAL: before the first call
- Group ids
- Load
- Verify the load
- Access
- Periodic updates
- CLI queries
- Large loads and MCP

## Where these facts come from

Read from source at tag v0.13.4; the docs no longer document these endpoints. The Open WebUI docs say its endpoints "are not documented any more" (https://docs.openwebui.com/reference/api-endpoints), and knowledge create, list and access-update are not on the docs pages that were read. Everything below comes from the v0.13.4 backend (`routers/knowledge.py`, `routers/files.py`, `routers/groups.py`, `routers/retrieval.py`, `utils/auth.py`), read on 2026-11-24 and not run. Say this in `rag.md`, and recheck it when the Open WebUI pin moves. Swagger (`/docs`, `/openapi.json`) exists only with `ENV=dev`; the container image sets `ENV=prod`, so do not rely on it.

## MANUAL: before the first call

1. An admin turns on `ENABLE_API_KEYS` (Settings, Authentication, API Keys). It defaults to False, and without it the API answers 403 even for admins and for keys that already exist.
2. Non-admin script users need the `features.api_keys` group permission (admin panel: Users, Groups, Permissions, Features, API Keys). Creating a knowledge base needs the admin role or the `workspace.knowledge` permission.
3. Each user creates their own key (Settings, Account, API keys). The key goes in an environment variable on the machine that runs the commands, never in a file of the repository or of `rag.md`.
4. If `ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS` is on, `API_KEYS_ALLOWED_ENDPOINTS` must list `/api/v1/files`, `/api/v1/knowledge`, `/api/v1/retrieval` and `/api/v1/groups`, or the calls return 403.
5. The user fills in the map in `rag.md`: folder, knowledge base name, groups with Read or Write. Every group needs its id, which "Group ids" finds. Keep each folder flat: this runbook uploads to the root of a knowledge base. Subfolders need Open WebUI's directory endpoints (`/dirs/create`), which it does not cover.
6. Set the variables in the shell that runs the commands. `OWUI_URL` is the internal base address of Open WebUI, `SRC` is the folder to load, and `OUT` is a folder for the answers (the upload answers hold the file ids that the checks need).

```
OWUI_URL=<internal base address of Open WebUI>
SRC=<folder to load>
OUT=<folder for the saved answers>
# OWUI_KEY: export it in the shell from the user's own key; never write it to a file
```

## Group ids

`GET /api/v1/groups/` returns a list of groups, each with `id`, `name` and `member_count` (read from source at tag v0.13.4, `routers/groups.py`). An admin sees all groups; a non-admin sees only the groups they belong to. The id is what `principal_id` takes in the access call.

```
curl -sS --fail -H "Authorization: Bearer $OWUI_KEY" "$OWUI_URL/api/v1/groups/"
```

Copy each `id` next to its group name in the map of `rag.md`. Check: every group of the map appears in the answer by name, once. A missing group means the key's user cannot see it (use an admin's key) or it does not exist yet (the admin creates it first, MANUAL).

## Load

Create the knowledge base: `POST /api/v1/knowledge/create`. The body needs `name` and `description`, both strings; the answer holds the knowledge base `id`. Save the answer and read the `id` from it.

```
curl -sS --fail -X POST -H "Authorization: Bearer $OWUI_KEY" -H "Content-Type: application/json" -d '{"name": "NAME", "description": "DESCRIPTION"}' -o "$OUT/kb.json" "$OWUI_URL/api/v1/knowledge/create"
```

Upload each file with `POST /api/v1/files/` (multipart field `file`) and the form field `metadata` holding `knowledge_id`, so the server links and indexes the file itself. The loop covers PDF, Word and PowerPoint files, saves every answer, and writes the names of files the upload refused to `upload-errors.txt`:

```
KB_ID=<id from kb.json>
META="{\"knowledge_id\": \"$KB_ID\"}"
for f in "$SRC"/*.pdf "$SRC"/*.docx "$SRC"/*.pptx; do
  [ -e "$f" ] || continue
  if ! curl -sS --fail -X POST -H "Authorization: Bearer $OWUI_KEY" -H "Accept: application/json" -F "file=@$f" --form-string "metadata=$META" -o "$OUT/$(basename "$f").json" "$OWUI_URL/api/v1/files/?process_in_background=false"; then
    echo "$f" >> "$OUT/upload-errors.txt"
  fi
done
```

- `--fail` makes curl exit non-zero on an HTTP 4xx or 5xx, and `-sS` still prints the error text. A file listed in `upload-errors.txt` was refused before processing: 413 (`rag.file.max_size` or the knowledge base's size limit), 400 (a type outside `rag.file.allowed_extensions`, or the knowledge base's file limit) or 403 (no write access). A name that is not listed was accepted, which is not the same as indexed: see "Verify the load".
- `process_in_background=false` makes each upload block until processing is done, so no polling is needed. The default is asynchronous: the answer returns at once with the file id, and `GET /api/v1/files/{id}/process/status` gives `{"status": ...}` (`pending`, `processing`, `completed` or `failed`).
- Even with `process_in_background=false`, a failed processing step does not fail the call: the handler records `failed` and the `error` on the file and the upload still answers 200, and its answer is the file as inserted, with `data.status` `pending`. So never judge a file by its upload answer (read from source at tag v0.13.4, `routers/files.py`; not run).
- The alternative path is two steps: upload without `knowledge_id`, then `POST /api/v1/knowledge/{id}/file/add` with `{"file_id": "<id>"}`, or the batch form `POST /api/v1/knowledge/{id}/files/batch/add` with a list. Adding a file before it is processed fails with 400 "content provided is empty" (`FILE_NOT_PROCESSED`); duplicate extracted text fails with 400 "Duplicate content detected".
- A knowledge base has its own file limits (`KNOWLEDGE_MAX_FILE_SIZE`, `KNOWLEDGE_MAX_FILE_COUNT`, `KNOWLEDGE_MAX_UPLOAD_COUNT`).
- Throttle bulk loads: uploads linked to a knowledge base share a semaphore of about half the thread pool. Load in batches and watch the extraction service (`catalog/docling-serve.md`). A file stuck in Processing after a restart is not re-uploaded by sync for an hour.

## Verify the load

After each batch, list what the knowledge base holds and what is still processing. A file that failed is unlinked from the knowledge base, so it is missing from the list (read from source at tag v0.13.4).

```
curl -sS --fail -H "Authorization: Bearer $OWUI_KEY" -o "$OUT/files.json" "$OWUI_URL/api/v1/knowledge/$KB_ID/files?page=1"
curl -sS --fail -H "Authorization: Bearer $OWUI_KEY" -o "$OUT/pending.json" "$OWUI_URL/api/v1/knowledge/$KB_ID/files/pending"
```

- `files.json` holds `items` (the linked files, with their ids and names) and `total`. Pages hold 30 items by default (the parameter's own description; an admin can pass `limit`): read `total`, and add `page=2` and later until `items` is empty.
- `pending.json` lists files that are still `pending` or `processing` and not yet linked. Wait until it is `[]` before judging the load.
- Pass: `total` equals the number of files uploaded without an entry in `upload-errors.txt`, and `pending.json` is `[]`.
- Fail: a file name from the load is missing from `items` once `pending.json` is `[]`. It failed. Take its id from its saved answer (`$OUT/NAME.json`, field `id`) and read the reason:

```
FILE_ID=<id from the saved answer of the missing file>
curl -sS --fail -H "Authorization: Bearer $OWUI_KEY" "$OWUI_URL/api/v1/files/$FILE_ID"
```

  The answer has `data.status` `failed` and `data.error`. The status endpoint of the polling path gives only the status; `?stream=true` adds the error, and this call is simpler. Fix the cause (often a missing OCR model: `references/verification.md`, check 3), then upload that file again. The failed file keeps its stored copy until it is deleted: `DELETE /api/v1/files/{id}` removes it (read from source at tag v0.13.4).

## Access

`POST /api/v1/knowledge/{id}/access/update` with a body of the form `{"access_grants": [{"principal_type": "group", "principal_id": "GROUP_ID", "permission": "read"}]}`.

- `principal_type` is `user`, `group` or `anyone`; `permission` is `read` or `write`. `anyone` is valid only as `principal_id` `*` with `read`, which is public read for every signed-in user.
- The call replaces the whole list: send every grant that should remain. Invalid entries are silently dropped, so read the knowledge base back after the call.
- The caller must be the owner, a `write` grantee or an admin. An empty or absent list means private to the owner (inferred from the source, not stated).
- The same `access_grants` list can be passed at create time; non-admins are filtered by their sharing permissions.
- Each knowledge base's groups come from the user's map in `rag.md`. Admins see private bases while `BYPASS_ADMIN_ACCESS_CONTROL` is on, which is the default: `references/verification.md`, check 4.

```
curl -sS --fail -X POST -H "Authorization: Bearer $OWUI_KEY" -H "Content-Type: application/json" -d '{"access_grants": [{"principal_type": "group", "principal_id": "GROUP_ID", "permission": "read"}]}' "$OWUI_URL/api/v1/knowledge/$KB_ID/access/update"
```

Read the knowledge base back and compare its grants with the map: `GET /api/v1/knowledge/{id}` returns the knowledge base with its `access_grants` (the model carries the field; not run).

```
curl -sS --fail -H "Authorization: Bearer $OWUI_KEY" "$OWUI_URL/api/v1/knowledge/$KB_ID"
```

## Periodic updates

Match the rate of the `updates` answer. A weekly batch is one run of the steps below. The folder stays flat, so every `path` is empty. Commands read from source at tag v0.13.4 (`routers/knowledge.py`); the diff and cleanup calls are also described at https://docs.openwebui.com/features/workspace/knowledge.

1. Build a manifest of the folder: for each file its name, its SHA-256 and its size. A file name with a quote or a backslash in it would break this JSON: rename it first.

```
MANIFEST="$OUT/manifest.json"
printf '{"manifest": [' > "$MANIFEST"
SEP=""
for f in "$SRC"/*.pdf "$SRC"/*.docx "$SRC"/*.pptx; do
  [ -e "$f" ] || continue
  SUM=$(sha256sum "$f" | cut -d' ' -f1)
  SIZE=$(stat -c %s "$f")
  printf '%s{"filename": "%s", "path": "", "checksum": "%s", "size": %s}' "$SEP" "$(basename "$f")" "$SUM" "$SIZE" >> "$MANIFEST"
  SEP=","
done
printf ']}' >> "$MANIFEST"
```

2. Ask the knowledge base what differs: `POST /api/v1/knowledge/{id}/sync/diff`.

```
curl -sS --fail -X POST -H "Authorization: Bearer $OWUI_KEY" -H "Content-Type: application/json" --data @"$MANIFEST" -o "$OUT/diff.json" "$OWUI_URL/api/v1/knowledge/$KB_ID/sync/diff"
```

   `diff.json` has `added` (`filename`, `path`), `modified` (`filename`, `path`, `stale_file_id`), `deleted` (`file_id`, `filename`) and `unmodified_count`. It also has `mkdir` and `rmdir`, which stay empty for a flat folder. A file whose name matches but whose checksum differs is `modified`.
3. Remove the stale and the deleted files in one call: `POST /api/v1/knowledge/{id}/sync/cleanup`, with every `stale_file_id` and every `file_id` of `deleted`. It unlinks each file, deletes its vectors and, unless the server keeps files (`ENABLE_KNOWLEDGE_FILE_RETENTION`), deletes the stored file when the caller owns it or is an admin.

```
IDS='"FILE_ID_1", "FILE_ID_2"'
curl -sS --fail -X POST -H "Authorization: Bearer $OWUI_KEY" -H "Content-Type: application/json" -d "{\"file_ids\": [$IDS], \"dir_ids\": []}" "$OWUI_URL/api/v1/knowledge/$KB_ID/sync/cleanup"
```

   The answer is `{"status": true}`. Ids that do not belong to this knowledge base are skipped silently, so check the result with "Verify the load". For a single file the alternative is `POST /api/v1/knowledge/{id}/file/remove` with `{"file_id": "<id>"}`; its query `delete_file` decides whether the stored file goes too (the default follows `ENABLE_KNOWLEDGE_FILE_RETENTION`).
4. Upload the `added` and `modified` files with the loop of "Load" (limit the loop to those names), then run "Verify the load". Removing the stale copy before uploading the new one is the order this runbook uses so that two versions never answer a query; the source does not say which order the official sync tool uses (unverified).
5. After changing the embedding model or the chunking settings, reindex (`references/models.md`, `references/extraction.md`).

## CLI queries

`POST /api/v1/retrieval/query/collection` returns the matching chunks of a knowledge base, with the same key and the same access rules. The body is `{"collection_names": ["<kb id>"], "query": "...", "k": 5}`; `hybrid` is an optional field. The knowledge base id is the vector collection name.

```
curl -sS --fail -X POST -H "Authorization: Bearer $OWUI_KEY" -H "Content-Type: application/json" -d '{"collection_names": ["KB_ID"], "query": "QUESTION", "k": 5}' "$OWUI_URL/api/v1/retrieval/query/collection"
```

Listing: `GET /api/v1/knowledge/?page=1` returns `{"items": [...], "total": N}`; each item has `write_access`. The page size (`PAGE_ITEM_COUNT`) was not read.

## Large loads and MCP

- **`oikb`**: the official sync tool (`pip install oikb`, Python 3.11 and later, Open WebUI 0.9.6 and later, `oikb sync ./docs --kb-id <id>`, environment `OPEN_WEBUI_URL` and `OPEN_WEBUI_API_KEY`) drives the sync endpoints, and the docs call it the way to load tens of thousands of files (https://docs.openwebui.com/ecosystem/knowledge-base-sync). It is a pip package, so it would have to be staged as a wheel. Its license, source and offline install were not checked: an open point. It is not recommended here until they are; plain API calls work without it.
- **MCP:** the official docs cover Open WebUI only as an MCP client, and the v0.13.4 source has no MCP server route. The one retrieval-focused community server is RonasIT/open-webui-mcp-server (MIT, v0.2.0, Node 22, npm package `open-webui-knowledge-mcp-server`): unverified, untested offline, and its README states support for Open WebUI 0.7.2 and later (https://github.com/RonasIT/open-webui-mcp-server). The supported path for agents is the LLM wiki (`references/wiki.md`).
