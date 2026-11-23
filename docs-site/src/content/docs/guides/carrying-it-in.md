---
title: Carrying it in
description: From the transfer manifest to a verified bundle, across the gap, and loaded inside without internet.
---

`airgap-architect` ends with `docs/airgap/transfer-manifest.md` and `transfer-manifest.json`: every image, model, package and setting the design needs inside. `airgap-transfer` turns the JSON file into a bundle that checks itself. Its steps, scripts and exit codes are on the [airgap-transfer reference](/reference/transfer/).

## On the connected side

1. **Answer a few questions.** Where to build the bundle (outside the git repository; it can be hundreds of gigabytes), where each model's files come from (a Hugging Face repository at a commit, or a local folder), and the medium or the channel's file limit. [Transfer questions](/reference/transfer/questions/) lists them.
2. **Approve the plan.** `plan.py` lists the items and the tools it found and writes `fetch.sh`. Nothing is downloaded before you approve it.
3. **Fetch.** `fetch.sh` writes single-platform image archives for the manifest's platform with their digests, downloads model files at the pinned commit (safetensors unless you allow otherwise), downloads packages and checks them against the publisher's checksum files. A failed item is logged and the next run fetches only what is missing. [fetch.sh](/reference/transfer/fetch/) gives the commands and their sources.
4. **Settle the manual items.** Parts outside the catalog (Docker Engine, for example) and runtime downloads become manual items: add their files under `manual/`, or mark them not needed with a reason.
5. **Pack and check.** `pack.py` hashes every file once, splits files over the medium's limit, plans the volumes, and writes the inventory for the people who approve the transfer. `check.py` must exit 0. [Bundle layout and check codes](/reference/transfer/bundle-layout/) lists the files and codes.
6. **Write the volumes,** one medium at a time; every file is read back. For a data diode, `SEND-ORDER.txt` gives the order. [Channels](/reference/transfer/channels/) has the rules per channel.

## Inside

Copy the volumes into one folder, then:

```bash
sh verify.sh /srv/airgap-bundle
sh load.sh /srv/airgap-bundle /srv/models
```

Both need only a POSIX shell and coreutils (and Docker for `load.sh`). `verify.sh` joins split files and checks every SHA-256; a missing or damaged file goes into `MISSING.txt` with the volume it was on, and the fix is made outside and carried in again. People follow `INSIDE.md`; an agent on a local model follows `AGENTS-INSIDE.md` and runs the same commands. [Inside the network](/reference/transfer/inside/) has both.

The telemetry settings of the manifest are not a step: no command applies them. Both files list them under "Settings to apply before the first start", for a person or the implementation plan to write into the deployment files before any service starts.

## When something changes

A new decision, model or GPU makes the manifest stale: architect's lint reports it (E8), and `plan.py` stops until `manifest.py` has written a fresh one. `pack.py` then refuses the old plan until you run `plan.py` again, and `check.py` reports B5 for a bundle packed from the old manifest.
