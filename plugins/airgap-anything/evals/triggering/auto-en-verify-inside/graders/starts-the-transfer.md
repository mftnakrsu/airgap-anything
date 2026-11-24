---
type: llm
weight: 1
---

The agent answers from the skill's inside steps: it tells the user to copy the volumes into one folder and follow `INSIDE.md` (or `AGENTS-INSIDE.md`) in the bundle, or gives its checks directly: `sha256sum -c` against `SHA256SUMS` (and `PARTS.sha256` for split files) before anything is loaded, and that a missing or damaged file is named with the volume it came on (`VOLUMES.txt`) and must be carried in again. It does not tell the user to download, pull or fetch anything inside the network.
