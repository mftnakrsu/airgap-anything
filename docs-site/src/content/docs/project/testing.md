---
title: Testing
description: How the markdown the three skills ship, the catalog, the sizing examples and the agent's behaviour are tested.
---

| What | How | When |
|---|---|---|
| The markdown the skills ship, the catalog, the sizing examples, packaging, README and site | Unit tests on Python 3.11 and the newest Python 3 | CI, on every push and pull request |
| What the agent does with each skill | Scenario runs with and without the skill, scored against expected decisions, plus runs under time pressure: the architect scenarios, the `airgap-transfer` scenarios in a plan phase and a pack phase, and the `airgap-agent` scenarios | By hand, before a release |
| Whether Claude Code picks the right skill | `claude plugin eval` on fifteen one-message cases for all three skills: natural requests in English and Turkish, the slash command, and requests the skills must leave alone | When any skill's description changes, and before a release |

## The unit tests

The skills need no Python; only the repository's checks do. From the repository root:

```bash
python3 -m unittest discover -s tests -t .
```

| File | Checks |
|---|---|
| `tests/test_skills.py` | Each skill's frontmatter, with a description that says what it does and when; `SKILL.md` under 500 lines; every file `SKILL.md` names exists, one level deep from it; a table of contents in long references; markdown only, no scripts |
| `tests/test_catalog.py` | Every catalog entry has its fields and its sections in the order the skill reads them; alternatives and the components a layer guide names are catalog entries; image references are pinned; every entry and every guide row has an evidence label, and evidence has sources; every GPU row has memory, a vendor and a source |
| `tests/test_sizing.py` | The worked examples in [Sizing](/reference/architect/sizing/) and the expected numbers of the eval scenarios follow from the constants in that page. `tests/sizing_reference.py` writes the procedure out once in Python for this check; the skill does not use it |
| `tests/test_packaging.py` | The plugin and marketplace manifests for Claude Code, Codex and Cursor name the same plugin and version; the skills are where installers look; the icon and the license; the plugin folder keeps to the directory's rules on file types, sizes and commands that download and run code |
| `tests/test_readme.py` | The README's install paths, links, anchors and images |
| `tests/test_docs_site.py` | The generated pages of this site are current, every sidebar entry has a page, and every internal link resolves |
| `tests/test_triggering_suite.py` | The shape of the triggering suite: every kind of case is there, each checks the right skill, and the three skills are kept apart |

## The behaviour evals

They need a model, so they are run by hand. Each scenario is run by a fresh agent with and without the skill, and the result is scored against the failures the skill is meant to prevent, such as GPU sizing given as one number, deployment files written before approval, or a download started before the plan was approved. The protocols are in [`evals/README.md`](https://github.com/mftnakrsu/airgap-anything/blob/main/evals/README.md).

The triggering suite runs real Claude Code sessions with `claude plugin eval` and costs money per run; `evals/README.md`, "Triggering", gives the command and the cost ceiling.

The protocols and the recorded results are in [`evals/`](https://github.com/mftnakrsu/airgap-anything/tree/main/evals).
