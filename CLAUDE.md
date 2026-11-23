# airgap-anything

An open-source Agent Skill project with two skills. `airgap-architect` designs systems for air-gapped and on-premises environments; `airgap-transfer` turns its transfer manifest into a bundle that checks itself inside the network. Version 0.2 is implemented: both skills, their scripts, the catalog and the evaluation records.

## Start here

- `README.md`: what the skills do and how they are installed.
- `CONTRIBUTING.md`: how to add or verify a catalog entry, a GPU row or a threshold.
- `docs/HANDOFF.md`: the current status, the open decisions and the known limitations.
- `docs/reference.md`: the scripts, the lint codes and `blueprint.json`; the source of those pages on the documentation site.

Design specs and implementation plans are working documents and are not kept in this repository; that holds for the `airgap-transfer` spec and plan too (both dated 2026-11-22). `docs/HANDOFF.md` lists the readings of that spec which the implementation chose.

This file is for agents that work on the repository. People who install the skill never load it: a plugin install gets only the plugin folder, `plugins/airgap-anything/`, and the other install routes copy one skill folder each (`plugins/airgap-anything/skills/airgap-architect/` or `plugins/airgap-anything/skills/airgap-transfer/`). Anything a skill must do belongs in its folder's `SKILL.md` or its reference files.

The repository root holds the marketplace (`.claude-plugin/marketplace.json`), which lists `plugins/airgap-anything/`. Keep that folder to what an install needs: the plugin manifest and icon, the skill, and the triggering suite (`claude plugin eval` reads suites only inside the plugin). Anthropic's directory checks every file in it; `tests/test_packaging.py` enforces its rules.

## Commands

From the repository root. CI runs the tests on Python 3.11 and on the newest Python 3; run them on both.

```bash
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
python3 plugins/airgap-anything/skills/airgap-architect/scripts/lint.py --catalog-only
claude plugin validate plugins/airgap-anything --profile directory
python3 design/demo/build_demo.py
python3 docs-site/scripts/generate_reference.py
python3 evals/transfer_fixture.py --scenario department --out "$(mktemp -d)" --fetched
```

`build_demo.py` rebuilds the README demo in `assets/demo/`. `generate_reference.py` rewrites the generated pages of the documentation site (`docs-site/`, Astro Starlight, Node.js 24: `npm ci && npm run build`). `transfer_fixture.py` builds a transfer scenario with a fake fetched bundle; `tests/test_inside_scripts.py` needs coreutils' `sha256sum` and runs in CI on Linux. The brand rebuild is described in `design/brand/README.md`; it needs `fontTools`, `Pillow` and Chrome. `claude plugin validate --profile directory` runs the part of the directory's checks that Claude Code knows; the developer portal runs more.

## Rules

1. Scripts that ship inside a skill use only the Python standard library (3.11+). No `pip install`, no network calls.
2. Nothing from memory: every catalog value, version and rule needs a source fetched at authoring time or a field note. Otherwise it is labeled `estimate`.
3. The tier measures organizational complexity. GPU count is a separate output of sizing. Hardware counts never appear in the tier definition.
4. Point to existing per-tool skills; do not copy their content.

## When you change

- A catalog entry or a GPU row: keep `lint.py --catalog-only` at `OK: no findings`, and set `last_verified` to the day you re-checked the sources of what you touched.
- A value in `catalog/rules.toml`: update the tests that pin the value in the same change.
- What either `SKILL.md` makes the agent do: rerun that skill's protocol in `evals/README.md` (architect: 'Runs'; transfer: 'airgap-transfer'), including the five pressure runs, and record the results under `evals/results/`.
- A command line in `transfer_lib/tools.py`: read it from the tool's documentation, record the URL in `source` and in `references/fetch.md`, and run `tests/test_fetch_script.py`.
- The `description` in either `SKILL.md`: rerun the triggering suite (`evals/README.md`, "Triggering"); it decides whether Claude Code picks the skill by itself.
- A catalog entry, a GPU row, `docs/reference.md`, `references/interview.md`, the demo blueprint, the README's Install section or `CONTRIBUTING.md`: run `docs-site/scripts/generate_reference.py` and commit its output; `tests/test_docs_site.py` checks it.
- The brand icon: copy `assets/brand/icons/icon-512.png` to `plugins/airgap-anything/.claude-plugin/icon.png`; a test checks they are the same file. The directory keeps the icon of the first submission.
- Generated files: never edit `assets/brand/` or `assets/demo/` by hand, nor the pages under `docs-site/src/content/docs/reference/`, `example/`, `start/install.md` and `project/contributing.md`. Change the tools in `design/brand/tools/`, or what `design/demo/build_demo.py` runs, and rebuild.

## Working agreements

- The repository is written in English.
- Design before code, then a plan, then implementation. Write `SKILL.md` and reference files with `superpowers:writing-skills`. Keep specs and plans out of the repository.
- When you produce visuals, open a preview for the maintainer while you work, not only at the end.
- Pushing, opening pull requests and changing repository visibility need the maintainer's explicit go-ahead.
