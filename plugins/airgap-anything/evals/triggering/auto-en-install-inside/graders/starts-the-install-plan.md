---
type: llm
weight: 1
---

The agent starts the install plan of the skill instead of answering from memory. Its reply reads or asks about the blueprint and the transfer manifest. If it finds them, it asks whether the blueprint is approved (or states that it was told so), and asks about, or shows defaults for, the host names, the paths and the TLS certificates, then stops after showing the plan or the questions. If it finds no blueprint or manifest, it asks the user for them or names `airgap-architect`, and writes nothing. It writes no deployment file (a Compose file or Kubernetes manifests) and no install script before the install plan is approved; `docs/airgap/install/plan.md` is the only file it may write before then. A reply that answers with a generic Compose file or install script from memory fails, and so does one that tells the people inside to pull or download anything. A reply in the same language as the request is expected.
