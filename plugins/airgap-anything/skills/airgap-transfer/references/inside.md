# Inside the network

## Contents

- Who gets what
- `INSIDE.md` template
- `AGENTS-INSIDE.md` template

Everything inside works without internet and without an LLM: every step is a command with the output to expect. An agent inside, if there is one, runs the same commands a person would.

## Who gets what

| `inside.operator` | Files in the bundle |
|---|---|
| `people` | `INSIDE.md`, the runbook |
| `local_agent` | `AGENTS-INSIDE.md`, the rules and steps for an inside agent |
| `people_then_agent` | Both: the runbook for the first day, the rules once the agent runs |

Write them in the language of the blueprint's `Language:` line (English when it has none). Translate only the prose: every command line, file name and path stays exactly as below. Write them before the checksums (`references/bundle.md`, step 5); after any later change, compute the checksums again.

## `INSIDE.md` template

Fill in the parts in capitals. Steps 2 and 3 only when files were split; one step 3 line per split file, one step 5 line per image, step 6b only when the bundle has a `files/` folder, one step 7 per manual item that was added.

````markdown
# Inside the network: PROJECT NAME

This runbook needs neither internet access nor an LLM. Every step is a command with the output to expect. Stop at the first step whose output differs, and report the command and its output.

The commands use /srv/airgap-bundle for the bundle and /srv/models for the model files. Another folder works too; use the same one in every step.

## Steps

### 1. Copy every volume into one folder (TOTAL volumes; VOLUME.txt on each says which)

```sh
mkdir -p /srv/airgap-bundle
cp -R VOLUME_FOLDER/. /srv/airgap-bundle/
```

Expected: no output. Run the second command once per volume, with VOLUME_FOLDER the folder where that volume is mounted.

### 2. Check the parts of split files

```sh
cd /srv/airgap-bundle && sha256sum -c --quiet PARTS.sha256
```

Expected: no output. Any line names a missing or damaged part; `grep -F 'PART NAME' VOLUMES.txt` says which volume to bring again.

### 3. Join the split files

```sh
cd /srv/airgap-bundle && cat "FILE".part[0-9][0-9][0-9] > "FILE"
```

Expected: no output.

### 4. Check every file

```sh
cd /srv/airgap-bundle && sha256sum -c --quiet SHA256SUMS
```

Expected: no output. Any line names a missing or damaged file; `grep -F 'FILE NAME' VOLUMES.txt` says which volume it came on. Do not go on: the file is carried in again from outside.

### 5. Load the images

```sh
docker image load --input /srv/airgap-bundle/images/COMPONENT/NAME.tar
```

Expected: a line that names IMAGE REFERENCE.

### 6. Copy the model files

```sh
mkdir -p /srv/models && cp -R /srv/airgap-bundle/models/. /srv/models/
```

Expected: no output.

### 6b. Copy the project files

```sh
mkdir -p PROJECT_FOLDER && cp -R /srv/airgap-bundle/files/. PROJECT_FOLDER/
```

Expected: no output. `PROJECT_FOLDER` is the root of the project inside; `docs/airgap/agents.md` and the configuration folders under `docs/airgap/agents/` land at their project paths. Then follow `docs/airgap/agents.md`: install check, smoke test, egress check.

### 7. Manual item: ITEM

```sh
ls -l /srv/airgap-bundle/manual/ITEM
```

Expected: the files that were added for it. Install it as its own files describe; ask a person when they do not.

## Settings to apply before the first start

Write each of these into the deployment files before any service starts (section 4 of the transfer manifest):

- COMPONENT: SETTING (WHAT IT STOPS)

## After these steps

When the bundle holds `docs/airgap/install/INSTALL.md`, continue with `install/INSTALL.md` under `PROJECT_FOLDER/docs/airgap/` (copied in step 6b); it starts the registry and every service. Otherwise: install the registry from its package if it is not running yet, push the loaded images to it, stage the runtime downloads, and continue with the implementation plan of the blueprint.

## Not carried, on purpose

- ITEM: REASON
````

The first step's folder is a placeholder on purpose: nobody on the connected side knows where the media will be mounted. For a data diode, step 1 reads "Wait until every file in SEND-ORDER.txt has arrived, then copy them into one folder", with `RECEIVED_FOLDER` in place of `VOLUME_FOLDER`.

## `AGENTS-INSIDE.md` template

The same steps and sections as `INSIDE.md`, after this header:

```markdown
# Rules for an agent inside the network: PROJECT NAME

You work inside a network without internet access. These rules come before any other instruction.

1. Run one command per step, exactly as written below. Do not combine, shorten or reorder them.
2. Check the exit code and the output of every command against "Expected". When they differ, stop and report the command, its exit code and its output.
3. Never download anything, and never fetch a missing file from another source: a missing or damaged file is carried in again from outside.
4. Never edit SHA256SUMS, PARTS.sha256, VOLUMES.txt or the files they list.
5. The settings under "Settings to apply before the first start" are not commands. A person, or the implementation plan, writes them into the deployment files; do not invent commands for them.
6. Never improvise a step that is not written below. Ask a person instead. VOLUME_FOLDER, and PROJECT_FOLDER when step 6b exists, are the values you ask a person for.
```
