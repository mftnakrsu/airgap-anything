# Example: a department platform

This is what `airgap-architect` produced for the `department` scenario of the evaluations (`evals/scenarios/department/prompt.md`): 180 people in four departments, separate budgets, no cross-department access, audit on every request, one 671-billion-parameter model at 8-bit on one server with eight 141 GB GPUs, files carried in on removable media. The user was not available for questions, so everything the request did not state took the interview's default.

It is the output of a real run, not a hand-written sample: Claude Opus 5.5 with the skill at commit 024b2e7, on 2026-11-24, graded against `evals/scenarios/department/expected.json` (tier, every sizing number and all eight decisions match; see `evals/results/2026-11-24-with-skill.md`). The template's disclaimer line was added on top, and three things were corrected after grading, so that the example does not teach what the skill now says differently: the Evidence column of the decision table shows each decision's label (`estimate`) instead of the catalog entries' (`docs`), and two statements with no catalog source were removed (that Harbor needs a project prefix for `postgres:18.7`, and that UI sessions survive a Keycloak outage).

- [`blueprint.md`](blueprint.md): the blueprint, with every sizing step written out
- [`transfer-manifest.md`](transfer-manifest.md): everything to carry into the network, copied from the catalog
