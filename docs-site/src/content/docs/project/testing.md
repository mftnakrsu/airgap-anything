---
title: Testing
description: How the skill, the catalog and the agent's behaviour are tested.
---

| What | How | When |
|---|---|---|
| Scripts, catalog, README and site | Unit tests on Python 3.11 and the newest Python 3, and `lint.py --catalog-only` | CI, on every push and pull request |
| What the agent does with the skill | Scenario runs with and without the skill, scored against expected decisions, plus five runs under time pressure | By hand, before a release |
| Whether Claude Code picks the skill | `claude plugin eval` on eight one-message cases: natural requests in English and Turkish, the slash command, and requests the skill must leave alone | When the skill's description changes, and before a release |

The protocols and the recorded results are in [`evals/`](https://github.com/mftnakrsu/airgap-anything/tree/main/evals).
