# airgap-anything

An open-source plugin of Agent Skills for air-gapped and on-premises environments. `airgap-architect` designs the system and writes the transfer manifest; `airgap-transfer` turns that manifest into a bundle that checks itself inside the network; `airgap-agent` sets up coding agents (Qwen Code, Codex CLI, opencode, Claude Code on a Claude route) for the same network; `airgap-rag` makes the organization's documents searchable inside it (the user chooses the platform: Open WebUI knowledge bases, a RAG server such as RAGFlow, or their own; it picks extraction and OCR, models and the vector store, sizes the first load and writes the configuration and a bulk-load runbook). Version 0.5: all four skills are markdown only.

## Start here

- `README.md`: what the skills do and how they are installed.
- `CONTRIBUTING.md`: how to add or verify a catalog entry, a GPU row, a threshold or a sizing constant.
- `docs/HANDOFF.md`: the current status, the open decisions and the known limitations.
- `plugins/airgap-anything/skills/*/SKILL.md`: the skills themselves; every file they use is named there.

Design specs and implementation plans are working documents and are not kept in this repository.

This file is for agents that work on the repository. People who install the skills never load it: a plugin install gets only the plugin folder, `plugins/airgap-anything/`, and the other install routes copy one skill folder each. Anything a skill must do belongs in its folder's `SKILL.md` or its reference files.

The repository root holds the marketplaces: `.claude-plugin/marketplace.json` (Claude Code), `.agents/plugins/marketplace.json` (Codex) and `.cursor-plugin/marketplace.json` (Cursor), each listing `plugins/airgap-anything/`. The plugin folder holds the manifests (`.claude-plugin/plugin.json`, the portable `plugin.json`), the icon, the skills and the triggering suite, and nothing else: Anthropic's directory checks every file in it, and `tests/test_packaging.py` enforces its rules.

## Commands

From the repository root. CI runs the tests on Python 3.11 and on the newest Python 3; the skills themselves need no Python.

```bash
python3 -m unittest discover -s tests -t .
claude plugin validate .
claude plugin validate plugins/airgap-anything --profile directory
python3 docs-site/scripts/generate_reference.py
```

`generate_reference.py` rewrites the generated pages of the documentation site (`docs-site/`, Astro Starlight, Node.js 24: `npm ci && npm run build`) from the skills' markdown, the README's Install section, `CONTRIBUTING.md` and `examples/department/`. The brand rebuild is described in `design/brand/README.md`; it needs `fontTools`, `Pillow` and Chrome. `claude plugin validate --profile directory` runs the part of the directory's checks that Claude Code knows; the developer portal runs more.

## Rules

1. Skills ship markdown only: no scripts, no TOML, no rule codes. The agent reasons and calculates from the references, and writes its work out so that a reader can check it. `tests/test_skills.py` enforces the file types.
2. Nothing from memory: every catalog value, version, command line and rule needs a source fetched at authoring time or a field note. Otherwise it is labeled `estimate`.
3. The tier measures organizational complexity. GPU count is a separate output of sizing. Hardware counts never appear in the tier definition.
4. Point to existing per-tool skills; do not copy their content.
5. Follow Anthropic's checklist for effective skills (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): a description that says what and when in the third person, `SKILL.md` under 500 lines, every file named by `SKILL.md` itself, contents at the top of a reference longer than 100 lines, a copyable workflow checklist, and explanations of why instead of rules in capitals.

## When you change

- A catalog entry or a GPU row: set "Last verified" to the day you re-checked the sources of what you touched; `tests/test_catalog.py` checks the format.
- A sizing constant, a tier threshold or a default: update the worked examples in `references/sizing.md`, `tests/sizing_reference.py` and the eval scenarios in the same change; `tests/test_sizing.py` fails until they agree.
- What either `SKILL.md` or its references make the agent do: rerun that skill's protocol in `evals/README.md`, including the pressure runs, and record the results under `evals/results/`.
- A command line in `airgap-transfer`'s references: read it from the tool's documentation and record the URL in the table at the end of `references/fetch.md`.
- The `description` in either `SKILL.md`: rerun the triggering suite (`evals/README.md`, "Triggering"); it decides whether Claude Code picks the skill by itself.
- A skill file, a catalog entry, `references/gpus.md`, the example, the README's Install section or `CONTRIBUTING.md`: run `docs-site/scripts/generate_reference.py` and commit its output; `tests/test_docs_site.py` checks it.
- The plugin's version: change it in `.claude-plugin/marketplace.json`, `plugins/airgap-anything/.claude-plugin/plugin.json` and `plugins/airgap-anything/plugin.json` together; `tests/test_packaging.py` checks they agree.
- The brand icon: copy `assets/brand/icons/icon-512.png` to `plugins/airgap-anything/.claude-plugin/icon.png`; a test checks they are the same file.
- Generated files: never edit `assets/brand/` by hand, nor the pages under `docs-site/src/content/docs/reference/`, `example/`, `start/install.md` and `project/contributing.md`. Change their sources and rebuild.

## Working agreements

- The repository is written in English.
- Design before code, then a plan, then implementation. Write `SKILL.md` and reference files with `superpowers:writing-skills`. Keep specs and plans out of the repository.
- When you produce visuals, open a preview for the maintainer while you work, not only at the end.
- Pushing, opening pull requests and changing repository visibility need the maintainer's explicit go-ahead.
