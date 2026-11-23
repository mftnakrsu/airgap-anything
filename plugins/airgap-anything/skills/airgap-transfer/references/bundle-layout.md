# Bundle layout

```
<bundle>/
├── bundle.json  SHA256SUMS  PARTS.txt  VOLUMES.txt  INVENTORY.md  INVENTORY.csv
├── verify.sh  load.sh  INSIDE.md  AGENTS-INSIDE.md  SEND-ORDER.txt
├── fetch.sh  fetch.log  .fetch/          connected side only; never written to volumes
├── images/<component>/<name>.tar          and <name>.digest, <name>.id
├── models/<model name>/...                as downloaded, at the pinned commit
├── packages/<component>/<file>            and checksums/<publisher checksum file>
└── manual/<item>/...                      files the user added
```

Files and folders whose names start with a dot inside an item folder are not carried, nor are unfinished `*.download` files; `pack.py` refuses to pack while one is left. `pack.py` names every other file that no item claims as not carried.

## The files pack.py writes

| File | Holds |
|---|---|
| `bundle.json` | Every item: kind, component, version, source (image reference, digest and image ID; URL; or model repository and commit), files with size, SHA-256 and volume, and the manifest digest the bundle was made from |
| `SHA256SUMS` | One line per original file in coreutils format (`<hash>  <path>`), and one for each file below except itself |
| `PARTS.txt` | For every split file: the number of parts, the SHA-256 of the whole file, the path. Part N is the path followed by `.partNNN` |
| `VOLUMES.txt` | For every file or part on a volume: the volume, the size, the SHA-256, the path |
| `INVENTORY.md`, `INVENTORY.csv` | For the people who approve the transfer: path, size, SHA-256, kind, component, version, source, licence, and the pickle mark, largest first |
| `verify.sh`, `load.sh` | Copied from `templates/`; `load.sh` with the `docker` command lines of `references/fetch.md` filled in |
| `INSIDE.md`, `AGENTS-INSIDE.md` | As `inside.operator` calls for; see `references/inside.md` |
| `SEND-ORDER.txt` | For `data_diode` only: the files in sending order |
| `VOLUME.txt` | On each medium only: "volume 2 of 3" |

`pack.py` also writes `pack` into `transfer.json`: the volume plan, the total size and the time it ran.

## check.py

Exit 0 clean (warnings allowed), 1 findings, 2 unreadable, missing or invalid input (an answer that does not fit, an incomplete `bundle.json`), 3 Python older than 3.11. `--deep` recomputes every hash; `--format json` prints the findings as JSON.

| Code | Check |
|---|---|
| B1 | Every item of the plan has its files in the bundle, or is a manual item marked not needed with a reason |
| B2 | Every file has a line in `SHA256SUMS` and its size matches `bundle.json`, and every file `pack.py` wrote matches its line; with `--deep`, every hash is recomputed |
| B3 | No file on a volume is larger than the channel allows |
| B4 | Every volume fits `medium.capacity_gb` minus the reserve |
| B5 | The bundle's manifest digest equals the project's current `transfer-manifest.json`, and the bundle was packed for the blueprint's current `inside.operator` and `transfer.channel` |
| B6 | A model carries pickle-based weights without the user's explicit permission |
| B7 | The runbook or the agent rules that `inside.operator` calls for are missing, or lack a command line |
| B8 | A file holds a value that looks like a token (`hf_` followed by 20 or more letters and digits, or the value of `HF_TOKEN` when it is set and 8 or more characters long); bundle files up to 16 MiB and `transfer.json` are read |

| Code | Warning |
|---|---|
| BW1 | A package has no publisher checksum file; its hash was first computed on the connected side |
| BW2 | An image has no recorded digest |
