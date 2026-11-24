# The plan file and the bundle

## Contents

- The plan file
- Bundle layout
- Packing, in order
- Writing the volumes

The commands assume GNU coreutils and `find` (Linux). On macOS, install them or use the BSD equivalents (`stat -f '%z %N'` for sizes, `shasum -a 256` for `sha256sum`).

## The plan file

`docs/airgap/transfer-plan.md` is the state of one transfer: an interrupted transfer resumes from it. Write it before you ask for approval and keep it current.

```markdown
# Transfer plan: PROJECT NAME

- Manifest: docs/airgap/transfer-manifest.md, generated YYYY-MM-DD
- Blueprint: PATH
- Channel: removable_media · Inside: people · Platform: linux/amd64 · Hardware: nvidia
- Bundle: /data/bundle
- Approved: not yet (or the date and the user's words)

## Answers

| ID | Answer |
|---|---|

## Items

| # | Kind | Component | Source | Bundle path | Size | Status |
|---|---|---|---|---|---|---|
| 1 | image | `vllm` | `vllm/vllm-openai:v0.34.0` | `images/vllm/vllm_vllm-openai_v0.34.0.tar` | | planned |
| 2 | model | | `org/name` at `REVISION` | `models/main-chat` | | planned |
| 3 | package | `k3s` | URL | `packages/k3s/FILE` | | planned |
| 4 | manual | `vllm` | runtime download: compiled kernels | `manual/vllm-kernels` | | ask after the fetch |
| 5 | file | `qwen-code` | `docs/airgap/agents/qwen-code/` | `files/agents/qwen-code/` | | planned |

## Volumes

Filled when packing: the part size, the volume count, what each volume holds.
```

One item per image row, model row, package row and project file row of the manifest, and one manual item per custom part and per runtime download. Benchmark-only rows are items unless `include_benchmark` is `false`. Status moves from `planned` to `fetched`, `copied` (project files) or `failed` (with the error), and for manual items to `added` or `not needed` (with the reason).

## Bundle layout

```
B/
├── SHA256SUMS  PARTS.sha256  VOLUMES.txt  INVENTORY.md  INSIDE.md  AGENTS-INSIDE.md  SEND-ORDER.txt
├── images/COMPONENT/NAME.tar           and NAME.digest
├── models/MODEL/...                    as downloaded, at the pinned commit
├── packages/COMPONENT/FILE             and checksums/SUMSFILE
├── files/PATH/...                      project folders, copied as they are
└── manual/ITEM/...                     files the user added
```

`INSIDE.md` and `AGENTS-INSIDE.md` only as `inside.operator` calls for (`references/inside.md`), `SEND-ORDER.txt` only for a data diode. The bundle folder stays outside the git repository: it can be hundreds of gigabytes.

## Packing, in order

Pack only when every item is `fetched` or `copied`, every manual item is settled, and the checks of `references/fetch.md` ("Checking what arrived") pass.

1. **Sizes.** `cd B && find images models packages files manual -type f -printf '%s %p\n' | sort -rn` lists every file, largest first. Record each item's size in the plan.
2. **Part size.** The smallest of the limits that apply: 4,294,967,295 bytes (4 GiB minus one byte) per file on `fat32`; `channel.max_file_gb` × 10^9 for a data diode or staging host; the volume capacity below. A file larger than the part size is split. No limit applies: nothing is split.
3. **Volume plan.** For removable media, the capacity of one volume is `medium.capacity_gb` × 10^9 × 0.98 (2 % reserve for the shared files and the filesystem). Take the files and parts largest first and put each on the first volume with room, opening a new volume when none has room. Every other channel is one volume. Write the plan into the plan file.
4. **Documents.** Write `INVENTORY.md` (below) and the runbook or agent rules of `references/inside.md`. They name the volume count and the split files, so they come after the volume plan.
5. **Checksums.** One line per file of the bundle, documents included, parts and the volume files excluded:

   ```sh
   cd B && find . -type f ! -name SHA256SUMS ! -name PARTS.sha256 ! -name VOLUMES.txt ! -name SEND-ORDER.txt ! -name 'VOLUME.txt' ! -name '*.part[0-9][0-9][0-9]' | sed 's|^\./||' | LC_ALL=C sort | xargs -d '\n' sha256sum > SHA256SUMS
   ```

   After a translation or any other change of a document, run this again.
6. **Split.** For each file above the part size:

   ```sh
   cd B && split -b PARTSIZE -a 3 --numeric-suffixes=1 "FILE" "FILE.part" && sha256sum "FILE".part[0-9][0-9][0-9] >> PARTS.sha256
   ```

   The parts are `FILE.part001`, `FILE.part002`, …; the whole file stays on the connected side and is not written to a volume. When disk space is short, delete the whole file once its parts are recorded: its line in `SHA256SUMS` stays, and the inside rebuilds it from the parts. With nothing to split, create an empty `PARTS.sha256`: it says that nothing was split. `sha256sum -c` exits 1 on an empty list ("no properly formatted checksum lines found"), so every check of it below runs only when it is not empty.
7. **`VOLUMES.txt`.** One line per file or part that goes onto a volume: `VOLUME SIZE PATH`, for example `2 4294967295 models/main-chat/model-00001-of-00004.safetensors.part001`.
8. **Data diode only: `SEND-ORDER.txt`.** The files in sending order, one path per line: `SEND-ORDER.txt` itself, `SHA256SUMS`, `PARTS.sha256`, `VOLUMES.txt`, `INVENTORY.md`, the runbook files, then every file and part of `VOLUMES.txt`. A resend uses the same names.
9. **Self-check** (`SKILL.md`), then write the volumes.

### `INVENTORY.md`

For the people who approve the transfer and for scanning stations, largest item first:

| Item | Kind | Component | Version | Source | License | Files | Size | Notes |
|---|---|---|---|---|---|---|---|---|

Source is the image reference and digest, the model repository and commit, or the URL. Notes name pickle files the user allowed, a package without publisher checksums, and manual items. The SHA-256 of every file is in `SHA256SUMS`.

## Writing the volumes

One medium at a time. For volume N, with the medium mounted at `M`:

```sh
cd B && { printf '%s\n' SHA256SUMS PARTS.sha256 VOLUMES.txt INVENTORY.md INSIDE.md AGENTS-INSIDE.md | while read -r f; do [ -f "$f" ] && echo "$f"; done; awk -v n=N '$1 == n { sub(/^[^ ]+ [^ ]+ /, ""); print }' VOLUMES.txt; } > /tmp/volume-N.list
cd B && xargs -d '\n' cp --parents -t "M" < /tmp/volume-N.list
echo "volume N of TOTAL" > "M/VOLUME.txt"
cd "M" && sha256sum -c --ignore-missing --quiet SHA256SUMS && { [ ! -s PARTS.sha256 ] || sha256sum -c --ignore-missing --quiet PARTS.sha256; }
cd "M" && while read -r f; do [ -f "$f" ] || echo "missing: $f"; done < /tmp/volume-N.list
```

Every volume carries the shared files, so any one volume tells what the set holds. The read-back checks every file on the medium against its checksum; `--ignore-missing` skips what belongs to other volumes, and the last line reports anything of this volume that did not arrive. Any output or a non-zero exit: the medium may be faulty; write the volume again or use another medium. Otherwise label the medium "volume N of TOTAL".

For a data diode, copy every file that `SEND-ORDER.txt` lists, `SEND-ORDER.txt` included, to the folder the diode sends from; for a staging host, the one volume. Then the same read-back.
