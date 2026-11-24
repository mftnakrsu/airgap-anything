---
title: Carrying it in
description: From the transfer manifest to a verified bundle, across the gap, and loaded inside without internet.
---

`airgap-architect` ends with `docs/airgap/transfer-manifest.md`: every image, model, package and setting the design needs inside. `airgap-transfer` turns it into a bundle that checks itself. Like the first skill it is plain markdown: the agent runs command lines taken from each tool's documentation (`skopeo` or `docker`, `hf`, `curl`, `sha256sum`, `split`) and writes the files itself. Its steps are on the [airgap-transfer reference](/reference/transfer/).

## On the connected side

1. **Check the inputs.** The agent reads the manifest and the blueprint it names. Every component and version of the blueprint's decision table must be in the manifest and the other way round, and the manifest must name a platform. If not, the manifest is out of date, and the agent sends you back to `airgap-architect`.
2. **Answer a few questions.** Where to build the bundle (outside the git repository; it can be hundreds of gigabytes), where each model's files come from (a Hugging Face repository at a full commit hash, or a local folder), the medium's size and filesystem or the channel's file limit, and whether to carry the components marked "(benchmark only)". The agent never asks for a token: a Hugging Face token comes only from `HF_TOKEN` in the environment. [Transfer questions](/reference/transfer/questions/) lists them.
3. **Approve the plan.** The agent writes `docs/airgap/transfer-plan.md`, one item per row of the manifest, and sends one message: the items by kind, the tools the commands use, the bundle folder, the sizes it knows and those it does not, and whether it may run the fetch commands or you will. Then it stops. Nothing is downloaded before you say yes to that message, not even one image to try the commands. "Prepare everything" asks for the plan; it is not the yes.
4. **Fetch.** After the yes, each item is fetched on its own. `skopeo` or `docker` writes a single-platform image archive for the manifest's platform and records the image's digest. `hf download` fetches model files at the pinned commit, safetensors weights and configuration only, unless you allowed pickle files for that model. `curl` downloads packages and, where the manifest names one, the publisher's checksum file, which is checked at once; a package without one is noted in the inventory. Each item is recorded in the plan as fetched or failed, a failed item does not stop the others, and running its commands again fetches it again. [Fetching](/reference/transfer/fetch/) gives the commands and the page each one was taken from.
5. **Settle the manual items.** Parts outside the catalog (Docker Engine, for example) and runtime downloads become manual items: add their files under `manual/`, or mark them not needed with a reason. The bundle is not packed while one is open.
6. **Pack.** The agent lists the files largest first and picks the part size: 4 GiB minus one byte on FAT32, the channel's file limit, or the medium's capacity, whichever is smallest. It plans the volumes with a 2 % reserve, writes `INVENTORY.md` and the runbook, writes `SHA256SUMS` over every file, splits the files above the part size and lists each part in `PARTS.sha256`, then writes `VOLUMES.txt`, and `SEND-ORDER.txt` for a data diode. [The plan file and the bundle](/reference/transfer/bundle/) has every command.
7. **Self-check.** Before anything goes onto a medium, the agent checks a list and fixes what fails: every item fetched or settled; `sha256sum -c --quiet SHA256SUMS` prints nothing and covers every file; no file, part or volume over its limit; every image for the manifest's platform, with a digest; no pickle weights without your permission; the runbook in the blueprint's language, with every file its commands name; and no Hugging Face token in any file.
8. **Write the volumes,** one medium at a time. Every volume carries the shared files and a `VOLUME.txt` ("volume N of TOTAL"), and is read back against the checksums before you label it. For a data diode, `SEND-ORDER.txt` gives the order, checksum lists first. [Channels](/reference/transfer/channels/) has the rules per channel.

At the end the agent tells you what to carry and in which order, what the inside does first, and what is still open: manual items marked not needed, packages without publisher checksums, and anything the self-check had to accept.

## Inside

Copy the volumes into one folder, then follow `INSIDE.md`. Every step is a command with the output to expect, for example:

```sh
cd /srv/airgap-bundle && sha256sum -c --quiet PARTS.sha256
cd /srv/airgap-bundle && cat "FILE".part[0-9][0-9][0-9] > "FILE"
cd /srv/airgap-bundle && sha256sum -c --quiet SHA256SUMS
docker image load --input /srv/airgap-bundle/images/COMPONENT/NAME.tar
```

The steps need coreutils, and Docker to load the images: no script, no internet, no LLM. The parts of split files are checked and joined, then every file is checked against `SHA256SUMS`; no output means every file arrived intact. A line of output names a missing or damaged file, `grep` on `VOLUMES.txt` says which volume it came on, and the file is carried in again from outside. Then the images are loaded and the model files copied.

People follow `INSIDE.md`. An agent on a local model follows `AGENTS-INSIDE.md`, which puts rules before the same steps: one command per step, exactly as written; stop and report at the first output that differs; never download; never edit the checksum lists. [Inside the network](/reference/transfer/inside/) has both templates.

The telemetry settings of the manifest are not a step: no command applies them. Both documents list them under "Settings to apply before the first start", for a person or the implementation plan to write into the deployment files before any service starts.

## When something changes

A new decision, model or GPU means a new manifest: change the design with `airgap-architect`, which writes the manifest again. `airgap-transfer` takes every name, version, URL and image reference from the manifest, at the manifest's version, and stops at its first step when the manifest and the blueprint disagree. A file the manifest does not name gets in only as a manual item you add, and a changed plan needs a new yes before anything is fetched.
