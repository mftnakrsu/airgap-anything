# Transfer questions

Goal: the few answers this transfer needs, recorded in the Answers table of `docs/airgap/transfer-plan.md` (`references/bundle.md`, "The plan file"). Ask only the questions whose "When" holds, and skip what the conversation or the project already answers.

## How to ask

- One question per message, in the user's language. Record each answer in the plan file before you ask the next one.
- Never ask for a token or a password. A model that needs a Hugging Face token gets it from `HF_TOKEN` in the environment of whoever runs the fetch commands, set by the user.

## Questions

| # | ID | Ask | Answer | When |
|---|---|---|---|---|
| 1 | `bundle.path` | Where should the bundle be built? It needs room for everything listed. | An absolute path outside the git repository | Always |
| 2 | `models` | For each model of the manifest: where do its files come from? | One entry per model, see below | The manifest lists models |
| 3 | `medium.capacity_gb` | How large is one medium (USB disk, SSD), in GB? | A number; for `other` also `none` | `transfer.channel` is `removable_media` or `other` |
| 4 | `medium.filesystem` | How is the medium formatted? | `fat32`, `exfat`, `ntfs`, `ext4`, `other` | Same, unless the capacity is `none` |
| 5 | `channel.max_file_gb` | Does the channel limit the size of one file, in GB? | A number, or `none` | `transfer.channel` is `data_diode` or `staging_host` |
| 6 | `include_benchmark` | Carry the components marked "(benchmark only)"? | `true` or `false`; unanswered means `true` | The manifest has such rows |

`transfer.channel`, `inside.operator` and the language come from the blueprint's Answers table; an `unknown` there takes the default the blueprint's assumptions list.

Sizes are decimal gigabytes (1 GB = 10^9 bytes).

## `models`

For a model from Hugging Face: the repository and the full 40-character commit hash, so that the bundle records exactly what was fetched. When the user gives a tag or a branch, look up the commit it points to on the model's page (reading a page is not a download) and confirm it with the user. For a model already on disk: an absolute path to its folder.

| Model | Source | Repository or path | Revision | Pickle files allowed |
|---|---|---|---|---|
| main chat model | huggingface | `org/name` | 40-character commit hash | no |
| embedder | local | `/data/models/embedder` | | no |

"Pickle files allowed" is `no` unless the user says that their scanning rules allow pickle-based weights (`.bin`, `.pt`, `.pth`, `.pkl`) for that model. Pickle files can run code when they are loaded; safetensors files cannot.

## Manual items

Every custom part and every runtime download of the manifest becomes a manual item: nothing in the catalog says exactly which files it needs. After the fetch, ask about each one: does the user add files for it under `<bundle>/manual/<item>/`, or is it not needed, and why? Record the answer in the plan's items table: `added` with the folder, or `not needed` with the reason.

The per-tool skills of manifest section 6 are offered the same way, one manual item each: the user adds a copy of the skill's folder at a commit they choose, or marks it not needed. The manifest names no version for them, so never fetch one yourself.

This is the only way a file the manifest does not name gets into the bundle, and only the user decides it (an operating-system package, for example). The bundle is not packed while a manual item is unsettled.
