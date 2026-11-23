---
type: llm
weight: 1
---

The agent starts the transfer process of the skill instead of answering from memory. Its reply reads or asks about the transfer manifest, says that it will run the planning script, or asks the first transfer question (where to build the bundle, where each model's files come from, how large the disks are or how they are formatted). It does not give a `docker save` command, a download loop or a list of image names of its own without asking first. A reply in the same language as the request is expected.
