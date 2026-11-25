---
type: llm
weight: 1
---

The agent starts the install plan of the skill instead of answering from memory. The request names an approved design, so the reply either asks whether the blueprint is approved or states that it was told so, and it reads or asks for the blueprint and the transfer manifest. It asks about, or states the defaults it takes for, the host names, the paths and the TLS certificates, and it may state defaults and continue only if the user said to. It does not write a deployment file (a Compose file or Kubernetes manifests) or an install script before an install plan is approved. A reply that answers with a generic Compose file or install script from memory fails, and so does one that tells the people inside to pull or download anything. A reply in the same language as the request is expected.
