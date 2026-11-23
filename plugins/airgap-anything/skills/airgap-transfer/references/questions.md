# Transfer questions

Goal: fill `answers` in `docs/airgap/transfer.json`. `plan.py` creates the file on its first run and, while an answer is missing or does not fit, lists the questions this transfer needs; ask only those.

The scripts import the `transfer_lib` package next to them, so run them as `python3 <skill root>/scripts/plan.py`, not with `python3 -I`: isolated mode leaves their folder off the import path, and they stop with `ModuleNotFoundError: No module named 'transfer_lib'`.

## Rules

1. One question per message, in the user's language. Store IDs and values exactly as written here. Each ID is one flat key of `answers`, dots included: `"bundle.path": "/data/bundle"`, not `"bundle": {"path": "/data/bundle"}`. `plan.py` does not read nested keys; it reports such an answer as missing and asks the question again.
2. Write each answer to `transfer.json` before you ask the next question.
3. Skip every question the conversation or the project's files already answer.
4. Never ask for a token or a password. A model that needs a Hugging Face token gets it from `HF_TOKEN` in the environment of `fetch.sh`, set by the user.

## Questions, in order

| # | ID | Ask | Store | When |
|---|---|---|---|---|
| 1 | `bundle.path` | Where should the bundle be built? It needs room for everything listed. | An absolute path outside the git repository | Always |
| 2 | `models` | For each model of the manifest: where do its files come from? | One entry per model name, see below | The manifest lists models |
| 3 | `medium.capacity_gb` | How large is one medium (USB disk, SSD), in GB? | Number; for `other` also `none` | `transfer.channel` is `removable_media` or `other` |
| 4 | `medium.filesystem` | How is the medium formatted? | `fat32`, `exfat`, `ntfs`, `ext4`, `other` | Same, unless `medium.capacity_gb` is `none` |
| 5 | `channel.max_file_gb` | Does the channel limit the size of one file, in GB? | Number, or `none` | `transfer.channel` is `data_diode` or `staging_host` |
| 6 | `include_benchmark` | Carry the components marked "(benchmark only)"? | `true` or `false`; unanswered means `true` | The manifest has such rows |

Sizes are decimal gigabytes (1 GB = 10^9 bytes).

## `models`

```json
{
  "division-671b": { "source": "huggingface", "repo": "org/name", "revision": "40-character commit hash" },
  "embedder": { "source": "local", "path": "/data/models/embedder" }
}
```

`revision` is the full commit hash of the model repository, so that the bundle records exactly what was fetched. When the user gives a tag or a branch, find the commit it points to on the model's page and confirm it with the user. A `local` path is an absolute path to an existing folder.

`allow_pickle: true` lets `fetch.sh` take pickle-based weights (`.bin`, `.pt`, `.pth`, `.pkl`) for that model. Set it only after the user says that the scanning rules allow them; the inventory marks those files.

## Manual items

`plan.py` turns every custom part and every runtime download of the manifest into an item of kind `manual`; their names are the `name` fields of those items in `plan.items` of `transfer.json`. After the fetch, ask about each one: does the user add files for it under `<bundle>/manual/`, or is it not needed, and why? Record each answer in `manual`:

```json
[
  { "item": "Docker Engine (outside the catalog)", "status": "added", "path": "manual/docker-engine" },
  { "item": "vllm: runtime download 1", "status": "not_needed", "reason": "The model folder carries the tokenizer." }
]
```

`item` is the item's name, exactly. An added item's `path` starts with `manual/`; a `not_needed` item needs a `reason`.

This is the only way a file the manifest does not name gets into the bundle, and only the user decides it, for example for an OS package. Give each such item a name and `status: added`. `pack.py` refuses to pack while an item is not settled.
