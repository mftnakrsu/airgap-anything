# Inside the network

Everything inside works without internet and without an LLM. An agent inside, if there is one, runs the same commands a person would.

## Who gets what

`inside.operator` in `blueprint.json` decides which files `pack.py` writes into the bundle:

| `inside.operator` | Files |
|---|---|
| `people` | `INSIDE.md`, the runbook |
| `local_agent` | `AGENTS-INSIDE.md`, the rules for an inside agent |
| `people_then_agent` | Both: the runbook for the first day, the rules once the agent runs |

Both are written in English. When the blueprint's `language` is another, translate the prose after `pack.py` has packed the bundle and before `check.py` and `pack.py --write-volume`: keep every command line, file name and key exactly as written, then run `pack.py --refresh-sums` to record their new hashes. `check.py` reports B7 when a file is missing or a command line of it went missing, and B2 when a translation's hash was not recorded.

## The steps

1. Copy every volume into one folder (for a data diode: wait until every file of `SEND-ORDER.txt` has arrived).
2. `sh verify.sh <folder>`: checks that every file and part of `VOLUMES.txt` is there, joins split files from `PARTS.txt`, and checks every file against its SHA-256 in `SHA256SUMS`. Exit 1 writes `MISSING.txt`: each file, its expected SHA-256, the volume it was on, and what to bring next time.
3. `sh load.sh <folder> <model folder>`: refuses to run until `verify.sh` has passed on the folder since `SHA256SUMS` last changed, runs `docker load` for every image archive `SHA256SUMS` lists and checks its image ID, and copies the model folders. Packages and manual items stay in the bundle.
4. Manual items: one step each in the runbook, with the folder that holds their files.
5. Switch off the telemetry settings that section 4 of the transfer manifest lists, before the first start.
6. Then: install the registry from its package if it is not running, push the images to it, stage the runtime downloads, and continue with the implementation plan.

An image ID that differs stops `load.sh`, unless the engine uses the containerd image store, which reports another ID; there it is a note. A person, not an agent, decides whether to run `load.sh` again with `AIRGAP_SKIP_IMAGE_ID_CHECK=1`; `verify.sh` has already checked every byte.

## Exit codes

| Code | Meaning | A person or an agent |
|---|---|---|
| 0 | Done | Goes on |
| 1 | Missing, damaged or not loaded | Stops and reports the message, and after `verify.sh` the contents of `MISSING.txt` (`load.sh` writes none) |
| 2 | Wrong arguments, or the folder is not a bundle | Fixes the command line, nothing else |

## Rules for an agent inside

`AGENTS-INSIDE.md` gives them, before its steps:

1. Run one command per step, exactly as written. Do not combine, shorten or reorder them.
2. Check the exit code of every command; stop at the first one that is not 0 and report it.
3. Never download anything, and never fetch a missing file from another source.
4. Never edit `verify.sh`, `load.sh`, `SHA256SUMS`, `PARTS.txt`, `VOLUMES.txt` or `bundle.json`.
5. Never improvise a step that is not written. Ask a person instead.

A missing or damaged file is fixed outside the network and carried in again.
