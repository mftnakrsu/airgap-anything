---
name: airgap-transfer
description: Use when an air-gapped design already has a transfer manifest (docs/airgap/transfer-manifest.json from airgap-architect) and its artifacts must be collected, packed, carried or checked - pulling and saving container images for one platform, downloading model weights, fetching packages, recording checksums, splitting a bundle across USB disks or other removable media, sending it through a data diode or staging host, or verifying and loading a bundle inside the network
---

# Airgap Transfer

## Overview

Turn the transfer manifest that `airgap-architect` wrote into a bundle that checks itself: a fetch script for the connected side, checksums, a split across media, an inventory for the people who approve the transfer, and the scripts and instructions for the inside.

You ask, plan, wait for approval and hand off. Scripts download, hash, split and check. Every name, version, URL and image reference comes from `transfer-manifest.json`, never from memory.

## When to use

- `docs/airgap/transfer-manifest.json` exists and someone asks to prepare, fetch, pack, split, carry or send its artifacts.
- Someone is inside the network with a bundle and asks how to check or load it: point them to `INSIDE.md` (or `AGENTS-INSIDE.md`), `verify.sh` and `load.sh` in the bundle.

Not for deciding what to carry: without a manifest, or when the design itself must change, that is `airgap-architect`. Not for one tool's own offline install; catalog entries name per-tool skills for that.

## The pipeline

Paths to `references/`, `scripts/` and `templates/` are relative to the skill root, the folder that holds this SKILL.md; `docs/` is in the project root.

| # | Step | What you do | Read |
|---|---|---|---|
| 1 | Inputs | Run `plan.py` once. Exit 2 naming airgap-architect: stop and send the user there | |
| 2 | Questions | Fill `answers` in `docs/airgap/transfer.json`, one question per message, only those `plan.py` lists | `references/questions.md` |
| 3 | Plan | Run `plan.py` until it exits 0; it writes `plan` and `<bundle>/fetch.sh` | `references/channels.md` |
| 4 | Approval | Send the plan message of `references/fetch.md` and end your turn. Stop until the user approves | `references/fetch.md` |
| 5 | Fetch | The user runs `sh <bundle>/fetch.sh`, or you run it after approval. Exit 1: show the `FAILED` lines of `fetch.log`, fix, run it again | `references/fetch.md` |
| 6 | Manual items | For every manual item: the user adds files under `<bundle>/manual/`, or marks it not needed with a reason | `references/questions.md` |
| 7 | Pack | Run `pack.py`. When the blueprint's `language` is not `en`: translate the prose of `INSIDE.md` and `AGENTS-INSIDE.md`, keep every command line, file name and key exactly as written, then run `pack.py --refresh-sums` | `references/bundle-layout.md`, `references/inside.md` |
| 8 | Check | Run `check.py`; fix and repeat until it exits 0. It reports B7 for a command line that went missing in a translation, B2 for a translation whose hash was not recorded | `references/bundle-layout.md` |
| 9 | Volumes | `pack.py --write-volume N --to <folder>` for each volume, one medium at a time | `references/channels.md` |
| 10 | Hand-off | Say what to carry, what the inside does first, and what is still manual | `references/inside.md` |

"Prepare everything" ends at step 4. Steps 1 to 4 download nothing.

The state of one transfer lives in `docs/airgap/transfer.json`. The bundle lives in the folder of `bundle.path`, outside the git repository: it can be hundreds of gigabytes.

## Scripts

`${CLAUDE_SKILL_DIR}` is the folder that holds this SKILL.md. Claude Code fills it in only when it loads the skill itself; if you see it written out, put that folder's path in its place. The scripts need Python 3.11 or newer and nothing else. Run them from the project root:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/plan.py"
python3 "${CLAUDE_SKILL_DIR}/scripts/pack.py"
python3 "${CLAUDE_SKILL_DIR}/scripts/check.py"
python3 "${CLAUDE_SKILL_DIR}/scripts/pack.py" --write-volume 1 --to /media/usb1
```

Each takes `--project-root` when you run it from elsewhere, and lists its options with `--help`.

| Exit code | Meaning | What you do |
|---|---|---|
| 0 | Done | Continue |
| 1 | `check.py` found errors (B1 to B8), or a volume did not read back | Fix each one and run it again |
| 2 | A file is missing or stale, an answer is missing or invalid, or the bundle cannot be packed yet | Do what the message says: another skill's step, a question, a fetch, a manual item |
| 3 | A tool is missing, or Python is older than 3.11 | Tell the user which tool and what needs it |

Warnings (BW1, BW2) do not change the exit code; tell the user about them.

## Rules

1. Never run `fetch.sh`, and download nothing else, before the user's approval of the plan in this conversation: it downloads hundreds of gigabytes. A `docker pull`, a `git clone`, a checksum file, a bandwidth test or a download started in the background is a download too; reading a model's page for its commit hash is not (`references/fetch.md`, "The approval rule").
2. Every name, version, URL and image reference comes from `transfer-manifest.json`, at the manifest's version: no file from a branch such as `main` when the manifest pins a release. A file the manifest does not name goes in only as a manual item the user adds. To change one, change the design with `airgap-architect` and run its `manifest.py` again, then `plan.py`.
3. No token, password or key in any file. A Hugging Face token comes only from `HF_TOKEN` in the environment of `fetch.sh`; never ask for it in the conversation.
4. A bundle is finished only when `check.py` exits 0. A bundle without its checksums is not finished, even when the skip is written down.
5. Nothing inside the network needs internet or an LLM: no step in the runbook or the agent rules downloads, and every step is a command with an expected output.
6. Write nothing outside `docs/airgap/` in the project and the bundle folder.

## Common mistakes

| Mistake | Instead |
|---|---|
| Taking "prepare everything" as the approval and starting downloads while you write the rest | Send the plan message and end your turn; the yes to that message is the approval |
| Skipping the checksums because time is short, and recording the skip as a deviation | Inside, nothing can then tell a damaged copy from a good one. Checksums cost no extra step: `fetch.sh` checks them, `pack.py` writes `SHA256SUMS` (`references/fetch.md`, "When time is short") |
| Writing the `docker save` one-liner that was asked for | After the yes, the one command is `sh <bundle>/fetch.sh`; it pins the platform and records each image's digest |

## Hand-off

Tell the user, in their language:

1. What to carry: the volumes and what `VOLUME.txt` on each says, or for a data diode the files of `SEND-ORDER.txt`, in that order.
2. What the inside does first: copy the volumes into one folder, `sh verify.sh <folder>`, then `sh load.sh <folder> <model folder>`, as `INSIDE.md` or `AGENTS-INSIDE.md` says.
3. What is still manual: the items marked not needed and their reasons, and the warnings `check.py` reported.
