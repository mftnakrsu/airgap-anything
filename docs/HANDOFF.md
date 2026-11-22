# Handoff

Where the project stands and how to continue. Last updated on 2026-11-22.

## Status

Version 0.1 is implemented.

- **Skill.** `plugins/airgap-anything/skills/airgap-architect/` holds `SKILL.md`, the reference files, the four scripts (`tier.py`, `size.py`, `manifest.py`, `lint.py`) and the catalog. The scripts use only the Python 3.11+ standard library.
- **Catalog.** 16 component entries, all labelled `docs`, and 17 GPU rows in `catalog/gpus.toml`. `lint.py --catalog-only` reports no findings.
- **Tests.** 395 unit tests, passing on Python 3.11 and on the newest Python 3; CI runs both.
- **Documentation site.** `docs-site/` (Astro Starlight) has the guides, the concepts, a worked example and a reference generated from the catalog, the spec and the skill's references. `.github/workflows/docs.yml` builds it on every change and deploys `main` to https://airgap-anything.mefby.com (GitHub Pages, HTTPS enforced).
- **Release.** v0.1.0 was published on 2026-11-22 as a GitHub release with the skill archive `airgap-architect-0.1.0.tar.gz` and its SHA-256 file.
- **Packaging.** The marketplace is `.claude-plugin/marketplace.json` at the root; it lists the plugin folder `plugins/airgap-anything/`, which holds the plugin manifest, the icon, the skill and the triggering suite, and nothing else, because a plugin install gets only that folder and Anthropic's directory checks every file in it. `claude plugin validate .` and `claude plugin validate plugins/airgap-anything --profile directory` pass. `tests/test_packaging.py` enforces the directory's rules for an organization that is not Verified, apart from the Python and TOML files, which the directory accepts only from a Verified organization (see `docs/packaging-facts.md`, Q8).
- **Evaluation.** A baseline without the skill and three rounds of runs with it, all on 2026-11-22, are in `evals/results/`; all six criteria pass in the current set. The results file states the caveats: the runs were dispatched from a session inside this repository that loaded the dispatching user's own instruction files, the standard rows rest on older skill commits, and a single targeted run is the only evidence for the `benchmark` path.
- **Triggering.** `plugins/airgap-anything/evals/triggering/` (a `claude plugin eval` suite) checks that Claude Code starts the skill on a natural English or Turkish request, starts it from `/airgap-anything:airgap-architect`, and leaves unrelated requests alone. All 24 runs passed on 2026-11-22 (`evals/results/2026-11-22-triggering.md`). Rerun it when the `description` in `SKILL.md` changes. `.github/workflows/triggering.yml` runs it in CI on such a change, on a `v*` tag and by hand; it needs a credential secret (`ANTHROPIC_API_KEY`, or `CLAUDE_CODE_OAUTH_TOKEN`, untested) and skips with a notice while none is set, which is the case today.
- **Since the last evaluated commit (2f38222).** The final review's fix round changed the scripts, catalog wording and `references/sizing.md` (a fifth option when the hardware does not fit). The move into `plugins/airgap-anything/` then removed the scripts' unused `#!` lines and reworded one note in the Ollama entry. `SKILL.md` did not change.

## Decisions taken (2026-11-22)

- **License holder:** Meftun Akarsu, in `LICENSE`.
- **Plugin icon:** the brand icon, copied to `plugins/airgap-anything/.claude-plugin/icon.png` and set as `icon` in the plugin manifest. The developer portal fixes the listing icon at the first submission.
- **Repository description:** "Design any system for air-gapped environments. An agent skill that interviews you, then writes the blueprint, GPU sizing and the list of what to carry in."
- **Documentation site:** English, like a library's documentation, at `airgap-anything.mefby.com`.
- **Going public:** from a new repository with a clean history, not by changing the visibility of the development repository. Done on 2026-11-22.
- **Anthropic's directory:** ask for Verified status, with `mefby.com` as the proven domain, so that the plugin can be listed. Requested on 2026-11-22.
- **Name:** `airgap-anything` stays. "Air gap" is a generic term; a quick search found no project or package with this name.

## Open decisions (the maintainer's)

None.

## Waiting for an answer

- **Anthropic's directory.** The developer portal refuses the skill's Python scripts and TOML catalog from an organization that is not Verified. On 2026-11-22 `mefby.com` was proven with a DNS TXT record, which must stay in place, and Verified status was requested from **Help and appeals** in the portal. A person at Anthropic decides, and the reply appears only on the request's case page there. Verified is meant for companies and the request says that the maintainer is an individual developer, so it may be declined. If it is granted, submit the folder `plugins/airgap-anything` from the portal (**Submit new**, then **Plugin bundle**; see `docs/packaging-facts.md`, Q8). The repository's own marketplace and `npx skills` work either way.

## Known limitations

- **No CPU-architecture question.** Catalog packages name the linux/amd64 files, and the files for other architectures are only in each entry's `airgap.notes`. Whether an arm64 host gets the right files depends on the agent noticing.
- **`alternatives_considered` may be empty.** Lint does not check it, so the convention "no other `<layer>` option in the catalog" is not checkable.
- **Decisions do not record their table row.** Lint compares a decision's evidence label only with its components' catalog entries and its custom parts, so a decision labelled stronger than its table row escapes the verification list (run 8 of round 2 in `evals/results/2026-11-22-with-skill.md`).
- **E8 does not cover the catalog.** The manifest digest covers `decisions`, `workload.models` and `hardware.gpus`. After a catalog refresh with the same decisions, an old manifest still passes lint.
- **Catalog freshness.** W1 warns when an entry was last verified more than 180 days ago. Seven entries were last verified on 2026-11-21, five of them used by the demo blueprint, so from 2027-05-21 lint warns W1 on them and `design/demo/build_demo.py` refuses to rebuild. CI stays green, because warnings do not fail it.
- **Estimates.** Every decision-table row, and every value in `catalog/rules.toml` apart from the two user thresholds of the tiers, is labelled `estimate`. Field data replaces them.

## Later

- Rerun, at the release commit and from a session outside this repository that loads no user instruction files: run 4 (department, superpowers absent), so that the absent case is seen at the current commit, and a targeted run on the `benchmark` path with AMD GPUs or an unknown vendor.
- Add a scenario with an `expected.json` whose hardware does not fit, so that the E10 path and the options for a shortfall are scored; only the targeted run 12 has reached it.
- Ask for the hosts' CPU architecture and list packages per architecture.
- Let lint warn on an empty `alternatives_considered`, and record the table row a decision took.
- CI: a scheduled lint run with a future `--today`, well before 2027-05-21; a test step without network access.
- Pin the remaining unpinned source URLs of the catalog entries when each entry is next touched.
- Split `code_assistant` into code completion and coding agent: GitHub telemetry puts inline completion at a duty of a few percent, while agentic tools keep a request in flight most of the time.
- Make concurrency depend on organization size (Anthropic's per-user allowance falls about 20x from teams of 1-5 users to 500+), and let a measured peak request rate override the estimate.
- Consider tying high availability to the availability requirement alone. Today the highly available defaults come with the T3 floor, which a base tier of T3 (more than 300 users or more than five departments) sets, as does `org.downtime_tolerance = none` for the orchestration, llm-serving and state floors (GitLab recommends HA from 3,000 users or when downtime is critical; Open WebUI calls 1,000+ users large scale).

## Continue on another machine

Clone the repository (its URL is in `plugins/airgap-anything/.claude-plugin/plugin.json`), start Claude Code in the folder and say: "Read docs/HANDOFF.md and continue from there."

| For | Needs |
|---|---|
| Working on the skill, the catalog or the tests | Python 3.11 or newer; nothing else |
| Running the evaluation protocol | Claude Code and the superpowers plugin; see `evals/README.md` |
| Rebuilding brand assets | `fontTools`, `Pillow`, Chrome or Chromium; see `design/brand/README.md` |

## Facts worth keeping

- GPU count is independent of the tier. A small team that serves a very large model can need as many GPUs as a large department, because the weights alone set the smallest GPU group.
- Published throughput numbers for inference engines conflict. The design therefore sizes memory by arithmetic and makes a benchmark step mandatory.
- GitHub code search treats a multi-word argument as an exact phrase. Pass terms separately when checking for prior art.
- On GitHub, the browser picks a `<picture>` source by the computer's colour scheme, while the page follows the GitHub theme. When the two differ, a switched image lands on the wrong background. The README's images therefore either bring their own background or are transparent with text on its own cards and lines that clear 3:1 on both GitHub page colours (`#ffffff`, `#0d1117`); `tests/test_readme.py` checks both kinds. An opaque diagram suits only one theme: on 2026-11-22 a dark panel looked out of place on the light page, so the diagram became transparent.
