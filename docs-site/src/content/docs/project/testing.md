---
title: Testing
description: How the two skills, the catalog and the agent's behaviour are tested.
---

| What | How | When |
|---|---|---|
| Scripts, catalog, README and site | Unit tests on Python 3.11 and the newest Python 3, and `lint.py --catalog-only` | CI, on every push and pull request |
| What the agent does with each skill | Scenario runs with and without the skill, scored against expected decisions, plus five runs under time pressure: the architect scenarios, and the `airgap-transfer` scenarios in a plan phase and a pack phase | By hand, before a release |
| Whether Claude Code picks the right skill | `claude plugin eval` on twelve one-message cases for both skills: natural requests in English and Turkish, the slash command, and requests the skills must leave alone | When either skill's description changes, and before a release |

The protocols and the recorded results are in [`evals/`](https://github.com/mftnakrsu/airgap-anything/tree/main/evals).
