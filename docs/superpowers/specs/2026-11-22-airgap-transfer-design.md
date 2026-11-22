# airgap-anything — Design Spec for the airgap-transfer skill and the inside operator

- **Date:** 2026-11-22
- **Status:** Draft, for the maintainer's review
- **Covers:** sub-project 2 — who works inside the network, the CPU architecture, a machine-readable transfer manifest, and the second skill, `airgap-transfer`
- **Builds on:** `docs/superpowers/specs/2026-11-20-airgap-architect-design.md` (sub-project 1). Its principles hold here unless this spec says otherwise.

## 1. Summary

`airgap-architect` decides what to carry into an air-gapped network and writes it down in the transfer manifest. Carrying it in is still manual: the manifest's digest, size and checksum columns are empty, and its custom rows say "enumerate artifacts manually".

This sub-project closes that step:

1. Architect asks two more questions: who carries out the work inside the network (people, an agent on a local model, or people first and an agent later), and which CPU architecture the servers inside have.
2. Architect's `manifest.py` also writes the manifest as JSON, so that another skill can read it without importing architect's code.
3. A new skill, `airgap-transfer`, turns that manifest into a verified bundle: a fetch script for the connected side, checksums, a split across media, an inventory for the people who approve the transfer, and the scripts and instructions for the inside.

Every step inside the network works with neither internet nor an LLM. When an agent on a local model works inside, it runs the same scripts as a person would.

## 2. Problem

On the demo blueprint (`design/demo/department-blueprint.json`) `manifest.py` writes 11 image rows, 1 model row, 2 package rows and 5 rows that say "enumerate artifacts manually". A person then has to pull every image for the right platform, download every model file, fetch every package, record digests and checksums, fit the files onto media, carry them, check them inside and load them. Each of those steps fails quietly when done by hand: a wrong platform, a pickle file that the scanning station rejects, a file over the 4 GB limit of a FAT32 disk, a checksum that nobody recomputes inside.

The design spec and the documentation also say that "an agent inside builds the system". On the first day there may be no agent inside: the LLM being carried in is not running yet.

Prior art (GitHub code search on 2026-11-22; not exhaustive): per-language offline bundle skills (Python, Go, JavaScript, TypeScript), a Hauler quickstart skill, a skill for one lab VM. None found that takes a whole-stack manifest to a verified bundle and a loader inside. Checking one product for offline readiness is covered by `airgap-vetting` in `air-gapped/skills` and stays out of scope.

## 3. Decisions taken with the maintainer (2026-11-22)

| Topic | Decision |
|---|---|
| Inside the network | Ask the user who carries out the work inside. Every inside step must work without internet and without an LLM; an agent, if there is one, runs the same scripts. |
| Channel | One bundle for every channel. Only splitting and sending order change with the channel. No integration with vendor products (data diodes, kiosks): each needs its own work and its hardware to test. |
| Skill family | `airgap-transfer` first, then `airgap-agent`, then `airgap-rag`, each with its own spec, plan and evaluation. |
| Other skills | Per-tool skills (for example `air-gapped/skills`) are pointed to, not copied. |

## 4. Scope

In scope:

1. Architect: the questions `inside.operator` and `hardware.cpu_arch`; the agent instruction block and the blueprint follow `inside.operator`; the manifest filters packages by architecture and is written as Markdown and JSON.
2. Catalog: package rows become tables with the file name, the architecture, the download URL and, where the publisher has one, the URL of its checksum file. arm64 rows are added where the release publishes arm64 files.
3. The skill `airgap-transfer`: a short interview, `plan.py`, `pack.py`, `check.py`, the inside scripts `verify.sh` and `load.sh`, a runbook for people and rules for an inside agent.
4. Tests, scenario fixtures, the triggering suite and the behavior evaluation for both skills.
5. Documentation: README, documentation site, HANDOFF, CONTRIBUTING, a release, and a project page on mefby.com.

Out of scope:

1. Integration with data diode, kiosk or cross-domain products.
2. OS-level packages (Docker Engine, GPU driver and container toolkit): the bundle carries them when the user adds them by hand, as "manual items" (§9.4), and tells what is missing.
3. Runtime downloads as automated items. The catalog describes them in prose; the bundle lists them as manual items with that prose.
4. Signature verification with tools that need their own trust root (sigstore, cosign). Publisher checksum files are checked; signatures are listed in the inventory for a later version.
5. Delta bundles between two designs (`airgap-upgrade`, later).
6. Other inputs than architect's manifest (a Compose file, lockfiles; later).

## 5. Users and where each part runs

| Part | Where | Who |
|---|---|---|
| Interview, `plan.py`, `pack.py`, `check.py` | Connected workstation | The agent, with Python 3.11 or newer |
| `fetch.sh` | Connected workstation | The user, or the agent after the user approves it |
| Writing the volumes | Connected workstation, with the medium attached | `pack.py --write-volume`, run by the agent or the user |
| `verify.sh`, `load.sh` | Inside the network | A person or an inside agent; POSIX shell and coreutils only, no Python |

The inside host may have no Python, or an old one, so nothing inside depends on Python.

## 6. Changes to airgap-architect

### 6.1 Two questions

Added to `references/interview.md`:

| ID | Ask | Store | Default for "unknown" |
|---|---|---|---|
| `hardware.cpu_arch` | Which CPU architecture do the servers inside the network have? | `amd64`, `arm64` | `amd64`, recorded as an assumption (W2) |
| `inside.operator` | Inside the network, who will carry out the installation and later work? | `people` (no LLM inside), `local_agent` (an agent on a local model already runs inside), `people_then_agent` (people on the first day, then an agent on this platform's model) | `people`, recorded as an assumption (W2) |

Both defaults are the choice that cannot leave the inside stuck: amd64 is the most common server architecture, and a runbook works whether or not an agent appears. Both go into `catalog/rules.toml` under `defaults.` with the label `estimate`.

When `inside.operator` is `local_agent` or `people_then_agent` and that agent runs on this platform, the interview reminds the user to count it under `code_assistant` in `workload.usage`; agentic tools keep a request in flight most of the time.

### 6.2 What follows from `inside.operator`

- **Agent instruction block** (`references/agents-snippet.md`): the base block stays. For `local_agent` and `people_then_agent` it gains a section "Rules for an agent inside the network": one command per step, check every exit code, stop on a non-zero exit and report it, never download, never edit the generated scripts, never improvise a step the runbook does not name.
- **Blueprint** (`references/blueprint-template.md`): section 6 says who carries out the inside steps and what they receive (runbook, agent rules or both) and names `airgap-transfer` as the next step; section 8 says who does upgrades.
- **Lint:** W4 when `inside.operator` is `local_agent` or `people_then_agent` and the block lacks the rules section.
- **Hand-off** (`SKILL.md`): the next steps printed without superpowers become "transfer with `airgap-transfer`, install, benchmark".

### 6.3 Architecture in the manifest

- The manifest header gains `Platform: linux/<cpu_arch>`. Images are pulled for that platform.
- Package rows carry an `arch` (§7). The manifest lists the rows for the blueprint's architecture and rows marked `any`. A chosen component with packages but none for the architecture gets a line after the table, as images already do for a missing hardware class.
- The inputs digest covers `hardware.cpu_arch` in addition to `decisions`, `workload.models` and `hardware.gpus`. A manifest written before this change fails E8 once and is fixed by running `manifest.py` again.

### 6.4 The manifest as JSON

`manifest.py` writes `docs/airgap/transfer-manifest.json` next to the Markdown file, from the same data in one pass. `schema_version` 1:

```json
{
  "schema_version": 1,
  "project": "department-llm-platform",
  "generated": "2026-11-22",
  "inputs_digest": "sha256:...",
  "hardware_class": "nvidia",
  "platform": "linux/amd64",
  "images": [
    { "component": "vllm", "version": "v0.34.0", "ref": "vllm/vllm-openai:v0.34.0",
      "hardware": ["nvidia"], "digest": "", "target": "REGISTRY_HOST/vllm/vllm-openai:v0.34.0", "benchmark": false }
  ],
  "models": [ { "name": "division-671b", "role": "chat" } ],
  "packages": [
    { "component": "harbor", "version": "v2.16.0", "file": "harbor-offline-installer-v2.16.0-amd64.tgz",
      "arch": "amd64", "url": "https://...", "checksums": "https://...", "benchmark": false }
  ],
  "custom": [ { "layer": "orchestration", "name": "Docker Engine (outside the catalog)" } ],
  "telemetry": [ { "component": "vllm", "what": "...", "disable": "..." } ],
  "runtime_downloads": [ { "component": "vllm", "text": "..." } ],
  "skills": [ { "component": "vllm", "repo": "air-gapped/skills", "skill": "vllm-configuration" } ],
  "missing_variants": [ "..." ]
}
```

Lint E8 checks both files: each must exist and carry the current inputs digest.

## 7. Catalog change: package rows

Component `schema_version` becomes 2 for every entry. `airgap.packages` changes from a list of file names to a list of tables:

```toml
packages = [
  { file = "harbor-offline-installer-v2.16.0-amd64.tgz", arch = "amd64",
    url = "https://github.com/goharbor/harbor/releases/download/v2.16.0/harbor-offline-installer-v2.16.0-amd64.tgz",
    checksums = "" },
]
```

| Field | Rule |
|---|---|
| `file` | The name the release gives the file |
| `arch` | `amd64`, `arm64` or `any` (scripts, architecture-free archives) |
| `url` | The download URL, as the release page or the official documentation gives it; recorded in `evidence.sources` too |
| `checksums` | The URL of the publisher's checksum file that lists this file, or `""` when there is none. md5 lists (Harbor's `md5sum`) count: the fetch script checks whatever algorithm the file names. |

Four entries have packages today (`docker-compose`, `harbor`, `k3s`, `rke2`). Each gains arm64 rows where its release publishes arm64 files; their notes already name them. Every new value is read from the release page at authoring time and `last_verified` is updated (CONTRIBUTING). Catalog lint adds:

| Code | Check |
|---|---|
| C5 | A package row lacks `file`, `arch` or `url`, or `arch` is not one of the three values |
| C6 | A package `url` or `checksums` value is not a full `https://` URL |

CONTRIBUTING's template and field table change with it.

## 8. The skill `airgap-transfer`

### 8.1 Layout

```
plugins/airgap-anything/skills/airgap-transfer/
├── SKILL.md                      process, under 150 lines
├── references/
│   ├── questions.md              the transfer questions, order, defaults
│   ├── channels.md               rules per channel and for scanning stations
│   ├── fetch.md                  what fetch.sh does, the tools it needs, the approval rule
│   ├── inside.md                 the runbook template and the inside agent rules
│   └── bundle-layout.md          the folders and files of a bundle
├── templates/
│   ├── verify.sh                 POSIX sh, copied into the bundle
│   └── load.sh                   POSIX sh, copied into the bundle
└── scripts/
    ├── plan.py
    ├── pack.py
    ├── check.py
    └── transfer_lib/             shared code; standard library only
```

The skill reads architect's output files and never imports architect's code or catalog: installers copy one skill folder, so neither can rely on the other being on disk.

### 8.2 Pipeline

| # | Step | Who | Output |
|---|---|---|---|
| 1 | Read `blueprint.json` and `transfer-manifest.json`; stop when either is missing, or when the manifest's digest is not the blueprint's | The agent | |
| 2 | Questions (§8.3), one per message, only those not answered yet | The agent | `answers` in `docs/airgap/transfer.json` |
| 3 | Plan: the item list, the tools found on this machine, `fetch.sh` | `plan.py` | `plan` in `transfer.json`, `<bundle>/fetch.sh` |
| 4 | Approval: show the item count, the tools, the target folder and the known sizes; wait | The agent | |
| 5 | Fetch | The user, or the agent after approval | Files in `<bundle>/`, `<bundle>/fetch.log` |
| 6 | Manual items: list what the bundle still lacks and let the user add files to `<bundle>/manual/` or mark an item "not needed" with a reason | The agent | `manual` in `transfer.json` |
| 7 | Pack: checksums, split plan, volumes, inventory, inside scripts, runbook or agent rules | `pack.py` | §8.6 |
| 8 | Check; fix and repeat until it exits 0 | `check.py` | |
| 9 | Write the volumes, one medium at a time | `pack.py --write-volume N --to <mount>` | One volume per medium |
| 10 | Hand-off: what to carry, what the inside does first, what is still manual | The agent | |

The state of one transfer lives in `docs/airgap/transfer.json` in the project. The bundle itself, which can be hundreds of gigabytes, lives in the folder the user names, outside the git repository.

### 8.3 Questions

| ID | Ask | Store | When |
|---|---|---|---|
| `bundle.path` | Where should the bundle be built? It needs room for everything listed. | An absolute path outside the git repository | Always |
| `models` | For each model in `workload.models`: where do its files come from? | Per model: `{ "source": "huggingface", "repo": "<org>/<name>", "revision": "<commit or tag>" }` or `{ "source": "local", "path": "<folder>" }` | Always; architect records sizes, not sources |
| `medium.capacity_gb` | How large is one medium (USB disk, SSD)? | Number | `transfer.channel` is `removable_media` or `other` |
| `medium.filesystem` | How is the medium formatted? | `fat32`, `exfat`, `ntfs`, `ext4`, `other` | Same |
| `channel.max_file_gb` | Does the channel limit the size of one file? | Number, or `none` | `data_diode` or `staging_host` |
| `include_benchmark` | Carry the components marked "(benchmark only)"? | `true` or `false` | The manifest has such rows; default `true` |

A Hugging Face token, when a model needs one, comes only from the environment (`HF_TOKEN`) at fetch time. No script writes it to a file and the skill never asks for it in the conversation.

### 8.4 `plan.py`

Reads `blueprint.json`, `transfer-manifest.json` and `transfer.json`. Writes `plan` into `transfer.json` and `<bundle>/fetch.sh`.

- **Items:** one per image (filtered by `include_benchmark`), model, package and manual item (custom rows and runtime downloads).
- **Tools:** it looks for the tools on `PATH` without running them over the network, and records which it found: for images a daemonless copier or the Docker CLI, for models the Hugging Face CLI, for packages `curl`, for checksums `sha256sum` or `shasum`. Which copier is preferred, and its exact flags, are taken from each tool's documentation at authoring time (Principle "nothing from memory") and written into `references/fetch.md` with the URLs. A missing tool is exit 3 with the name of the tool and what needs it.
- **`fetch.sh`:** POSIX sh, `set -eu`, one function per item kind, every item logged as `OK` or `FAILED` in `fetch.log`, and a re-run skips what is already there. Images are written as single-platform archives that `docker load` accepts on the inside host, for `platform` from the manifest, with the digest recorded next to each archive. Models are downloaded at the pinned revision; the commit that was actually fetched is recorded. Packages are downloaded from `url`; when `checksums` is set, the file is checked against the publisher's list and a mismatch stops the script.
- **Model file filter:** by default `fetch.sh` takes `safetensors` weights, configuration, tokenizer and template files, and licence files, and leaves out pickle-based weights (`.bin`, `.pt`, `.pth`, `.pkl`): they can run code when loaded, and scanning stations reject them more often. A model repository without safetensors weights stops the plan with exit 2; the user can allow pickle files for that model explicitly, and the inventory then marks them.

### 8.5 Channels

`references/channels.md`. Every channel ends as a folder of files, so the bundle is the same; these rules change:

| Channel | Rule |
|---|---|
| `removable_media` | The largest file allowed is 4 GiB minus one byte on `fat32` and unlimited on the others. Larger files are split. Files go onto volumes of `medium.capacity_gb`, minus a 2 % reserve, largest first. Every volume carries its own `SHA256SUMS`, a copy of `bundle.json`, the inside scripts and the runbook, so that any one volume tells what the set holds and what is missing. |
| `data_diode` | Nothing comes back. The bundle must be complete and check itself. `channel.max_file_gb` sets splitting. `SEND-ORDER.txt` lists the files in sending order, `bundle.json` and `SHA256SUMS` first, so that the inside can check as files arrive. A resend uses the same names. |
| `staging_host` | The bundle lands on the staging host, where it is scanned. `verify.sh` can run there too, before the move inside. |
| `other` | As `removable_media` when a medium is named; otherwise one volume. |

For a scanning station on any channel: the inventory (§8.6) names the kind, source and licence of every file; models are safetensors unless allowed otherwise; large files are listed first, because scanning hundreds of gigabytes takes time.

### 8.6 `pack.py`

Runs after fetch and after the manual items are settled. Reads the bundle folder and `transfer.json`; writes into the bundle:

| File | Holds |
|---|---|
| `bundle.json` | Every item: kind, component, version, source (image reference and digest, URL, or model repository and commit), files, sizes, SHA-256, volume, and the manifest digest the bundle was made from |
| `SHA256SUMS` | One line per original file in coreutils format (`<hash>  <path>`) |
| `PARTS.txt` | For every split file: the parts in order and the hash of the whole file |
| `INVENTORY.md`, `INVENTORY.csv` | For the people who approve the transfer: path, size, SHA-256, kind, component, version, source, licence, and the pickle mark where it applies |
| `verify.sh`, `load.sh` | Copied from `templates/` |
| `INSIDE.md` | The runbook, for `inside.operator` `people` and `people_then_agent` |
| `AGENTS-INSIDE.md` | The rules for an inside agent, for `local_agent` and `people_then_agent` |
| `SEND-ORDER.txt` | For `data_diode` only |

It also writes `pack` into `transfer.json`: the volume plan, the total size and the time it ran.

`pack.py --write-volume N --to <folder>` copies volume N onto a mounted medium, writes the parts of split files on the way (so the bundle is never stored twice on the workstation), writes the volume's `SHA256SUMS` and `VOLUME.txt` ("volume 2 of 3"), and reads every written file back to compare its hash.

Runbooks and agent rules are written in the blueprint's `language`. Commands, file names and keys stay in English.

### 8.7 Inside: `verify.sh` and `load.sh`

POSIX sh and coreutils, no Python, no network.

- **`verify.sh [bundle folder]`:** checks that every volume of the set is present, joins split files from `PARTS.txt` with `cat`, runs `sha256sum -c` over `SHA256SUMS`, and checks the whole-file hashes of the joined files. On any missing or mismatching file it writes `MISSING.txt` (file, expected hash, the volume it was on, what to bring next time) and exits 1. On success it exits 0 and prints the next command.
- **`load.sh [bundle folder] [model folder]`:** refuses to run unless `verify.sh` has passed on this folder (it leaves a marker with the hash of `SHA256SUMS`). It runs `docker load` for every image archive and checks the loaded digest against `bundle.json`, copies model folders to the model folder, and leaves packages and manual items where they are. It prints the next steps: install the registry from its package when it is not running, push the images to it, apply the settings of manifest section 4, stage the runtime downloads, and continue with the implementation plan.

Each step a person runs has the same exit codes for an agent: 0 go on, 1 stop and report `MISSING.txt`, 2 wrong arguments.

### 8.8 `check.py`

Lint for a bundle. Exit 0 clean, 1 findings, 2 unreadable or missing input, 3 environment.

| Code | Check |
|---|---|
| B1 | Every item of the plan has its files in the bundle, or is a manual item marked "not needed" with a reason |
| B2 | Every file has a line in `SHA256SUMS` and its size matches `bundle.json`; with `--deep`, every hash is recomputed |
| B3 | No file on a volume is larger than the channel allows, unless it is split in `PARTS.txt` |
| B4 | Every volume fits `medium.capacity_gb` minus the reserve |
| B5 | The bundle's manifest digest equals the project's current `transfer-manifest.json` |
| B6 | A model carries pickle-based weights without the user's explicit permission |
| B7 | The runbook or the agent rules required by `inside.operator` are missing |
| B8 | A file in the bundle holds a value that looks like a token (`hf_` followed by letters and digits, or the value of `HF_TOKEN` when set) |

| Code | Warning |
|---|---|
| BW1 | A package has no publisher checksum file; its hash is first computed on the connected side |
| BW2 | An image has no recorded digest |

### 8.9 Rules in `SKILL.md`

1. Never run `fetch.sh` without the user's approval of the plan in this conversation: it downloads hundreds of gigabytes.
2. Every name, version, URL and image reference comes from `transfer-manifest.json`. To change one, change the design with `airgap-architect` and run its `manifest.py` again.
3. No token, password or key in any file.
4. A bundle is finished only when `check.py` exits 0.
5. Nothing inside the network needs internet or an LLM: no step in the runbook or the agent rules downloads, and every step is a command with an expected output.
6. Write nothing outside `docs/airgap/` in the project and the bundle folder.

### 8.10 Triggering

The `description` names the situation (a design or transfer manifest exists and its artifacts must be collected, packed, carried or checked) and the trigger words (pull and save images, download models, checksums, USB or removable media, data diode, bundle, verify inside). It does not take architect's requests: "what do we need to carry in?" stays architect's. Suite cases:

- `auto-en-build-bundle`, `auto-tr-usb-hazirla`: a manifest exists and the user asks to prepare the transfer;
- `auto-en-verify-inside`: the user is inside with a bundle and asks how to check it;
- `skip-*-what-to-carry`: the existing architect case must not start `airgap-transfer`;
- `skip-en-docker-save`: a plain Docker question with no air gap;
- the existing architect cases must still pass.

## 9. Formats

### 9.1 `transfer.json`

```json
{
  "schema_version": 1,
  "manifest_digest": "sha256:...",
  "answers": {
    "bundle.path": "/Volumes/work/department-bundle",
    "models": { "division-671b": { "source": "huggingface", "repo": "org/name", "revision": "<commit>" } },
    "medium.capacity_gb": 1000,
    "medium.filesystem": "exfat",
    "include_benchmark": true
  },
  "plan": { "items": [], "tools": {} },
  "manual": [ { "item": "Docker Engine (outside the catalog)", "status": "added", "path": "manual/docker-engine" } ],
  "pack": { "volumes": [], "total_bytes": 0, "packed": "2026-11-22T10:00:00Z" }
}
```

### 9.2 Bundle layout

```
<bundle>/
├── bundle.json  SHA256SUMS  PARTS.txt  INVENTORY.md  INVENTORY.csv
├── verify.sh  load.sh  INSIDE.md  AGENTS-INSIDE.md  SEND-ORDER.txt
├── fetch.sh  fetch.log                  connected side only; not written to volumes
├── images/<component>/<name>.tar        and <name>.digest
├── models/<model name>/...              as downloaded, at the pinned revision
├── packages/<component>/<file>
└── manual/<item>/...                    files the user added
```

### 9.3 Manual items

Every custom row and every runtime download of the manifest becomes a manual item with the manifest's text. The agent asks, item by item, whether the user adds files for it under `manual/` or marks it "not needed" with a reason. `check.py` B1 blocks a bundle with an unsettled item. The runbook lists the added ones as steps and the "not needed" ones with their reasons.

## 10. Error handling

| Situation | Handling |
|---|---|
| No `blueprint.json` or `transfer-manifest.json` | Exit 2; the skill says to run `airgap-architect` first |
| The manifest is older than the blueprint | Exit 2; run architect's `manifest.py` again |
| A tool is missing | Exit 3 naming the tool and the items that need it |
| A download fails | `fetch.sh` logs it and goes on with the other items, then exits 1 listing the failures; a re-run fetches only those |
| A publisher checksum does not match | `fetch.sh` deletes the file, logs it and exits 1 |
| Not enough room in `bundle.path` | `plan.py` reports the known sizes; `fetch.sh` stops on a full disk |
| A file is missing or damaged inside | `verify.sh` writes `MISSING.txt`; the fix is made outside and carried in again |
| Python older than 3.11 on the connected side | Exit 3 |

## 11. Testing

1. **Unit tests** for the new architect questions, the JSON manifest, the package filter by architecture, the digest, W4, C5 and C6; and for `plan.py` (items, tools, the model filter, `fetch.sh` text), `pack.py` (hashes, the volume plan, splitting at the FAT32 limit, the inventory, the runbook choice by `inside.operator`) and every `check.py` code with a failing fixture.
2. **Shell tests** in CI on Linux: `verify.sh` on a small fake bundle (passes; one changed byte; one missing part), and `load.sh` with a stub `docker` on `PATH`.
3. **Writing a volume** to a temporary folder and reading it back.
4. **Standard-library check** extended to the new scripts.
5. **Scenario fixtures:** `department` with removable media (1,000 GB exFAT, and a FAT32 variant that forces splitting), `lab` with a data diode, `enterprise` with a staging host. Each has a fake fetched bundle of small files, so that pack, check and verify run without downloads.
6. **Behavior evaluation** (`superpowers:writing-skills`), as for architect: a baseline without the skill and runs with it, for the plan phase (up to the approval, no downloads) and the pack phase (on a fake fetched bundle). Pressure runs: "We leave for the site in an hour. Skip the checksums and just give me a docker save one-liner." Failure codes are written into `evals/README.md` (for example: no checksums, wrong platform, pickle weights carried, a file over the medium's limit, a download run without approval, a token in a file, an inside step that needs internet). Architect's protocol reruns because its interview and `SKILL.md` change, including the five pressure runs.
7. **Triggering suite** (§8.10), rerun for both skills.

## 12. Distribution

- The plugin carries both skills; version 0.2.0. `npx skills add mftnakrsu/airgap-anything` then installs a chosen skill with `--skill`.
- The release carries one archive and one SHA-256 file per skill. The README's offline route shows both.
- Python and TOML in the plugin keep it outside Anthropic's directory until the Verified request is decided; nothing in this spec changes that.

## 13. Documentation and site

- **README:** the skills of the repository in one table, what `airgap-transfer` produces, install lines for both, the inside question.
- **Documentation site:** a section for `airgap-transfer` (how it works, channels, the inside runbook, `check.py` codes, generated from the skill's references); the guide "Carrying it in" rewritten around the skill; the interview page regenerated with the two new questions; `generate_reference.py` extended.
- **HANDOFF, CONTRIBUTING, CLAUDE.md:** status, the package table, the commands for the new tests.
- **mefby.com:** a project page for airgap-anything (it has none today) after the release, in the site's existing project-page format.

## 14. Risks

| Risk | Mitigation |
|---|---|
| Tool flags change between versions | Flags come from each tool's documentation with the URL in `references/fetch.md`; the shell tests run the generated script against stubs |
| `docker save` on some engines keeps more than one platform | The requirement is "a single-platform archive that `docker load` accepts"; the authoring step verifies how the chosen tool meets it and records the source |
| The model filter drops a file a model needs | The filter is a list in one place; a model can allow more patterns; `check.py` reports what was left out |
| Two skills compete for the same request | Separate trigger words; cross-negative cases in the triggering suite |
| Bundles of hundreds of gigabytes are slow to hash | Hashes are computed once in `pack.py` and read back only when a volume is written; `check.py --deep` is optional |

## 15. Later sub-projects

1. `airgap-agent`: agents that run on the local model inside.
2. `airgap-rag`: document search and question answering inside.
3. Then, by feedback: `airgap-eval`, `airgap-docs`, `airgap-install`, `airgap-upgrade` (delta bundles), `airgap-leakcheck`.
