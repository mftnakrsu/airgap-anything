# Handoff

Where the project stands and how to continue. Last updated on 2026-11-24 (version 0.5.0 prepared).

## Status

Version 0.5.0 is prepared on branch `feat/airgap-rag` and is not merged, tagged or released. It adds the fourth skill, `airgap-rag`, and raises the version to 0.5.0 in all manifests (`.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`, `plugins/airgap-anything/.claude-plugin/plugin.json`, the portable `plugin.json`). Merge only after the launch on 2026-12-01: the maintainer's decision.

- **Done on the branch (0.5).** The skill: `SKILL.md`, a catalog of eight components (docling-serve v1.39.0, pgvector 0.8.7, Qdrant v1.20.2, RAGFlow v1.0.0, Qwen3-Embedding-0.6B, bge-m3, Qwen3-Reranker-0.6B, bge-reranker-v2-m3) with every value sourced, and eight references (interview, decisions, extraction, models, sizing, ingestion, wiki, verification). The user chooses the platform (Open WebUI knowledge bases, a RAG server, or something else recorded as custom with `unverified` values); the skill asks and waits unless one is named. `airgap-transfer` accepts "(from airgap-rag)" rows and carries `docs/airgap/rag.md` and `docs/airgap/rag/` as project files (the transfer marker). Triggering cases (18 in the suite) and behavior scenarios with pressure prompts under `evals/rag-scenarios/`. README, a guide (`docs-site/src/content/docs/guides/searchable-documents.md`), generated reference pages with the rag catalog, and the sidebar entries. 105 tests, all passing on 2026-11-24. `claude plugin validate plugins/airgap-anything --profile directory` was run for the manifests. The site build (`npm run build`) was not run locally, since `node_modules` is absent; CI builds it.
- **Evaluated (0.5).** The evals ran on 2026-11-24. Triggering on 301bf75 (the later 2a76739 changed no description): 18 of 18 cases pass the rule, 53 of 54 runs pass every grader, overall score 0.995, USD 9.47 (`evals/results/2026-11-24-triggering-0.5.md`); the one missed grader is a single judge verdict on `auto-en-coding-agent`. Behavior on Haiku, Sonnet and Opus (`evals/results/2026-11-24-rag-with-skill.md`): round 1 on 301bf75 passed 11 of 12; Haiku wrote a loader program in `custom-platform`, which fixed 2a76739 (Rule 10: the skill writes no programs into the project), and the rerun of `custom-platform` on 2a76739 passed on all three models, so 12 of 12 after the fix. The 10 pressure runs (Sonnet, 5 each) passed. Not done: no live install inside a network, the Open WebUI endpoints were not called against a running instance, and only `custom-platform` was rerun after 2a76739.
- **Waiting (0.5).** The pull request; the merge only after the launch on 2026-12-01 (the maintainer's decision); then tag v0.5.0, release with four archives (one per skill, each with its `.sha256` file), and the developer portal's "Submit latest version".
- **Rules the skill keeps (0.5).** Documents from inside the network never go to a cloud agent outside it; the connected-side agent may convert only public documents. The Open WebUI API endpoints in the runbook were read from source at v0.13.4, because its docs no longer document them. The skill downloads nothing and runs nothing; no key is written to a file.

### Version 0.4 (released)

Version 0.4.0 added the third skill, `airgap-agent`, and raised the version to 0.4.0 in all manifests.

- **Done (0.4).** The skill: `SKILL.md` (checklist, seven rules, seven-item self-check), a catalog of four tools (Qwen Code 0.28.4, Codex CLI 0.172.0, opencode 2.4.1 on the V2 line, Claude Code 2.1.331) with every value sourced, and six references (interview, decisions, serving, mcp, templates, verification). `airgap-transfer` carries `docs/airgap/agents.md` and `docs/airgap/agents/<tool>/{user,central}/` as project files. Triggering cases (15 in the suite) and behavior scenarios with expectations under `evals/agent-scenarios/`. README, a guide (`docs-site/src/content/docs/guides/coding-agents.md`), generated reference pages with the agent catalog, and the sidebar entries. 85 tests, all passing on 2026-11-24. `claude plugin validate plugins/airgap-anything` was run for the manifests.
- **Rules the skill keeps.** Claude Code is never configured against an open-weight model (Anthropic "doesn't support routing Claude Code to non-Claude models through any gateway", https://code.claude.com/docs/en/llm-gateway); Qwen Code's `tools.approvalMode` is always written; every outbound switch of a tool is written and proved by the egress check; no key is written to a file.
- **Evaluated (0.4).** The evals ran on e95a6d2 on 2026-11-24. Triggering: 15 of 15 cases, 45 of 45 runs pass every grader, overall score 1.000, USD 7.96 (`evals/results/2026-11-24-triggering-0.4.md`). Behavior: `department` and `enterprise` pass on Haiku, Sonnet and Opus; the three `claude-pairing` runs declined Claude Code with GLM with the `llm-gateway` reason, recommended Qwen Code and stopped to ask before swapping the tool, which the maintainer's ruling made the correct behavior (the first expectation was wrong and was corrected in `evals/agent-scenarios/claude-pairing/expected.json`); pressure runs 5 of 5 and 5 of 5 on Sonnet, sent as part of the first prompt rather than as a second message (`evals/results/2026-11-24-agent-with-skill.md`).
- **Released (0.4).** Merged as pull request #19 (74d5346) after CI, the docs build and the triggering workflow passed; tagged v0.4.0 and released on 2026-11-24 with one archive and one `.sha256` file per skill. The directory portal was asked to check the latest version on 2026-11-24 ("Submit latest version"); the 0.3.0 submission was still waiting for an Anthropic reviewer, and no version is live yet. Launch posts are drafted outside the repository for Tuesday 2026-12-01; the maintainer posts them.

Version 0.3 was merged into `main` on 2026-11-24 (pull request #18, merge c307ae0) and released as v0.3.0 the same day, with one archive per skill and its SHA-256 file; the documentation site deployed it. Both skills are markdown only: no scripts, no TOML, no lint codes. The agent reasons and calculates from the references and writes its work out so that a reader can check it. Release 0.2.0 (2026-11-23) is the last version with scripts.

- **`airgap-architect` (0.3).** `SKILL.md` (a copyable workflow checklist, four rules, a nine-item self-review that replaces lint, common mistakes from the baseline runs), `references/` (interview, tiers, sizing with four worked examples, GPU table, three layer guides, blueprint and transfer-manifest templates, AGENTS.md block) and `catalog/<component>.md`, 16 entries with every value, evidence label and source of the former TOML catalog.
- **`airgap-transfer` (0.3).** `SKILL.md` (checklist, six rules, a seven-item self-check that replaces `check.py`) and five references: questions, fetch commands with their documentation sources, the plan file and bundle (checksums, split, volumes), channels, and the inside runbook and agent-rules templates. Inside the network, `sha256sum -c` alone checks the bundle.
- **Packaging (0.3).** One plugin folder, `plugins/airgap-anything/`, with `.claude-plugin/plugin.json` and the portable `plugin.json` (agent-plugins.org schema). Marketplaces at the root: `.claude-plugin/marketplace.json` (Claude Code), `.agents/plugins/marketplace.json` (Codex), `.cursor-plugin/marketplace.json` (Cursor). `npx skills` covers the other agents, Antigravity included. Gemini CLI was replaced by Antigravity CLI on 2026-06-18 and is not packaged. `claude plugin validate .` and `--profile directory` pass.
- **Anthropic's directory (0.3).** The plugin folder now holds only Markdown, JSON and the PNG icon, so the file-type rule that needed Verified status no longer applies (`docs/packaging-facts.md`, Q8 and its 0.3 update). The portal's own Validate has not been run on 0.3.
- **Tests (0.3).** The repository checks the markdown: `tests/test_skills.py` (Anthropic's checklist: frontmatter, size, every file named by `SKILL.md`, contents in long references, markdown only), `tests/test_catalog.py`, `tests/test_sizing.py` with `tests/sizing_reference.py` (the worked examples and the eval scenarios' numbers follow from the constants), packaging, README, docs site, triggering suite. 65 tests, all passing on Python 3.12 on 2026-11-24.
- **Evaluation (0.3).** 37 runs on Haiku, Sonnet and Opus (`evals/results/2026-11-24-with-skill.md`). Architect: every run matches the expected tier, every sizing number and every decision, including the enterprise case with KV-cache packing on Haiku; 5 of 5 pressure runs show neither F3 nor F6. Transfer: 9 of 9 plan runs and 5 of 5 pressure runs downloaded nothing before approval and refused to skip the checksums; 3 of 3 pack runs produced media that verify. The runs found real bugs (an empty `PARTS.sha256` failing `sha256sum -c`, `SEND-ORDER.txt` not listing itself, Haiku leaving out or merging manifest items), all fixed and confirmed by reruns.
- **Example (0.3).** `examples/department/` holds the blueprint and transfer manifest of the Opus department run, with the three corrections its README lists. The README and the docs site show it.
- **Documentation site (0.3).** `docs-site/` is generated from the skills' markdown by `docs-site/scripts/generate_reference.py`; the site build itself (`npm ci && npm run build`) was not run locally, since `node_modules` is absent; CI builds it.

## Waiting for the maintainer

- **Anthropic's directory:** submitted for review on 2026-11-24 from the developer portal (claude.ai/directory/manage): `plugins/airgap-anything` on `main` at fec5bed, listed on Claude Code, Cowork and the Claude apps, auto-publish on. The portal's Validate passed with four notes, all fields the directory reads for the listing (`icon`, `supportUrl`, `documentationUrl`, `privacyPolicyUrl`). It waits for the security scan and a reviewer; the answer appears on the submission's page and by email. Bisecting with Validate showed that its download-and-run check flags `curl` followed on the same prose line by a `|` or a URL; `tests/test_packaging.py` now applies that rule.
- **Cursor marketplace and the ChatGPT and Codex plugin directory: skipped for now, the maintainer's decision on 2026-11-24.** Each needs another publisher agreement for a listing that adds little: Cursor's Marketplace Publisher Terms (cursor.com/marketplace-publisher-terms) carry an indemnity that survives removal and binding arbitration, and OpenAI's directory (platform.openai.com/plugins) needs an individually verified Platform organization. Both agents already install from this repository (README, Install). If users ask for a listing: the OpenAI listing fields are in the portable `plugin.json` under `extensions.com.openai.interface` (f799573), the upload is a ZIP of the plugin folder (`git archive --format=zip HEAD:plugins/airgap-anything`), and Cursor's form takes the raw URL of `assets/brand/icons/icon-512.png` as the logo.
- **Not re-evaluated:** the disclaimer line added to `references/blueprint-template.md` on 2026-11-24 (fec5bed). It is one fixed sentence under the status line; the protocol in `evals/README.md` has not been rerun for it.

The triggering suite ran on the 0.3 descriptions on 2026-11-24: 12 of 12 cases pass, every skill check in every run, USD 5.65 (`evals/results/2026-11-24-triggering.md`).

## Decisions taken (2026-11-24)

- The skills ship no scripts (the maintainer: "i dont wanna bunch of pyscript sh sciprt at my skills").
- The catalog stays, as markdown, with every source; nothing is written from memory.
- Simplifications against 0.2: decision tables became defaults with reasons; replicas pack whole requests per user group instead of first-fit packing (it reproduces all scenario numbers; mixed contexts can come out one replica higher); no image-ID check inside; one manifest file, markdown.
- The project aims at a family of `airgap-<role>` skills in one plugin: `airgap-agent` (#10) shipped in 0.4; `airgap-rag` (#11) is on the 0.5 branch, then the ideas of #12.

## Known limitations

- **Arithmetic by the model.** The sizing is done by the agent. Every model got every scenario number right, but a design outside the worked examples has no script behind it; the sizing section writes every step out so that a person can check it.
- **Haiku on long lists.** Haiku merged manifest items until the template asked for one row per catalog item and the self-review compared the counts; the rerun after that change copied every item. Other long lists may need the same structural treatment.
- **The first step of the inside runbook has a placeholder** (`VOLUME_FOLDER` or `RECEIVED_FOLDER`): nobody on the connected side knows the mount path.
- **Gaps the catalog does not close.** No catalog route passes the signed-in person from Open WebUI to LiteLLM; whether Keycloak's optimized image can be built offline is unclear in its entry; Harbor's Trivy telemetry has no documented switch. Designs name these as custom choices and verification items.
- **Catalog freshness.** Entries were last verified on 2026-11-21 and 2026-11-22. The self-review flags any chosen entry older than 180 days, so from 2027-05-20 designs list them for re-checking.
- **Estimates.** Most thresholds and sizing constants are `estimate`; field data replaces them.

## Later

- The ideas of #12, each as its own `airgap-<role>` skill in the same markdown-only form.
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
