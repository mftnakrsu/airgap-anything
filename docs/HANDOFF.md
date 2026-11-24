# Handoff

Where the project stands and how to continue. Last updated on 2026-11-24.

## Status

Version 0.3 is on branch `feat/knowledge-first`, not yet merged or released. Both skills are markdown only: no scripts, no TOML, no lint codes. The agent reasons and calculates from the references and writes its work out so that a reader can check it. Release 0.2.0 (2026-11-23) is the last version with scripts.

- **`airgap-architect`.** `SKILL.md` (a copyable workflow checklist, four rules, a nine-item self-review that replaces lint, common mistakes from the baseline runs), `references/` (interview, tiers, sizing with four worked examples, GPU table, three layer guides, blueprint and transfer-manifest templates, AGENTS.md block) and `catalog/<component>.md`, 16 entries with every value, evidence label and source of the former TOML catalog.
- **`airgap-transfer`.** `SKILL.md` (checklist, six rules, a seven-item self-check that replaces `check.py`) and five references: questions, fetch commands with their documentation sources, the plan file and bundle (checksums, split, volumes), channels, and the inside runbook and agent-rules templates. Inside the network, `sha256sum -c` alone checks the bundle.
- **Packaging.** One plugin folder, `plugins/airgap-anything/`, with `.claude-plugin/plugin.json` and the portable `plugin.json` (agent-plugins.org schema). Marketplaces at the root: `.claude-plugin/marketplace.json` (Claude Code), `.agents/plugins/marketplace.json` (Codex), `.cursor-plugin/marketplace.json` (Cursor). `npx skills` covers the other agents, Antigravity included. Gemini CLI was replaced by Antigravity CLI on 2026-06-18 and is not packaged. `claude plugin validate .` and `--profile directory` pass.
- **Anthropic's directory.** The plugin folder now holds only Markdown, JSON and the PNG icon, so the file-type rule that needed Verified status no longer applies (`docs/packaging-facts.md`, Q8 and its 0.3 update). The portal's own Validate has not been run on 0.3.
- **Tests.** The repository checks the markdown: `tests/test_skills.py` (Anthropic's checklist: frontmatter, size, every file named by `SKILL.md`, contents in long references, markdown only), `tests/test_catalog.py`, `tests/test_sizing.py` with `tests/sizing_reference.py` (the worked examples and the eval scenarios' numbers follow from the constants), packaging, README, docs site, triggering suite. 65 tests, all passing on Python 3.12 on 2026-11-24.
- **Evaluation.** 37 runs on Haiku, Sonnet and Opus (`evals/results/2026-11-24-with-skill.md`). Architect: every run matches the expected tier, every sizing number and every decision, including the enterprise case with KV-cache packing on Haiku; 5 of 5 pressure runs show neither F3 nor F6. Transfer: 9 of 9 plan runs and 5 of 5 pressure runs downloaded nothing before approval and refused to skip the checksums; 3 of 3 pack runs produced media that verify. The runs found real bugs (an empty `PARTS.sha256` failing `sha256sum -c`, `SEND-ORDER.txt` not listing itself, Haiku leaving out or merging manifest items), all fixed and confirmed by reruns.
- **Example.** `examples/department/` holds the blueprint and transfer manifest of the Opus department run, with the three corrections its README lists. The README and the docs site show it.
- **Documentation site.** `docs-site/` is generated from the skills' markdown by `docs-site/scripts/generate_reference.py`; the site build itself (`npm ci && npm run build`) was not run locally, since `node_modules` is absent; CI builds it.

## Waiting for the maintainer

1. Push `feat/knowledge-first` and open the pull request.
2. The triggering suite: both descriptions gained a leading sentence ("Designs systems for …", "Packs the transfer manifest …"), so `claude plugin eval` must run again (about USD 6.50 on the maintainer's account).
3. Merge, tag v0.3.0 and publish the release; then submit to Anthropic's directory and, if wanted, the Codex plugin directory and the Cursor marketplace.

## Decisions taken (2026-11-24)

- The skills ship no scripts (the maintainer: "i dont wanna bunch of pyscript sh sciprt at my skills").
- The catalog stays, as markdown, with every source; nothing is written from memory.
- Simplifications against 0.2: decision tables became defaults with reasons; replicas pack whole requests per user group instead of first-fit packing (it reproduces all scenario numbers; mixed contexts can come out one replica higher); no image-ID check inside; one manifest file, markdown.
- The project aims at a family of `airgap-<role>` skills in one plugin: `airgap-rag` (#11) and `airgap-agent` (#10) next, then the ideas of #12.

## Known limitations

- **Arithmetic by the model.** The sizing is done by the agent. Every model got every scenario number right, but a design outside the worked examples has no script behind it; the sizing section writes every step out so that a person can check it.
- **Haiku on long lists.** Haiku merged manifest items until the template asked for one row per catalog item and the self-review compared the counts; the rerun after that change copied every item. Other long lists may need the same structural treatment.
- **The first step of the inside runbook has a placeholder** (`VOLUME_FOLDER` or `RECEIVED_FOLDER`): nobody on the connected side knows the mount path.
- **Gaps the catalog does not close.** No catalog route passes the signed-in person from Open WebUI to LiteLLM; whether Keycloak's optimized image can be built offline is unclear in its entry; Harbor's Trivy telemetry has no documented switch. Designs name these as custom choices and verification items.
- **Catalog freshness.** Entries were last verified on 2026-11-21 and 2026-11-22. The self-review flags any chosen entry older than 180 days, so from 2027-05-20 designs list them for re-checking.
- **Estimates.** Most thresholds and sizing constants are `estimate`; field data replaces them.

## Later

- `airgap-rag` (#11) and `airgap-agent` (#10), each with its own design, in the same markdown-only form.
- Eval scenarios that state `inside.operator` (`local_agent`, `people_then_agent`) and `hardware.cpu_arch = arm64`, and one whose hardware does not fit.
- Turn the behavior evals into `claude plugin eval` cases, so that contributors can run them.
- Split `code_assistant` into code completion and coding agent; make concurrency depend on organization size.
- Publisher signatures are not checked by `airgap-transfer`.

## Continue on another machine

Clone the repository, start Claude Code in the folder and say: "Read docs/HANDOFF.md and continue from there." Working on the skills needs nothing; the repository checks need Python 3.11 or newer; the evaluation protocol needs Claude Code (see `evals/README.md`); the brand rebuild needs `fontTools`, `Pillow` and Chrome (`design/brand/README.md`).

## Facts worth keeping

- GPU count is independent of the tier. A small team that serves a very large model can need as many GPUs as a large department, because the weights alone set the smallest GPU group.
- Published throughput numbers for inference engines conflict. The design therefore sizes memory by arithmetic and makes a benchmark step mandatory.
- GitHub code search treats a multi-word argument as an exact phrase. Pass terms separately when checking for prior art.
- On GitHub, the browser picks a `<picture>` source by the computer's colour scheme, while the page follows the GitHub theme. The README's images therefore either bring their own background or are transparent with text on its own cards and lines that clear 3:1 on both GitHub page colours; `tests/test_readme.py` checks both kinds.
- In a session without a shell, the 0.2 skills stalled ("the transfer steps are Python scripts"); the 0.3 skills need no shell to design.
