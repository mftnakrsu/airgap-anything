---
title: With superpowers
description: How the skill works together with the superpowers plugin, and without it.
---

[superpowers](https://github.com/obra/superpowers) is optional.

| Situation | What happens |
|---|---|
| superpowers is installed | The blueprint is written where superpowers keeps its specs, `docs/superpowers/specs/YYYY-MM-DD-PROJECT-airgap-blueprint-design.md`. After the self-review and your approval, the skill hands it to `superpowers:writing-plans` for an implementation plan. |
| superpowers is not installed | The blueprint is written to `docs/airgap/blueprint.md`. After you approve, the agent gives the next steps itself: carry the artifacts in with `airgap-transfer`, install, benchmark. |
| `superpowers:brainstorming` starts too | There is still one interview. Brainstorming keeps the rhythm and the approval gates; this skill supplies the questions, the references and the template, and its self-review becomes part of brainstorming's spec review. |

In every case nothing is implemented before you approve the blueprint.
