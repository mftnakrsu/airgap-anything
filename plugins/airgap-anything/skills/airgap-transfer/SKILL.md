---
name: airgap-transfer
description: Packs the transfer manifest of an air-gapped design into a bundle that checks itself inside the network. Use when an air-gapped design already has a transfer manifest (docs/airgap/transfer-manifest.md from airgap-architect) and its artifacts must be collected, packed, carried or checked - pulling and saving container images for one platform, downloading model weights, fetching packages, recording checksums, splitting a bundle across USB disks or other removable media, sending it through a data diode or staging host, or verifying and loading a bundle inside the network
---

# Airgap Transfer

## Overview

Turn the transfer manifest that `airgap-architect` wrote into a bundle that checks itself: fetch commands for the connected side, a checksum list, a split across media, an inventory for the people who approve the transfer, and a runbook or agent rules for the inside.

Why the skill exists: a transfer fails in two expensive ways. Hundreds of gigabytes get downloaded before anyone agreed on what to carry; or a file arrives damaged and nothing inside can tell, so the fault shows up at installation and costs another trip. So nothing is downloaded before the user approves the plan, and nothing leaves without a checksum list the inside can check with `sha256sum` alone.

Paths in this skill are relative to the folder that holds this file. `docs/` is in the user's project.

## When to use

- `docs/airgap/transfer-manifest.md` exists and someone asks to prepare, fetch, pack, split, carry or send its artifacts.
- Someone is inside the network with a bundle and asks how to check or load it: point them to `INSIDE.md` (or `AGENTS-INSIDE.md`) in the bundle.

Not for deciding what to carry: without a manifest, or when the design itself must change, that is `airgap-architect`. Not for one tool's own offline install: catalog entries name per-tool skills for that.

## Workflow

Copy this checklist into your reply and tick it off as you go:

```
Air-gap transfer:
- [ ] 1. Inputs match
- [ ] 2. Questions
- [ ] 3. Plan file
- [ ] 4. Approval: send the plan message, then wait
- [ ] 5. Fetch and check what arrived
- [ ] 6. Manual items settled
- [ ] 7. Pack: sizes, split, volumes, documents, checksums
- [ ] 8. Self-check, until every item holds
- [ ] 9. Write the volumes, one medium at a time
- [ ] 10. Hand-off
```

1. **Inputs.** Read the manifest and the blueprint its `Blueprint:` line names. Every component and version in the blueprint's decision table must appear in the manifest and the other way round, and the manifest must name a platform. A row marked "(from airgap-agent)" after its component needs no blueprint row when its component is listed in `docs/airgap/agents.md`: `airgap-agent` adds coding-agent rows without changing the blueprint. The same holds for a row marked "(from airgap-rag)" whose component (for section 2, the name in the Model cell) is listed in `docs/airgap/rag.md`. The same holds for a row marked "(from airgap-install)": the project files under `docs/airgap/install/`, and any image or file that `docs/airgap/install/plan.md` lists under "Manifest rows added" (the NVIDIA device plugin image, a custom image). Section 7 has no component, so a step there whose text ends "(from airgap-agent)", "(from airgap-rag)" or "(from airgap-install)" is accepted the same way. If not, the manifest is out of date: send the user back to `airgap-architect` and stop.
2. **Questions.** Read `references/questions.md`; ask only what this transfer needs.
3. **Plan.** Write `docs/airgap/transfer-plan.md` (`references/bundle.md`, "The plan file"), one item per row of the manifest. Read `references/channels.md` for how the channel splits and orders files.
4. **Approval.** Send the plan message of `references/fetch.md` and end your turn. "Prepare everything" ends here.
5. **Fetch.** After the yes, run the commands of `references/fetch.md` (or the user runs them), record every item's status, and run its checks of what arrived.
6. **Manual items.** For each one, the user adds files under `<bundle>/manual/` or marks it not needed with a reason (`references/questions.md`).
7. **Pack.** Follow `references/bundle.md`, "Packing, in order", and write the inside documents from `references/inside.md`.
8. **Self-check.** Check every item below; fix what fails and check again.
9. **Volumes.** `references/bundle.md`, "Writing the volumes".
10. **Hand-off.** Below.

## Rules

1. **Download nothing before the user approves the plan in this conversation.** A `docker pull`, a `git clone`, a checksum file, a bandwidth test, or a download started in the background is a download too; reading a model's page for its commit hash is not. The plan is cheap to change; hundreds of gigabytes of the wrong files are not.
2. **Every name, version, URL and image reference comes from the transfer manifest**, at the manifest's version: no file from a branch such as `main` when the manifest pins a release. A file the manifest does not name goes in only as a manual item the user adds. To change what is carried, change the design with `airgap-architect`, or, for rows marked "(from airgap-agent)", rerun `airgap-agent`, and for rows marked "(from airgap-rag)", rerun `airgap-rag`, and for rows marked "(from airgap-install)", rerun `airgap-install`.
3. **No token, password or key in any file.** A Hugging Face token comes only from `HF_TOKEN` in the environment; never ask for it in the conversation.
4. **A bundle without its checksum list is not finished**, even when the skip is written down: inside, nothing could tell a damaged copy from a good one.
5. **Nothing inside the network needs internet or an LLM.** Every step of the runbook is a command with the output to expect.
6. **Write nothing outside `docs/airgap/` in the project and the bundle folder.**

## Self-check

Before writing the volumes, check each item; fix what fails and check all of them again.

1. Every item of the plan is `fetched` or `copied` with its files in the bundle, or is a manual item marked `added` or `not needed` with a reason.
2. `cd B && sha256sum -c --quiet SHA256SUMS` prints nothing, and every file of the bundle except the parts and the volume files is listed in `SHA256SUMS`.
3. No file or part on a volume is larger than the part size, and no volume holds more than its capacity (`references/bundle.md`).
4. Every image was fetched for the manifest's platform and has a digest; every package with publisher checksums matched them.
5. No model carries pickle-based weights without the user's permission.
6. The runbook or agent rules that `inside.operator` calls for exist, in the blueprint's language, and every file and folder their commands name exists in the bundle.
7. `grep -rIlE 'hf_[A-Za-z0-9]{20,}' B docs/airgap` finds nothing, nor does a search for the value of `HF_TOKEN` when it is set.

## Hand-off

Tell the user, in their language:

1. What to carry: the volumes and the "volume N of TOTAL" label of each, or for a data diode the files of `SEND-ORDER.txt`, in that order.
2. What the inside does first: copy the volumes into one folder and follow `INSIDE.md` (or `AGENTS-INSIDE.md`), which checks every file before anything is loaded.
3. What is still open: manual items marked not needed and their reasons, packages without publisher checksums, and anything the self-check had to accept.

## Common mistakes

| Mistake | Instead |
|---|---|
| Taking "prepare everything" as the approval and starting downloads while writing the rest | Send the plan message and end your turn; the yes to that message is the approval |
| Skipping the checksums because time is short, and recording the skip as a deviation | Checksums add no step for the user: the fetch commands check publisher sums, and `SHA256SUMS` is one command (`references/fetch.md`, "When time is short") |
| Writing the `docker save` one-liner that was asked for | After the yes, use the image commands of `references/fetch.md`: they pin the platform and record each image's digest |
| Letting the inside improvise when a file is missing | The runbook stops, names the file and its volume from `VOLUMES.txt`, and the file is carried in again from outside |
