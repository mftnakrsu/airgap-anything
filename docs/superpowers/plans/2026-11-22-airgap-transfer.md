# airgap-transfer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add sub-project 2 to `airgap-anything`: `airgap-architect` asks who works inside the network and which CPU architecture its servers have, and writes the transfer manifest as Markdown and JSON; a second skill, `airgap-transfer`, turns that JSON manifest into a bundle that checks itself, with a fetch script for the connected side, checksums, a split across media, an inventory, and POSIX shell scripts plus a runbook or agent rules for the inside.

**Architecture:** Same hybrid shape as the first skill. Architect's changes are small edits to its `airgap_lib`, catalog and references. The new skill lives in `plugins/airgap-anything/skills/airgap-transfer/` and is self-contained: three standard-library scripts (`plan.py`, `pack.py`, `check.py`) over a package `transfer_lib`, which reads architect's output files (`blueprint.json`, `transfer-manifest.json`) and never imports architect's code. State lives in `docs/airgap/transfer.json`; the bundle lives in a folder outside the git repository. The inside runs only `verify.sh` and `load.sh` (POSIX sh, coreutils, docker). Deterministic code is built test-first; tool command lines and catalog package rows are research steps with recorded URLs; `SKILL.md` and its references are written after baseline runs without them.

**Tech Stack:** Python 3.11+ (standard library only: `json`, `hashlib`, `tarfile`, `argparse`, `shutil`, `unittest`), POSIX sh, TOML, Markdown, Astro Starlight (generated pages only), GitHub Actions, `claude plugin eval`.

**Spec:** `docs/superpowers/specs/2026-11-22-airgap-transfer-design.md` (§N below). Architect's spec, `docs/superpowers/specs/2026-11-20-airgap-architect-design.md`, is "the architect spec". Read both before any task.

**How the code in this plan was checked:** every code block below was run in a scratch copy of this repository at commit `94b590e` (the spec commit on `spec/airgap-transfer`), on Python 3.11.14 and 3.15.2 on macOS, with `sh` and `dash`. Phase A was built and tested task by task; each Phase A diff below is the scratch commit of that task, and each "Expected" failure in a Phase A task is what the scratch copy printed with only that task's test changes applied. Phase B and the Phase C fixtures were built as a whole, split into the tasks below, and replayed task by task from the end of Phase A, with the suite green after each task at the counts the tasks give; the full suite ended at 541 tests passing on both interpreters, with `fetch.sh` and `verify.sh` run for real against stub tools. Two kinds of values were only stand-ins in the scratch copy and are **not** in this plan: the catalog package rows (Task 2 researches them) and the tool command lines (Tasks 9 and 11 research them). The behavior runs of Phase C and the triggering suite need a model and were not run.

## Global Constraints

- **Names.** Skills: `airgap-architect` (exists), `airgap-transfer` (new). Packages: `airgap_lib` (exists), `transfer_lib` (new). Plugin: `airgap-anything`, version `0.2.0` from Task 23 on.
- **Python.** Scripts shipped in a skill use Python 3.11+ and only the standard library plus that skill's own package. `transfer_lib` never imports `airgap_lib`, and the reverse: an installer may copy one skill folder alone. No network modules (`tests/test_stdlib_only.py` enforces both), no network calls from Python.
- **Inside scripts.** `verify.sh` and `load.sh` are POSIX sh with coreutils (and `docker` in `load.sh`): no Python, no `curl`, no `wget`, no bashisms, no shebang line. They are run as `sh verify.sh`.
- **Test commands,** from the repository root, both interpreters, every time the plan says "run the suite":
  - `python3.11 -m unittest discover -s tests -t .`
  - `python3 -m unittest discover -s tests -t .`
  - One module: `python3.11 -m unittest tests.test_NAME -v`.
- **Shell tests.** `tests/test_fetch_script.py` runs `fetch.sh` with `sh` (and `dash` when present) and needs `sha256sum` or `shasum`. `tests/test_inside_scripts.py` needs coreutils' `sha256sum`; it is skipped where that is missing and runs in CI on Ubuntu. macOS 27 ships `/sbin/sha256sum`, so both run locally there.
- **Nothing from memory.** No tool option (skopeo, docker, hf, curl, md5sum, sha256sum, shasum), package file name, download URL, checksum-file URL or arm64 file name is typed from memory, including from this plan's examples. Each comes from the official page named in the step, opened at implementation time, and its URL is recorded next to the value (`evidence.sources` in the catalog; `source` in `transfer_lib/tools.py`; the table in `references/fetch.md`). Tasks 2, 9 and 11 carry explicit "fetch and record the sources" steps. If a page does not say what the step needs, stop and report; do not guess.
- **No installs.** Never `pip install`, `brew install`, `npm install` or `uv add` on the maintainer's machine. Anything that needs a tool not present (Linux coreutils, a registry) is checked in CI or reported.
- **Generated files** are never edited by hand: `assets/demo/`, `docs-site/src/content/docs/reference/` (including the new `reference/transfer/`), `example/department.md`, `start/install.md`, `project/contributing.md`, and the copied images. Change the source, then run `python3 design/demo/build_demo.py` and `python3 docs-site/scripts/generate_reference.py`.
- **Exit codes** for the transfer scripts: 0 done; 1 `check.py` errors or a volume that did not read back; 2 missing, stale or invalid input, or a bundle that cannot be packed yet; 3 environment (missing tool, Python older than 3.11). Inside scripts: 0 go on, 1 stop and report, 2 wrong arguments.
- **Finding codes.** Architect gains `C5`, `C6` (catalog), `W4` (warning) and a second file under `E8`. Transfer: errors `B1` to `B8`, warnings `BW1`, `BW2` (a code starting with `BW` is a warning).
- **Fixed strings.** `docs/airgap/transfer-manifest.json`, `docs/airgap/transfer.json`, `<!-- airgap-architect:inside-agent -->` (the marker of the agent-rules section), the bundle file names of §9.2 plus `VOLUMES.txt`, `VOLUME.txt`, `MISSING.txt`, `.verified`, and the part suffix `.partNNN` (three digits, from 001).
- **Language.** The repository is English. No personal data and no employer names in any file, fixture, prompt or commit.
- **Git.** Work on a feature branch made from `spec/airgap-transfer` (Task 1, Step 1). One commit per task; stage the listed paths by name; never `git add -A`, `git add .` or `git commit -a`. End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never push and never open a pull request; Task 24 describes those as the coordinator's steps, gated on the maintainer.
- **Skill text.** `SKILL.md` and the reference files of `airgap-transfer` are written with `superpowers:writing-skills`, after the baseline of Task 15. A change to what architect's `SKILL.md` makes the agent do is followed by its protocol rerun (Task 19). A changed `description` is followed by the triggering suite (Task 20).
- **When blocked,** stop and report. Do not invent a value to get past a step.

## Where this plan reads the spec

The spec leaves these points open or the code needed a narrower reading. Each is built as written here; the maintainer may overrule any of them before Phase B starts.

| # | Spec | This plan |
|---|---|---|
| 1 | §8.3: a model `revision` is "commit or tag"; §8.4: "the commit actually fetched is recorded" | `revision` must be the full 40-character commit hash. With a tag, the fetched commit would need a network call the scripts may not make. The agent turns a tag into its commit with the user (references/questions.md). |
| 2 | §8.4: a model repository without safetensors weights stops the plan with exit 2 | `plan.py` can see only a `local` folder offline, so exit 2 applies there. For a Hugging Face model the same check runs in `fetch.sh`, which fails that item. |
| 3 | §8.7: `load.sh` checks "the loaded digest against `bundle.json`" | `docker load` does not keep the registry digest. `pack.py` reads each archive's image ID (the SHA-256 of its config) into `<name>.id` and `bundle.json`; `load.sh` checks that ID. The registry digest stays in `<name>.digest` and the inventory. |
| 4 | §8.5, §8.6: every volume carries "its own `SHA256SUMS`" | Every volume carries the same bundle-wide `SHA256SUMS`, `bundle.json`, `PARTS.txt` and a new `VOLUMES.txt` (which file or part is on which volume, with its size and hash), plus `VOLUME.txt` as its label. One set of files tells any volume what the whole set holds and what is missing. |
| 5 | §6.4: the JSON rows | Image and package rows also carry `license`, which the inventory needs. Additive. |
| 6 | §8.6: runbooks "are written in the blueprint's `language`" | `pack.py` writes them in English; when `language` is not `en`, `pack.py` says so and the agent translates the prose, keeping every command line. `check.py` B7 checks that every command line survived. |
| 7 | §8.6: pack runs "after the manual items are settled" | `pack.py` exits 2 while a manual item is unsettled, or when an image archive names another platform than the manifest. |
| 8 | §11.5: scenario channels (`lab` with a data diode, `enterprise` with a staging host) | Architect's scenarios use other channels (`lab` removable media, `enterprise` data diode) and are scored as they are. The transfer scenarios are separate fixtures under `evals/transfer-scenarios/` that set the channels of §11.5. |
| 9 | §8.10: `skip-*-what-to-carry` | Read as a `does-not-fire-transfer.md` grader added to the existing case `auto-tr-tasima-listesi`, which keeps its architect graders. |
| 10 | §7: `.sh` files in the plugin | `tests/test_packaging.py` gains `.sh` as a third Verified-only file type, next to Python and TOML; still no shebang. |
| 11 | §14: "a model can allow more patterns; `check.py` reports what was left out" | Not built. Only `allow_pickle` widens the filter; the filter is one tuple in `transfer_lib/constants.py`. Task 24 lists it for the maintainer. |

## File Structure

```
airgap-anything/
├── CONTRIBUTING.md                                   Task 2 (package rows)
├── README.md  CLAUDE.md  docs/HANDOFF.md             Task 21
├── .claude-plugin/marketplace.json                   Task 23 (0.2.0)
├── .github/workflows/triggering.yml                  Task 20
├── design/demo/build_demo.py                         Task 4
├── docs-site/
│   ├── astro.config.mjs                              Task 22
│   ├── scripts/generate_reference.py                 Tasks 2, 22
│   └── src/content/docs/guides/carrying-it-in.md     Task 22 (rewritten)
├── docs/superpowers/specs/2026-11-20-airgap-architect-design.md   Tasks 1, 4 (§7, §11.1, §12 rows)
├── evals/
│   ├── README.md                                     Task 15 (transfer protocol)
│   ├── transfer_fixture.py                           Task 15
│   ├── transfer-scenarios/{department,lab,enterprise}/   Task 15
│   ├── scenarios/*/answers.json                      Task 1
│   └── results/DATE-transfer-*.md, DATE-*.md         Tasks 15, 18, 19, 20
├── plugins/airgap-anything/
│   ├── .claude-plugin/plugin.json                    Task 23 (0.2.0)
│   ├── evals/triggering/                             Task 20 (four new cases, two graders)
│   └── skills/
│       ├── airgap-architect/                         Tasks 1 to 4
│       │   ├── SKILL.md  references/{interview,agents-snippet,blueprint-template}.md
│       │   ├── catalog/rules.toml  catalog/components/*.toml
│       │   └── scripts/manifest.py  scripts/airgap_lib/{constants,answers,catalog,blueprint,transfer,checks}.py
│       └── airgap-transfer/
│           ├── SKILL.md                              Task 17
│           ├── references/questions.md channels.md fetch.md inside.md bundle-layout.md   Task 16
│           ├── templates/verify.sh  load.sh          Task 12
│           └── scripts/
│               ├── plan.py                           Task 10
│               ├── pack.py                           Task 12
│               ├── check.py                          Task 13
│               └── transfer_lib/
│                   ├── __init__.py   Python guard               Task 6
│                   ├── constants.py  names and limits           Task 6
│                   ├── findings.py   B codes, report formats    Task 6
│                   ├── cli.py        parser, fail()             Task 6
│                   ├── inputs.py     blueprint and manifest     Task 8
│                   ├── state.py      transfer.json              Task 8
│                   ├── items.py      the item list              Task 8
│                   ├── questions.py  which questions, checks    Task 7
│                   ├── tools.py      tools and command lines    Task 9
│                   ├── fetch_script.py  fetch.sh text           Task 10
│                   ├── hashing.py  volumes.py  archive.py       Task 11
│                   ├── bundle.py  inventory.py  runbook.py  pack_files.py   Task 12
│                   └── checks.py     B1-B8, BW1-BW2             Task 13
└── tests/
    ├── __init__.py                                   Task 6
    ├── support.py  projects.py                       Tasks 1 to 4
    ├── fetch_stubs.py  transfer_projects.py          Tasks 10, 8
    ├── test_transfer_*.py  test_fetch_script.py  test_inside_scripts.py   Tasks 6 to 13
    ├── test_transfer_skill_file.py                   Tasks 16, 17
    ├── test_transfer_scenarios.py                    Task 15
    └── test_packaging.py  test_stdlib_only.py  test_triggering_suite.py  test_real_catalog.py   Tasks 2, 12, 14, 17, 20
```

## Phases

| Phase | Tasks | Ends with |
|---|---|---|
| A. Architect changes | 1 to 5 | Two new questions, catalog schema 2 with researched package rows, the JSON manifest filtered by architecture, W4 and the agent rules, demo and docs rebuilt; suite green |
| B. The skill's scripts | 6 to 14 | `plan.py`, `pack.py`, `check.py`, `verify.sh`, `load.sh`, with researched command lines; suite green; no `SKILL.md` yet |
| C. Skill text and behavior | 15 to 20 | Transfer fixtures and baseline, references, `SKILL.md`, runs with the skill, architect's rerun, the triggering suite |
| D. Release and docs | 21 to 25 | README, HANDOFF, CLAUDE.md, docs site, version 0.2.0, release archives, final check, the mefby.com page |

---

## Phase A: Architect changes

Phase A changes files that exist. Its code is given as unified diffs against the commit before the task; apply each with the editor (or save it to a file in your scratch folder and run `git apply FILE`), and read every hunk: a hunk that does not apply means the file moved on, so stop and report.

### Task 1: Two questions, `hardware.cpu_arch` and `inside.operator`

§6.1, §6.2. Both questions are required, so `unknown` gives W2 and takes the default from `rules.toml`; `airgap-transfer` later reads the default from the blueprint's `assumptions`.

**Files:**
- Modify: `plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py`
- Modify: `plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/answers.py`
- Modify: `plugins/airgap-anything/skills/airgap-architect/catalog/rules.toml`
- Modify: `plugins/airgap-anything/skills/airgap-architect/references/interview.md`
- Modify: `tests/support.py`, `tests/test_answers.py`, `tests/test_rules.py`
- Modify: `evals/scenarios/{lab,department,enterprise}/answers.json`, `design/demo/department-blueprint.json`
- Modify: `docs/superpowers/specs/2026-11-20-airgap-architect-design.md` (§7 table)
- Regenerate: `docs-site/src/content/docs/reference/interview-questions.md`

**Interfaces:**
- Consumes: `answers.QUESTIONS`, `Question(id, kind, required, choices)`, `rules.default_answer(rules, qid)`.
- Produces: `constants.CPU_ARCHES = ("amd64", "arm64")`, `constants.INSIDE_OPERATORS = ("people", "local_agent", "people_then_agent")`, `constants.AGENT_OPERATORS = ("local_agent", "people_then_agent")`; question `inside.operator` after `org.kubernetes_experience`, question `hardware.cpu_arch` after `hardware.power_budget_kw` (21 questions, 16 required); defaults `amd64` and `people` with evidence `estimate`.

- [ ] **Step 1: Make the feature branch**

Run:

```bash
git switch spec/airgap-transfer
git switch -c feat/airgap-transfer
git log --oneline -1
```

Expected: `Switched to a new branch 'feat/airgap-transfer'` and the spec commit `docs: design spec for airgap-transfer and the inside operator` (or the plan commit after it) on top.

- [ ] **Step 2: Write the failing tests**

```diff
diff --git a/tests/support.py b/tests/support.py
--- a/tests/support.py
+++ b/tests/support.py
@@ -158,10 +158,12 @@ def base_answers(**overrides) -> dict:
             {"name": "example-70b", "role": "chat", "params_b": 70, "precision": "fp8"}
         ],
         "hardware.gpus": [{"model": "TG141", "count": 8}],
+        "hardware.cpu_arch": "amd64",
         "existing.identity": "ad_ldap",
         "existing.api_gateway": "none",
         "existing.kubernetes": "none",
         "transfer.channel": "removable_media",
+        "inside.operator": "people",
     }
     answers.update(overrides)
     return answers
diff --git a/tests/test_answers.py b/tests/test_answers.py
--- a/tests/test_answers.py
+++ b/tests/test_answers.py
@@ -15,8 +15,33 @@ class ResolveAnswersTest(unittest.TestCase):
         return resolve_answers(answers, self.rules, needed)[2]
 
     def test_question_table_matches_the_spec(self):
-        self.assertEqual(len(QUESTIONS), 19)
-        self.assertEqual(len(REQUIRED_IDS), 14)
+        self.assertEqual(len(QUESTIONS), 21)
+        self.assertEqual(len(REQUIRED_IDS), 16)
+
+    def test_cpu_arch_and_inside_operator_take_their_choices(self):
+        for key, good, bad in (
+            ("hardware.cpu_arch", ("amd64", "arm64"), "x86_64"),
+            ("inside.operator", ("people", "local_agent", "people_then_agent"), "robots"),
+        ):
+            for value in good:
+                with self.subTest(key=key, value=value):
+                    self.assertEqual(self.problems(support.base_answers(**{key: value})), [])
+            self.assertEqual(
+                self.problems(support.base_answers(**{key: bad})),
+                [f"{key}: must be one of " + ", ".join(good)],
+            )
+
+    def test_unknown_cpu_arch_and_operator_take_the_safe_defaults(self):
+        answers = support.base_answers(**{"hardware.cpu_arch": "unknown", "inside.operator": "unknown"})
+        resolved, assumptions, problems = resolve_answers(answers, self.rules)
+        self.assertEqual(problems, [])
+        self.assertEqual(resolved["hardware.cpu_arch"], "amd64")
+        self.assertEqual(resolved["inside.operator"], "people")
+        self.assertEqual(
+            sorted(item["id"] for item in assumptions),
+            ["answers.hardware.cpu_arch", "answers.inside.operator"],
+        )
+        self.assertTrue(all(item["evidence"] == "estimate" for item in assumptions))
 
     def test_complete_answers_have_no_problems(self):
         resolved, assumptions, problems = resolve_answers(support.base_answers(), self.rules)
diff --git a/tests/test_rules.py b/tests/test_rules.py
--- a/tests/test_rules.py
+++ b/tests/test_rules.py
@@ -45,6 +45,8 @@ class ShippedRulesTest(unittest.TestCase):
         self.assertEqual(self.rules.default_answer("org.audit_required")["value"], True)
         self.assertEqual(self.rules.default_answer("workload.usage")["value"], {"chat": 1.0})
         self.assertIsNone(self.rules.default_answer("org.users_total"))
+        self.assertEqual(self.rules.default_answer("hardware.cpu_arch")["value"], "amd64")
+        self.assertEqual(self.rules.default_answer("inside.operator")["value"], "people")
 
     def test_four_escalators(self):
         self.assertEqual(
```

- [ ] **Step 3: Run them to see them fail**

Run: `python3.11 -m unittest discover -s tests -t .`

Expected: `FAILED (failures=3, errors=1)`: `test_question_table_matches_the_spec`, `test_cpu_arch_and_inside_operator_take_their_choices`, `test_unknown_cpu_arch_and_operator_take_the_safe_defaults` fail, and `test_default_answer` errors on the missing defaults.

- [ ] **Step 4: Add the constants, the questions and the defaults**

```diff
diff --git a/plugins/airgap-anything/skills/airgap-architect/catalog/rules.toml b/plugins/airgap-anything/skills/airgap-architect/catalog/rules.toml
--- a/plugins/airgap-anything/skills/airgap-architect/catalog/rules.toml
+++ b/plugins/airgap-anything/skills/airgap-architect/catalog/rules.toml
@@ -294,3 +294,13 @@ notes = "No existing infrastructure is assumed."
 value = "removable_media"
 evidence = "estimate"
 notes = "The most restrictive common transfer channel."
+
+[defaults.hardware.cpu_arch]
+value = "amd64"
+evidence = "estimate"
+notes = "Taken as the most common server architecture (design spec 2026-11-22, section 6.1); not sourced. A wrong value gives the wrong package files, so the blueprint lists it among the assumptions."
+
+[defaults.inside.operator]
+value = "people"
+evidence = "estimate"
+notes = "A runbook for people works whether or not an agent appears later, so this default cannot leave the inside without instructions (design spec 2026-11-22, section 6.1)."
diff --git a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/answers.py b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/answers.py
--- a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/answers.py
+++ b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/answers.py
@@ -5,7 +5,9 @@ from collections.abc import Iterable
 from dataclasses import dataclass
 
 from .constants import (
+    CPU_ARCHES,
     GPU_VENDORS,
+    INSIDE_OPERATORS,
     INTERACTIVE_USAGE,
     MODEL_ROLES,
     SIZE_CLASSES,
@@ -32,12 +34,14 @@ QUESTIONS = (
     Question("org.downtime_tolerance", "enum", True, ("accepted", "planned_only", "none")),
     Question("org.ops_capacity", "enum", True, ("part_time_one", "small_team", "platform_team")),
     Question("org.kubernetes_experience", "bool", True),
+    Question("inside.operator", "enum", True, INSIDE_OPERATORS),
     Question("workload.usage", "usage", True),
     Question("workload.models", "models", True),
     Question("workload.context_tokens", "contexts", False),
     Question("hardware.gpus", "gpus", True),
     Question("hardware.ram_gb", "number", False),
     Question("hardware.power_budget_kw", "number", False),
+    Question("hardware.cpu_arch", "enum", True, CPU_ARCHES),
     Question("existing.identity", "enum", True, ("none", "ad_ldap", "oidc")),
     Question("existing.api_gateway", "enum", True, ("none", "kong", "other")),
     Question("existing.kubernetes", "enum", True, ("none", "kubernetes", "openshift")),
diff --git a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py
--- a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py
+++ b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py
@@ -29,6 +29,11 @@ SIZE_CLASSES = ("S", "M", "L", "XL")
 GPU_VENDORS = ("nvidia", "amd", "intel")
 HARDWARE_CLASSES = GPU_VENDORS + ("cpu",)
 
+# CPU architectures of the servers inside, and who works inside the network.
+CPU_ARCHES = ("amd64", "arm64")
+INSIDE_OPERATORS = ("people", "local_agent", "people_then_agent")
+AGENT_OPERATORS = ("local_agent", "people_then_agent")
+
 # Requirements an escalator in rules.toml may switch on.
 ESCALATOR_REQUIREMENTS = (
     "gateway_non_empty",
```

- [ ] **Step 5: Add the questions to the interview and the architect spec**

```diff
diff --git a/docs/superpowers/specs/2026-11-20-airgap-architect-design.md b/docs/superpowers/specs/2026-11-20-airgap-architect-design.md
--- a/docs/superpowers/specs/2026-11-20-airgap-architect-design.md
+++ b/docs/superpowers/specs/2026-11-20-airgap-architect-design.md
@@ -159,12 +159,14 @@ Questions:
 | `org.downtime_tolerance` | How much downtime is acceptable | `accepted`, `planned_only`, `none` | yes |
 | `org.ops_capacity` | Who operates the system | `part_time_one`, `small_team`, `platform_team` | yes |
 | `org.kubernetes_experience` | Whether the operating team runs Kubernetes today | boolean | yes |
+| `inside.operator` | Who carries out the installation and later work inside the network | `people`, `local_agent`, `people_then_agent` | yes |
 | `workload.usage` | Share of each usage type: `chat`, `code_assistant`, `rag`, `batch` | map of shares summing to 1 | yes |
 | `workload.models` | Models to serve: role, parameter count and precision, or weight size; optional context length and architecture numbers | list | yes |
 | `workload.context_tokens` | Typical context length per user group: `chat`, `code_assistant`, `rag` | map of group to tokens | no |
 | `hardware.gpus` | GPUs that exist or will be bought: model, count, optional VRAM and vendor (`nvidia`, `amd`, `intel`) | list, may be empty | yes |
 | `hardware.ram_gb` | System RAM, asked only when there is no GPU | number | conditional |
 | `hardware.power_budget_kw` | Power available for the system | number | no |
+| `hardware.cpu_arch` | CPU architecture of the servers inside the network | `amd64`, `arm64` | yes |
 | `existing.identity` | Existing identity provider | `none`, `ad_ldap`, `oidc` | yes |
 | `existing.api_gateway` | Existing API gateway | `none`, `kong`, `other` | yes |
 | `existing.kubernetes` | Existing cluster platform | `none`, `kubernetes`, `openshift` | yes |
diff --git a/plugins/airgap-anything/skills/airgap-architect/references/interview.md b/plugins/airgap-anything/skills/airgap-architect/references/interview.md
--- a/plugins/airgap-anything/skills/airgap-architect/references/interview.md
+++ b/plugins/airgap-anything/skills/airgap-architect/references/interview.md
@@ -46,21 +46,25 @@ Paths such as `catalog/rules.toml` and `catalog/gpus.toml` are relative to the s
 | 5 | `org.downtime_tolerance` | How much downtime is acceptable? | `accepted`, `planned_only`, `none` |
 | 6 | `org.ops_capacity` | Who will operate the system? | `part_time_one`, `small_team`, `platform_team` |
 | 7 | `org.kubernetes_experience` | Does the operating team run Kubernetes today? | `true` or `false` |
-| 8 | `workload.usage` | What will people use it for, in rough shares? | map of `chat`, `code_assistant`, `rag`, `batch` to shares that sum to 1 |
-| 9 | `workload.models` | Which model or models will be served? | list, see below |
-| 10 | `workload.context_tokens` | How long is a typical request of each group, prompt and history together, in tokens? Ask it when the groups differ. Optional. | map of `chat`, `code_assistant`, `rag` to a whole number of tokens, see below |
-| 11 | `hardware.gpus` | Which GPUs exist or will be bought? | list, see below; `[]` when there is no GPU |
-| 12 | `hardware.ram_gb` | How much system RAM does the server have? Ask only when there is no GPU. | number |
-| 13 | `hardware.power_budget_kw` | How much power is available for this system? Optional. | number |
-| 14 | `existing.identity` | Is there an identity provider already? | `none`, `ad_ldap`, `oidc` |
-| 15 | `existing.api_gateway` | Is there an API gateway already? | `none`, `kong`, `other` |
-| 16 | `existing.kubernetes` | Is there a cluster platform already? | `none`, `kubernetes`, `openshift` |
-| 17 | `existing.registry` | Is there an artifact registry already? Optional. | `none`, `harbor`, `nexus`, `artifactory`, `other` |
-| 18 | `transfer.channel` | How do files enter the network? | `removable_media`, `data_diode`, `staging_host`, `other` |
-| 19 | `transfer.cadence` | How often can updates be carried in? Optional. | `ad_hoc`, `monthly`, `quarterly` |
+| 8 | `inside.operator` | Inside the network, who will carry out the installation and later work? | `people` (no LLM inside), `local_agent` (an agent on a local model already runs inside), `people_then_agent` (people on the first day, then an agent on this platform's model) |
+| 9 | `workload.usage` | What will people use it for, in rough shares? | map of `chat`, `code_assistant`, `rag`, `batch` to shares that sum to 1 |
+| 10 | `workload.models` | Which model or models will be served? | list, see below |
+| 11 | `workload.context_tokens` | How long is a typical request of each group, prompt and history together, in tokens? Ask it when the groups differ. Optional. | map of `chat`, `code_assistant`, `rag` to a whole number of tokens, see below |
+| 12 | `hardware.gpus` | Which GPUs exist or will be bought? | list, see below; `[]` when there is no GPU |
+| 13 | `hardware.ram_gb` | How much system RAM does the server have? Ask only when there is no GPU. | number |
+| 14 | `hardware.power_budget_kw` | How much power is available for this system? Optional. | number |
+| 15 | `hardware.cpu_arch` | Which CPU architecture do the servers inside the network have? | `amd64` or `arm64` |
+| 16 | `existing.identity` | Is there an identity provider already? | `none`, `ad_ldap`, `oidc` |
+| 17 | `existing.api_gateway` | Is there an API gateway already? | `none`, `kong`, `other` |
+| 18 | `existing.kubernetes` | Is there a cluster platform already? | `none`, `kubernetes`, `openshift` |
+| 19 | `existing.registry` | Is there an artifact registry already? Optional. | `none`, `harbor`, `nexus`, `artifactory`, `other` |
+| 20 | `transfer.channel` | How do files enter the network? | `removable_media`, `data_diode`, `staging_host`, `other` |
+| 21 | `transfer.cadence` | How often can updates be carried in? Optional. | `ad_hoc`, `monthly`, `quarterly` |
 
 Usage types: `chat` is conversation in a chat window. `code_assistant` covers agentic coding tools, which keep a request in flight most of the time; people who only use inline completion in an editor are counted under `chat`. That is a deliberate overestimate, not a sourced placement: the notes of `sizing.code_assistant.duty_low` and `sizing.code_assistant.duty_high` in `catalog/rules.toml` show that inline completion keeps a request in flight only a few percent of the time, far below `code_assistant` and far below the duty of `chat`. `rag` is question answering over documents. `batch` is unattended jobs.
 
+`inside.operator`: when the answer is `local_agent` or `people_then_agent` and that agent will run on this platform's model, say so when you ask `workload.usage`, and count the agent's users under `code_assistant`: an agentic tool keeps a request in flight most of the time. `hardware.cpu_arch` decides which package files the transfer manifest lists (its `Platform:` line); "unknown" gives `amd64`, recorded as an assumption.
+
 ## `workload.models`
 
 One object per model.
```

- [ ] **Step 6: Give the scenario fixtures and the demo blueprint the two answers**

The scenario prompts state neither fact, so a correct interview stores `unknown` (scenario rule: what the prompt does not state is unknown). The demo blueprint shows the case the spec is about: people first, then an agent.

```diff
diff --git a/design/demo/department-blueprint.json b/design/demo/department-blueprint.json
--- a/design/demo/department-blueprint.json
+++ b/design/demo/department-blueprint.json
@@ -12,6 +12,7 @@
     "org.downtime_tolerance": "planned_only",
     "org.ops_capacity": "small_team",
     "org.kubernetes_experience": false,
+    "inside.operator": "people_then_agent",
     "workload.usage": {
       "chat": 1.0
     },
@@ -31,6 +32,7 @@
         "tdp_w": 700
       }
     ],
+    "hardware.cpu_arch": "amd64",
     "existing.identity": "ad_ldap",
     "existing.api_gateway": "none",
     "existing.kubernetes": "none",
diff --git a/evals/scenarios/department/answers.json b/evals/scenarios/department/answers.json
--- a/evals/scenarios/department/answers.json
+++ b/evals/scenarios/department/answers.json
@@ -6,6 +6,7 @@
   "org.downtime_tolerance": "planned_only",
   "org.ops_capacity": "small_team",
   "org.kubernetes_experience": false,
+  "inside.operator": "unknown",
   "workload.usage": { "chat": 1.0 },
   "workload.models": [
     { "name": "division-671b", "role": "chat", "params_b": 671, "precision": "fp8" }
@@ -13,6 +14,7 @@
   "hardware.gpus": [
     { "model": "generic-141gb", "count": 8, "vram_gb": 141, "tdp_w": 700 }
   ],
+  "hardware.cpu_arch": "unknown",
   "existing.identity": "ad_ldap",
   "existing.api_gateway": "none",
   "existing.kubernetes": "none",
diff --git a/evals/scenarios/enterprise/answers.json b/evals/scenarios/enterprise/answers.json
--- a/evals/scenarios/enterprise/answers.json
+++ b/evals/scenarios/enterprise/answers.json
@@ -6,6 +6,7 @@
   "org.downtime_tolerance": "none",
   "org.ops_capacity": "platform_team",
   "org.kubernetes_experience": true,
+  "inside.operator": "unknown",
   "workload.usage": { "chat": 0.7, "code_assistant": 0.2, "rag": 0.1 },
   "workload.models": [
     {
@@ -20,6 +21,7 @@
   "hardware.gpus": [
     { "model": "generic-141gb", "count": 24, "vram_gb": 141, "tdp_w": 700 }
   ],
+  "hardware.cpu_arch": "unknown",
   "existing.identity": "ad_ldap",
   "existing.api_gateway": "kong",
   "existing.kubernetes": "openshift",
diff --git a/evals/scenarios/lab/answers.json b/evals/scenarios/lab/answers.json
--- a/evals/scenarios/lab/answers.json
+++ b/evals/scenarios/lab/answers.json
@@ -6,11 +6,13 @@
   "org.downtime_tolerance": "accepted",
   "org.ops_capacity": "part_time_one",
   "org.kubernetes_experience": false,
+  "inside.operator": "unknown",
   "workload.usage": { "chat": 1.0 },
   "workload.models": [
     { "name": "lab-8b", "role": "chat", "params_b": 8, "precision": "fp8" }
   ],
   "hardware.gpus": [{ "model": "generic-24gb", "count": 1, "vram_gb": 24 }],
+  "hardware.cpu_arch": "unknown",
   "existing.identity": "none",
   "existing.api_gateway": "none",
   "existing.kubernetes": "none",
```

- [ ] **Step 7: Regenerate the documentation pages and run the suite**

Run:

```bash
python3 docs-site/scripts/generate_reference.py
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
python3 plugins/airgap-anything/skills/airgap-architect/scripts/lint.py --catalog-only
```

Expected: `wrote 25 pages and 5 images`, both suites end with `OK` (397 tests), and lint prints `OK: no findings`. `git status --short` lists `docs-site/src/content/docs/reference/interview-questions.md` among the changes.

- [ ] **Step 8: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py \
  plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/answers.py \
  plugins/airgap-anything/skills/airgap-architect/catalog/rules.toml \
  plugins/airgap-anything/skills/airgap-architect/references/interview.md \
  tests/support.py tests/test_answers.py tests/test_rules.py \
  evals/scenarios/lab/answers.json evals/scenarios/department/answers.json evals/scenarios/enterprise/answers.json \
  design/demo/department-blueprint.json docs/superpowers/specs/2026-11-20-airgap-architect-design.md \
  docs-site/src/content/docs/reference/interview-questions.md
git commit -m "feat(architect): ask who works inside and the CPU architecture

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Catalog schema 2: package rows as tables, C5 and C6, researched rows

§7. A package row becomes `{ file, arch, url, checksums }`. The validator, the fixture helpers, the docs generator and CONTRIBUTING change first; then the four real entries with packages are rewritten from their release pages, with arm64 rows where the release has them.

**Files:**
- Modify: `plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py`, `catalog.py`, `transfer.py`
- Modify: `tests/support.py`, `tests/test_catalog.py`, `tests/test_transfer.py`, `tests/test_real_catalog.py`
- Modify: every file in `plugins/airgap-anything/skills/airgap-architect/catalog/components/` (schema_version), and the package rows of `docker-compose.toml`, `harbor.toml`, `k3s.toml`, `rke2.toml`
- Modify: `CONTRIBUTING.md`, `docs-site/scripts/generate_reference.py`
- Regenerate: `docs-site/src/content/docs/reference/catalog/*.md`, `docs-site/src/content/docs/project/contributing.md`

**Interfaces:**
- Consumes: `catalog.validate_component(entry) -> list[Finding]`, `support.component(...)`.
- Produces: `constants.SCHEMA_VERSION = 1` (blueprint.json, unchanged), `constants.COMPONENT_SCHEMA_VERSION = 2`, `constants.PACKAGE_ARCHES = ("amd64", "arm64", "any")`; `catalog.is_https_url(value) -> bool`; findings `C5` (a row lacks `file`, `arch` or `url`, or `arch` is not one of the three) and `C6` (`url` or `checksums` is not a full `https://` URL; `checksums` may be `""`); `support.package(file, arch="amd64", checksums="") -> dict` with `url` `https://downloads.example.test/<file>`.

- [ ] **Step 1: Write the failing tests**

```diff
diff --git a/tests/support.py b/tests/support.py
--- a/tests/support.py
+++ b/tests/support.py
@@ -29,7 +29,7 @@ last_verified = 2026-11-20
 def component(component_id: str, layer: str, **overrides) -> dict:
     """A valid synthetic component entry. Dict overrides merge into sub-tables."""
     entry = {
-        "schema_version": 1,
+        "schema_version": 2,
         "id": component_id,
         "name": component_id.title(),
         "layer": layer,
@@ -71,6 +71,16 @@ def component(component_id: str, layer: str, **overrides) -> dict:
     return entry
 
 
+def package(file: str, arch: str = "amd64", checksums: str = "") -> dict:
+    """A valid synthetic package row, downloaded from example.test."""
+    return {
+        "file": file,
+        "arch": arch,
+        "url": f"https://downloads.example.test/{file}",
+        "checksums": checksums,
+    }
+
+
 def fixture_components() -> list[dict]:
     return [
         component("alpha-engine", "llm-serving"),
diff --git a/tests/test_catalog.py b/tests/test_catalog.py
--- a/tests/test_catalog.py
+++ b/tests/test_catalog.py
@@ -286,9 +286,76 @@ class ComponentValidationTest(unittest.TestCase):
         self.assertEqual(codes(findings), ["C1"])
         self.assertEqual(findings[0].message, "x: unknown key 'airgap.images[0].arch'")
 
-    def test_packages_take_no_hardware_key(self):
-        entry = support.component("x", "ui", airgap={"packages": [{"name": "a", "hardware": ["cpu"]}]})
-        self.assertIn("C1", codes(self.check(entry)))
+    def package_findings(self, *rows):
+        return self.check(support.component("x", "ui", airgap={"packages": list(rows)}))
+
+    def test_package_rows_are_accepted(self):
+        rows = (
+            support.package("x-1.0-amd64.tgz"),
+            support.package("x-1.0-arm64.tgz", "arm64", "https://downloads.example.test/SHA256SUMS"),
+            support.package("install.sh", "any"),
+        )
+        self.assertEqual(self.package_findings(*rows), [])
+
+    def test_packages_must_be_tables(self):
+        for packages in (["x-1.0-amd64.tgz"], "x.tgz", [support.package("a"), "b"]):
+            with self.subTest(packages=packages):
+                findings = self.check(support.component("x", "ui", airgap={"packages": packages}))
+                self.assertEqual(codes(findings), ["C1"])
+                self.assertEqual(
+                    findings[0].message,
+                    "x: airgap.packages must be a list of { file, arch, url, checksums } tables",
+                )
+
+    def test_unknown_package_key_is_c1(self):
+        row = dict(support.package("a"), hardware=["cpu"])
+        findings = self.package_findings(row)
+        self.assertEqual(codes(findings), ["C1"])
+        self.assertEqual(findings[0].message, "x: airgap.packages[0]: unknown key 'hardware'")
+
+    def test_c5_missing_fields(self):
+        row = support.package("a")
+        for key in ("file", "arch", "url"):
+            for value in (None, "", "  ", 3):
+                with self.subTest(key=key, value=value):
+                    broken = dict(row)
+                    if value is None:
+                        del broken[key]
+                    else:
+                        broken[key] = value
+                    findings = self.package_findings(broken)
+                    self.assertEqual(codes(findings), ["C5"])
+                    self.assertEqual(findings[0].message, f"x: airgap.packages[0] lacks {key}")
+
+    def test_c5_arch_outside_the_three_values(self):
+        findings = self.package_findings(support.package("a", "x86_64"))
+        self.assertEqual(codes(findings), ["C5"])
+        self.assertEqual(
+            findings[0].message, "x: airgap.packages[0].arch must be one of amd64, arm64, any"
+        )
+
+    def test_c6_url_must_be_full_https(self):
+        for url in ("http://downloads.example.test/a", "downloads.example.test/a", "https://localhost/a", "https://a b.test/x"):
+            with self.subTest(url=url):
+                findings = self.package_findings(dict(support.package("a"), url=url))
+                self.assertEqual(codes(findings), ["C6"])
+                self.assertEqual(findings[0].message, "x: airgap.packages[0].url must be a full https:// URL")
+
+    def test_c6_checksums_url_or_empty(self):
+        self.assertEqual(self.package_findings(support.package("a", checksums="")), [])
+        for checksums in ("md5sum", "ftp://downloads.example.test/md5sum", 5):
+            with self.subTest(checksums=checksums):
+                findings = self.package_findings(dict(support.package("a"), checksums=checksums))
+                self.assertEqual(codes(findings), ["C6"])
+                self.assertEqual(
+                    findings[0].message,
+                    "x: airgap.packages[0].checksums must be a full https:// URL or empty",
+                )
+
+    def test_schema_version_must_be_2(self):
+        findings = self.check(support.component("x", "ui", schema_version=1))
+        self.assertEqual(codes(findings), ["C1"])
+        self.assertEqual(findings[0].message, "x: schema_version must be 2")
 
     def test_unknown_layer_and_tier(self):
         self.assertIn("C1", codes(self.check(support.component("x", "no-such-layer"))))
diff --git a/tests/test_transfer.py b/tests/test_transfer.py
--- a/tests/test_transfer.py
+++ b/tests/test_transfer.py
@@ -37,7 +37,7 @@ class ManifestTest(unittest.TestCase):
                 "images": [
                     {"ref": "registry.example.test/synthetic/alpha-engine:1.2.3", "digest": "sha256:abc"}
                 ],
-                "packages": ["alpha-cli 1.2.3 binary"],
+                "packages": [support.package("alpha-cli-1.2.3-amd64", checksums="https://downloads.example.test/SHA256SUMS")],
                 "runtime_downloads": ["model weights"],
                 "telemetry": [{"what": "usage statistics", "disable": "ALPHA_TELEMETRY=0"}],
             },
@@ -74,7 +74,12 @@ class ManifestTest(unittest.TestCase):
 
     def test_other_tables_are_filled_from_the_catalog(self):
         self.assertIn("| example-70b | chat | weights, tokenizer and configuration files |  |", self.text)
-        self.assertIn("| alpha-engine | 1.2.3 | alpha-cli 1.2.3 binary |", self.text)
+        self.assertIn(
+            "| alpha-engine | 1.2.3 | alpha-cli-1.2.3-amd64 | amd64 "
+            "| https://downloads.example.test/alpha-cli-1.2.3-amd64 "
+            "| https://downloads.example.test/SHA256SUMS |",
+            self.text,
+        )
         self.assertIn("| alpha-engine | usage statistics | ALPHA_TELEMETRY=0 |", self.text)
         self.assertIn("| alpha-engine | model weights |", self.text)
         self.assertIn("| alpha-engine | example/skills | alpha-deployment |", self.text)
@@ -87,7 +92,7 @@ class ManifestTest(unittest.TestCase):
     def test_custom_components_are_listed_for_manual_work(self):
         self.blueprint["decisions"][2]["custom"] = ["in-house portal"]
         text = render_manifest(self.blueprint, self.catalog, "2026-11-20")
-        self.assertIn("| custom: in-house portal |  | enumerate artifacts manually |", text)
+        self.assertIn("| custom: in-house portal |  | enumerate artifacts manually |  |  |  |", text)
 
     def test_without_benchmark_nothing_is_marked(self):
         self.assertNotIn("benchmark only", self.text)
@@ -127,7 +132,7 @@ class BenchmarkManifestTest(unittest.TestCase):
                     {"ref": "registry.example.test/synthetic/beta-nv:1", "hardware": ["nvidia"]},
                     {"ref": "registry.example.test/synthetic/beta-intel:1", "hardware": ["intel"]},
                 ],
-                "packages": ["beta-cli binary"],
+                "packages": [support.package("beta-cli")],
                 "runtime_downloads": ["tokenizer data"],
                 "telemetry": [{"what": "beta usage ping", "disable": "BETA_PING=0"}],
             },
@@ -151,7 +156,7 @@ class BenchmarkManifestTest(unittest.TestCase):
             "| nvidia | ",
             text,
         )
-        self.assertIn(f"| {self.MARK} | 1.2.3 | beta-cli binary |", text)
+        self.assertIn(f"| {self.MARK} | 1.2.3 | beta-cli | amd64 | ", text)
         self.assertIn(f"| {self.MARK} | beta usage ping | BETA_PING=0 |", text)
         self.assertIn(f"| {self.MARK} | tokenizer data |", text)
         self.assertIn(f"| {self.MARK} | example/skills | beta-deployment |", text)
```

Add to `tests/test_real_catalog.py`, after the `V1_COMPONENTS` dictionary:

```python
# The entries with packages (design spec 2026-11-22, section 7).
PACKAGE_COMPONENTS = ("docker-compose", "harbor", "k3s", "rke2")
NO_ARM64 = "The release publishes no arm64 files."
```

and inside `ShippedCatalogTest`, before `test_gpu_rows_come_from_vendor_pages`:

```python
    def test_every_package_url_is_a_recorded_source(self):
        for cid, entry in self.catalog.components.items():
            sources = set(entry["evidence"]["sources"])
            for package in entry["airgap"].get("packages", []):
                with self.subTest(component=cid, file=package["file"]):
                    self.assertIn(package["url"], sources)
                    if package["checksums"]:
                        self.assertIn(package["checksums"], sources)

    def test_package_entries_carry_both_architectures(self):
        # An entry without arm64 rows says so in airgap.notes, in these words.
        for cid in PACKAGE_COMPONENTS:
            entry = self.catalog.components[cid]
            arches = {package["arch"] for package in entry["airgap"]["packages"]}
            with self.subTest(component=cid):
                self.assertIn("amd64", arches)
                if NO_ARM64 not in entry["airgap"].get("notes", ""):
                    self.assertIn("arm64", arches)
```

- [ ] **Step 2: Run them to see them fail**

Run: `python3.11 -m unittest discover -s tests -t .`

Expected: `FAILED` with about 80 failures (the scratch copy showed `failures=80` before `test_real_catalog` was extended): every fixture component now says `schema_version = 2` and the validator still wants 1, and the new C5/C6 tests fail.

- [ ] **Step 3: Validate package tables**

```diff
diff --git a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/catalog.py b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/catalog.py
--- a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/catalog.py
+++ b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/catalog.py
@@ -8,13 +8,21 @@ from dataclasses import dataclass
 from datetime import date, datetime
 from pathlib import Path
 
-from .constants import GPU_VENDORS, HARDWARE_CLASSES, LAYERS, SCHEMA_VERSION, TIERS
+from .constants import (
+    COMPONENT_SCHEMA_VERSION,
+    GPU_VENDORS,
+    HARDWARE_CLASSES,
+    LAYERS,
+    PACKAGE_ARCHES,
+    TIERS,
+)
 from .evidence import evidence_problems
 from .findings import Finding
 from .rules import Rules, load_rules, validate_rules
 
 _ID_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
 _PLACEHOLDER = re.compile(r"<[^<>]+>")
+_HTTPS_URL = re.compile(r"https://[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+(:[0-9]+)?(/\S*)?")
 
 _TOP_KEYS = {
     "schema_version", "id", "name", "layer", "summary", "tiers", "requires",
@@ -28,6 +36,7 @@ _AIRGAP_KEYS = {
 }
 _CHOOSE_KEYS = {"when", "avoid_when", "alternatives", "caveats"}
 _IMAGE_KEYS = {"ref", "digest", "hardware"}
+_PACKAGE_KEYS = {"file", "arch", "url", "checksums"}
 _GPU_KEYS = {
     "model", "aliases", "vendor", "vram_gb", "tdp_w", "evidence", "sources",
     "verified_by", "notes", "last_verified",
@@ -132,8 +141,8 @@ def validate_component(entry: dict, known_ids: set[str]) -> list[Finding]:
 
     for key in sorted(set(entry) - _TOP_KEYS):
         c1(f"unknown key '{key}'")
-    if entry.get("schema_version") != SCHEMA_VERSION:
-        c1(f"schema_version must be {SCHEMA_VERSION}")
+    if entry.get("schema_version") != COMPONENT_SCHEMA_VERSION:
+        c1(f"schema_version must be {COMPONENT_SCHEMA_VERSION}")
     if not isinstance(entry.get("id"), str) or not _ID_PATTERN.fullmatch(entry["id"]):
         c1("id must be lower-case words joined by hyphens")
     for key in ("name", "summary", "license", "version"):
@@ -201,9 +210,9 @@ def validate_component(entry: dict, known_ids: set[str]) -> list[Finding]:
                     f"airgap.images[{index}].hardware must be a non-empty list of: "
                     + ", ".join(HARDWARE_CLASSES)
                 )
-        for key in ("packages", "runtime_downloads"):
-            if not _strings(airgap.get(key)):
-                c1(f"airgap.{key} must be a list of strings")
+        findings += _package_findings(name, airgap.get("packages"))
+        if not _strings(airgap.get("runtime_downloads")):
+            c1("airgap.runtime_downloads must be a list of strings")
         telemetry = airgap.get("telemetry")
         if not isinstance(telemetry, list) or any(
             not isinstance(item, dict)
@@ -250,6 +259,46 @@ def validate_component(entry: dict, known_ids: set[str]) -> list[Finding]:
     return findings
 
 
+def is_https_url(value) -> bool:
+    """A full https:// URL: a host with a dot, no spaces."""
+    return isinstance(value, str) and _HTTPS_URL.fullmatch(value) is not None
+
+
+def _package_findings(name: str, packages) -> list[Finding]:
+    """C1 for the shape of airgap.packages, C5 for missing fields, C6 for URLs."""
+    if not isinstance(packages, list) or any(not isinstance(row, dict) for row in packages):
+        return [
+            Finding(
+                "C1",
+                f"{name}: airgap.packages must be a list of {{ file, arch, url, checksums }} tables",
+            )
+        ]
+    findings: list[Finding] = []
+    for index, row in enumerate(packages):
+        where = f"{name}: airgap.packages[{index}]"
+        for key in sorted(set(row) - _PACKAGE_KEYS):
+            findings.append(Finding("C1", f"{where}: unknown key '{key}'"))
+        missing = [
+            key
+            for key in ("file", "arch", "url")
+            if not isinstance(row.get(key), str) or not row[key].strip()
+        ]
+        if missing:
+            findings.append(Finding("C5", f"{where} lacks " + ", ".join(missing)))
+        if isinstance(row.get("arch"), str) and row["arch"].strip() and row["arch"] not in PACKAGE_ARCHES:
+            findings.append(
+                Finding("C5", f"{where}.arch must be one of " + ", ".join(PACKAGE_ARCHES))
+            )
+        if "url" not in missing and not is_https_url(row["url"]):
+            findings.append(Finding("C6", f"{where}.url must be a full https:// URL"))
+        checksums = row.get("checksums", "")
+        if not isinstance(checksums, str) or (checksums and not is_https_url(checksums)):
+            findings.append(
+                Finding("C6", f"{where}.checksums must be a full https:// URL or empty")
+            )
+    return findings
+
+
 def validate_gpus(gpus: list[dict]) -> list[Finding]:
     findings: list[Finding] = []
     first_use: dict[str, int] = {}
diff --git a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py
--- a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py
+++ b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py
@@ -3,7 +3,8 @@ from __future__ import annotations
 
 from collections.abc import Iterable
 
-SCHEMA_VERSION = 1
+SCHEMA_VERSION = 1  # blueprint.json
+COMPONENT_SCHEMA_VERSION = 2  # catalog component entries
 
 TIERS = ("T1", "T2", "T3")
 LAYERS = (
@@ -33,6 +34,8 @@ HARDWARE_CLASSES = GPU_VENDORS + ("cpu",)
 CPU_ARCHES = ("amd64", "arm64")
 INSIDE_OPERATORS = ("people", "local_agent", "people_then_agent")
 AGENT_OPERATORS = ("local_agent", "people_then_agent")
+# What a package row of a catalog entry is built for; "any" is architecture-free.
+PACKAGE_ARCHES = CPU_ARCHES + ("any",)
 
 # Requirements an escalator in rules.toml may switch on.
 ESCALATOR_REQUIREMENTS = (
```

- [ ] **Step 4: Read package tables in the manifest**

A stop-gap so that the suite stays green; Task 3 rewrites `transfer.py`.

```diff
diff --git a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/transfer.py b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/transfer.py
--- a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/transfer.py
+++ b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/transfer.py
@@ -116,7 +116,16 @@ def render_manifest(blueprint: dict, catalog: Catalog, generated: str) -> str:
                 ]
             )
         for package in airgap.get("packages", []):
-            packages.append([label, entry["version"], package])
+            packages.append(
+                [
+                    label,
+                    entry["version"],
+                    package["file"],
+                    package["arch"],
+                    package["url"],
+                    package.get("checksums", ""),
+                ]
+            )
         for item in airgap.get("telemetry", []):
             telemetry.append([label, item["what"], item["disable"]])
         for download in airgap.get("runtime_downloads", []):
@@ -124,7 +133,7 @@ def render_manifest(blueprint: dict, catalog: Catalog, generated: str) -> str:
         for skill in entry.get("deeper_skills", []):
             skills.append([label, skill["repo"], skill["skill"]])
     for name in custom:
-        packages.append([f"custom: {name}", "", "enumerate artifacts manually"])
+        packages.append([f"custom: {name}", "", "enumerate artifacts manually", "", "", ""])
 
     model_rows = [
         [
@@ -163,7 +172,7 @@ def render_manifest(blueprint: dict, catalog: Catalog, generated: str) -> str:
     lines += ["## 2. Model artifacts", ""]
     lines += _table(["Model", "Role", "Files to carry", "SHA-256"], model_rows)
     lines += ["## 3. Packages and binaries", ""]
-    lines += _table(["Component", "Version", "Artifact"], packages)
+    lines += _table(["Component", "Version", "File", "Arch", "URL", "Checksums"], packages)
     lines += ["## 4. Telemetry and egress settings to switch off before first start", ""]
     lines += _table(["Component", "What", "Setting"], telemetry)
     lines += ["## 5. Runtime downloads to stage in advance", ""]
```

- [ ] **Step 5: Show package tables on the catalog pages and in CONTRIBUTING**

````diff
diff --git a/CONTRIBUTING.md b/CONTRIBUTING.md
--- a/CONTRIBUTING.md
+++ b/CONTRIBUTING.md
@@ -28,7 +28,7 @@ An entry carries one label for the whole entry. Use `docs` only when the version
    | `version` | The latest stable release on the project's release page. That is the highest stable version, which is not always the release GitHub marks as latest: a project that patches an older line can publish that patch after a newer release. An exact version, never `latest`. When other entries list this component in `requires` and their documentation names the versions they support, pin the newest release that all of them support, and say why in `airgap.notes`. |
    | `license` | The SPDX identifier of the repository's license file. If the project has paid editions, say in `choose.caveats` which features need them. |
    | `airgap.images` | One row per image the official installation documentation names for a hardware class, with the tag of that exact version. Leave `digest` empty unless the publisher documents it. `hardware` lists the classes the image is for, drawn from `nvidia`, `amd`, `intel` and `cpu`; leave it out when the image is for any hardware. The transfer manifest lists only the rows that match the hardware in the blueprint. Do not list aliases of the same image (the same digest under another tag) or images that are only needed to build. |
-   | `airgap.packages` | Binaries, archives or packages the official offline or air-gap installation needs, named exactly as the release names them; the transfer manifest lists each one as something to carry. Name the files for linux/amd64 (x86_64) hosts and give the files for other architectures in `airgap.notes`. When the entry lists container images, list here only what the image route needs; other install routes (wheels, OS packages, tarballs) go into `airgap.notes`. |
+   | `airgap.packages` | One table per file that the official offline or air-gap installation needs: `file` exactly as the release names it; `arch`, one of `amd64`, `arm64` or `any` (scripts and archives that run on either); `url`, the download URL as the release page or the official documentation gives it, also recorded in `evidence.sources`; and `checksums`, the URL of the publisher's checksum file that lists this file, or `""` when the publisher has none (an md5 list counts). Give rows for `amd64` and, where the release publishes them, for `arm64`; the transfer manifest lists the rows for the blueprint's `hardware.cpu_arch` and the `any` rows. When the entry lists container images, list here only what the image route needs; other install routes (wheels, OS packages, tarballs) go into `airgap.notes`. Lint reports `C5` for a row without `file`, `arch` or `url`, or with another `arch`, and `C6` when `url` or a non-empty `checksums` is not a full `https://` URL. |
    | `airgap.runtime_downloads` | What the software fetches while it runs: models, plugins, update checks. |
    | `airgap.telemetry` | Each telemetry, analytics or update-check feature the documentation describes, with the documented setting that turns it off. If the documentation says nothing, leave the list empty and say so in `airgap.notes`. |
    | `airgap.license_server` | `true` when any license check needs network access. |
@@ -45,7 +45,7 @@ An entry carries one label for the whole entry. Use `docs` only when the version
 ### Template
 
 ```toml
-schema_version = 1
+schema_version = 2
 id = "<component id>"
 name = "<display name>"
 layer = "<llm-serving | llm-gateway | ui | identity | observability | orchestration | state | registry>"
@@ -64,7 +64,7 @@ notes = ""
 
 [airgap]
 images = [{ ref = "<registry/repository:tag>", digest = "" }]
-packages = []
+packages = [{ file = "<file name>", arch = "<amd64 | arm64 | any>", url = "<URL>", checksums = "" }]
 runtime_downloads = []
 telemetry = [{ what = "<what is sent>", disable = "<documented setting>" }]
 license_server = false
diff --git a/docs-site/scripts/generate_reference.py b/docs-site/scripts/generate_reference.py
--- a/docs-site/scripts/generate_reference.py
+++ b/docs-site/scripts/generate_reference.py
@@ -159,7 +159,11 @@ def component_page(entry: dict, order: int) -> str:
     else:
         out += "No container images.\n\n"
     if airgap.get("packages"):
-        out += "Packages:\n\n" + _list(airgap["packages"])
+        out += "Packages:\n\n| File | Architecture | Publisher checksums |\n|---|---|---|\n"
+        for package in airgap["packages"]:
+            checksums = f"[checksum file]({package['checksums']})" if package.get("checksums") else "none published"
+            out += f"| [`{package['file']}`]({package['url']}) | {package['arch']} | {checksums} |\n"
+        out += "\n"
     if airgap.get("runtime_downloads"):
         out += "### Downloads at run time\n\nWhat the software tries to fetch while it runs, and how to stage it instead.\n\n" + _list(airgap["runtime_downloads"])
     out += "### License server\n\n" + (
````

- [ ] **Step 6: Raise schema_version in every entry**

Run:

```bash
for f in plugins/airgap-anything/skills/airgap-architect/catalog/components/*.toml; do
  sed -i.bak 's/^schema_version = 1$/schema_version = 2/' "$f" && rm "$f.bak"
done
grep -c '^schema_version = 2$' plugins/airgap-anything/skills/airgap-architect/catalog/components/*.toml | grep -vc ':1$'
```

Expected: `0` (every file has exactly one `schema_version = 2` line).

- [ ] **Step 7: Fetch and record the package rows of the four entries**

Nothing in this step comes from memory, nor from the examples in §7. For each entry, in this order: `docker-compose.toml`, `harbor.toml`, `k3s.toml`, `rke2.toml`:

1. Read the entry's `version` and its `airgap.packages` (the file names it lists today) and `airgap.notes`.
2. Open the GitHub API release page that is already in its `evidence.sources`: `https://api.github.com/repos/<owner>/<repo>/releases/tags/<tag>`, with owner, repo and tag exactly as that source URL gives them (for example the k3s tag is URL-encoded, `v1.37.2%2Bk3s1`). From `assets`, take `name` and `browser_download_url`.
3. Write one row per file the entry lists today, with `file` = the asset `name`, `url` = its `browser_download_url`, and `arch` = `amd64`, `arm64` or `any` as the asset name says (a script or a file for every platform is `any`). A listed file that is not a release asset (for example a script served from another host) keeps the URL the entry's sources give for it; when no source gives one, stop and report.
4. Add the arm64 counterpart of every `amd64` row when the release has that asset; the names are on the same API page. When the release has no arm64 assets at all, add no rows and append `The release publishes no arm64 files.` to `airgap.notes`.
5. `checksums`: when the release has a checksum asset (a file such as an `md5sum` or `sha256sum-<arch>.txt` list), open it and check that it lists the row's `file` by name; then set `checksums` to that asset's `browser_download_url`. Otherwise `""`. A checksum list that the install itself needs (for example the rke2 one that `install.sh` reads) stays a package row too.
6. Add every `url` and `checksums` value to `evidence.sources`, set `last_verified` to today, and add one sentence to `evidence.notes`: "Package rows (file, arch, url, checksums) were read on DATE from the GitHub API release page in sources."

The row format, one table per line:

```toml
packages = [
  { file = "<asset name>", arch = "<amd64 | arm64 | any>", url = "<browser_download_url>", checksums = "<checksum asset URL or empty>" },
]
```

- [ ] **Step 8: Run catalog lint, regenerate the pages, run the suite**

Run:

```bash
python3 plugins/airgap-anything/skills/airgap-architect/scripts/lint.py --catalog-only
python3 docs-site/scripts/generate_reference.py
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
```

Expected: `OK: no findings`, `wrote 25 pages and 5 images`, and `OK` on both interpreters. The catalog pages of the four entries now show `| File | Architecture | Publisher checksums |` tables.

- [ ] **Step 9: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py \
  plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/catalog.py \
  plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/transfer.py \
  plugins/airgap-anything/skills/airgap-architect/catalog/components \
  tests/support.py tests/test_catalog.py tests/test_transfer.py tests/test_real_catalog.py \
  CONTRIBUTING.md docs-site/scripts/generate_reference.py \
  docs-site/src/content/docs/reference/catalog docs-site/src/content/docs/project/contributing.md
git commit -m "feat(catalog): package rows with architecture, URL and publisher checksums

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: The manifest by architecture, as Markdown and JSON, under E8

§6.3, §6.4. `transfer.py` builds the manifest once as data and renders it twice. Package rows are filtered by `hardware.cpu_arch` (an `any` row always stays), the header gains a Platform line, the digest covers `cpu_arch`, and E8 checks both files.

**Files:**
- Modify (rewrite): `plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/transfer.py`
- Modify: `plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/blueprint.py`, `checks.py`, `scripts/manifest.py`
- Modify: `tests/projects.py`, `tests/test_blueprint.py`, `tests/test_checks.py`, `tests/test_cli.py`, `tests/test_transfer.py`

**Interfaces:**
- Consumes: `blueprint.inputs_digest(blueprint, catalog)`, `rules.default_answer`, `checks.lint_blueprint`, `checks.lint_project`.
- Produces:
  - `transfer.MANIFEST_JSON_FILENAME = "transfer-manifest.json"`, `transfer.MANIFEST_JSON_SCHEMA_VERSION = 1`
  - `transfer.cpu_arch(answers, catalog) -> str | None`: the answer, or the rules default for `unknown`; `None` when missing or invalid
  - `transfer.build_manifest(blueprint, catalog, generated) -> dict` with keys, in order: `schema_version`, `project`, `generated`, `inputs_digest`, `hardware_class` (`""` when unknown), `platform` (`"linux/<arch>"` or `""`), `images`, `models`, `packages`, `custom`, `telemetry`, `runtime_downloads`, `skills`, `missing_variants`
  - rows: image `{component, version, ref, hardware, digest, target, license, benchmark}`, package `{component, version, file, arch, url, checksums, license, benchmark}`, model `{name, role}`, custom `{layer, name}`; telemetry, runtime-download and skill rows carry `benchmark`
  - `transfer.render_markdown(data) -> str`, `transfer.render_json(data) -> str`, `transfer.render_manifest(blueprint, catalog, generated) -> str` (kept, Markdown), `transfer.read_manifest_json_digest(text) -> str | None`
  - `checks.lint_blueprint(..., manifest_json_text=None)`; E8 messages `transfer-manifest.json not found; run manifest.py`, `transfer-manifest.json is stale; run manifest.py again`, `transfer-manifest.json cannot be read: it is not valid UTF-8` (and the same three for the `.md` file)
  - `projects.write_manifests(blueprint_path, catalog, blueprint)` in the test helpers
  - `manifest.py` writes `transfer-manifest.md` and `transfer-manifest.json` side by side and prints `Wrote <path>` for each

- [ ] **Step 1: Write the failing tests**

```diff
diff --git a/tests/projects.py b/tests/projects.py
--- a/tests/projects.py
+++ b/tests/projects.py
@@ -15,7 +15,13 @@ from airgap_lib.constants import (
 )
 from airgap_lib.sizing import compute_sizing
 from airgap_lib.tiering import compute_tier
-from airgap_lib.transfer import MANIFEST_FILENAME, render_manifest
+from airgap_lib.transfer import (
+    MANIFEST_FILENAME,
+    MANIFEST_JSON_FILENAME,
+    build_manifest,
+    render_json,
+    render_markdown,
+)
 from tests import support
 
 AGENTS_TEXT = f"{AGENT_BLOCK_START}\nFollow the blueprint.\n{AGENT_BLOCK_END}\n"
@@ -67,13 +73,19 @@ def write_project(root: Path, catalog: Catalog, blueprint: dict, verification: s
     (path.parent / "blueprint.md").write_text(
         blueprint_markdown(blueprint, catalog, verification, isolation), encoding="utf-8"
     )
-    (path.parent / MANIFEST_FILENAME).write_text(
-        render_manifest(blueprint, catalog, "2026-11-20"), encoding="utf-8"
-    )
+    write_manifests(path, catalog, blueprint)
     (root / "AGENTS.md").write_text(AGENTS_TEXT, encoding="utf-8")
     return path
 
 
+def write_manifests(blueprint_path: Path, catalog: Catalog, blueprint: dict) -> None:
+    """Write transfer-manifest.md and .json next to blueprint.json, as manifest.py does."""
+    data = build_manifest(blueprint, catalog, "2026-11-20")
+    folder = Path(blueprint_path).parent
+    (folder / MANIFEST_FILENAME).write_text(render_markdown(data), encoding="utf-8")
+    (folder / MANIFEST_JSON_FILENAME).write_text(render_json(data), encoding="utf-8")
+
+
 def make_project(root: Path, catalog: Catalog, answers=None, decisions=None, verification: str = "", isolation: bool = False) -> Path:
     blueprint = build_blueprint(catalog, answers, decisions)
     return write_project(root, catalog, blueprint, verification, isolation)
diff --git a/tests/test_blueprint.py b/tests/test_blueprint.py
--- a/tests/test_blueprint.py
+++ b/tests/test_blueprint.py
@@ -249,6 +249,20 @@ class DigestTest(unittest.TestCase):
         self.data["decisions"][0]["benchmark"] = ["beta-engine", "gamma-engine"]
         self.assertNotEqual(with_benchmark, inputs_digest(self.data))
 
+    def test_digest_changes_with_cpu_arch(self):
+        before = inputs_digest(self.data)
+        self.data["answers"]["hardware.cpu_arch"] = "amd64"
+        amd64 = inputs_digest(self.data)
+        self.assertNotEqual(before, amd64)
+        self.data["answers"]["hardware.cpu_arch"] = "arm64"
+        self.assertNotEqual(amd64, inputs_digest(self.data))
+
+    def test_digest_ignores_other_answers(self):
+        before = inputs_digest(self.data)
+        self.data["answers"]["inside.operator"] = "local_agent"
+        self.data["answers"]["transfer.channel"] = "data_diode"
+        self.assertEqual(before, inputs_digest(self.data))
+
     def test_digest_ignores_other_keys(self):
         before = inputs_digest(self.data)
         self.data["project"] = "renamed"
diff --git a/tests/test_checks.py b/tests/test_checks.py
--- a/tests/test_checks.py
+++ b/tests/test_checks.py
@@ -6,7 +6,7 @@ from pathlib import Path
 from tests import projects, support
 from airgap_lib.checks import lint_project, split_sections
 from airgap_lib.constants import SECTION_MARKERS, section_marker
-from airgap_lib.transfer import MANIFEST_FILENAME, render_manifest
+from airgap_lib.transfer import MANIFEST_FILENAME, MANIFEST_JSON_FILENAME
 
 
 class LintTestCase(unittest.TestCase):
@@ -31,9 +31,7 @@ class LintTestCase(unittest.TestCase):
     def edit(self, change, refresh_manifest=True):
         data = projects.edit_blueprint(self.path, change)
         if refresh_manifest:
-            (self.path.parent / MANIFEST_FILENAME).write_text(
-                render_manifest(data, self.catalog, "2026-11-20"), encoding="utf-8"
-            )
+            projects.write_manifests(self.path, self.catalog, data)
         return data
 
     def decision(self, data, layer):
@@ -187,9 +185,26 @@ class ErrorRulesTest(LintTestCase):
             lambda data: self.decision(data, "ui").update(rationale="Changed."),
             refresh_manifest=False,
         )
-        self.assertEqual(self.codes(), ["E8"])
+        self.assertEqual(self.codes(), ["E8", "E8"])
         (self.path.parent / MANIFEST_FILENAME).unlink()
-        self.assertEqual(self.codes(), ["E8"])
+        (self.path.parent / MANIFEST_JSON_FILENAME).unlink()
+        self.assertEqual(self.codes(), ["E8", "E8"])
+
+    def test_e8_checks_each_file_on_its_own(self):
+        self.project()
+        (self.path.parent / MANIFEST_JSON_FILENAME).unlink()
+        findings = self.lint()
+        self.assertEqual([f.code for f in findings], ["E8"])
+        self.assertEqual(findings[0].message, "transfer-manifest.json not found; run manifest.py")
+        self.project()
+        (self.path.parent / MANIFEST_JSON_FILENAME).write_text('{"inputs_digest": "sha256:old"}', encoding="utf-8")
+        findings = self.lint()
+        self.assertEqual([f.message for f in findings], ["transfer-manifest.json is stale; run manifest.py again"])
+
+    def test_e8_a_changed_cpu_arch_makes_both_files_stale(self):
+        self.project()
+        self.edit(lambda data: data["answers"].update({"hardware.cpu_arch": "arm64"}), refresh_manifest=False)
+        self.assertEqual(self.codes(), ["E8", "E8"])
 
     def test_e9_estimate_decision_must_be_listed(self):
         decisions = support.base_decisions()
@@ -428,11 +443,13 @@ class UnreadableFilesTest(LintTestCase):
         self.assertNotIn("not found", findings[0].message)
 
     def test_non_utf8_manifest_is_an_e8_finding(self):
-        self.project()
-        (self.path.parent / MANIFEST_FILENAME).write_bytes(b"\xff\xfe\x00bad")
-        findings = self.lint()
-        self.assertEqual([f.code for f in findings], ["E8"])
-        self.assertIn("cannot be read", findings[0].message)
+        for name in (MANIFEST_FILENAME, MANIFEST_JSON_FILENAME):
+            with self.subTest(name=name):
+                self.project()
+                (self.path.parent / name).write_bytes(b"\xff\xfe\x00bad")
+                findings = self.lint()
+                self.assertEqual([f.code for f in findings], ["E8"])
+                self.assertEqual(findings[0].message, f"{name} cannot be read: it is not valid UTF-8")
 
     def test_blueprint_path_below_a_regular_file(self):
         self.project()
diff --git a/tests/test_cli.py b/tests/test_cli.py
--- a/tests/test_cli.py
+++ b/tests/test_cli.py
@@ -11,7 +11,7 @@ from pathlib import Path
 from tests import SCRIPTS_DIR, projects, support
 from airgap_lib.blueprint import load_blueprint, save_blueprint
 from airgap_lib.catalog import load_catalog
-from airgap_lib.transfer import MANIFEST_FILENAME
+from airgap_lib.transfer import MANIFEST_FILENAME, MANIFEST_JSON_FILENAME
 
 
 class CliTestCase(unittest.TestCase):
@@ -78,6 +78,11 @@ class PipelineTest(CliTestCase):
         manifest = self.with_blueprint("manifest.py", "--date", "2026-11-20")
         self.assertEqual(manifest.returncode, 0, manifest.stderr)
         self.assertTrue((self.blueprint.parent / MANIFEST_FILENAME).is_file())
+        self.assertTrue((self.blueprint.parent / MANIFEST_JSON_FILENAME).is_file())
+        self.assertEqual(
+            manifest.stdout.splitlines(),
+            [f"Wrote {self.blueprint.parent / MANIFEST_FILENAME}", f"Wrote {self.blueprint.parent / MANIFEST_JSON_FILENAME}"],
+        )
 
         catalog, _ = load_catalog(self.catalog_dir)
         (self.blueprint.parent / "blueprint.md").write_text(
@@ -250,6 +255,7 @@ class ManifestCliTest(CliTestCase):
         result = self.with_blueprint("manifest.py", "--out", str(target))
         self.assertEqual(result.returncode, 0, result.stderr)
         self.assertTrue(target.is_file())
+        self.assertTrue((target.parent / MANIFEST_JSON_FILENAME).is_file())
 
     def test_answers_that_are_not_an_object_exit_2_as_in_tier_and_size(self):
         for value in (["chat"], "chat", 5, [], None):
diff --git a/tests/test_transfer.py b/tests/test_transfer.py
--- a/tests/test_transfer.py
+++ b/tests/test_transfer.py
@@ -1,3 +1,4 @@
+import json
 import tempfile
 import unittest
 from pathlib import Path
@@ -5,9 +6,14 @@ from pathlib import Path
 from tests import support
 from airgap_lib.blueprint import inputs_digest
 from airgap_lib.transfer import (
+    MANIFEST_JSON_SCHEMA_VERSION,
     UnknownComponentError,
+    build_manifest,
     read_manifest_digest,
+    read_manifest_json_digest,
+    render_json,
     render_manifest,
+    render_markdown,
     split_image_ref,
 )
 
@@ -56,10 +62,11 @@ class ManifestTest(unittest.TestCase):
         self.assertIn("- Generated: 2026-11-20", self.text)
         self.assertEqual(read_manifest_digest(self.text), inputs_digest(self.blueprint))
 
-    def test_hardware_line_follows_the_digest_line(self):
+    def test_hardware_and_platform_lines_follow_the_digest_line(self):
         lines = self.text.splitlines()
         digest_at = next(i for i, line in enumerate(lines) if line.startswith("- Decisions digest: "))
         self.assertEqual(lines[digest_at + 1], "- Hardware: nvidia")
+        self.assertEqual(lines[digest_at + 2], "- Platform: linux/amd64")
 
     def test_seven_sections_in_order(self):
         headings = [line for line in self.text.splitlines() if line.startswith("## ")]
@@ -335,5 +342,178 @@ class HardwareManifestTest(unittest.TestCase):
         self.assertEqual(read_manifest_digest(text), inputs_digest(blueprint))
 
 
+class ArchitectureManifestTest(unittest.TestCase):
+    """Package rows follow hardware.cpu_arch; `any` rows always come along."""
+
+    def setUp(self):
+        self.tmp = tempfile.TemporaryDirectory()
+        self.addCleanup(self.tmp.cleanup)
+        self.catalog = self.catalog_with(
+            [
+                support.package("alpha-1.2.3-amd64.tgz", "amd64"),
+                support.package("alpha-1.2.3-arm64.tgz", "arm64"),
+                support.package("install.sh", "any"),
+            ]
+        )
+
+    def catalog_with(self, packages):
+        components = support.fixture_components()
+        components[0] = support.component("alpha-engine", "llm-serving", airgap={"packages": packages})
+        root = Path(self.tmp.name) / f"catalog{len(list(Path(self.tmp.name).iterdir()))}"
+        return support.load_fixture_catalog(root, components)
+
+    def blueprint(self, arch):
+        answers = support.base_answers()
+        if arch is None:
+            del answers["hardware.cpu_arch"]
+        else:
+            answers["hardware.cpu_arch"] = arch
+        return {"project": "example", "answers": answers, "decisions": support.base_decisions()}
+
+    def files(self, arch, catalog=None):
+        data = build_manifest(self.blueprint(arch), catalog or self.catalog, "2026-11-20")
+        return [row["file"] for row in data["packages"]]
+
+    def test_amd64_takes_amd64_and_any_rows(self):
+        self.assertEqual(self.files("amd64"), ["alpha-1.2.3-amd64.tgz", "install.sh"])
+
+    def test_arm64_takes_arm64_and_any_rows(self):
+        self.assertEqual(self.files("arm64"), ["alpha-1.2.3-arm64.tgz", "install.sh"])
+
+    def test_unknown_takes_the_default_from_rules(self):
+        self.assertEqual(self.files("unknown"), ["alpha-1.2.3-amd64.tgz", "install.sh"])
+        text = render_manifest(self.blueprint("unknown"), self.catalog, "2026-11-20")
+        self.assertIn("- Platform: linux/amd64", text)
+
+    def test_unanswered_lists_every_row_and_says_so(self):
+        for arch in (None, "sparc"):
+            with self.subTest(arch=arch):
+                self.assertEqual(len(self.files(arch)), 3)
+                text = render_manifest(self.blueprint(arch), self.catalog, "2026-11-20")
+                self.assertIn(
+                    "- Platform: unknown; carry only the package rows for your CPU architecture", text
+                )
+                self.assertEqual(build_manifest(self.blueprint(arch), self.catalog, "2026-11-20")["platform"], "")
+
+    def test_a_component_without_rows_for_the_platform_gets_a_line(self):
+        catalog = self.catalog_with([support.package("alpha-1.2.3-amd64.tgz", "amd64")])
+        self.assertEqual(self.files("arm64", catalog), [])
+        text = render_manifest(self.blueprint("arm64"), catalog, "2026-11-20")
+        line = "- alpha-engine: the catalog lists no package for linux/arm64; check the entry's notes before carrying."
+        self.assertIn(line, text)
+        # The line sits right after the packages table, before section 4.
+        self.assertTrue(text.split("## 4. ")[0].rstrip().endswith("before carrying."))
+
+    def test_package_row_columns(self):
+        text = render_manifest(self.blueprint("arm64"), self.catalog, "2026-11-20")
+        self.assertIn("| Component | Version | File | Arch | URL | Checksums |", text)
+        self.assertIn(
+            "| alpha-engine | 1.2.3 | alpha-1.2.3-arm64.tgz | arm64 "
+            "| https://downloads.example.test/alpha-1.2.3-arm64.tgz |  |",
+            text,
+        )
+
+
+class ManifestJsonTest(unittest.TestCase):
+    def setUp(self):
+        self.tmp = tempfile.TemporaryDirectory()
+        self.addCleanup(self.tmp.cleanup)
+        components = support.fixture_components()
+        components[0] = support.component(
+            "alpha-engine",
+            "llm-serving",
+            airgap={
+                "images": [{"ref": "registry.example.test/synthetic/alpha:1", "digest": "", "hardware": ["nvidia"]}],
+                "packages": [support.package("alpha-cli", "amd64", "https://downloads.example.test/SUMS")],
+                "runtime_downloads": ["tokenizer data"],
+                "telemetry": [{"what": "usage ping", "disable": "ALPHA_PING=0"}],
+            },
+            deeper_skills=[{"repo": "example/skills", "skill": "alpha-deployment"}],
+        )
+        self.catalog = support.load_fixture_catalog(Path(self.tmp.name), components)
+        self.blueprint = {
+            "project": "example",
+            "answers": support.base_answers(),
+            "decisions": support.base_decisions(),
+        }
+        self.blueprint["decisions"][0]["benchmark"] = ["beta-engine"]
+        self.blueprint["decisions"][5]["custom"] = ["Docker Engine (outside the catalog)"]
+        self.data = build_manifest(self.blueprint, self.catalog, "2026-11-20")
+
+    def test_top_level_keys_of_schema_version_1(self):
+        self.assertEqual(
+            list(self.data),
+            [
+                "schema_version", "project", "generated", "inputs_digest", "hardware_class",
+                "platform", "images", "models", "packages", "custom", "telemetry",
+                "runtime_downloads", "skills", "missing_variants",
+            ],
+        )
+        self.assertEqual(self.data["schema_version"], MANIFEST_JSON_SCHEMA_VERSION)
+        self.assertEqual(self.data["schema_version"], 1)
+        self.assertEqual(self.data["inputs_digest"], inputs_digest(self.blueprint))
+        self.assertEqual((self.data["hardware_class"], self.data["platform"]), ("nvidia", "linux/amd64"))
+
+    def test_rows(self):
+        self.assertEqual(
+            self.data["images"][0],
+            {
+                "component": "alpha-engine",
+                "version": "1.2.3",
+                "ref": "registry.example.test/synthetic/alpha:1",
+                "hardware": ["nvidia"],
+                "digest": "",
+                "target": "REGISTRY_HOST/synthetic/alpha:1",
+                "license": "MIT",
+                "benchmark": False,
+            },
+        )
+        self.assertEqual(
+            self.data["packages"],
+            [
+                {
+                    "component": "alpha-engine",
+                    "version": "1.2.3",
+                    "file": "alpha-cli",
+                    "arch": "amd64",
+                    "url": "https://downloads.example.test/alpha-cli",
+                    "checksums": "https://downloads.example.test/SUMS",
+                    "license": "MIT",
+                    "benchmark": False,
+                }
+            ],
+        )
+        self.assertEqual(self.data["models"], [{"name": "example-70b", "role": "chat"}])
+        self.assertEqual(self.data["custom"], [{"layer": "orchestration", "name": "Docker Engine (outside the catalog)"}])
+        self.assertEqual(
+            self.data["runtime_downloads"],
+            [{"component": "alpha-engine", "text": "tokenizer data", "benchmark": False}],
+        )
+        self.assertEqual(
+            self.data["skills"],
+            [{"component": "alpha-engine", "repo": "example/skills", "skill": "alpha-deployment", "benchmark": False}],
+        )
+
+    def test_benchmark_rows_are_flagged(self):
+        beta = [row for row in self.data["images"] if row["component"] == "beta-engine"]
+        self.assertEqual([row["benchmark"] for row in beta], [True])
+
+    def test_an_image_for_any_hardware_has_an_empty_list(self):
+        gamma = next(row for row in self.data["images"] if row["component"] == "gamma-gateway")
+        self.assertEqual(gamma["hardware"], [])
+
+    def test_markdown_and_json_come_from_the_same_rows(self):
+        self.assertEqual(render_markdown(self.data), render_manifest(self.blueprint, self.catalog, "2026-11-20"))
+        text = render_json(self.data)
+        self.assertTrue(text.endswith("}\n"))
+        self.assertEqual(json.loads(text), self.data)
+        self.assertEqual(read_manifest_json_digest(text), inputs_digest(self.blueprint))
+
+    def test_json_digest_reader_tolerates_other_text(self):
+        for text in ("", "not json", "[]", '{"inputs_digest": 5}'):
+            with self.subTest(text=text):
+                self.assertIsNone(read_manifest_json_digest(text))
+
+
 if __name__ == "__main__":
     unittest.main()
```

- [ ] **Step 2: Run them to see them fail**

Run: `python3.11 -m unittest discover -s tests -t .`

Expected: `FAILED (failures=1, errors=3)`: `tests.test_checks`, `tests.test_cli` and `tests.test_transfer` cannot import (`MANIFEST_JSON_FILENAME`, `write_manifests`, `build_manifest`), and `test_digest_changes_with_cpu_arch` fails.

- [ ] **Step 3: Rewrite transfer.py**

Replace the whole file with:

```python
"""The transfer manifest: everything that has to be carried into the network.

`build_manifest` collects the rows once; `render_markdown` and `render_json` write the
same rows as transfer-manifest.md, for people, and transfer-manifest.json, for the
airgap-transfer skill, which reads the JSON file and never imports this package.
"""
from __future__ import annotations

import json

from .blueprint import benchmark_components, chosen_components, decisions_of, inputs_digest
from .catalog import Catalog
from .constants import CPU_ARCHES, GPU_VENDORS
from .sizing import SizingInputError, pick_primary_gpu

MANIFEST_FILENAME = "transfer-manifest.md"
MANIFEST_JSON_FILENAME = "transfer-manifest.json"
MANIFEST_JSON_SCHEMA_VERSION = 1
DIGEST_PREFIX = "- Decisions digest: "
REGISTRY_TOKEN = "REGISTRY_HOST"
BENCHMARK_MARK = " (benchmark only)"


class UnknownComponentError(Exception):
    def __init__(self, component_ids: list[str]):
        super().__init__("unknown component(s): " + ", ".join(component_ids))
        self.component_ids = list(component_ids)


def split_image_ref(ref: str) -> tuple[str, str]:
    """Split 'registry.example/repo/name:tag' into (registry, 'repo/name:tag')."""
    first, slash, rest = ref.partition("/")
    if slash and ("." in first or ":" in first or first == "localhost"):
        return first, rest
    return "", ref


def read_manifest_digest(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(DIGEST_PREFIX):
            return line[len(DIGEST_PREFIX):].strip()
    return None


def read_manifest_json_digest(text: str) -> str | None:
    """The inputs digest recorded in transfer-manifest.json, or None."""
    try:
        data = json.loads(text)
    except (ValueError, RecursionError):
        return None
    digest = data.get("inputs_digest") if isinstance(data, dict) else None
    return digest if isinstance(digest, str) else None


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    if not rows:
        return ["None.", ""]
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(_cell(cell) for cell in row) + " |" for row in rows]
    lines.append("")
    return lines


def hardware_class(answers: dict, catalog: Catalog) -> str | None:
    """'cpu' without GPUs, else the vendor of the primary GPU; None when unknown."""
    entries = (answers or {}).get("hardware.gpus")
    if not isinstance(entries, list):
        return None
    if not entries:
        return "cpu"
    try:
        primary = pick_primary_gpu(entries, catalog.gpu)
    except (SizingInputError, KeyError, TypeError):
        return None
    if primary is None:
        return None
    for entry in entries:
        if entry["model"] == primary["model"] and entry["count"] == primary["count"]:
            if entry.get("vendor") in GPU_VENDORS:
                return entry["vendor"]
            break
    row = catalog.gpu(primary["model"]) or {}
    return row.get("vendor") if row.get("vendor") in GPU_VENDORS else None


def cpu_arch(answers: dict, catalog: Catalog) -> str | None:
    """The answer to hardware.cpu_arch; for 'unknown' the default in rules.toml.

    None when the question is unanswered or holds something else, so that the
    manifest lists every package row instead of guessing.
    """
    value = (answers or {}).get("hardware.cpu_arch")
    if value == "unknown":
        default = catalog.rules.default_answer("hardware.cpu_arch")
        value = default.get("value") if default else None
    return value if value in CPU_ARCHES else None


def _for_hardware(image: dict, hardware: str | None) -> bool:
    return hardware is None or "hardware" not in image or hardware in image["hardware"]


def _for_arch(package: dict, arch: str | None) -> bool:
    return arch is None or package["arch"] in (arch, "any")


def build_manifest(blueprint: dict, catalog: Catalog, generated: str) -> dict:
    """Every row of the manifest, in the shape of transfer-manifest.json."""
    chosen_ids = chosen_components(blueprint)
    benchmark_ids = benchmark_components(blueprint)
    unknown = [cid for cid in chosen_ids + benchmark_ids if cid not in catalog.components]
    if unknown:
        raise UnknownComponentError(unknown)
    entries = [(catalog.components[cid], False) for cid in chosen_ids]
    entries += [(catalog.components[cid], True) for cid in benchmark_ids]
    answers = blueprint.get("answers")
    hardware = hardware_class(answers, catalog)
    arch = cpu_arch(answers, catalog)

    data = {
        "schema_version": MANIFEST_JSON_SCHEMA_VERSION,
        "project": blueprint.get("project", ""),
        "generated": generated,
        "inputs_digest": inputs_digest(blueprint),
        "hardware_class": hardware or "",
        "platform": f"linux/{arch}" if arch else "",
        "images": [],
        "models": [],
        "packages": [],
        "custom": [],
        "telemetry": [],
        "runtime_downloads": [],
        "skills": [],
        "missing_variants": [],
    }
    for entry, benchmark in entries:
        cid = entry["id"]
        label = cid + (BENCHMARK_MARK if benchmark else "")
        airgap = entry.get("airgap", {})
        component_images = airgap.get("images", [])
        wanted = [image for image in component_images if _for_hardware(image, hardware)]
        if component_images and not wanted:
            data["missing_variants"].append(
                f"{label}: the catalog lists no image for {hardware} hardware; "
                "check the entry's notes before carrying."
            )
        for image in wanted:
            _, remainder = split_image_ref(image["ref"])
            data["images"].append(
                {
                    "component": cid,
                    "version": entry["version"],
                    "ref": image["ref"],
                    "hardware": list(image.get("hardware", [])),
                    "digest": image.get("digest", ""),
                    "target": f"{REGISTRY_TOKEN}/{remainder}",
                    "license": entry["license"],
                    "benchmark": benchmark,
                }
            )
        component_packages = airgap.get("packages", [])
        packages = [package for package in component_packages if _for_arch(package, arch)]
        if component_packages and not packages:
            data["missing_variants"].append(
                f"{label}: the catalog lists no package for linux/{arch}; "
                "check the entry's notes before carrying."
            )
        for package in packages:
            data["packages"].append(
                {
                    "component": cid,
                    "version": entry["version"],
                    "file": package["file"],
                    "arch": package["arch"],
                    "url": package["url"],
                    "checksums": package.get("checksums", ""),
                    "license": entry["license"],
                    "benchmark": benchmark,
                }
            )
        for item in airgap.get("telemetry", []):
            data["telemetry"].append(
                {"component": cid, "what": item["what"], "disable": item["disable"], "benchmark": benchmark}
            )
        for download in airgap.get("runtime_downloads", []):
            data["runtime_downloads"].append({"component": cid, "text": download, "benchmark": benchmark})
        for skill in entry.get("deeper_skills", []):
            data["skills"].append(
                {"component": cid, "repo": skill["repo"], "skill": skill["skill"], "benchmark": benchmark}
            )
    for decision in decisions_of(blueprint):
        for name in decision.get("custom") or []:
            data["custom"].append({"layer": decision.get("layer", ""), "name": name})
    models = ((answers or {}).get("workload.models") if isinstance(answers, dict) else None) or []
    for index, model in enumerate(models if isinstance(models, list) else []):
        if isinstance(model, dict):
            data["models"].append(
                {"name": model.get("name") or f"model {index + 1}", "role": model.get("role", "")}
            )
    return data


def _label(row: dict) -> str:
    return row["component"] + (BENCHMARK_MARK if row.get("benchmark") else "")


def render_markdown(data: dict) -> str:
    """transfer-manifest.md from the rows of build_manifest."""
    arch = data["platform"]
    lines = [
        f"# Transfer manifest: {data['project']}",
        "",
        f"- Generated: {data['generated']}",
        f"{DIGEST_PREFIX}{data['inputs_digest']}",
        "- Hardware: "
        + (data["hardware_class"] or "unknown; carry only the image rows for your hardware"),
        "- Platform: "
        + (arch or "unknown; carry only the package rows for your CPU architecture"),
        "",
        "Fill the digest, size and checksum columns when you pull each artifact, or let the "
        "airgap-transfer skill do it from transfer-manifest.json. "
        f"Replace `{REGISTRY_TOKEN}` with the address of the registry inside the network.",
        "",
        "## 1. Container images",
        "",
    ]
    images = [
        [
            _label(row),
            row["version"],
            row["ref"],
            ", ".join(row["hardware"]) or "any",
            row["digest"],
            "",
            row["target"],
        ]
        for row in data["images"]
    ]
    lines += _table(["Component", "Version", "Image", "For", "Digest", "Size", "Target path"], images)
    image_gaps = [line for line in data["missing_variants"] if "lists no image for" in line]
    if image_gaps:
        lines += [f"- {line}" for line in image_gaps] + [""]
    lines += ["## 2. Model artifacts", ""]
    lines += _table(
        ["Model", "Role", "Files to carry", "SHA-256"],
        [[row["name"], row["role"], "weights, tokenizer and configuration files", ""] for row in data["models"]],
    )
    lines += ["## 3. Packages and binaries", ""]
    packages = [
        [_label(row), row["version"], row["file"], row["arch"], row["url"], row["checksums"]]
        for row in data["packages"]
    ]
    packages += [
        [f"custom: {row['name']}", "", "enumerate artifacts manually", "", "", ""] for row in data["custom"]
    ]
    lines += _table(["Component", "Version", "File", "Arch", "URL", "Checksums"], packages)
    package_gaps = [line for line in data["missing_variants"] if "lists no package for" in line]
    if package_gaps:
        lines += [f"- {line}" for line in package_gaps] + [""]
    lines += ["## 4. Telemetry and egress settings to switch off before first start", ""]
    lines += _table(
        ["Component", "What", "Setting"],
        [[_label(row), row["what"], row["disable"]] for row in data["telemetry"]],
    )
    lines += ["## 5. Runtime downloads to stage in advance", ""]
    lines += _table(["Component", "Download"], [[_label(row), row["text"]] for row in data["runtime_downloads"]])
    lines += ["## 6. Per-tool skills worth carrying inside", ""]
    lines += _table(
        ["Component", "Repository", "Skill"],
        [[_label(row), row["repo"], row["skill"]] for row in data["skills"]],
    )
    lines += [
        "## 7. Verification steps",
        "",
        "1. On the connected side, record a SHA-256 checksum for every file and the digest of every image.",
        "2. Verify publisher signatures where the publisher provides them.",
        "3. After the transfer, recompute every checksum inside the network before importing anything.",
        "4. Import only artifacts whose checksums match, then set the items in section 4 before first start.",
        "",
    ]
    return "\n".join(lines)


def render_json(data: dict) -> str:
    """transfer-manifest.json from the rows of build_manifest."""
    return json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def render_manifest(blueprint: dict, catalog: Catalog, generated: str) -> str:
    """transfer-manifest.md for a blueprint."""
    return render_markdown(build_manifest(blueprint, catalog, generated))
```

- [ ] **Step 4: Cover cpu_arch in the digest, check both files under E8, write both from manifest.py**

```diff
diff --git a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/blueprint.py b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/blueprint.py
--- a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/blueprint.py
+++ b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/blueprint.py
@@ -68,10 +68,12 @@ def save_blueprint(path: Path, data: dict) -> None:
 
 def inputs_digest(data: dict) -> str:
     """Digest of what the transfer manifest is generated from."""
+    answers = data.get("answers") or {}
     payload = {
         "decisions": data.get("decisions", []),
-        "models": (data.get("answers") or {}).get("workload.models", []),
-        "hardware": (data.get("answers") or {}).get("hardware.gpus", []),
+        "models": answers.get("workload.models", []),
+        "hardware": answers.get("hardware.gpus", []),
+        "cpu_arch": answers.get("hardware.cpu_arch"),
     }
     canonical = json.dumps(
         payload,
diff --git a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/checks.py b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/checks.py
--- a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/checks.py
+++ b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/checks.py
@@ -29,7 +29,12 @@ from .constants import (
 from .findings import SEVERITIES, Finding
 from .sizing import SizingInputError, compute_sizing
 from .tiering import compute_tier
-from .transfer import MANIFEST_FILENAME, read_manifest_digest
+from .transfer import (
+    MANIFEST_FILENAME,
+    MANIFEST_JSON_FILENAME,
+    read_manifest_digest,
+    read_manifest_json_digest,
+)
 
 
 def split_sections(text: str) -> tuple[dict[str, str], list[str]]:
@@ -94,12 +99,14 @@ def lint_blueprint(
     manifest_text: str | None,
     agents_text: str | None,
     today: date,
+    manifest_json_text: str | None = None,
 ) -> list[Finding]:
     return _lint(
         blueprint=blueprint,
         catalog=catalog,
         blueprint_text=blueprint_text,
         manifest_text=manifest_text,
+        manifest_json_text=manifest_json_text,
         agents_text=agents_text,
         today=today,
         unreadable={},
@@ -112,12 +119,14 @@ def _lint(
     catalog: Catalog,
     blueprint_text: str | None,
     manifest_text: str | None,
+    manifest_json_text: str | None,
     agents_text: str | None,
     today: date,
     unreadable: dict[str, str],
 ) -> list[Finding]:
-    """The lint run. `unreadable` maps "blueprint", "manifest" or "agents" to the reason
-    that file could not be read; such a file is reported instead of "not found"."""
+    """The lint run. `unreadable` maps "blueprint", "manifest", "manifest_json" or
+    "agents" to the reason that file could not be read; such a file is reported
+    instead of "not found"."""
     findings: list[Finding] = []
     rules = catalog.rules
 
@@ -259,15 +268,18 @@ def _lint(
                 Finding("E7", f"marker '{section_marker(ISOLATION_MARKER)}' is missing")
             )
 
-    # E8: transfer manifest exists and matches the decisions.
-    if "manifest" in unreadable:
-        findings.append(
-            Finding("E8", f"{MANIFEST_FILENAME} cannot be read: {unreadable['manifest']}")
-        )
-    elif manifest_text is None:
-        findings.append(Finding("E8", f"{MANIFEST_FILENAME} not found; run manifest.py"))
-    elif read_manifest_digest(manifest_text) != inputs_digest(blueprint):
-        findings.append(Finding("E8", f"{MANIFEST_FILENAME} is stale; run manifest.py again"))
+    # E8: both transfer manifest files exist and match the decisions.
+    digest = inputs_digest(blueprint)
+    for key, name, text, reader in (
+        ("manifest", MANIFEST_FILENAME, manifest_text, read_manifest_digest),
+        ("manifest_json", MANIFEST_JSON_FILENAME, manifest_json_text, read_manifest_json_digest),
+    ):
+        if key in unreadable:
+            findings.append(Finding("E8", f"{name} cannot be read: {unreadable[key]}"))
+        elif text is None:
+            findings.append(Finding("E8", f"{name} not found; run manifest.py"))
+        elif reader(text) != digest:
+            findings.append(Finding("E8", f"{name} is stale; run manifest.py again"))
 
     # E9: estimate-backed decisions are listed for verification.
     verification_text = sections.get("verification")
@@ -408,6 +420,7 @@ def lint_project(
     texts: dict[str, str | None] = {"blueprint": None}
     sources = {
         "manifest": blueprint_path.parent / MANIFEST_FILENAME,
+        "manifest_json": blueprint_path.parent / MANIFEST_JSON_FILENAME,
         "agents": project_root / "AGENTS.md",
     }
     if isinstance(relative, str) and relative.strip():
@@ -421,6 +434,7 @@ def lint_project(
         catalog=catalog,
         blueprint_text=texts["blueprint"],
         manifest_text=texts["manifest"],
+        manifest_json_text=texts["manifest_json"],
         agents_text=texts["agents"],
         today=today,
         unreadable=unreadable,
diff --git a/plugins/airgap-anything/skills/airgap-architect/scripts/manifest.py b/plugins/airgap-anything/skills/airgap-architect/scripts/manifest.py
--- a/plugins/airgap-anything/skills/airgap-architect/scripts/manifest.py
+++ b/plugins/airgap-anything/skills/airgap-architect/scripts/manifest.py
@@ -1,15 +1,24 @@
-"""Generate transfer-manifest.md from the decisions in blueprint.json."""
+"""Generate transfer-manifest.md and transfer-manifest.json from blueprint.json."""
 from datetime import date
 from pathlib import Path
 
 from airgap_lib import cli
-from airgap_lib.transfer import MANIFEST_FILENAME, UnknownComponentError, render_manifest
+from airgap_lib.transfer import (
+    MANIFEST_FILENAME,
+    MANIFEST_JSON_FILENAME,
+    UnknownComponentError,
+    build_manifest,
+    render_json,
+    render_markdown,
+)
 
 
 def main(argv=None) -> int:
     parser = cli.make_parser(__doc__)
     parser.add_argument(
-        "--out", help=f"output file (default: {MANIFEST_FILENAME} next to blueprint.json)"
+        "--out",
+        help=f"Markdown output file (default: {MANIFEST_FILENAME} next to blueprint.json); "
+        f"{MANIFEST_JSON_FILENAME} is written in the same directory",
     )
     parser.add_argument(
         "--date",
@@ -22,18 +31,22 @@ def main(argv=None) -> int:
     blueprint = cli.open_blueprint(args.blueprint)
     cli.answers_of(blueprint)  # exit 2 unless 'answers' is an object, as in tier.py
     try:
-        text = render_manifest(blueprint, catalog, args.date)
+        data = build_manifest(blueprint, catalog, args.date)
+        texts = {"md": render_markdown(data), "json": render_json(data)}
     except UnknownComponentError as error:
         cli.fail(cli.EXIT_INPUT, [str(error)])
     except (ValueError, OverflowError) as error:
         cli.fail_on_unusable_value(error)
     out = Path(args.out) if args.out else Path(args.blueprint).parent / MANIFEST_FILENAME
-    try:
-        out.parent.mkdir(parents=True, exist_ok=True)
-        out.write_text(text, encoding="utf-8")
-    except OSError as error:
-        cli.fail_on_write_error(out, error)
-    print(f"Wrote {out}")
+    outputs = ((out, texts["md"]), (out.parent / MANIFEST_JSON_FILENAME, texts["json"]))
+    for path, text in outputs:
+        try:
+            path.parent.mkdir(parents=True, exist_ok=True)
+            path.write_text(text, encoding="utf-8")
+        except OSError as error:
+            cli.fail_on_write_error(path, error)
+    for path, _ in outputs:
+        print(f"Wrote {path}")
     return cli.EXIT_OK
 
 
```

- [ ] **Step 5: Run the suite and the demo**

Run:

```bash
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
python3 docs-site/scripts/generate_reference.py && git status --short docs-site
```

Expected: `OK` on both; the generator prints `wrote 25 pages and 5 images` and `git status` lists nothing under `docs-site` (the pages do not show the manifest).

- [ ] **Step 6: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/transfer.py \
  plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/blueprint.py \
  plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/checks.py \
  plugins/airgap-anything/skills/airgap-architect/scripts/manifest.py \
  tests/projects.py tests/test_blueprint.py tests/test_checks.py tests/test_cli.py tests/test_transfer.py
git commit -m "feat(architect): manifest by CPU architecture, also as transfer-manifest.json

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Agent rules for the inside, W4, the blueprint template and the hand-off

§6.2. When `inside.operator` is `local_agent` or `people_then_agent`, the agent instruction block must carry the section "Rules for an agent inside the network"; lint warns with W4 when it does not. The blueprint template gains the Platform line and names `airgap-transfer` as the next step. The demo's `AGENTS.md` follows its operator.

**Files:**
- Modify: `plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py`, `checks.py`
- Modify: `plugins/airgap-anything/skills/airgap-architect/references/agents-snippet.md`, `references/blueprint-template.md`, `SKILL.md`
- Modify: `design/demo/build_demo.py`
- Modify: `docs/superpowers/specs/2026-11-20-airgap-architect-design.md` (§11.1, §12 rows, Revised line)
- Modify: `tests/projects.py`, `tests/test_checks.py`, `tests/test_reference_docs.py`
- Regenerate: `assets/demo/*`, `docs-site/public/terminal-dark.svg`, `docs-site/src/content/docs/reference/lint-codes.md`, `reference/scripts.md`

**Interfaces:**
- Consumes: `constants.AGENT_OPERATORS` (Task 1), `checks._lint(...)`, the W3 check of the agent block.
- Produces: `constants.AGENT_RULES_MARKER = "<!-- airgap-architect:inside-agent -->"`; warning `W4` with the message `inside.operator is {op}: the agent instruction block lacks the section 'Rules for an agent inside the network'` (a missing block stays W3 only); `projects.AGENTS_TEXT_WITH_RULES`; `build_demo.agents_text(blueprint_path, operator) -> str`.

This task changes what architect's `SKILL.md` says in two lines (the W codes and the hand-off). The behavior rerun for that change is Task 19.

- [ ] **Step 1: Write the failing tests**

````diff
diff --git a/tests/projects.py b/tests/projects.py
--- a/tests/projects.py
+++ b/tests/projects.py
@@ -9,6 +9,7 @@ from airgap_lib.catalog import Catalog
 from airgap_lib.constants import (
     AGENT_BLOCK_END,
     AGENT_BLOCK_START,
+    AGENT_RULES_MARKER,
     ISOLATION_MARKER,
     SECTION_MARKERS,
     section_marker,
@@ -25,6 +26,10 @@ from airgap_lib.transfer import (
 from tests import support
 
 AGENTS_TEXT = f"{AGENT_BLOCK_START}\nFollow the blueprint.\n{AGENT_BLOCK_END}\n"
+AGENTS_TEXT_WITH_RULES = (
+    f"{AGENT_BLOCK_START}\nFollow the blueprint.\n{AGENT_RULES_MARKER}\n"
+    f"### Rules for an agent inside the network\n{AGENT_BLOCK_END}\n"
+)
 
 
 def blueprint_markdown(blueprint: dict, catalog: Catalog, verification: str = "", isolation: bool = False) -> str:
diff --git a/tests/test_checks.py b/tests/test_checks.py
--- a/tests/test_checks.py
+++ b/tests/test_checks.py
@@ -309,6 +309,42 @@ class WarningRulesTest(LintTestCase):
         self.assertEqual(self.codes(), ["W3"])
 
 
+class InsideAgentRulesTest(LintTestCase):
+    def agents(self, text):
+        (self.root / "AGENTS.md").write_text(text, encoding="utf-8")
+
+    def test_w4_when_an_agent_works_inside_and_the_rules_are_missing(self):
+        for operator in ("local_agent", "people_then_agent"):
+            with self.subTest(operator=operator):
+                self.project(support.base_answers(**{"inside.operator": operator}))
+                findings = self.lint()
+                self.assertEqual([f.code for f in findings], ["W4"])
+                self.assertEqual(findings[0].severity, "warning")
+                self.assertEqual(
+                    findings[0].message,
+                    f"inside.operator is {operator}: the agent instruction block lacks the "
+                    "section 'Rules for an agent inside the network'",
+                )
+                self.agents(projects.AGENTS_TEXT_WITH_RULES)
+                self.assertEqual(self.lint(), [])
+
+    def test_no_w4_for_people(self):
+        self.project(support.base_answers(**{"inside.operator": "people"}))
+        self.assertEqual(self.codes(), [])
+        self.project(support.base_answers(**{"inside.operator": "unknown"}))
+        self.assertEqual(self.codes(), ["W2"])
+
+    def test_the_marker_counts_only_inside_the_block(self):
+        self.project(support.base_answers(**{"inside.operator": "local_agent"}))
+        self.agents(projects.AGENTS_TEXT + "<!-- airgap-architect:inside-agent -->\n")
+        self.assertEqual(self.codes(), ["W4"])
+
+    def test_a_missing_block_is_reported_once_as_w3(self):
+        self.project(support.base_answers(**{"inside.operator": "local_agent"}))
+        self.agents("# Agents\n")
+        self.assertEqual(self.codes(), ["W3"])
+
+
 class VerificationTokenTest(LintTestCase):
     def estimate_decisions(self, layer):
         decisions = support.base_decisions()
diff --git a/tests/test_reference_docs.py b/tests/test_reference_docs.py
--- a/tests/test_reference_docs.py
+++ b/tests/test_reference_docs.py
@@ -5,6 +5,7 @@ from airgap_lib.answers import QUESTIONS
 from airgap_lib.constants import (
     AGENT_BLOCK_END,
     AGENT_BLOCK_START,
+    AGENT_RULES_MARKER,
     ISOLATION_MARKER,
     SECTION_MARKERS,
     section_marker,
@@ -54,6 +55,24 @@ class TemplateReferenceTest(unittest.TestCase):
         self.assertLess(text.find(AGENT_BLOCK_START), text.find(AGENT_BLOCK_END))
         self.assertNotEqual(text.find(AGENT_BLOCK_START), -1)
 
+    def test_agents_snippet_has_the_inside_agent_rules_in_a_block_of_their_own(self):
+        text = read(REFERENCES / "agents-snippet.md")
+        rules_at = text.find(AGENT_RULES_MARKER)
+        self.assertGreater(rules_at, text.find(AGENT_BLOCK_END))
+        rules = text[rules_at : text.index("```", rules_at)]
+        self.assertIn("### Rules for an agent inside the network", rules)
+        for phrase in ("exit code", "MISSING.txt", "Never download", "Never edit", "Never improvise"):
+            self.assertIn(phrase, rules)
+        self.assertNotIn(AGENT_BLOCK_END, rules)
+
+    def test_blueprint_template_names_the_inside_operator_and_the_next_skill(self):
+        text = read(REFERENCES / "blueprint-template.md")
+        transfer = text[text.find(section_marker("transfer")) : text.find(section_marker("data-flow"))]
+        for phrase in ("inside.operator", "INSIDE.md", "AGENTS-INSIDE.md", "airgap-transfer", "Platform:"):
+            self.assertIn(phrase, transfer)
+        operations = text[text.find(section_marker("operations")) : text.find(section_marker("verification"))]
+        self.assertIn("inside.operator", operations)
+
 
 if __name__ == "__main__":
     unittest.main()
````

- [ ] **Step 2: Run them to see them fail**

Run: `python3.11 -m unittest discover -s tests -t .`

Expected: `FAILED (errors=3)`: `tests.test_checks`, `tests.test_cli` and `tests.test_reference_docs` cannot import `AGENT_RULES_MARKER` or `AGENTS_TEXT_WITH_RULES`.

- [ ] **Step 3: Add the marker and W4**

```diff
diff --git a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/checks.py b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/checks.py
--- a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/checks.py
+++ b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/checks.py
@@ -1,4 +1,4 @@
-"""Blueprint lint: errors E1-E11, warnings W1-W3 and note N1 of the design spec."""
+"""Blueprint lint: errors E1-E11, warnings W1-W4 and note N1 of the design specs."""
 from __future__ import annotations
 
 import re
@@ -19,6 +19,8 @@ from .catalog import Catalog, is_stale
 from .constants import (
     AGENT_BLOCK_END,
     AGENT_BLOCK_START,
+    AGENT_OPERATORS,
+    AGENT_RULES_MARKER,
     ISOLATION_MARKER,
     LAYERS,
     SECTION_MARKERS,
@@ -385,6 +387,19 @@ def _lint(
     ):
         findings.append(Finding("W3", "the agent instruction block is missing from AGENTS.md"))
 
+    # W4: an agent works inside, so the block carries the rules for it.
+    operator = resolved.get("inside.operator")
+    if operator in AGENT_OPERATORS and agents_text is not None:
+        start, end = agents_text.find(AGENT_BLOCK_START), agents_text.find(AGENT_BLOCK_END)
+        if 0 <= start < end and AGENT_RULES_MARKER not in agents_text[start:end]:
+            findings.append(
+                Finding(
+                    "W4",
+                    f"inside.operator is {operator}: the agent instruction block lacks the "
+                    "section 'Rules for an agent inside the network'",
+                )
+            )
+
     # N1: every override in effect is reported.
     for decision in decisions:
         if has_override(decision):
diff --git a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py
--- a/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py
+++ b/plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py
@@ -61,6 +61,8 @@ SECTION_MARKERS = (
 ISOLATION_MARKER = "isolation-design"
 AGENT_BLOCK_START = "<!-- airgap-architect:start -->"
 AGENT_BLOCK_END = "<!-- airgap-architect:end -->"
+# Opens the section "Rules for an agent inside the network" within the block.
+AGENT_RULES_MARKER = "<!-- airgap-architect:inside-agent -->"
 
 UNKNOWN = "unknown"
 
```

- [ ] **Step 4: Write the rules into the agent snippet, the template and SKILL.md**

````diff
diff --git a/plugins/airgap-anything/skills/airgap-architect/SKILL.md b/plugins/airgap-anything/skills/airgap-architect/SKILL.md
--- a/plugins/airgap-anything/skills/airgap-architect/SKILL.md
+++ b/plugins/airgap-anything/skills/airgap-architect/SKILL.md
@@ -30,7 +30,7 @@ Work through the steps in order. Read a step's reference file when you reach the
 | 4 | Decisions | Write one decision per layer into `decisions` | `references/layers/llm-serving.md`, `references/layers/llm-gateway.md`, `references/layers/supporting-defaults.md` |
 | 5 | Transfer manifest | Run `manifest.py`; it is the list of what to carry in | |
 | 6 | Blueprint | Set `blueprint_path`, then write the blueprint file | `references/blueprint-template.md` |
-| 7 | Agent instructions | Add the block to `AGENTS.md` | `references/agents-snippet.md` |
+| 7 | Agent instructions | Add the block to `AGENTS.md`, with the inside-agent rules when `inside.operator` names an agent | `references/agents-snippet.md` |
 | 8 | Lint | Run `lint.py`; fix and repeat until it exits 0 | |
 | 9 | Hand-off | Show the blueprint and the step that follows approval (third column of the table below), then stop until the user approves | "Blueprint path and superpowers" below |
 
@@ -47,7 +47,7 @@ python3 "${CLAUDE_SKILL_DIR}/scripts/manifest.py" --blueprint docs/airgap/bluepr
 python3 "${CLAUDE_SKILL_DIR}/scripts/lint.py" --blueprint docs/airgap/blueprint.json
 ```
 
-`manifest.py` writes `docs/airgap/transfer-manifest.md` next to `blueprint.json`. `lint.py` reads `blueprint_path` and `AGENTS.md` relative to `--project-root` (default `.`); from another directory, pass `--project-root` with the project root. Each script lists its other options with `--help`.
+`manifest.py` writes `docs/airgap/transfer-manifest.md` and `docs/airgap/transfer-manifest.json` next to `blueprint.json`; the JSON file is what the `airgap-transfer` skill reads. `lint.py` reads `blueprint_path` and `AGENTS.md` relative to `--project-root` (default `.`); from another directory, pass `--project-root` with the project root. Each script lists its other options with `--help`.
 
 | Exit code | Meaning | What you do |
 |---|---|---|
@@ -56,7 +56,7 @@ python3 "${CLAUDE_SKILL_DIR}/scripts/lint.py" --blueprint docs/airgap/blueprint.
 | 2 | An answer is missing or invalid, `blueprint.json` cannot be read, or, in `manifest.py`, a decision names a component that is not in the catalog | Go back to the question or decision the message names |
 | 3 | Python is older than 3.11, or the catalog cannot be read | Stop and tell the user |
 
-`lint.py` reports a component that is not in the catalog as error E2, exit 1. Warnings (W1 to W3) and notes (N1) do not change the exit code.
+`lint.py` reports a component that is not in the catalog as error E2, exit 1. Warnings (W1 to W4) and notes (N1) do not change the exit code.
 
 ## Decisions
 
@@ -92,7 +92,7 @@ A decision may also carry `benchmark`: a list of catalog IDs that are carried in
 | Situation | Blueprint path | After the user approves |
 |---|---|---|
 | `superpowers:writing-plans` is available | `docs/superpowers/specs/`, then the date, the project name and `-airgap-blueprint-design.md`, for example `docs/superpowers/specs/2026-11-20-example-airgap-blueprint-design.md` | Invoke `superpowers:writing-plans` with that file |
-| Superpowers is not installed | `docs/airgap/blueprint.md` | Print the next steps yourself: transfer, install, benchmark |
+| Superpowers is not installed | `docs/airgap/blueprint.md` | Print the next steps yourself: transfer with `airgap-transfer`, install, benchmark |
 | `superpowers:brainstorming` is already running, because it started before this skill; this skill does not start it | As in the first row | Run one interview, not two. Brainstorming owns the rhythm and the approval gates; this skill supplies the questions, tables, scripts and template. Run `lint.py` as part of the spec self-review. |
 
 The interview starts the blueprint with `"blueprint_path": ""`, and lint rejects an empty value. Set it to the path above in `blueprint.json` before you write the blueprint.
diff --git a/plugins/airgap-anything/skills/airgap-architect/references/agents-snippet.md b/plugins/airgap-anything/skills/airgap-architect/references/agents-snippet.md
--- a/plugins/airgap-anything/skills/airgap-architect/references/agents-snippet.md
+++ b/plugins/airgap-anything/skills/airgap-architect/references/agents-snippet.md
@@ -2,6 +2,8 @@
 
 Add the block below to `AGENTS.md` in the project root. Create the file if it does not exist. If the block is already there, replace everything from the start marker to the end marker. Replace `BLUEPRINT_PATH` with the value of `blueprint_path`.
 
+When `inside.operator` in `blueprint.json` is `local_agent` or `people_then_agent`, also put the section from "Rules for an agent inside the network" below into the block, directly before the end marker. Lint reports W4 while it is missing. For `people`, leave it out.
+
 If the project has a `CLAUDE.md` that does not import `AGENTS.md`, ask the user before adding the line `@AGENTS.md` to it.
 
 ```markdown
@@ -16,3 +18,19 @@ This project follows the blueprint at `BLUEPRINT_PATH`. Its machine-readable sta
 - Decisions listed in the blueprint's verification section rest on estimates. Measure before relying on them.
 <!-- airgap-architect:end -->
 ```
+
+## Rules for an agent inside the network
+
+```markdown
+<!-- airgap-architect:inside-agent -->
+### Rules for an agent inside the network
+
+The installation inside follows the bundle that `airgap-transfer` builds: its runbook, `AGENTS-INSIDE.md`, `verify.sh` and `load.sh`.
+
+- Run one command per step, exactly as the runbook gives it.
+- Check the exit code of every command. 0 means go on.
+- Stop at the first non-zero exit code and report the command, its exit code and its output; when `verify.sh` stops, report the contents of `MISSING.txt`.
+- Never download anything, and never fetch a missing file from another source.
+- Never edit the generated scripts or the files they check.
+- Never improvise a step the runbook does not name. Ask a person instead.
+```
diff --git a/plugins/airgap-anything/skills/airgap-architect/references/blueprint-template.md b/plugins/airgap-anything/skills/airgap-architect/references/blueprint-template.md
--- a/plugins/airgap-anything/skills/airgap-architect/references/blueprint-template.md
+++ b/plugins/airgap-anything/skills/airgap-architect/references/blueprint-template.md
@@ -50,7 +50,9 @@ Inputs (users, usage shares, the context per group when `workload.context_tokens
 <!-- airgap:section transfer -->
 ## 6. Air-gap transfer plan
 
-How artifacts enter the network (`transfer.channel`, `transfer.cadence`), who carries them, where they land first, and how they are checked. Link to `docs/airgap/transfer-manifest.md` for the list itself. The manifest's `Hardware:` line must match the design's GPUs; when it says unknown, carry only the image rows for the hardware. Package files are for linux/amd64 hosts: on arm64 hosts, carry the files that the entries' notes name instead. Name the telemetry settings that must be off before first start.
+How artifacts enter the network (`transfer.channel`, `transfer.cadence`), who carries them, where they land first, and how they are checked. Link to `docs/airgap/transfer-manifest.md` for the list itself. The manifest's `Hardware:` line must match the design's GPUs; when it says unknown, carry only the image rows for the hardware. Its `Platform:` line must match `hardware.cpu_arch`. Name the telemetry settings that must be off before first start.
+
+Who carries out the steps inside the network (`inside.operator`) and what they receive: for `people`, the runbook `INSIDE.md`; for `local_agent`, the agent rules `AGENTS-INSIDE.md`; for `people_then_agent`, both, the runbook for the first day and the rules once the agent runs. Every step inside works without internet and without an LLM. Name `airgap-transfer` as the next step: it turns the manifest into a checked bundle, the inside scripts and these instructions.
 
 <!-- airgap:section data-flow -->
 ## 7. Data flow
@@ -60,7 +62,7 @@ The path of one request from the user to the model and back, naming each compone
 <!-- airgap:section operations -->
 ## 8. Failure modes and operations
 
-What happens when each component fails and how it is noticed. Backups of state. How upgrades are carried in and applied without internet access.
+What happens when each component fails and how it is noticed. Backups of state. How upgrades are carried in and applied without internet access, and who applies them (`inside.operator`): people following a runbook, or the agent inside under the rules in `AGENTS.md`.
 
 <!-- airgap:section verification -->
 ## 9. Verification plan
````

- [ ] **Step 5: Record W4, E8 and manifest.py in the architect spec**

````diff
diff --git a/docs/superpowers/specs/2026-11-20-airgap-architect-design.md b/docs/superpowers/specs/2026-11-20-airgap-architect-design.md
--- a/docs/superpowers/specs/2026-11-20-airgap-architect-design.md
+++ b/docs/superpowers/specs/2026-11-20-airgap-architect-design.md
@@ -3,7 +3,7 @@
 - **Date:** 2026-11-20
 - **Status:** Approved by the maintainer on 2026-11-20
 - **Names:** repository and plugin `airgap-anything`; skill `airgap-architect` (see §18)
-- **Revised:** 2026-11-21, after research: T1 user threshold 25 → 50 and chat/RAG duty 0.15-0.30 → 0.25-0.50 (sources in rules.toml). 2026-11-21 and 2026-11-22, during implementation: a context per user group and a KV cache counted in tokens and packed in whole requests, with a note on larger GPU groups (§7, §10.2, §16); a GPU vendor, image rows per hardware class and a manifest digest over decisions, models and GPUs (§7, §10.5, §11.1, §14.2); GPU names that stay unique after normalization (§10.5); source code at the release tag as `docs` evidence (§11.2). 2026-11-22, after the final review: the E8 and E9 rows, exit 3 and the `manifest.py` row in §12, the decision's `benchmark` list (§13, §14.2), and the vLLM links of §10.2 pinned to v0.34.0
+- **Revised:** 2026-11-21, after research: T1 user threshold 25 → 50 and chat/RAG duty 0.15-0.30 → 0.25-0.50 (sources in rules.toml). 2026-11-21 and 2026-11-22, during implementation: a context per user group and a KV cache counted in tokens and packed in whole requests, with a note on larger GPU groups (§7, §10.2, §16); a GPU vendor, image rows per hardware class and a manifest digest over decisions, models and GPUs (§7, §10.5, §11.1, §14.2); GPU names that stay unique after normalization (§10.5); source code at the release tag as `docs` evidence (§11.2). 2026-11-22, after the final review: the E8 and E9 rows, exit 3 and the `manifest.py` row in §12, the decision's `benchmark` list (§13, §14.2), and the vLLM links of §10.2 pinned to v0.34.0; during sub-project 2 (design spec `2026-11-22-airgap-transfer-design.md`): the questions `inside.operator` and `hardware.cpu_arch` (§7), package rows as tables with an architecture (§11.1), the JSON manifest, E8 over both manifest files and W4 (§12)
 - **Covers:** sub-project 1 — the core pipeline plus the LLM platform layer
 
 ## 1. Summary
@@ -318,7 +318,7 @@ A table of common datacenter and workstation GPUs: model, vendor, VRAM, TDP, sou
 One TOML file per component, named after its `id`:
 
 ```toml
-schema_version = 1
+schema_version = 2
 id = "vllm"
 name = "vLLM"
 layer = "llm-serving"
@@ -354,7 +354,7 @@ repo = "air-gapped/skills"
 skill = "vllm-deployment"
 ```
 
-`airgap.images` rows are `{ ref, digest, hardware }`. `hardware` names the hardware classes an image is for (`nvidia`, `amd`, `intel`, `cpu`); without it the image is for any hardware. There is one image row per hardware class the project's installation documentation names; aliases of the same image are not listed. Angle-bracket values are filled per component during implementation. `version` is always an exact version, never `latest`, and it is the highest stable version, which is not always the release GitHub marks as latest (a project that patches an older line can publish that patch after a newer release). `airgap.packages` names the files for linux/amd64 (x86_64) hosts exactly as the release names them, and `airgap.notes` gives the files for other architectures; the transfer manifest lists each `airgap.packages` string as a carry item. `requires` drives the `state` layer: PostgreSQL or Valkey is chosen when a chosen component requires it. When other entries list a component in `requires` and their documentation names the versions they support, `version` is the newest release that all of them support, and `airgap.notes` says why.
+`airgap.images` rows are `{ ref, digest, hardware }`. `hardware` names the hardware classes an image is for (`nvidia`, `amd`, `intel`, `cpu`); without it the image is for any hardware. There is one image row per hardware class the project's installation documentation names; aliases of the same image are not listed. Angle-bracket values are filled per component during implementation. `version` is always an exact version, never `latest`, and it is the highest stable version, which is not always the release GitHub marks as latest (a project that patches an older line can publish that patch after a newer release). `airgap.packages` rows are `{ file, arch, url, checksums }` (component `schema_version` 2, design spec `2026-11-22-airgap-transfer-design.md` §7): the file as the release names it, `amd64`, `arm64` or `any`, the download URL, and the URL of the publisher's checksum file or `""`; the transfer manifest lists the rows for `hardware.cpu_arch` and the `any` rows as carry items. `requires` drives the `state` layer: PostgreSQL or Valkey is chosen when a chosen component requires it. When other entries list a component in `requires` and their documentation names the versions they support, `version` is the newest release that all of them support, and `airgap.notes` says why.
 
 ### 11.2 Evidence policy
 
@@ -380,7 +380,7 @@ All scripts require Python 3.11 or newer, import only standard-library modules,
 |---|---|---|---|
 | `tier.py` | `answers` | `tier` | 0 ok, 2 missing or invalid answers (listed by ID), 3 environment |
 | `size.py` | `answers` | `sizing`, `assumptions` | 0 ok, 2 missing or invalid answers, 3 environment |
-| `manifest.py` | `decisions`, `workload.models` and `hardware.gpus` from `answers`, catalog | `transfer-manifest.md` | 0 ok, 2 unknown component or no `answers` object, 3 environment |
+| `manifest.py` | `decisions`, and `workload.models`, `hardware.gpus` and `hardware.cpu_arch` from `answers`, catalog | `transfer-manifest.md`, `transfer-manifest.json` | 0 ok, 2 unknown component or no `answers` object, 3 environment |
 | `lint.py` | Everything | Report as text or JSON | 0 clean, 1 errors found, 3 environment |
 
 Every script also exits 2 when `blueprint.json` cannot be read, holds a value the scripts cannot use, or, for a script that writes, cannot be written. Exit 3, environment, means that Python is older than 3.11 or that the catalog cannot be read or fails validation; the skill then stops and tells the user.
@@ -398,7 +398,7 @@ Lint errors:
 | E5 | No escalator is violated without an override |
 | E6 | `tier` and `sizing` equal a fresh computation from `answers` |
 | E7 | The blueprint file has all template sections, names every chosen component with its version, and has an "Isolation design" subsection when `org.isolation = multi_level` |
-| E8 | The transfer manifest exists and its recorded digest matches the current `decisions`, `workload.models` and `hardware.gpus` |
+| E8 | Both transfer manifest files, `transfer-manifest.md` and `transfer-manifest.json`, exist and their recorded digest matches the current `decisions`, `workload.models`, `hardware.gpus` and `hardware.cpu_arch` |
 | E9 | Every decision labeled `estimate` appears in the blueprint's verification section, and so does every component in a decision's `benchmark` list |
 | E10 | `sizing.fits` is true, or an override explains how the gap is closed |
 | E11 | Everything listed in a chosen component's `requires` is itself chosen or named in `existing` |
@@ -410,6 +410,7 @@ Lint warnings:
 | W1 | A catalog entry used by the blueprint was last verified more than 180 days ago |
 | W2 | A required answer is "unknown" and a default was used |
 | W3 | The agent instruction block is missing from `AGENTS.md` |
+| W4 | `inside.operator` is `local_agent` or `people_then_agent` and the agent instruction block lacks the section "Rules for an agent inside the network" |
 
 Lint notes:
 
````

- [ ] **Step 6: Let the demo's AGENTS.md follow its operator**

````diff
diff --git a/design/demo/build_demo.py b/design/demo/build_demo.py
--- a/design/demo/build_demo.py
+++ b/design/demo/build_demo.py
@@ -37,6 +37,8 @@ from airgap_lib.catalog import default_catalog_dir, load_catalog  # noqa: E402
 from airgap_lib.constants import (  # noqa: E402
     AGENT_BLOCK_END,
     AGENT_BLOCK_START,
+    AGENT_OPERATORS,
+    AGENT_RULES_MARKER,
     SECTION_MARKERS,
     section_marker,
 )
@@ -152,10 +154,16 @@ def blueprint_markdown(blueprint: dict, versions: dict[str, str]) -> str:
     return "\n".join(lines)
 
 
-def agents_text(blueprint_path: str) -> str:
+def agents_text(blueprint_path: str, operator: str) -> str:
+    """The block of references/agents-snippet.md, with the inside-agent rules when
+    `operator` names an agent, as the skill's step 7 writes it."""
     snippet = (SKILL_DIR / "references" / "agents-snippet.md").read_text(encoding="utf-8")
     start, end = snippet.index(AGENT_BLOCK_START), snippet.index(AGENT_BLOCK_END)
-    return snippet[start : end + len(AGENT_BLOCK_END)].replace("BLUEPRINT_PATH", blueprint_path) + "\n"
+    block = snippet[start:end]
+    if operator in AGENT_OPERATORS:
+        rules_at = snippet.index(AGENT_RULES_MARKER)
+        block += snippet[rules_at : snippet.index("```", rules_at)]
+    return (block + AGENT_BLOCK_END).replace("BLUEPRINT_PATH", blueprint_path) + "\n"
 
 
 def capture() -> list[dict]:
@@ -172,7 +180,10 @@ def capture() -> list[dict]:
         blueprint_file = project / blueprint["blueprint_path"]
         blueprint_file.parent.mkdir(parents=True, exist_ok=True)
         blueprint_file.write_text(blueprint_markdown(blueprint, versions), encoding="utf-8")
-        (project / "AGENTS.md").write_text(agents_text(blueprint["blueprint_path"]), encoding="utf-8")
+        operator = blueprint["answers"].get("inside.operator", "people")
+        (project / "AGENTS.md").write_text(
+            agents_text(blueprint["blueprint_path"], operator), encoding="utf-8"
+        )
 
         env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", NO_COLOR="1")
         private = [str(Path.home()), tmp, Path(tmp).name]
````

- [ ] **Step 7: Rebuild the demo and the pages, run the suite**

Run:

```bash
python3 design/demo/build_demo.py
python3 docs-site/scripts/generate_reference.py
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
git status --short
```

Expected: `build_demo.py` ends with `font 12.5 px, 112 columns, 32 rows, loop ...`; the generator prints `wrote 25 pages and 5 images`; both suites `OK` (426 tests); `git status` lists the files of this task plus `assets/demo/terminal-dark.svg`, `assets/demo/terminal-light.svg`, `docs-site/public/terminal-dark.svg`, `docs-site/src/content/docs/reference/lint-codes.md` and `reference/scripts.md`.

- [ ] **Step 8: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/constants.py \
  plugins/airgap-anything/skills/airgap-architect/scripts/airgap_lib/checks.py \
  plugins/airgap-anything/skills/airgap-architect/references/agents-snippet.md \
  plugins/airgap-anything/skills/airgap-architect/references/blueprint-template.md \
  plugins/airgap-anything/skills/airgap-architect/SKILL.md \
  design/demo/build_demo.py docs/superpowers/specs/2026-11-20-airgap-architect-design.md \
  tests/projects.py tests/test_checks.py tests/test_reference_docs.py \
  assets/demo docs-site/public/terminal-dark.svg \
  docs-site/src/content/docs/reference/lint-codes.md docs-site/src/content/docs/reference/scripts.md
git commit -m "feat(architect): rules for an agent inside the network, W4, hand-off to airgap-transfer

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Phase A check

No new code. This task proves Phase A on a whole design before Phase B builds on its output.

**Files:**
- None changed. A scratch folder only.

**Interfaces:**
- Consumes: the four architect scripts, `design/demo/department-blueprint.json`.
- Produces: nothing in the repository; the evidence that `transfer-manifest.json` is what Phase B reads.

- [ ] **Step 1: Run the architect pipeline on the demo blueprint in a scratch folder**

Run:

```bash
RUN=$(mktemp -d)
mkdir -p "$RUN/docs/airgap" && cp design/demo/department-blueprint.json "$RUN/docs/airgap/blueprint.json"
S=plugins/airgap-anything/skills/airgap-architect/scripts
python3 $S/tier.py --blueprint "$RUN/docs/airgap/blueprint.json" >/dev/null
python3 $S/size.py --blueprint "$RUN/docs/airgap/blueprint.json" >/dev/null
python3 $S/manifest.py --blueprint "$RUN/docs/airgap/blueprint.json"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['platform'], len(d['images']), len(d['packages']), [p['arch'] for p in d['packages']])" "$RUN/docs/airgap/transfer-manifest.json"
grep -n "Platform" "$RUN/docs/airgap/transfer-manifest.md"
```

Expected: two `Wrote` lines (`.md` and `.json`), then `linux/amd64 11` followed by the package count and a list in which every arch is `amd64` or `any`, and `6:- Platform: linux/amd64`.

- [ ] **Step 2: The same with arm64**

Run:

```bash
python3 - "$RUN/docs/airgap/blueprint.json" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
data["answers"]["hardware.cpu_arch"] = "arm64"
json.dump(data, open(path, "w"), indent=2)
PY
python3 $S/lint.py --blueprint "$RUN/docs/airgap/blueprint.json" --project-root "$RUN"; echo "lint exit: $?"
python3 $S/manifest.py --blueprint "$RUN/docs/airgap/blueprint.json" >/dev/null
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['platform'], sorted({p['arch'] for p in d['packages']}))" "$RUN/docs/airgap/transfer-manifest.json"
```

Expected: lint reports `E8 error: transfer-manifest.md is stale; run manifest.py again` and the same for `transfer-manifest.json` (besides E7 and W3, because the scratch folder has no `blueprint.md` and no `AGENTS.md`), and `lint exit: 1`. After `manifest.py`: `linux/arm64` and a set drawn from `arm64` and `any` only; the demo's packages come from `docker-compose`, so the set is `['arm64']` when Task 2 found an arm64 asset for it.

- [ ] **Step 3: Check the catalog, the plugin and the suite**

Run:

```bash
python3 plugins/airgap-anything/skills/airgap-architect/scripts/lint.py --catalog-only
claude plugin validate plugins/airgap-anything --profile directory
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
git status --short
```

Expected: `OK: no findings`; the validator passes as before Phase A (when `claude` is not on PATH, say so in the task report and go on); both suites `OK`; a clean tree.

---

## Phase B: The scripts of `airgap-transfer`

Phase B builds everything the skill runs, test-first, and no skill text: `SKILL.md` and the references wait for the baseline of Task 15. Every file below is new unless a step says otherwise, so the code is given whole. Paths below `plugins/airgap-anything/skills/airgap-transfer/` are written as `$T/` in the prose; the commands spell them out.

### Task 6: Skill folder, test paths, Python guard, constants, findings, CLI helpers

**Files:**
- Modify: `tests/__init__.py`
- Create: `$T/scripts/transfer_lib/__init__.py`, `constants.py`, `findings.py`, `cli.py`
- Create: `tests/test_transfer_foundation.py`

**Interfaces:**
- Consumes: nothing of architect's.
- Produces:
  - `tests.SKILLS_DIR`, `tests.TRANSFER_DIR`, `tests.TRANSFER_SCRIPTS_DIR`, `tests.TRANSFER_TEMPLATES_DIR`, `tests.SKILL_DIRS = (SKILL_DIR, TRANSFER_DIR)`, `tests.SCENARIOS_DIR`; importing `tests` puts both skills' `scripts/` on `sys.path`. `SKILL_DIR`, `SCRIPTS_DIR`, `CATALOG_DIR` keep their meaning (architect).
  - `transfer_lib.MINIMUM_PYTHON = (3, 11)`, `transfer_lib.check_python(version_info=None) -> str | None`; importing `transfer_lib` on an older Python prints the message and exits 3.
  - `transfer_lib.constants`: the exit codes, file names, channel, operator and filesystem tuples, `GB = 10**9`, `FAT32_MAX_FILE_BYTES = 4 * 1024**3 - 1`, `VOLUME_RESERVE = 0.02`, `MODEL_FILE_PATTERNS`, `PICKLE_SUFFIXES = (".bin", ".pt", ".pth", ".pkl")`, `PICKLE_PATTERNS`, `PART_SUFFIX = ".part{:03d}"`.
  - `findings.Finding(code, message)` with `severity` `"warning"` for a `BW` code and `"error"` otherwise; `has_errors(findings)`, `format_text(findings)` (last line `N error(s), M warning(s)`), `format_json(findings)`.
  - `cli.fail(code, lines)` (prints to stderr, raises `SystemExit(code)`), `cli.make_parser(description)` with `--project-root` (default `.`).

- [ ] **Step 1: Write the failing test**

Create `tests/test_transfer_foundation.py`:

```python
import json
import unittest

import tests  # noqa: F401  (puts both skills' scripts on sys.path)
import transfer_lib
from transfer_lib.constants import FAT32_MAX_FILE_BYTES, GB, PICKLE_SUFFIXES, VOLUME_RESERVE
from transfer_lib.findings import Finding, format_json, format_text, has_errors


class PythonGuardTest(unittest.TestCase):
    def test_old_interpreter_gets_a_message_naming_both_versions(self):
        message = transfer_lib.check_python((3, 10, 12))
        self.assertIn("airgap-transfer", message)
        self.assertIn("3.11", message)
        self.assertIn("3.10", message)

    def test_supported_interpreters_pass(self):
        self.assertIsNone(transfer_lib.check_python((3, 11, 0)))
        self.assertIsNone(transfer_lib.check_python((3, 13, 1)))


class ConstantsTest(unittest.TestCase):
    def test_the_values_of_the_spec(self):
        self.assertEqual(FAT32_MAX_FILE_BYTES, 4 * 1024**3 - 1)
        self.assertEqual(VOLUME_RESERVE, 0.02)
        self.assertEqual(GB, 1_000_000_000)
        self.assertEqual(PICKLE_SUFFIXES, (".bin", ".pt", ".pth", ".pkl"))


class FindingsTest(unittest.TestCase):
    def test_b_codes_are_errors_and_bw_codes_warnings(self):
        self.assertEqual(Finding("B3", "x").severity, "error")
        self.assertEqual(Finding("BW1", "x").severity, "warning")
        self.assertTrue(has_errors([Finding("B1", "x")]))
        self.assertFalse(has_errors([Finding("BW2", "x")]))

    def test_reports(self):
        self.assertEqual(format_text([]), "OK: no findings")
        text = format_text([Finding("B2", "size"), Finding("BW1", "no list")])
        self.assertEqual(text.splitlines(), ["B2 error: size", "BW1 warning: no list", "1 error(s), 1 warning(s)"])
        self.assertEqual(json.loads(format_json([Finding("BW1", "no list")])),
                         [{"code": "BW1", "severity": "warning", "message": "no list"}])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to see it fail**

Run: `python3.11 -m unittest tests.test_transfer_foundation`

Expected: `ModuleNotFoundError: No module named 'transfer_lib'`, `FAILED (errors=1)`.

- [ ] **Step 3: Put both skills on the test path**

```diff
diff --git a/tests/__init__.py b/tests/__init__.py
--- a/tests/__init__.py
+++ b/tests/__init__.py
@@ -1,13 +1,23 @@
-"""Test package. Importing it puts the skill's scripts on sys.path."""
+"""Test package. Importing it puts the scripts of both skills on sys.path.
+
+The two skills ship separately and never import each other; their packages,
+`airgap_lib` and `transfer_lib`, have different names, so tests can use both.
+"""
 import sys
 from pathlib import Path
 
 REPO_ROOT = Path(__file__).resolve().parent.parent
 PLUGIN_DIR = REPO_ROOT / "plugins" / "airgap-anything"
-SKILL_DIR = PLUGIN_DIR / "skills" / "airgap-architect"
+SKILLS_DIR = PLUGIN_DIR / "skills"
+SKILL_DIR = SKILLS_DIR / "airgap-architect"
 SCRIPTS_DIR = SKILL_DIR / "scripts"
 CATALOG_DIR = SKILL_DIR / "catalog"
+TRANSFER_DIR = SKILLS_DIR / "airgap-transfer"
+TRANSFER_SCRIPTS_DIR = TRANSFER_DIR / "scripts"
+TRANSFER_TEMPLATES_DIR = TRANSFER_DIR / "templates"
+SKILL_DIRS = (SKILL_DIR, TRANSFER_DIR)
 SCENARIOS_DIR = REPO_ROOT / "evals" / "scenarios"
 
-if str(SCRIPTS_DIR) not in sys.path:
-    sys.path.insert(0, str(SCRIPTS_DIR))
+for _scripts in (SCRIPTS_DIR, TRANSFER_SCRIPTS_DIR):
+    if str(_scripts) not in sys.path:
+        sys.path.insert(0, str(_scripts))
```

- [ ] **Step 4: Write the package's first modules**

Create `$T/scripts/transfer_lib/__init__.py`:

```python
"""Shared code for the airgap-transfer scripts.

Importing this package checks the Python version first, so every script fails
with a clear message on an interpreter older than 3.11. Nothing here imports the
airgap-architect skill: an installer may copy one skill folder without the other.
"""
import sys

MINIMUM_PYTHON = (3, 11)
EXIT_ENVIRONMENT = 3


def check_python(version_info=None):
    """Return an error message when the interpreter is too old, else None."""
    version = tuple((version_info or sys.version_info)[:2])
    if version < MINIMUM_PYTHON:
        return "airgap-transfer needs Python %d.%d or newer (found %d.%d)." % (
            MINIMUM_PYTHON + version
        )
    return None


_message = check_python()
if _message:
    sys.stderr.write(_message + "\n")
    raise SystemExit(EXIT_ENVIRONMENT)
```

Create `$T/scripts/transfer_lib/constants.py`:

```python
"""Names shared by every module of airgap-transfer."""
from __future__ import annotations

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_INPUT = 2
EXIT_ENVIRONMENT = 3

# Files in the project, under docs/airgap/.
AIRGAP_DIR = "docs/airgap"
BLUEPRINT_FILE = "blueprint.json"
MANIFEST_FILE = "transfer-manifest.json"
STATE_FILE = "transfer.json"
MANIFEST_SCHEMA_VERSION = 1
STATE_SCHEMA_VERSION = 1
BUNDLE_SCHEMA_VERSION = 1

# Answers of airgap-architect that this skill reads from blueprint.json.
CHANNELS = ("removable_media", "data_diode", "staging_host", "other")
MEDIUM_CHANNELS = ("removable_media", "other")
FILE_LIMIT_CHANNELS = ("data_diode", "staging_host")
OPERATORS = ("people", "local_agent", "people_then_agent")
RUNBOOK_OPERATORS = ("people", "people_then_agent")
AGENT_RULES_OPERATORS = ("local_agent", "people_then_agent")

FILESYSTEMS = ("fat32", "exfat", "ntfs", "ext4", "other")
GB = 10**9  # medium and file sizes are given in decimal gigabytes
FAT32_MAX_FILE_BYTES = 4 * 1024**3 - 1
VOLUME_RESERVE = 0.02

# The model file filter of design spec section 8.4, in one place.
MODEL_FILE_PATTERNS = (
    "*.safetensors",
    "*.json",
    "*.txt",
    "*.model",
    "*.tiktoken",
    "*.jinja",
    "*.md",
    "LICENSE*",
    "LICENCE*",
)
PICKLE_SUFFIXES = (".bin", ".pt", ".pth", ".pkl")
PICKLE_PATTERNS = tuple(f"*{suffix}" for suffix in PICKLE_SUFFIXES)

# The bundle folder.
FETCH_SCRIPT = "fetch.sh"
FETCH_LOG = "fetch.log"
FETCH_STATE_DIR = ".fetch"
CONNECTED_ONLY = (FETCH_SCRIPT, FETCH_LOG, FETCH_STATE_DIR)
BUNDLE_JSON = "bundle.json"
SUMS_FILE = "SHA256SUMS"
PARTS_FILE = "PARTS.txt"
VOLUMES_FILE = "VOLUMES.txt"
VOLUME_LABEL = "VOLUME.txt"
INVENTORY_MD = "INVENTORY.md"
INVENTORY_CSV = "INVENTORY.csv"
RUNBOOK_FILE = "INSIDE.md"
AGENT_RULES_FILE = "AGENTS-INSIDE.md"
SEND_ORDER_FILE = "SEND-ORDER.txt"
INSIDE_SCRIPTS = ("verify.sh", "load.sh")
PART_SUFFIX = ".part{:03d}"
```

Create `$T/scripts/transfer_lib/findings.py`:

```python
"""Bundle check findings: B codes are errors, BW codes are warnings."""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    code: str
    message: str

    @property
    def severity(self) -> str:
        return "warning" if self.code.startswith("BW") else "error"


def has_errors(findings: Iterable[Finding]) -> bool:
    return any(finding.severity == "error" for finding in findings)


def format_text(findings: list[Finding]) -> str:
    if not findings:
        return "OK: no findings"
    lines = [f"{f.code} {f.severity}: {f.message}" for f in findings]
    errors = sum(1 for f in findings if f.severity == "error")
    lines.append(f"{errors} error(s), {len(findings) - errors} warning(s)")
    return "\n".join(lines)


def format_json(findings: list[Finding]) -> str:
    return json.dumps(
        [{"code": f.code, "severity": f.severity, "message": f.message} for f in findings],
        indent=2,
    )
```

Create `$T/scripts/transfer_lib/cli.py`:

```python
"""Argument parsing and exit codes shared by plan.py, pack.py and check.py."""
from __future__ import annotations

import argparse
import sys


def fail(code: int, lines: list[str]) -> None:
    for line in lines:
        print(line, file=sys.stderr)
    raise SystemExit(code)


def make_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--project-root",
        default=".",
        help="the project that holds docs/airgap/ (default: .)",
    )
    return parser
```

- [ ] **Step 5: Run the suite**

Run: `python3.11 -m unittest discover -s tests -t .` and `python3 -m unittest discover -s tests -t .`

Expected: `Ran 431 tests` and `OK` on both. `tests/test_packaging.py` still passes: the new folder has no `SKILL.md` yet and only `.py` files.

- [ ] **Step 6: Commit**

```bash
git add tests/__init__.py tests/test_transfer_foundation.py plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib
git commit -m "feat(transfer): package skeleton, constants, findings and Python guard

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Transfer questions

§8.3. Which questions a transfer needs depends on the channel and the manifest; `answer_problems` is what `plan.py` prints before it plans.

**Files:**
- Create: `$T/scripts/transfer_lib/questions.py`
- Create: `tests/test_transfer_questions.py`

**Interfaces:**
- Consumes: `constants.CHANNELS`, `MEDIUM_CHANNELS`, `FILE_LIMIT_CHANNELS`, `FILESYSTEMS`.
- Produces: `QUESTION_IDS = ("bundle.path", "models", "medium.capacity_gb", "medium.filesystem", "channel.max_file_gb", "include_benchmark")`; `has_benchmark_rows(manifest) -> bool`; `needed_questions(channel, manifest, answers=None) -> list[str]`; `inside_git_repository(path) -> bool`; `answer_problems(answers, channel, manifest, project_root) -> list[str]` (each `"<id>: <problem>"`); `include_benchmark(answers) -> bool` (default `True`). A model source is `{"source": "huggingface", "repo": "<org>/<name>", "revision": "<40 hex>"}` or `{"source": "local", "path": "<absolute folder>"}`, each with optional `"allow_pickle": true|false`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_transfer_questions.py`:

```python
import tempfile
import unittest
from pathlib import Path

from transfer_lib.questions import answer_problems, include_benchmark, inside_git_repository, needed_questions

COMMIT = "0123456789abcdef0123456789abcdef01234567"
MANIFEST = {"models": [{"name": "chat-model", "role": "chat"}], "images": [], "packages": []}


class NeededQuestionsTest(unittest.TestCase):
    def test_per_channel(self):
        self.assertEqual(needed_questions("removable_media", MANIFEST),
                         ["bundle.path", "models", "medium.capacity_gb", "medium.filesystem"])
        self.assertEqual(needed_questions("data_diode", MANIFEST), ["bundle.path", "models", "channel.max_file_gb"])
        self.assertEqual(needed_questions("staging_host", MANIFEST), ["bundle.path", "models", "channel.max_file_gb"])
        self.assertEqual(needed_questions("other", MANIFEST),
                         ["bundle.path", "models", "medium.capacity_gb", "medium.filesystem"])

    def test_other_without_a_medium_skips_the_filesystem(self):
        self.assertEqual(needed_questions("other", MANIFEST, {"medium.capacity_gb": "none"}),
                         ["bundle.path", "models", "medium.capacity_gb"])

    def test_models_and_benchmark_only_when_the_manifest_has_them(self):
        manifest = {"models": [], "images": [{"benchmark": True}], "packages": []}
        self.assertEqual(needed_questions("data_diode", manifest), ["bundle.path", "channel.max_file_gb", "include_benchmark"])

    def test_include_benchmark_defaults_to_true(self):
        self.assertTrue(include_benchmark({}))
        self.assertFalse(include_benchmark({"include_benchmark": False}))


class AnswerProblemsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "project"
        self.project.mkdir()
        self.answers = {
            "bundle.path": str(Path(self.tmp.name) / "bundle"),
            "models": {"chat-model": {"source": "huggingface", "repo": "example/chat", "revision": COMMIT}},
            "medium.capacity_gb": 1000,
            "medium.filesystem": "exfat",
        }

    def problems(self, channel="removable_media", **changes):
        answers = dict(self.answers, **changes)
        return answer_problems(answers, channel, MANIFEST, self.project)

    def test_complete_answers_pass(self):
        self.assertEqual(self.problems(), [])

    def test_missing_answers_are_listed(self):
        self.assertEqual(answer_problems({}, "data_diode", MANIFEST, self.project),
                         ["bundle.path: missing", "models: missing", "channel.max_file_gb: missing"])

    def test_bundle_path_must_be_absolute_and_outside_git(self):
        self.assertEqual(self.problems(**{"bundle.path": "bundle"}), ["bundle.path: must be an absolute path"])
        inside = str(self.project / "bundle")
        self.assertEqual(self.problems(**{"bundle.path": inside}),
                         ["bundle.path: must be outside the git repository: a bundle can be hundreds of gigabytes"])
        repo = Path(self.tmp.name) / "repo"
        (repo / ".git").mkdir(parents=True)
        self.assertTrue(inside_git_repository(repo / "a" / "b"))
        self.assertEqual(self.problems(**{"bundle.path": str(repo / "bundle")}),
                         ["bundle.path: must be outside the git repository: a bundle can be hundreds of gigabytes"])

    def test_model_sources(self):
        local = Path(self.tmp.name) / "weights"
        local.mkdir()
        good = [
            {"source": "huggingface", "repo": "example/chat", "revision": COMMIT},
            {"source": "huggingface", "repo": "example/chat", "revision": COMMIT, "allow_pickle": True},
            {"source": "local", "path": str(local)},
        ]
        for source in good:
            with self.subTest(source=source):
                self.assertEqual(self.problems(models={"chat-model": source}), [])
        bad = [
            ({"source": "huggingface", "repo": "chat", "revision": COMMIT}, "'chat-model': repo must be <organization>/<name>"),
            ({"source": "huggingface", "repo": "example/chat", "revision": "main"},
             "'chat-model': revision must be the full 40-character commit hash; a tag or branch cannot be recorded as what was fetched"),
            ({"source": "local", "path": "weights"}, "'chat-model': path must be an absolute path to an existing folder"),
            ({"source": "ftp"}, "'chat-model': source must be huggingface or local"),
            ({"source": "local", "path": str(local), "allow_pickle": "yes"}, "'chat-model': allow_pickle must be true or false"),
        ]
        for source, message in bad:
            with self.subTest(source=source):
                self.assertEqual(self.problems(models={"chat-model": source}), [f"models: {message}"])
        self.assertEqual(self.problems(models={}), ["models: 'chat-model': missing; give its source"])
        self.assertEqual(self.problems(models={"chat-model": good[0], "other": good[0]}),
                         ["models: 'other': not a model of the manifest"])

    def test_medium_answers(self):
        self.assertEqual(self.problems(**{"medium.capacity_gb": 0}),
                         ["medium.capacity_gb: must be a number of gigabytes above 0"])
        self.assertEqual(self.problems(**{"medium.filesystem": "hfs"}),
                         ["medium.filesystem: must be one of fat32, exfat, ntfs, ext4, other"])
        self.assertEqual(self.problems("other", **{"medium.capacity_gb": "none", "medium.filesystem": None}), [])

    def test_file_limit_answers(self):
        for value in (4, 0.5, "none"):
            self.assertEqual(self.problems("data_diode", **{"channel.max_file_gb": value}), [])
        self.assertEqual(self.problems("staging_host", **{"channel.max_file_gb": -1}),
                         ["channel.max_file_gb: must be a number of gigabytes above 0, or 'none'"])
```

- [ ] **Step 2: Run it to see it fail**

Run: `python3.11 -m unittest tests.test_transfer_questions`

Expected: `ModuleNotFoundError: No module named 'transfer_lib.questions'`, `FAILED (errors=1)`.

- [ ] **Step 3: Write questions.py**

Create `$T/scripts/transfer_lib/questions.py`:

```python
"""The transfer questions (design spec section 8.3): which apply, and whether answers fit."""
from __future__ import annotations

import re
from pathlib import Path

from .constants import FILE_LIMIT_CHANNELS, FILESYSTEMS, MEDIUM_CHANNELS

QUESTION_IDS = (
    "bundle.path",
    "models",
    "medium.capacity_gb",
    "medium.filesystem",
    "channel.max_file_gb",
    "include_benchmark",
)
_REPO = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*")
_COMMIT = re.compile(r"[0-9a-f]{40}")
NONE = "none"


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def has_benchmark_rows(manifest: dict) -> bool:
    rows = list(manifest.get("images", [])) + list(manifest.get("packages", []))
    return any(isinstance(row, dict) and row.get("benchmark") for row in rows)


def needed_questions(channel: str, manifest: dict, answers: dict | None = None) -> list[str]:
    """The questions to ask for this channel and manifest, in order."""
    answers = answers or {}
    needed = ["bundle.path"]
    if manifest.get("models"):
        needed.append("models")
    if channel in MEDIUM_CHANNELS:
        needed.append("medium.capacity_gb")
        if not (channel == "other" and answers.get("medium.capacity_gb") == NONE):
            needed.append("medium.filesystem")
    if channel in FILE_LIMIT_CHANNELS:
        needed.append("channel.max_file_gb")
    if has_benchmark_rows(manifest):
        needed.append("include_benchmark")
    return needed


def inside_git_repository(path: Path) -> bool:
    """True when `path`, or the nearest folder above it that exists, is in a git work tree."""
    for folder in [Path(path), *Path(path).parents]:
        if (folder / ".git").exists():
            return True
    return False


def _bundle_path_problems(value, project_root: Path) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return ["must be a path"]
    path = Path(value)
    if not path.is_absolute():
        return ["must be an absolute path"]
    root = Path(project_root).resolve()
    resolved = path.resolve()
    if resolved == root or root in resolved.parents or inside_git_repository(resolved):
        return ["must be outside the git repository: a bundle can be hundreds of gigabytes"]
    if resolved.exists() and not resolved.is_dir():
        return ["exists and is not a folder"]
    return []


def _model_problems(value, manifest: dict) -> list[str]:
    names = [model.get("name") for model in manifest.get("models", []) if isinstance(model, dict)]
    if not isinstance(value, dict):
        return ["must be an object with one entry per model: " + ", ".join(names)]
    problems = []
    for name in names:
        source = value.get(name)
        where = f"'{name}'"
        if not isinstance(source, dict):
            problems.append(f"{where}: missing; give its source")
            continue
        if "allow_pickle" in source and not isinstance(source["allow_pickle"], bool):
            problems.append(f"{where}: allow_pickle must be true or false")
        if source.get("source") == "huggingface":
            if not isinstance(source.get("repo"), str) or not _REPO.fullmatch(source["repo"]):
                problems.append(f"{where}: repo must be <organization>/<name>")
            if not isinstance(source.get("revision"), str) or not _COMMIT.fullmatch(source["revision"]):
                problems.append(
                    f"{where}: revision must be the full 40-character commit hash; a tag or "
                    "branch cannot be recorded as what was fetched"
                )
        elif source.get("source") == "local":
            path = source.get("path")
            if not isinstance(path, str) or not Path(path).is_absolute() or not Path(path).is_dir():
                problems.append(f"{where}: path must be an absolute path to an existing folder")
        else:
            problems.append(f"{where}: source must be huggingface or local")
    for extra in sorted(set(value) - set(names)):
        problems.append(f"'{extra}': not a model of the manifest")
    return problems


def answer_problems(answers: dict, channel: str, manifest: dict, project_root: Path) -> list[str]:
    """'question id: reason' for every needed answer that is missing or does not fit."""
    problems = []
    for question_id in needed_questions(channel, manifest, answers):
        value = answers.get(question_id)
        if value is None:
            if question_id != "include_benchmark":
                problems.append(f"{question_id}: missing")
            continue
        if question_id == "bundle.path":
            reasons = _bundle_path_problems(value, project_root)
        elif question_id == "models":
            reasons = _model_problems(value, manifest)
        elif question_id == "medium.capacity_gb":
            allowed_none = channel == "other" and value == NONE
            reasons = [] if allowed_none or (_is_number(value) and value > 0) else [
                "must be a number of gigabytes above 0" + (", or 'none'" if channel == "other" else "")
            ]
        elif question_id == "medium.filesystem":
            reasons = [] if value in FILESYSTEMS else ["must be one of " + ", ".join(FILESYSTEMS)]
        elif question_id == "channel.max_file_gb":
            reasons = [] if value == NONE or (_is_number(value) and value > 0) else [
                "must be a number of gigabytes above 0, or 'none'"
            ]
        else:
            reasons = [] if isinstance(value, bool) else ["must be true or false"]
        problems += [f"{question_id}: {reason}" for reason in reasons]
    return problems


def include_benchmark(answers: dict) -> bool:
    return answers.get("include_benchmark", True) is not False
```

- [ ] **Step 4: Run the suite**

Run both suite commands. Expected: `Ran 441 tests`, `OK` on both.

- [ ] **Step 5: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/questions.py tests/test_transfer_questions.py
git commit -m "feat(transfer): the transfer questions and their checks

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Inputs, transfer.json and the item list

§8.2 step 1, §8.4 "Items", §9.1, §9.3. The skill reads architect's two files without architect's code: `architect_digest` repeats architect's digest algorithm, and a test pins it against `airgap_lib.blueprint.inputs_digest`.

**Files:**
- Create: `$T/scripts/transfer_lib/inputs.py`, `state.py`, `items.py`
- Create: `tests/transfer_projects.py` (builders shared by the later transfer tests)
- Create: `tests/test_transfer_inputs.py`, `tests/test_transfer_items.py`

**Interfaces:**
- Consumes: `questions.include_benchmark`; architect's `transfer-manifest.json` keys (Task 3).
- Produces:
  - `inputs.InputError`; `read_json(path) -> dict`; `architect_digest(blueprint) -> str`; `airgap_dir(project_root) -> Path`; `load_inputs(project_root) -> (blueprint, manifest)`, which raises `InputError` for a missing file ("run airgap-architect first"), a schema other than 1, a stale manifest ("is older than blueprint.json: run airgap-architect's manifest.py again") or an empty `platform`; `blueprint_answer(blueprint, qid)` (an `unknown` answer resolves to the blueprint's assumption `answers.<qid>`); `channel_of`, `operator_of`, `language_of`.
  - `state.state_path(project_root)`, `new_state(manifest_digest)`, `state_problems(state) -> list[str]`, `load_state(path)`, `save_state(path, state)`; `MANUAL_STATUSES = ("added", "not_needed")`: `added` needs a `path` under `manual/`, `not_needed` needs a `reason`.
  - `items.safe_name(text)`, `image_archive(component, ref) -> "images/<component>/<safe ref>.tar"`, `manual_items(manifest, keep_benchmark=True)`, `build_items(manifest, answers) -> list[dict]` with ids `image:<component>:<ref>`, `model:<name>`, `package:<component>:<file>`, `manual:<name>` (a runtime download is named `<component>: runtime download N`), `checksums_path(item) -> "packages/<component>/checksums/<basename>" | None`.
  - `tests.transfer_projects`: `COMMIT`, `SUMS_URL`, `transfer_catalog(root)`, `make_project(root, catalog, answers=None, decisions=None, language="en")`, `default_answers(bundle, **overrides)`, `write_state(project, answers, manual=(), plan=None)`, `image_archive(ref, arch="amd64", payload=b"layer") -> bytes` (a small archive with `manifest.json` and a config), `fake_fetch(bundle, items, sizes=None, arch="amd64")`, `run_script(name, project, *args, env=None)`, `planned_project(tmp, ...) -> (project, bundle)`, `load_state_of`, `update_state`, `settle_manual`, `packed_project(tmp, sizes=None, **kwargs)`. The last three call `pack.py`, which arrives in Task 12; nothing calls them before then.

- [ ] **Step 1: Write the test builders and the failing tests**

Create `tests/transfer_projects.py`:

```python
"""Builders for airgap-transfer tests: a finished architect project, transfer.json answers
and a fake fetched bundle. The architect side is built with airgap-architect's own code,
so these tests also check that the two skills agree on the manifest."""
from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

from airgap_lib.catalog import Catalog
from tests import projects, support
from transfer_lib.items import checksums_path
from transfer_lib.state import new_state, save_state, state_path

COMMIT = "0123456789abcdef0123456789abcdef01234567"
SUMS_URL = "https://downloads.example.test/alpha/SHA256SUMS"


def transfer_catalog(root: Path) -> Catalog:
    """The fixture catalog with packages on the engine: one per architecture and a script."""
    components = support.fixture_components()
    components[0] = support.component(
        "alpha-engine",
        "llm-serving",
        airgap={
            "images": [{"ref": "registry.example.test/synthetic/alpha-engine:1.2.3", "digest": ""}],
            "packages": [
                support.package("alpha-cli-1.2.3-amd64", "amd64", SUMS_URL),
                support.package("alpha-cli-1.2.3-arm64", "arm64", SUMS_URL),
                support.package("install.sh", "any"),
            ],
            "runtime_downloads": ["Tokenizer data, fetched on first start."],
            "telemetry": [{"what": "usage ping", "disable": "ALPHA_PING=0"}],
        },
    )
    return support.load_fixture_catalog(Path(root), components)


def make_project(root: Path, catalog: Catalog, answers=None, decisions=None, language="en") -> Path:
    """A project with blueprint.json and both manifest files; returns the project root."""
    blueprint = projects.build_blueprint(catalog, answers, decisions)
    blueprint["language"] = language
    projects.write_project(Path(root), catalog, blueprint)
    return Path(root)


def default_answers(bundle: Path, **overrides) -> dict:
    answers = {
        "bundle.path": str(bundle),
        "models": {"example-70b": {"source": "huggingface", "repo": "example/model-70b", "revision": COMMIT}},
        "medium.capacity_gb": 1000,
        "medium.filesystem": "exfat",
    }
    answers.update(overrides)
    return answers


def write_state(project: Path, answers: dict, manual=(), plan=None) -> Path:
    manifest = json.loads((project / "docs" / "airgap" / "transfer-manifest.json").read_text(encoding="utf-8"))
    state = new_state(manifest["inputs_digest"])
    state["answers"] = answers
    state["manual"] = list(manual)
    if plan is not None:
        state["plan"] = plan
    path = state_path(project)
    save_state(path, state)
    return path


def image_archive(ref: str, arch: str = "amd64", payload: bytes = b"layer") -> bytes:
    """A small archive in the layout docker load reads: manifest.json, a config, a layer."""
    config = json.dumps({"architecture": arch, "os": "linux"}).encode()
    config_name = "blobs/sha256/" + hashlib.sha256(config).hexdigest()
    layer_name = "blobs/sha256/" + hashlib.sha256(payload).hexdigest()
    manifest = json.dumps([{"Config": config_name, "RepoTags": [ref], "Layers": [layer_name]}]).encode()
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, data in (("manifest.json", manifest), (config_name, config), (layer_name, payload)):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def fake_fetch(bundle: Path, items: list[dict], sizes: dict | None = None, arch: str = "amd64") -> None:
    """Write what fetch.sh would leave for every non-manual item. `sizes` maps an item id
    to the number of bytes of its main file (default: a few bytes)."""
    sizes = sizes or {}
    bundle = Path(bundle)
    lists: dict[Path, list[str]] = {}
    for item in items:
        target = bundle / item["path"]
        size = sizes.get(item["id"])
        if item["kind"] == "image":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(image_archive(item["ref"], arch, b"x" * (size or 5)))
            target.with_suffix(".digest").write_text("sha256:" + "a" * 64 + "\n", encoding="utf-8")
        elif item["kind"] == "model":
            target.mkdir(parents=True, exist_ok=True)
            (target / "model.safetensors").write_bytes(b"w" * (size or 7))
            (target / "config.json").write_text("{}", encoding="utf-8")
            (target / "LICENSE").write_text("Example licence\n", encoding="utf-8")
        elif item["kind"] == "package":
            target.parent.mkdir(parents=True, exist_ok=True)
            data = (item["file"].encode() * ((size or 9) // max(1, len(item["file"])) + 1))[: size or 9]
            target.write_bytes(data)
            listed = checksums_path(item)
            if listed:
                lists.setdefault(bundle / listed, []).append(f"{hashlib.sha256(data).hexdigest()}  {item['file']}")
    for path, lines in lists.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_script(name: str, project: Path, *args, env=None):
    """Run one of airgap-transfer's scripts as the agent does; returns the CompletedProcess."""
    import subprocess
    import sys

    from tests import TRANSFER_SCRIPTS_DIR

    command = [sys.executable, str(TRANSFER_SCRIPTS_DIR / name), "--project-root", str(project), *args]
    return subprocess.run(command, capture_output=True, text=True, env=env)


def planned_project(tmp: Path, answers=None, architect_answers=None, decisions=None, language="en", **transfer):
    """A project whose transfer.json has answers and a plan (made without plan.py, so no
    tools are needed), and an empty bundle folder. Returns (project, bundle)."""
    from transfer_lib.inputs import channel_of
    from transfer_lib.items import build_items

    tmp = Path(tmp)
    catalog = transfer_catalog(tmp / "catalog")
    architect_answers = support.base_answers(**(architect_answers or {}))
    project = make_project(tmp / "project", catalog, architect_answers, decisions, language)
    bundle = tmp / "bundle"
    bundle.mkdir(exist_ok=True)
    answers = default_answers(bundle, **transfer) if answers is None else answers
    folder = project / "docs" / "airgap"
    manifest = json.loads((folder / "transfer-manifest.json").read_text(encoding="utf-8"))
    blueprint = json.loads((folder / "blueprint.json").read_text(encoding="utf-8"))
    plan = {
        "items": build_items(manifest, answers),
        "tools": {},
        "platform": manifest["platform"],
        "channel": channel_of(blueprint),
        "planned": "2026-11-22T10:00:00Z",
    }
    write_state(project, answers, plan=plan)
    return project, bundle


def load_state_of(project: Path) -> dict:
    from transfer_lib.state import load_state, state_path

    return load_state(state_path(project))


def update_state(project: Path, change) -> dict:
    from transfer_lib.state import save_state, state_path

    state = load_state_of(project)
    change(state)
    save_state(state_path(project), state)
    return state


def settle_manual(project: Path) -> None:
    """Mark every manual item of the plan 'not needed', with a reason."""
    def change(state):
        state["manual"] = [
            {"item": item["name"], "status": "not_needed", "reason": "Staged by the operator from an earlier transfer."}
            for item in state["plan"]["items"]
            if item["kind"] == "manual"
        ]
    update_state(project, change)


def packed_project(tmp: Path, sizes=None, **kwargs):
    """planned_project, fetched with fake files, manual items settled and packed with pack.py.
    Returns (project, bundle)."""
    project, bundle = planned_project(tmp, **kwargs)
    fake_fetch(bundle, load_state_of(project)["plan"]["items"], sizes)
    settle_manual(project)
    result = run_script("pack.py", project)
    assert result.returncode == 0, result.stdout + result.stderr
    return project, bundle
```

Create `tests/test_transfer_inputs.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from tests import projects, support, transfer_projects
from airgap_lib.blueprint import inputs_digest
from transfer_lib.inputs import (
    InputError,
    architect_digest,
    blueprint_answer,
    channel_of,
    language_of,
    load_inputs,
    operator_of,
)
from transfer_lib.state import load_state, new_state, save_state, state_problems


class ArchitectDigestTest(unittest.TestCase):
    """The transfer skill repeats architect's digest; the two must never drift apart."""

    def test_both_skills_compute_the_same_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = support.load_fixture_catalog(Path(tmp))
            cases = [
                projects.build_blueprint(catalog),
                projects.build_blueprint(catalog, support.base_answers(**{"hardware.cpu_arch": "arm64"})),
                {"answers": {}, "decisions": []},
                {"answers": {"workload.models": [{"name": "ü", "role": "chat", "weights_gb": 1.5}]}},
            ]
            for blueprint in cases:
                with self.subTest(blueprint=str(blueprint)[:60]):
                    self.assertEqual(architect_digest(blueprint), inputs_digest(blueprint))


class LoadInputsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        catalog = transfer_projects.transfer_catalog(Path(self.tmp.name) / "catalog")
        self.project = transfer_projects.make_project(Path(self.tmp.name) / "project", catalog)
        self.folder = self.project / "docs" / "airgap"

    def error(self):
        with self.assertRaises(InputError) as caught:
            load_inputs(self.project)
        return str(caught.exception)

    def test_a_finished_project_loads(self):
        blueprint, manifest = load_inputs(self.project)
        self.assertEqual(manifest["platform"], "linux/amd64")
        self.assertEqual(manifest["inputs_digest"], architect_digest(blueprint))

    def test_missing_files_name_the_architect_step(self):
        (self.folder / "transfer-manifest.json").unlink()
        self.assertIn("run airgap-architect's manifest.py first", self.error())
        (self.folder / "blueprint.json").unlink()
        self.assertIn("design the system with airgap-architect first", self.error())

    def test_a_manifest_older_than_the_blueprint_is_refused(self):
        data = json.loads((self.folder / "blueprint.json").read_text(encoding="utf-8"))
        data["answers"]["hardware.cpu_arch"] = "arm64"
        (self.folder / "blueprint.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("is older than blueprint.json", self.error())

    def test_a_manifest_without_platform_is_refused(self):
        data = json.loads((self.folder / "transfer-manifest.json").read_text(encoding="utf-8"))
        data["platform"] = ""
        (self.folder / "transfer-manifest.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("answer hardware.cpu_arch", self.error())

    def test_another_schema_version_is_refused(self):
        data = json.loads((self.folder / "transfer-manifest.json").read_text(encoding="utf-8"))
        data["schema_version"] = 2
        (self.folder / "transfer-manifest.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("schema_version must be 1", self.error())

    def test_invalid_json_is_an_input_error(self):
        (self.folder / "transfer-manifest.json").write_text("{", encoding="utf-8")
        self.assertIn("invalid JSON", self.error())


class BlueprintAnswerTest(unittest.TestCase):
    def test_unknown_takes_the_default_architect_recorded(self):
        blueprint = {
            "answers": {"transfer.channel": "unknown", "inside.operator": "local_agent"},
            "assumptions": [{"id": "answers.transfer.channel", "value": "removable_media", "evidence": "estimate"}],
        }
        self.assertEqual(blueprint_answer(blueprint, "transfer.channel"), "removable_media")
        self.assertEqual(channel_of(blueprint), "removable_media")
        self.assertEqual(operator_of(blueprint), "local_agent")

    def test_an_unusable_answer_is_an_input_error(self):
        for key, function in (("transfer.channel", channel_of), ("inside.operator", operator_of)):
            with self.subTest(key=key):
                with self.assertRaises(InputError):
                    function({"answers": {key: "unknown"}, "assumptions": []})

    def test_language_defaults_to_english(self):
        self.assertEqual(language_of({"language": "tr"}), "tr")
        self.assertEqual(language_of({}), "en")


class StateTest(unittest.TestCase):
    def test_a_new_state_is_valid_and_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "docs" / "airgap" / "transfer.json"
            state = new_state("sha256:abc")
            save_state(path, state)
            self.assertEqual(load_state(path), state)
            self.assertEqual(state_problems(state), [])

    def test_manual_entries_are_checked(self):
        state = new_state("sha256:abc")
        state["manual"] = [
            {"item": "a", "status": "added", "path": "elsewhere/a"},
            {"item": "b", "status": "not_needed"},
            {"item": "c", "status": "maybe"},
            {"status": "added"},
        ]
        self.assertEqual(
            state_problems(state),
            [
                "manual[0]: an added item needs a 'path' under manual/",
                "manual[1]: an item marked not needed needs a 'reason'",
                "manual[2].status must be one of added, not_needed",
                "manual[3] needs an 'item' name",
            ],
        )

    def test_wrong_types_are_listed(self):
        state = new_state("sha256:abc")
        state["answers"] = []
        state["schema_version"] = True
        self.assertEqual(state_problems(state), ["'schema_version' must be of type int", "'answers' must be of type dict"])


if __name__ == "__main__":
    unittest.main()
```

Create `tests/test_transfer_items.py`:

```python
import unittest

import tests  # noqa: F401  (puts both skills' scripts on sys.path)
from transfer_lib.items import build_items, checksums_path, image_archive, safe_name

MANIFEST = {
    "images": [
        {"component": "alpha", "version": "1", "ref": "registry.example.test/a/alpha:1", "digest": "", "license": "MIT", "benchmark": False},
        {"component": "beta", "version": "2", "ref": "beta:2", "digest": "", "license": "MIT", "benchmark": True},
    ],
    "models": [{"name": "chat model", "role": "chat"}],
    "packages": [
        {"component": "alpha", "version": "1", "file": "alpha-1-amd64.tgz", "arch": "amd64",
         "url": "https://downloads.example.test/alpha-1-amd64.tgz", "checksums": "https://downloads.example.test/md5sum",
         "license": "MIT", "benchmark": False},
    ],
    "custom": [{"layer": "orchestration", "name": "Docker Engine (outside the catalog)"}],
    "runtime_downloads": [{"component": "alpha", "text": "Tokenizer files.", "benchmark": False},
                          {"component": "beta", "text": "Price table.", "benchmark": True}],
}
SOURCE = {"source": "huggingface", "repo": "example/chat", "revision": "0" * 40}


class ItemsTest(unittest.TestCase):
    def items(self, **answers):
        return build_items(MANIFEST, {"models": {"chat model": SOURCE}, **answers})

    def test_one_item_per_image_model_package_and_manual_item(self):
        self.assertEqual(
            [item["id"] for item in self.items()],
            [
                "image:alpha:registry.example.test/a/alpha:1",
                "image:beta:beta:2",
                "model:chat model",
                "package:alpha:alpha-1-amd64.tgz",
                "manual:Docker Engine (outside the catalog)",
                "manual:alpha: runtime download 1",
                "manual:beta: runtime download 1",
            ],
        )

    def test_benchmark_rows_can_be_left_out(self):
        ids = [item["id"] for item in self.items(include_benchmark=False)]
        self.assertNotIn("image:beta:beta:2", ids)
        self.assertNotIn("manual:beta: runtime download 1", ids)

    def test_paths_in_the_bundle(self):
        items = {item["id"]: item for item in self.items()}
        self.assertEqual(items["image:alpha:registry.example.test/a/alpha:1"]["path"],
                         "images/alpha/registry.example.test_a_alpha_1.tar")
        self.assertEqual(items["model:chat model"]["path"], "models/chat_model")
        self.assertEqual(items["model:chat model"]["source"], SOURCE)
        package = items["package:alpha:alpha-1-amd64.tgz"]
        self.assertEqual(package["path"], "packages/alpha/alpha-1-amd64.tgz")
        self.assertEqual(checksums_path(package), "packages/alpha/checksums/md5sum")
        self.assertEqual(items["manual:Docker Engine (outside the catalog)"]["path"],
                         "manual/Docker_Engine_outside_the_catalog")

    def test_safe_names(self):
        self.assertEqual(safe_name("one very large chat model"), "one_very_large_chat_model")
        self.assertEqual(safe_name("../.."), "item")
        self.assertEqual(image_archive("vllm", "vllm/vllm-openai:v0.34.0"), "images/vllm/vllm_vllm-openai_v0.34.0.tar")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to see them fail**

Run: `python3.11 -m unittest tests.test_transfer_inputs tests.test_transfer_items`

Expected: both modules fail to import with `ModuleNotFoundError: No module named 'transfer_lib.items'`, `FAILED (errors=2)`.

- [ ] **Step 3: Write inputs.py, state.py and items.py**

Create `$T/scripts/transfer_lib/inputs.py`:

```python
"""The files airgap-architect leaves in the project, read without its code.

`architect_digest` repeats airgap-architect's `inputs_digest` (airgap_lib/blueprint.py)
so that this skill can tell whether transfer-manifest.json still matches
blueprint.json. tests/test_transfer_inputs.py checks that the two agree.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .constants import (
    AIRGAP_DIR,
    BLUEPRINT_FILE,
    CHANNELS,
    MANIFEST_FILE,
    MANIFEST_SCHEMA_VERSION,
    OPERATORS,
)

UNKNOWN = "unknown"


class InputError(Exception):
    """A file this skill reads is missing, unreadable or does not fit; exit 2."""


def _reject_constant(name: str):
    raise ValueError(f"non-finite number {name} is not allowed")


def read_json(path: Path) -> dict:
    """A JSON object from `path`; InputError naming the path otherwise."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise InputError(f"{path}: file not found") from None
    except UnicodeDecodeError:
        raise InputError(f"{path}: not readable as UTF-8 text") from None
    except OSError as error:
        raise InputError(f"{path}: cannot be read ({error.strerror or type(error).__name__})") from None
    try:
        data = json.loads(text, parse_constant=_reject_constant)
    except (ValueError, RecursionError) as error:
        raise InputError(f"{path}: invalid JSON ({error})") from None
    if not isinstance(data, dict):
        raise InputError(f"{path}: the top level must be an object")
    return data


def architect_digest(blueprint: dict) -> str:
    """The digest airgap-architect records in its transfer manifest."""
    answers = blueprint.get("answers") or {}
    payload = {
        "decisions": blueprint.get("decisions", []),
        "models": answers.get("workload.models", []),
        "hardware": answers.get("hardware.gpus", []),
        "cpu_arch": answers.get("hardware.cpu_arch"),
    }
    canonical = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def airgap_dir(project_root: Path) -> Path:
    return Path(project_root) / AIRGAP_DIR


def load_inputs(project_root: Path) -> tuple[dict, dict]:
    """(blueprint, manifest) of a project; InputError when either is missing or stale."""
    folder = airgap_dir(project_root)
    if not (folder / BLUEPRINT_FILE).is_file():
        raise InputError(
            f"{AIRGAP_DIR}/{BLUEPRINT_FILE} not found: design the system with airgap-architect first"
        )
    if not (folder / MANIFEST_FILE).is_file():
        raise InputError(
            f"{AIRGAP_DIR}/{MANIFEST_FILE} not found: run airgap-architect's manifest.py first"
        )
    blueprint = read_json(folder / BLUEPRINT_FILE)
    manifest = read_json(folder / MANIFEST_FILE)
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise InputError(
            f"{AIRGAP_DIR}/{MANIFEST_FILE}: schema_version must be {MANIFEST_SCHEMA_VERSION}"
        )
    if manifest.get("inputs_digest") != architect_digest(blueprint):
        raise InputError(
            f"{AIRGAP_DIR}/{MANIFEST_FILE} is older than {BLUEPRINT_FILE}: "
            "run airgap-architect's manifest.py again"
        )
    if not manifest.get("platform"):
        raise InputError(
            f"{AIRGAP_DIR}/{MANIFEST_FILE} names no platform: answer hardware.cpu_arch "
            "with airgap-architect and run its manifest.py again"
        )
    return blueprint, manifest


def blueprint_answer(blueprint: dict, question_id: str):
    """An architect answer, with the default architect applied for 'unknown'.

    The default comes from the assumption airgap-architect recorded for it, so this
    skill needs no copy of architect's rules. None when neither is there.
    """
    value = (blueprint.get("answers") or {}).get(question_id)
    if value != UNKNOWN:
        return value
    for item in blueprint.get("assumptions") or []:
        if isinstance(item, dict) and item.get("id") == f"answers.{question_id}":
            return item.get("value")
    return None


def channel_of(blueprint: dict) -> str:
    channel = blueprint_answer(blueprint, "transfer.channel")
    if channel not in CHANNELS:
        raise InputError(
            "blueprint.json: transfer.channel must be one of " + ", ".join(CHANNELS)
            + "; finish the design with airgap-architect"
        )
    return channel


def operator_of(blueprint: dict) -> str:
    operator = blueprint_answer(blueprint, "inside.operator")
    if operator not in OPERATORS:
        raise InputError(
            "blueprint.json: inside.operator must be one of " + ", ".join(OPERATORS)
            + "; answer it with airgap-architect"
        )
    return operator


def language_of(blueprint: dict) -> str:
    language = blueprint.get("language")
    return language if isinstance(language, str) and language.strip() else "en"
```

Create `$T/scripts/transfer_lib/state.py`:

```python
"""docs/airgap/transfer.json: the state of one transfer."""
from __future__ import annotations

import json
from pathlib import Path

from .constants import AIRGAP_DIR, STATE_FILE, STATE_SCHEMA_VERSION
from .inputs import InputError, read_json

_TOP_LEVEL = (
    ("schema_version", int),
    ("manifest_digest", str),
    ("answers", dict),
    ("plan", dict),
    ("manual", list),
    ("pack", dict),
)
MANUAL_STATUSES = ("added", "not_needed")


def state_path(project_root: Path) -> Path:
    return Path(project_root) / AIRGAP_DIR / STATE_FILE


def new_state(manifest_digest: str) -> dict:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "manifest_digest": manifest_digest,
        "answers": {},
        "plan": {},
        "manual": [],
        "pack": {},
    }


def state_problems(state: dict) -> list[str]:
    problems = []
    for key, kind in _TOP_LEVEL:
        if not isinstance(state.get(key), kind) or isinstance(state.get(key), bool):
            problems.append(f"'{key}' must be of type {kind.__name__}")
    if not problems and state["schema_version"] != STATE_SCHEMA_VERSION:
        problems.append(f"'schema_version' must be {STATE_SCHEMA_VERSION}")
    for index, entry in enumerate(state.get("manual") if isinstance(state.get("manual"), list) else []):
        where = f"manual[{index}]"
        if not isinstance(entry, dict) or not isinstance(entry.get("item"), str) or not entry["item"].strip():
            problems.append(f"{where} needs an 'item' name")
            continue
        status = entry.get("status")
        if status not in MANUAL_STATUSES:
            problems.append(f"{where}.status must be one of " + ", ".join(MANUAL_STATUSES))
        elif status == "added" and not (isinstance(entry.get("path"), str) and entry["path"].startswith("manual/")):
            problems.append(f"{where}: an added item needs a 'path' under manual/")
        elif status == "not_needed" and not (isinstance(entry.get("reason"), str) and entry["reason"].strip()):
            problems.append(f"{where}: an item marked not needed needs a 'reason'")
    return problems


def load_state(path: Path) -> dict:
    state = read_json(path)
    problems = state_problems(state)
    if problems:
        raise InputError(f"{path}: " + "; ".join(problems))
    return state


def save_state(path: Path, state: dict) -> None:
    path = Path(path)
    text = json.dumps(state, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
```

Create `$T/scripts/transfer_lib/items.py`:

```python
"""The item list of a transfer: one item per image, model, package and manual item."""
from __future__ import annotations

import re

from .questions import include_benchmark

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_name(text: str) -> str:
    """A file or folder name from free text: letters, digits, '.', '_' and '-' only."""
    name = _UNSAFE.sub("_", str(text)).strip("._-")
    return name or "item"


def image_archive(component: str, ref: str) -> str:
    """Bundle path of an image archive, relative to the bundle folder."""
    return f"images/{safe_name(component)}/{safe_name(ref)}.tar"


def _unique(path: str, taken: set[str]) -> str:
    candidate, number = path, 2
    while candidate in taken:
        candidate, number = f"{path}-{number}", number + 1
    taken.add(candidate)
    return candidate


def manual_items(manifest: dict, keep_benchmark: bool = True) -> list[dict]:
    """Custom parts and runtime downloads of the manifest, as items the user settles by hand."""
    items = []
    for row in manifest.get("custom", []):
        items.append(
            {
                "kind": "manual",
                "name": row["name"],
                "text": f"A custom part of the {row.get('layer') or 'design'} layer, outside the catalog.",
            }
        )
    counts: dict[str, int] = {}
    for row in manifest.get("runtime_downloads", []):
        if row.get("benchmark") and not keep_benchmark:
            continue
        counts[row["component"]] = counts.get(row["component"], 0) + 1
        items.append(
            {
                "kind": "manual",
                "name": f"{row['component']}: runtime download {counts[row['component']]}",
                "text": row["text"],
            }
        )
    return items


def build_items(manifest: dict, answers: dict) -> list[dict]:
    """Every item of the plan, each with a unique `id` and a bundle `path`."""
    keep_benchmark = include_benchmark(answers)
    sources = answers.get("models") or {}
    items: list[dict] = []
    taken: set[str] = set()
    for row in manifest.get("images", []):
        if row.get("benchmark") and not keep_benchmark:
            continue
        items.append(
            {
                "id": f"image:{row['component']}:{row['ref']}",
                "kind": "image",
                "component": row["component"],
                "version": row["version"],
                "ref": row["ref"],
                "digest": row.get("digest", ""),
                "license": row.get("license", ""),
                "benchmark": bool(row.get("benchmark")),
                "path": _unique(image_archive(row["component"], row["ref"]), taken),
            }
        )
    for row in manifest.get("models", []):
        source = dict(sources.get(row["name"]) or {})
        items.append(
            {
                "id": f"model:{row['name']}",
                "kind": "model",
                "name": row["name"],
                "role": row.get("role", ""),
                "source": {key: source[key] for key in ("source", "repo", "revision", "path") if key in source},
                "allow_pickle": source.get("allow_pickle") is True,
                "path": _unique(f"models/{safe_name(row['name'])}", taken),
            }
        )
    for row in manifest.get("packages", []):
        if row.get("benchmark") and not keep_benchmark:
            continue
        items.append(
            {
                "id": f"package:{row['component']}:{row['file']}",
                "kind": "package",
                "component": row["component"],
                "version": row["version"],
                "file": row["file"],
                "arch": row["arch"],
                "url": row["url"],
                "checksums": row.get("checksums", ""),
                "license": row.get("license", ""),
                "benchmark": bool(row.get("benchmark")),
                "path": _unique(f"packages/{safe_name(row['component'])}/{safe_name(row['file'])}", taken),
            }
        )
    for item in manual_items(manifest, keep_benchmark):
        items.append(
            dict(item, id=f"manual:{item['name']}", path=_unique(f"manual/{safe_name(item['name'])}", taken))
        )
    return items


def checksums_path(item: dict) -> str | None:
    """Where fetch.sh keeps the publisher's checksum file of a package item."""
    url = item.get("checksums") or ""
    if item.get("kind") != "package" or not url:
        return None
    return f"packages/{safe_name(item['component'])}/checksums/{safe_name(url.rsplit('/', 1)[-1])}"
```

- [ ] **Step 4: Run the suite**

Run both suite commands. Expected: `Ran 458 tests`, `OK` on both.

- [ ] **Step 5: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/inputs.py \
  plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/state.py \
  plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/items.py \
  tests/transfer_projects.py tests/test_transfer_inputs.py tests/test_transfer_items.py
git commit -m "feat(transfer): read architect's files, keep transfer.json, list the items

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Tools and their command lines (research)

§8.4 "Tools", §14 first row. `tools.py` holds one table of every command line the skill writes into a shell script, so the lines are read from documentation once, in one place, with their sources. `plan.py` only looks tools up on `PATH`; it never runs them.

**Files:**
- Create: `$T/scripts/transfer_lib/tools.py`
- Create: `tests/test_transfer_tools.py`

**Interfaces:**
- Consumes: the item dicts of `items.build_items`.
- Produces: `Command(tool, does, uses, line, source)` (frozen dataclass); `COMMANDS: dict[str, Command]` with the keys `skopeo.copy`, `skopeo.digest`, `docker.pull`, `docker.save`, `docker.digest`, `docker.load`, `docker.image_id`, `hf.download`, `hf.include`, `curl.download`, `md5sum.hash`, `md5.hash`, `sha256sum.hash`, `shasum.sha256`, `sha512sum.hash`, `shasum.sha512`; `COPIER = "skopeo"`, `IMAGE_TOOLS = (COPIER, "docker")`, `HASH_TOOLS`, `HASH_COMMANDS[(algorithm, tool)] -> key`, `TEMPLATE_COMMANDS = ("docker.load", "docker.image_id")` (the two lines `pack.py` writes into `load.sh`); `MissingToolError(missing)` with `.missing = {tool or alternatives: [item ids]}`; `find_tools(items, which=shutil.which) -> {"images": ..., "models": ..., "packages": ..., "hash.md5": ..., ...}` with only the jobs the items need.

- [ ] **Step 1: Write the failing test**

Create `tests/test_transfer_tools.py`:

```python
import unittest

from tests.test_transfer_items import MANIFEST, SOURCE
from transfer_lib.items import build_items
from transfer_lib.tools import COMMANDS, MissingToolError, find_tools


class ToolsTest(unittest.TestCase):
    def items(self):
        return build_items(MANIFEST, {"models": {"chat model": SOURCE}})

    def test_the_preferred_tool_is_chosen(self):
        everything = lambda name: f"/usr/bin/{name}"  # noqa: E731
        tools = find_tools(self.items(), everything)
        self.assertEqual(tools["images"], "skopeo")
        self.assertEqual((tools["models"], tools["packages"]), ("hf", "curl"))
        self.assertEqual(tools["hash.md5"], "md5sum")

    def test_docker_is_used_without_the_copier(self):
        tools = find_tools(self.items(), lambda name: None if name == "skopeo" else name)
        self.assertEqual(tools["images"], "docker")

    def test_a_missing_tool_names_what_needs_it(self):
        with self.assertRaises(MissingToolError) as caught:
            find_tools(self.items(), lambda name: None if name in ("hf", "curl") else name)
        self.assertEqual(caught.exception.missing, {"hf": ["model:chat model"], "curl": ["package:alpha:alpha-1-amd64.tgz"]})

    def test_only_the_tools_the_items_need(self):
        self.assertEqual(find_tools([], lambda name: None), {})


class CommandTableTest(unittest.TestCase):
    """Each command line is filled from the tool's documentation (references/fetch.md)."""

    def test_every_command_is_filled_and_sourced(self):
        for key, command in COMMANDS.items():
            with self.subTest(command=key):
                self.assertTrue(command.line.strip(), "fill `line` from the documentation")
                self.assertTrue(command.source.startswith("https://"), "record the page in `source`")
                for variable in command.uses:
                    self.assertIn(variable, command.line)
                if command.uses:
                    self.assertTrue(command.line.startswith(command.tool + " "), command.line)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to see it fail**

Run: `python3.11 -m unittest tests.test_transfer_tools`

Expected: `ModuleNotFoundError: No module named 'transfer_lib.tools'`, `FAILED (errors=1)`.

- [ ] **Step 3: Write tools.py with the lines still empty**

Create `$T/scripts/transfer_lib/tools.py`. Every `line` and `source` is `""` here on purpose: Step 5 fills them from the documentation.

```python
"""The tools fetch.sh runs on the connected side, and the command lines it uses.

Every command line comes from the tool's own documentation, read when this file was
written, with the page in `source` (principle "nothing from memory"). A line is a
shell snippet that may use only the variables in `uses`; fetch.sh sets them before
it runs the line. references/fetch.md repeats each source.
"""
from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass

COPIER = "skopeo"  # the daemonless image copier, preferred over the Docker CLI
IMAGE_TOOLS = (COPIER, "docker")
HASH_TOOLS = {
    "md5": ("md5sum", "md5"),
    "sha256": ("sha256sum", "shasum"),
    "sha512": ("sha512sum", "shasum"),
}


@dataclass(frozen=True)
class Command:
    tool: str
    does: str
    uses: tuple[str, ...]
    line: str
    source: str


COMMANDS: dict[str, Command] = {
    "skopeo.copy": Command(
        "skopeo",
        "copy the image $ref for linux/$ARCH into a single-platform archive at $out that docker load accepts",
        ("$ref", "$ARCH", "$out"),
        "",
        "",
    ),
    "skopeo.digest": Command(
        "skopeo",
        "print the registry digest (sha256:...) of $ref for linux/$ARCH",
        ("$ref", "$ARCH"),
        "",
        "",
    ),
    "docker.pull": Command(
        "docker",
        "pull $ref for $PLATFORM",
        ("$ref", "$PLATFORM"),
        "",
        "",
    ),
    "docker.save": Command(
        "docker",
        "write $ref for $PLATFORM as a single-platform archive at $out",
        ("$ref", "$PLATFORM", "$out"),
        "",
        "",
    ),
    "docker.digest": Command(
        "docker",
        "print the registry digest (sha256:...) of the pulled $ref",
        ("$ref",),
        "",
        "",
    ),
    "docker.load": Command(
        "docker",
        "load the image archive $archive (used by load.sh inside)",
        ("$archive",),
        "",
        "",
    ),
    "docker.image_id": Command(
        "docker",
        "print the image ID (sha256:...) of the loaded image $expected (used by load.sh inside)",
        ("$expected",),
        "",
        "",
    ),
    "hf.download": Command(
        "hf",
        "download the files of $repo matching $include_args at commit $revision into the folder $dest",
        ("$repo", "$revision", "$dest", "$include_args"),
        "",
        "",
    ),
    "hf.include": Command(
        "hf",
        "the option that names one file pattern for hf.download; fetch.sh repeats it per pattern",
        (),
        "",
        "",
    ),
    "curl.download": Command(
        "curl",
        "download $url to the file $out, failing on an HTTP error",
        ("$url", "$out"),
        "",
        "",
    ),
    "md5sum.hash": Command("md5sum", "print only the md5 of $file", ("$file",), "", ""),
    "md5.hash": Command("md5", "print only the md5 of $file", ("$file",), "", ""),
    "sha256sum.hash": Command("sha256sum", "print only the SHA-256 of $file", ("$file",), "", ""),
    "shasum.sha256": Command("shasum", "print only the SHA-256 of $file", ("$file",), "", ""),
    "sha512sum.hash": Command("sha512sum", "print only the SHA-512 of $file", ("$file",), "", ""),
    "shasum.sha512": Command("shasum", "print only the SHA-512 of $file", ("$file",), "", ""),
}

# The commands load.sh runs inside; pack.py writes their lines into its copy of the template.
TEMPLATE_COMMANDS = ("docker.load", "docker.image_id")

# Which command computes which hash with which tool.
HASH_COMMANDS = {
    ("md5", "md5sum"): "md5sum.hash",
    ("md5", "md5"): "md5.hash",
    ("sha256", "sha256sum"): "sha256sum.hash",
    ("sha256", "shasum"): "shasum.sha256",
    ("sha512", "sha512sum"): "sha512sum.hash",
    ("sha512", "shasum"): "shasum.sha512",
}


class MissingToolError(Exception):
    def __init__(self, missing: dict[str, list[str]]):
        lines = [f"{tool} (needed for {', '.join(needs)})" for tool, needs in missing.items()]
        super().__init__("missing tools: " + "; ".join(lines))
        self.missing = missing


def find_tools(items: list[dict], which: Callable[[str], str | None] = shutil.which) -> dict:
    """The tool chosen for each job the items need; MissingToolError when one is absent."""
    tools: dict[str, str] = {}
    missing: dict[str, list[str]] = {}

    def need(job: str, candidates: tuple[str, ...], users: list[str]) -> None:
        if not users:
            return
        found = next((name for name in candidates if which(name)), None)
        if found:
            tools[job] = found
        else:
            missing[" or ".join(candidates)] = users

    def ids(kind, test=lambda item: True):
        return [item["id"] for item in items if item["kind"] == kind and test(item)]

    need("images", IMAGE_TOOLS, ids("image"))
    need("models", ("hf",), ids("model", lambda item: item["source"].get("source") == "huggingface"))
    packages = ids("package")
    need("packages", ("curl",), packages)
    listed = ids("package", lambda item: bool(item.get("checksums")))
    for algorithm, candidates in HASH_TOOLS.items():
        need(f"hash.{algorithm}", candidates, listed)
    if missing:
        raise MissingToolError(missing)
    return tools
```

- [ ] **Step 4: Run the test to see the command table fail**

Run: `python3.11 -m unittest tests.test_transfer_tools`

Expected: the four `ToolsTest` tests pass; `test_every_command_is_filled_and_sourced` fails sixteen subtests with `fill `line` from the documentation`.

- [ ] **Step 5: Fetch and record the command lines**

Nothing in this step comes from memory or from this plan. For each key, open the tool's official documentation for the version on the release or documentation page, find the option that does exactly what `does` says, and write `line` as a shell snippet that uses only the variables in `uses` (`"$ref"`, `"$out"` and so on, always double-quoted) and `source` as the URL you read it on.

| Keys | Open | What the line must do |
|---|---|---|
| `skopeo.copy`, `skopeo.digest` | The skopeo command reference in the `containers/skopeo` repository (`docs/skopeo-copy.1.md`, `docs/skopeo-inspect.1.md`) and the `docker-archive:` transport in `containers-transports(5)` (`containers/image` repository, `docs/containers-transports.5.md`) | Copy one image for linux/`$ARCH` into a single-platform archive at `$out` that `docker load` accepts, tagged `$ref`; print the registry digest of `$ref` for linux/`$ARCH` |
| `docker.pull`, `docker.save`, `docker.digest`, `docker.load`, `docker.image_id` | The Docker CLI reference on docs.docker.com: `docker image pull`, `docker image save`, `docker image inspect`, `docker image load` | Pull `$ref` for `$PLATFORM`; save it as a single-platform archive at `$out`; print its registry digest (`sha256:...`, the repo digest); load `$archive`; print the image ID of `$expected` |
| `hf.download`, `hf.include` | The Hugging Face Hub CLI guide in the `huggingface_hub` documentation on huggingface.co | Download the files of `$repo` matching the patterns into `$dest` at `$revision`; `hf.include` is only the option that names one pattern, which `fetch.sh` repeats per pattern into `$include_args` |
| `curl.download` | The curl manual page on curl.se | Download `$url` to `$out`, follow redirects, fail with a non-zero exit on an HTTP error, print no progress meter but print errors |
| `md5sum.hash`, `sha256sum.hash`, `sha512sum.hash` | The GNU coreutils manual: "md5sum invocation" and "sha2 utilities" | Print only the hash of `$file` (no file name) |
| `md5.hash` | The `md5(1)` manual page of macOS (`man md5` on a Mac) | Print only the hash of `$file` |
| `shasum.sha256`, `shasum.sha512` | The `shasum` documentation (`perldoc shasum` or `man shasum`; the perldoc.perl.org page) | Print only the SHA-256 or SHA-512 of `$file` |

Also confirm from the same pages, and fix the code and tests to match when a page says otherwise:

1. The executable names `skopeo`, `docker`, `hf`, `curl`, `md5sum`, `md5`, `sha256sum`, `shasum`, `sha512sum`. If the Hugging Face CLI's current executable has another name, change `Command.tool`, `find_tools` and the names in `tests/test_transfer_tools.py` and `tests/fetch_stubs.py` (Task 10) together.
2. That the daemonless copier can write a single-platform archive for a chosen platform and print a digest (§14, second row). If it cannot, set `COPIER` to the tool that can, as its documentation shows, rename its keys `<tool>.copy` and `<tool>.digest`, and record why in the module docstring.
3. That each digest line prints a string containing `sha256:` followed by 64 hex digits (`fetch.sh` takes the first such string), and that `docker.image_id` prints the ID as `sha256:` plus 64 hex digits.

Keep a list of the sixteen keys with the URL of each for Task 16, which repeats them in `references/fetch.md`.

- [ ] **Step 6: Run the suite**

Run both suite commands. Expected: `Ran 463 tests`, `OK` on both.

- [ ] **Step 7: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/tools.py tests/test_transfer_tools.py
git commit -m "feat(transfer): tool lookup and command lines taken from each tool's documentation

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: fetch.sh and plan.py

§8.2 steps 1 to 3, §8.4, §10 rows 1 to 5. `plan.py` creates `transfer.json` on its first run, lists the questions, checks the answers, finds the tools, and writes `plan` and `<bundle>/fetch.sh`. The shell tests run `fetch.sh` for real with stub tools on a `PATH` that holds nothing else, so no test can reach the network.

**Files:**
- Create: `$T/scripts/transfer_lib/fetch_script.py`, `$T/scripts/plan.py`
- Create: `tests/fetch_stubs.py`, `tests/test_transfer_plan.py`, `tests/test_fetch_script.py`

**Interfaces:**
- Consumes: `tools.COMMANDS`, `HASH_COMMANDS`, `find_tools`; `items.build_items`, `checksums_path`; `questions.needed_questions`, `answer_problems`; `inputs.load_inputs`, `channel_of`; `state.*`.
- Produces:
  - `fetch_script.sh_quote(value) -> str`, `MIN_FREE_KB` (1 GiB), `render_fetch_script(plan, platform, generated) -> str`: POSIX sh, `set -eu`, `PLATFORM='linux/<arch>'`, `ARCH='<arch>'`, shell functions `log`, `fail`, `room`, `listed_hash`, `hash_file`, `fetch_image REF ARCHIVE`, `fetch_model NAME FOLDER SOURCE REPO_OR_PATH REVISION ALLOW_PICKLE`, `fetch_package FILE PATH URL CHECKSUMS_URL CHECKSUMS_PATH`; one `fetch_<kind> ... || fail '<kind> <name>'` line per item; exit 1 with `N item(s) failed:` when any failed. A checksum mismatch deletes the file, logs `checksum does not match` and exits 1 at once.
  - `plan.py [--project-root DIR]`: exit 2 on a missing or stale input, on questions still open (it prints `Questions for this transfer: ...`), on invalid answers, and on a `local` model folder without safetensors weights (unless `allow_pickle`); exit 3 naming a missing tool and the items that need it; exit 0 after writing `plan = {items, tools, platform, channel, planned}` into `transfer.json` and `<bundle>/fetch.sh`, printing the counts (`Plan: N items (a image, b model, c package, d manual)`), the tools, the bundle folder, the known weight sizes from the blueprint and `... only after they approve it`.
  - `tests.fetch_stubs`: `install_stubs(folder, names=...) -> Path`, `stub_env(stubs, bundle, files, **extra) -> dict`; stubs `skopeo`, `docker`, `hf`, `curl` that ignore options and write small files at the argument that lies under `$BUNDLE`; `STUB_FAIL_IMAGE`, `STUB_FAIL_MODEL`, `STUB_PICKLE_ONLY`, `STUB_FILES` change their behavior.

- [ ] **Step 1: Write the stubs and the failing tests**

Create `tests/fetch_stubs.py`:

```python
"""Stub download tools for the fetch.sh tests, in a temporary folder that becomes the whole
PATH: the real skopeo, docker, hf or curl can never run, so no test touches the network.
The basic tools fetch.sh needs are linked into the same folder.

A stub does not parse the tool's options. It finds the argument that names a path inside
the bundle (BUNDLE in its environment) and writes a small file there, so the tests keep
working whatever exact options references/fetch.md records."""
from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

SYSTEM_TOOLS = (
    "sh", "dash", "awk", "sed", "df", "find", "head", "cut", "tr", "wc", "sort", "ls",
    "mkdir", "mv", "rm", "cp", "cat", "dirname", "basename",
    "sha256sum", "shasum", "md5sum", "md5", "sha512sum",
)

_FIND_TARGET = r'''
target=""
for arg in "$@"; do
  case $arg in
    *"$BUNDLE"/*) target=${arg#*"$BUNDLE"/}; target="$BUNDLE/${target%%:*}" ;;
  esac
done
'''

STUBS = {
    # An image copier: writes the archive it is asked for; prints a digest otherwise.
    "skopeo": "#!/bin/sh\n" + _FIND_TARGET + r'''
if [ -n "$target" ]; then
  [ -n "${STUB_FAIL_IMAGE:-}" ] && exit 1
  printf 'archive of %s\n' "$*" > "$target"
else
  echo "sha256:$(printf '%064d' 7)"
fi
''',
    # The Docker CLI: pull does nothing, save writes the archive, inspect prints a digest.
    "docker": "#!/bin/sh\n" + _FIND_TARGET + r'''
if [ -n "$target" ]; then printf 'archive\n' > "$target"; fi
case "$*" in *inspect*) echo "example@sha256:$(printf '%064d' 7)" ;; esac
''',
    # The Hugging Face CLI: fills the folder it is given with one weight and one config file.
    "hf": "#!/bin/sh\n" + _FIND_TARGET + r'''
[ -n "${STUB_FAIL_MODEL:-}" ] && exit 1
mkdir -p "$target"
if [ -n "${STUB_PICKLE_ONLY:-}" ]; then printf 'w' > "$target/pytorch_model.bin"; else printf 'w' > "$target/model.safetensors"; fi
printf '{}' > "$target/config.json"
''',
    # curl: copies $STUB_FILES/<last part of the URL> to the file it is given; 22 when absent.
    "curl": "#!/bin/sh\n" + _FIND_TARGET + r'''
url=""
for arg in "$@"; do case $arg in https://*) url=$arg ;; esac; done
source="$STUB_FILES/${url##*/}"
[ -f "$source" ] || exit 22
cp "$source" "$target"
''',
}


def install_stubs(folder: Path, names=tuple(STUBS)) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for tool in SYSTEM_TOOLS:
        found = shutil.which(tool)
        if found and not (folder / tool).exists():
            (folder / tool).symlink_to(found)
    for name in names:
        path = folder / name
        path.write_text(STUBS[name], encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return folder


def stub_env(stubs: Path, bundle: Path, files: Path, **extra) -> dict:
    env = dict(os.environ, PATH=str(stubs),
               BUNDLE=str(Path(bundle).resolve()), STUB_FILES=str(files))
    env.update({key: str(value) for key, value in extra.items()})
    return env
```

Create `tests/test_transfer_plan.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from tests import fetch_stubs, support, transfer_projects
from tests.test_transfer_items import MANIFEST, SOURCE
from transfer_lib.constants import MODEL_FILE_PATTERNS, PICKLE_PATTERNS
from transfer_lib.fetch_script import render_fetch_script, sh_quote
from transfer_lib.items import build_items
from transfer_lib.tools import find_tools


class FetchScriptTextTest(unittest.TestCase):
    def setUp(self):
        items = build_items(MANIFEST, {"models": {"chat model": SOURCE}})
        tools = find_tools(items, lambda name: name)
        self.text = render_fetch_script({"items": items, "tools": tools}, "linux/arm64", "2026-11-22T10:00:00Z")

    def test_posix_header(self):
        lines = self.text.splitlines()
        self.assertFalse(self.text.startswith("#!"))
        self.assertIn("set -eu", lines)
        self.assertIn("PLATFORM='linux/arm64'", lines)
        self.assertIn("ARCH='arm64'", lines)
        self.assertNotIn("HF_TOKEN", self.text)

    def test_one_call_per_item_and_no_call_for_manual_items(self):
        calls = [line for line in self.text.splitlines() if line.startswith("fetch_") and " || fail " in line]
        self.assertEqual(len(calls), 4)
        self.assertIn("fetch_image 'beta:2' 'images/beta/beta_2.tar' || fail 'image beta:2'", calls)
        self.assertIn(
            "fetch_package 'alpha-1-amd64.tgz' 'packages/alpha/alpha-1-amd64.tgz' "
            "'https://downloads.example.test/alpha-1-amd64.tgz' 'https://downloads.example.test/md5sum' "
            "'packages/alpha/checksums/md5sum' || fail 'package alpha-1-amd64.tgz'",
            calls,
        )
        self.assertIn(
            "fetch_model 'chat model' 'models/chat_model' 'huggingface' 'example/chat' '" + "0" * 40 + "' 'no' "
            "|| fail 'model chat model'",
            calls,
        )

    def test_the_model_filter_is_in_the_script(self):
        self.assertIn('patterns="' + " ".join(MODEL_FILE_PATTERNS) + '"', self.text)
        self.assertIn(" ".join(PICKLE_PATTERNS), self.text)

    def test_quoting(self):
        self.assertEqual(sh_quote("it's"), "'it'\\''s'")


class PlanScriptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        catalog = transfer_projects.transfer_catalog(tmp / "catalog")
        self.project = transfer_projects.make_project(tmp / "project", catalog)
        self.bundle = tmp / "bundle"
        self.stubs = fetch_stubs.install_stubs(tmp / "stubs")
        self.env = fetch_stubs.stub_env(self.stubs, self.bundle, tmp)

    def plan(self, env=None):
        return transfer_projects.run_script("plan.py", self.project, env=env or self.env)

    def test_first_run_writes_transfer_json_and_lists_the_questions(self):
        result = self.plan()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertTrue((self.project / "docs" / "airgap" / "transfer.json").is_file())
        self.assertIn("bundle.path: missing", result.stderr)
        self.assertIn("Questions for this transfer: bundle.path, models, medium.capacity_gb, medium.filesystem", result.stderr)

    def test_a_complete_plan_writes_fetch_sh_and_the_plan(self):
        transfer_projects.write_state(self.project, transfer_projects.default_answers(self.bundle))
        result = self.plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.bundle / "fetch.sh").is_file())
        self.assertIn("Plan: 12 items (8 image, 1 model, 2 package, 1 manual)", result.stdout)
        self.assertIn("about 70.0 GB of weights", result.stdout)
        self.assertIn("only after they approve it", result.stdout)
        state = transfer_projects.load_state_of(self.project)
        self.assertEqual(state["plan"]["platform"], "linux/amd64")
        self.assertEqual(state["plan"]["tools"]["images"], "skopeo")
        self.assertEqual([i["file"] for i in state["plan"]["items"] if i["kind"] == "package"],
                         ["alpha-cli-1.2.3-amd64", "install.sh"])

    def test_arm64_takes_the_arm64_package(self):
        catalog = transfer_projects.transfer_catalog(Path(self.tmp.name) / "catalog-arm")
        project = transfer_projects.make_project(
            Path(self.tmp.name) / "arm", catalog, support.base_answers(**{"hardware.cpu_arch": "arm64"})
        )
        transfer_projects.write_state(project, transfer_projects.default_answers(self.bundle))
        result = transfer_projects.run_script("plan.py", project, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ARCH='arm64'", (self.bundle / "fetch.sh").read_text(encoding="utf-8"))
        state = transfer_projects.load_state_of(project)
        self.assertIn("alpha-cli-1.2.3-arm64", [i.get("file") for i in state["plan"]["items"]])

    def test_a_missing_tool_is_exit_3(self):
        transfer_projects.write_state(self.project, transfer_projects.default_answers(self.bundle))
        (self.stubs / "hf").unlink()
        env = self.env
        result = self.plan(env)
        self.assertEqual(result.returncode, 3)
        self.assertIn("hf is not on PATH; it is needed for: model:example-70b", result.stderr)

    def test_a_stale_manifest_is_exit_2(self):
        blueprint = self.project / "docs" / "airgap" / "blueprint.json"
        data = json.loads(blueprint.read_text(encoding="utf-8"))
        data["decisions"][0]["rationale"] = "Changed."
        blueprint.write_text(json.dumps(data), encoding="utf-8")
        result = self.plan()
        self.assertEqual(result.returncode, 2)
        self.assertIn("run airgap-architect's manifest.py again", result.stderr)

    def test_a_local_model_without_safetensors_is_exit_2(self):
        weights = Path(self.tmp.name) / "weights"
        weights.mkdir()
        (weights / "pytorch_model.bin").write_bytes(b"w")
        answers = transfer_projects.default_answers(self.bundle, models={"example-70b": {"source": "local", "path": str(weights)}})
        transfer_projects.write_state(self.project, answers)
        result = self.plan()
        self.assertEqual(result.returncode, 2)
        self.assertIn("holds no safetensors weights (pickle files: pytorch_model.bin)", result.stderr)
        answers["models"]["example-70b"]["allow_pickle"] = True
        transfer_projects.write_state(self.project, answers)
        self.assertEqual(self.plan().returncode, 0)


if __name__ == "__main__":
    unittest.main()
```

Create `tests/test_fetch_script.py`:

```python
"""fetch.sh run for real with stub download tools: no network, small files."""
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import fetch_stubs, transfer_projects
from transfer_lib.tools import COMMANDS

SHELLS = [name for name in ("sh", "dash") if shutil.which(name)]


@unittest.skipUnless(shutil.which("sha256sum") or shutil.which("shasum"), "needs a SHA-256 tool")
class FetchScriptRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        catalog = transfer_projects.transfer_catalog(tmp / "catalog")
        self.project = transfer_projects.make_project(tmp / "project", catalog)
        self.bundle = tmp / "bundle"
        self.files = tmp / "files"
        self.files.mkdir()
        self.serve("alpha-cli-1.2.3-amd64", b"cli binary")
        self.serve("install.sh", b"echo install\n")
        self.serve("SHA256SUMS", f"{hashlib.sha256(b'cli binary').hexdigest()}  alpha-cli-1.2.3-amd64\n".encode())
        self.stubs = fetch_stubs.install_stubs(tmp / "stubs")

    def serve(self, name, data):
        (self.files / name).write_bytes(data)

    def plan(self, **env):
        transfer_projects.write_state(self.project, transfer_projects.default_answers(self.bundle))
        self.env = fetch_stubs.stub_env(self.stubs, self.bundle, self.files, **env)
        result = transfer_projects.run_script("plan.py", self.project, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)

    def fetch(self, shell="sh"):
        return subprocess.run([shell, str(self.bundle / "fetch.sh")], capture_output=True, text=True, env=self.env)

    def log(self):
        return (self.bundle / "fetch.log").read_text(encoding="utf-8")

    def test_every_item_is_fetched_and_a_second_run_skips_them(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                shutil.rmtree(self.bundle, ignore_errors=True)
                self.plan()
                result = self.fetch(shell)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual((self.bundle / "packages/alpha-engine/alpha-cli-1.2.3-amd64").read_bytes(), b"cli binary")
                self.assertTrue((self.bundle / "packages/alpha-engine/checksums/SHA256SUMS").is_file())
                self.assertTrue((self.bundle / "models/example-70b/model.safetensors").is_file())
                digest = self.bundle / "images/alpha-engine/registry.example.test_synthetic_alpha-engine_1.2.3.digest"
                self.assertRegex(digest.read_text(encoding="utf-8"), r"^sha256:[0-9a-f]{64}\n$")
                self.assertNotIn("FAILED", self.log())
                again = self.fetch(shell)
                self.assertEqual(again.returncode, 0)
                self.assertIn("OK package alpha-cli-1.2.3-amd64 (already present)", again.stdout)

    def test_a_failed_download_is_logged_and_the_others_go_on(self):
        (self.files / "install.sh").unlink()
        self.plan()
        result = self.fetch()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAILED package install.sh", self.log())
        self.assertIn("OK package alpha-cli-1.2.3-amd64", self.log())
        self.assertIn("1 item(s) failed:", result.stderr)
        self.assertFalse((self.bundle / "packages/alpha-engine/install.sh.download").exists())
        self.serve("install.sh", b"echo install\n")
        self.assertEqual(self.fetch().returncode, 0)

    def test_a_checksum_mismatch_deletes_the_file_and_stops(self):
        self.serve("SHA256SUMS", ("0" * 64 + "  alpha-cli-1.2.3-amd64\n").encode())
        self.plan()
        result = self.fetch()
        self.assertEqual(result.returncode, 1)
        self.assertIn("checksum does not match", self.log())
        self.assertFalse((self.bundle / "packages/alpha-engine/alpha-cli-1.2.3-amd64").exists())
        self.assertNotIn("install.sh", self.log())

    def test_other_checksum_list_formats(self):
        digest = hashlib.sha256(b"cli binary").hexdigest()
        for text in (f"SHA256 (alpha-cli-1.2.3-amd64) = {digest}\n", f"{digest.upper()} *dist/alpha-cli-1.2.3-amd64\n"):
            with self.subTest(text=text):
                shutil.rmtree(self.bundle, ignore_errors=True)
                self.serve("SHA256SUMS", text.encode())
                self.plan()
                self.assertEqual(self.fetch().returncode, 0, self.log())

    def test_a_model_without_safetensors_fails(self):
        self.plan(STUB_PICKLE_ONLY=1)
        self.assertEqual(self.fetch().returncode, 1)
        self.assertIn("model example-70b: no safetensors weights", self.log())

    def test_docker_is_used_when_the_copier_is_missing(self):
        (self.stubs / "skopeo").unlink()
        self.plan()
        self.assertIn(COMMANDS["docker.save"].line, (self.bundle / "fetch.sh").read_text(encoding="utf-8"))
        self.assertEqual(self.fetch().returncode, 0, self.log())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to see them fail**

Run: `python3.11 -m unittest tests.test_transfer_plan tests.test_fetch_script`

Expected: `tests.test_transfer_plan` fails to import (`No module named 'transfer_lib.fetch_script'`), and the `test_fetch_script` tests fail with `can't open file '.../scripts/plan.py'`: `FAILED (failures=8, errors=1)` or close to it, depending on which shells exist.

- [ ] **Step 3: Write fetch_script.py**

Create `$T/scripts/transfer_lib/fetch_script.py`:

```python
"""fetch.sh: the download script for the connected side (design spec section 8.4)."""
from __future__ import annotations

from .constants import FETCH_LOG, FETCH_STATE_DIR, MODEL_FILE_PATTERNS, PICKLE_PATTERNS
from .items import checksums_path
from .tools import COMMANDS, HASH_COMMANDS

MIN_FREE_KB = 1024 * 1024  # stop when less than 1 GiB is left in the bundle folder


def sh_quote(value: str) -> str:
    """One shell word, single-quoted."""
    return "'" + str(value).replace("'", "'\\''") + "'"


def _line(key: str) -> str:
    return COMMANDS[key].line


def _hash_function(tools: dict) -> list[str]:
    lines = [
        "hash_file() {  # hash_file LENGTH FILE: print the hex digest of FILE whose length is LENGTH",
        '  file=$2',
        '  case $1 in',
    ]
    for length, algorithm in (("32", "md5"), ("64", "sha256"), ("128", "sha512")):
        tool = tools.get(f"hash.{algorithm}")
        if tool:
            lines.append(f"    {length}) {_line(HASH_COMMANDS[(algorithm, tool)])} ;;")
    lines += ["    *) return 1 ;;", "  esac", "}"]
    return lines


_COMMON = r"""log() {  # log STATUS TEXT: one line in fetch.log and on the screen
  printf '%s %s\n' "$1" "$2" >> "$LOG"
  printf '%s %s\n' "$1" "$2"
}

fail() {  # fail TEXT: count a failed item and go on with the next one
  log FAILED "$1"
  FAILED=$((FAILED + 1))
  FAILURES="$FAILURES
  $1"
}

room() {  # stop the whole run on a full disk
  free=$(df -Pk "$BUNDLE" | awk 'NR == 2 { print $4 }')
  if [ "$free" -lt __MIN_FREE_KB__ ]; then
    log FAILED "disk full: less than 1 GiB left in $BUNDLE"
    exit 1
  fi
}

listed_hash() {  # listed_HASH LIST NAME: the hash that LIST gives for NAME, in either common format
  awk -v name="$2" '
    $1 ~ /^[0-9A-Fa-f]+$/ && NF >= 2 { f = $2; sub(/^\*/, "", f); g = f; sub(/.*\//, "", g); if (f == name || g == name) { print tolower($1); exit } }
    $2 ~ /^\(/ && $(NF - 1) == "=" { f = $2; sub(/^\(/, "", f); sub(/\)$/, "", f); if (f == name) { print tolower($NF); exit } }
    NF == 1 && $1 ~ /^[0-9A-Fa-f]+$/ { only = tolower($1); count++ }
    END { if (count == 1 && NR == 1) print only }
  ' "$1"
}
"""


def _functions(plan: dict) -> str:
    tools = plan["tools"]
    parts = [_COMMON.replace("__MIN_FREE_KB__", str(MIN_FREE_KB))]
    parts.append("\n".join(_hash_function(tools)) + "\n")
    image_tool = tools.get("images")
    if image_tool:
        if image_tool == "docker":
            get = f"  {_line('docker.pull')} || return 1\n  {_line('docker.save')} || {{ rm -f \"$out\"; return 1; }}\n"
            digest = _line("docker.digest")
        else:
            get = f"  {_line(image_tool + '.copy')} || {{ rm -f \"$out\"; return 1; }}\n"
            digest = _line(image_tool + ".digest")
        parts.append(
            "fetch_image() {  # fetch_image REF ARCHIVE\n"
            '  ref=$1; archive="$BUNDLE/$2"; digest_file="${archive%.tar}.digest"\n'
            '  if [ -s "$archive" ] && [ -s "$digest_file" ]; then log OK "image $ref (already present)"; return 0; fi\n'
            "  room\n"
            '  mkdir -p "$(dirname "$archive")" || return 1\n'
            '  out="$archive.download"; rm -f "$out"\n'
            + get
            + f'  digest=$({digest} | sed -n \'s/.*\\(sha256:[0-9a-f]\\{{64\\}}\\).*/\\1/p\' | head -n 1)\n'
            '  if [ -z "$digest" ]; then rm -f "$out"; log FAILED "image $ref: no digest reported"; return 1; fi\n'
            '  mv "$out" "$archive" || return 1\n'
            "  printf '%s\\n' \"$digest\" > \"$digest_file\" || return 1\n"
            '  log OK "image $ref $digest"\n'
            "}\n"
        )
    if tools.get("models") or any(i["kind"] == "model" for i in plan["items"]):
        include = _line("hf.include") if tools.get("models") else ""
        parts.append(
            "fetch_model() {  # fetch_model NAME FOLDER SOURCE REPO_OR_PATH REVISION ALLOW_PICKLE\n"
            '  dest="$BUNDLE/$2"; done_file="$BUNDLE/' + FETCH_STATE_DIR + '/$(basename "$2").done"\n'
            '  if [ -f "$done_file" ]; then log OK "model $1 (already present)"; return 0; fi\n'
            "  room\n"
            '  mkdir -p "$dest" "$BUNDLE/' + FETCH_STATE_DIR + '" || return 1\n'
            '  patterns="' + " ".join(MODEL_FILE_PATTERNS) + '"\n'
            '  if [ "$6" = yes ]; then patterns="$patterns ' + " ".join(PICKLE_PATTERNS) + '"; fi\n'
            '  if [ "$3" = local ]; then\n'
            '    cp -R "$4/." "$dest/" || return 1\n'
            '    if [ "$6" != yes ]; then\n'
            '      find "$dest" -type f \\( ' + " -o ".join(f"-name '{p}'" for p in PICKLE_PATTERNS) + ' \\) -exec rm -f {} + || return 1\n'
            "    fi\n"
            "  else\n"
            '    repo=$4; revision=$5; include_args=""\n'
            f'    for pattern in $patterns; do include_args="$include_args {include} $pattern"; done\n'
            + (f"    {_line('hf.download')} || return 1\n" if tools.get("models") else "    return 1\n")
            + "  fi\n"
            '  if [ "$6" != yes ] && [ -z "$(find "$dest" -type f -name \'*.safetensors\' | head -n 1)" ]; then\n'
            '    log FAILED "model $1: no safetensors weights; allow pickle files for it in transfer.json or choose another source"\n'
            "    return 1\n"
            "  fi\n"
            '  printf \'%s\\n\' "$5" > "$done_file" || return 1\n'
            '  log OK "model $1 $5"\n'
            "}\n"
        )
    if tools.get("packages"):
        parts.append(
            "fetch_package() {  # fetch_package FILE PATH URL CHECKSUMS_URL CHECKSUMS_PATH\n"
            '  name=$1; target="$BUNDLE/$2"\n'
            '  if [ -s "$target" ]; then log OK "package $name (already present)"; return 0; fi\n'
            "  room\n"
            '  mkdir -p "$(dirname "$target")" || return 1\n'
            '  url=$3; out="$target.download"; rm -f "$out"\n'
            f"  {_line('curl.download')} || {{ rm -f \"$out\"; return 1; }}\n"
            '  if [ -n "$4" ]; then\n'
            '    list="$BUNDLE/$5"; mkdir -p "$(dirname "$list")" || return 1\n'
            '    url=$4; out_file=$out; out="$list.download"\n'
            f"    {_line('curl.download')} || {{ rm -f \"$out\" \"$out_file\"; return 1; }}\n"
            '    mv "$out" "$list"; out=$out_file\n'
            '    expected=$(listed_hash "$list" "$name")\n'
            '    if [ -z "$expected" ]; then rm -f "$out"; log FAILED "package $name: not listed in $4"; return 1; fi\n'
            '    actual=$(hash_file "${#expected}" "$out" | tr "A-F" "a-f") || actual=""\n'
            '    if [ "$actual" != "$expected" ]; then\n'
            '      rm -f "$out"\n'
            '      log FAILED "package $name: checksum does not match $4; the file was deleted"\n'
            "      exit 1\n"
            "    fi\n"
            "  fi\n"
            '  mv "$out" "$target" || return 1\n'
            '  log OK "package $name"\n'
            "}\n"
        )
    return "\n".join(parts)


def _calls(plan: dict) -> list[str]:
    calls = []
    for item in plan["items"]:
        if item["kind"] == "image":
            calls.append(
                f"fetch_image {sh_quote(item['ref'])} {sh_quote(item['path'])} || fail {sh_quote('image ' + item['ref'])}"
            )
        elif item["kind"] == "model":
            source = item["source"]
            where = source.get("repo") if source.get("source") == "huggingface" else source.get("path")
            calls.append(
                "fetch_model "
                + " ".join(
                    sh_quote(value)
                    for value in (
                        item["name"],
                        item["path"],
                        source.get("source", ""),
                        where or "",
                        source.get("revision", ""),
                        "yes" if item.get("allow_pickle") else "no",
                    )
                )
                + f" || fail {sh_quote('model ' + item['name'])}"
            )
        elif item["kind"] == "package":
            calls.append(
                "fetch_package "
                + " ".join(
                    sh_quote(value)
                    for value in (item["file"], item["path"], item["url"], item["checksums"], checksums_path(item) or "")
                )
                + f" || fail {sh_quote('package ' + item['file'])}"
            )
    return calls


def render_fetch_script(plan: dict, platform: str, generated: str) -> str:
    """POSIX sh for the plan; `platform` is the manifest's, for example linux/amd64."""
    arch = platform.split("/", 1)[1]
    header = [
        "# fetch.sh: written by airgap-transfer's plan.py on " + generated + ". Do not edit it;",
        "# change the design or the answers and run plan.py again.",
        "# Downloads every item of the plan into this folder. Run it only after the plan",
        "# was approved: sh fetch.sh. A second run fetches only what is missing.",
        "set -eu",
        "set -f",
        'BUNDLE=$(cd "$(dirname "$0")" && pwd)',
        f'LOG="$BUNDLE/{FETCH_LOG}"',
        f"PLATFORM={sh_quote(platform)}",
        f"ARCH={sh_quote(arch)}",
        "FAILED=0",
        'FAILURES=""',
        "",
    ]
    footer = [
        "",
        'if [ "$FAILED" -gt 0 ]; then',
        "  printf 'fetch.sh: %s item(s) failed:%s\\nRun sh fetch.sh again to fetch only those.\\n' \"$FAILED\" \"$FAILURES\" >&2",
        "  exit 1",
        "fi",
        'log OK "every item is in $BUNDLE; next: pack.py"',
        "",
    ]
    return "\n".join(header) + _functions(plan) + "\n" + "\n".join(_calls(plan)) + "\n" + "\n".join(footer)
```

- [ ] **Step 4: Write plan.py**

Create `$T/scripts/plan.py`:

```python
"""Plan a transfer: the item list, the tools on this machine and fetch.sh."""
from datetime import datetime, timezone
from pathlib import Path

from transfer_lib import cli
from transfer_lib.constants import EXIT_ENVIRONMENT, EXIT_INPUT, EXIT_OK, FETCH_SCRIPT, PICKLE_SUFFIXES
from transfer_lib.fetch_script import render_fetch_script
from transfer_lib.inputs import InputError, channel_of, load_inputs
from transfer_lib.items import build_items
from transfer_lib.questions import answer_problems, needed_questions
from transfer_lib.state import load_state, new_state, save_state, state_path
from transfer_lib.tools import MissingToolError, find_tools


def local_model_problems(items: list[dict]) -> list[str]:
    """A local model folder without safetensors weights stops the plan (exit 2)."""
    problems = []
    for item in items:
        if item["kind"] != "model" or item["source"].get("source") != "local" or item["allow_pickle"]:
            continue
        files = [p for p in Path(item["source"]["path"]).rglob("*") if p.is_file()]
        if not any(p.suffix == ".safetensors" for p in files):
            pickles = [p.name for p in files if p.suffix in PICKLE_SUFFIXES]
            problems.append(
                f"models: '{item['name']}': {item['source']['path']} holds no safetensors weights"
                + (f" (pickle files: {', '.join(sorted(pickles)[:3])})" if pickles else "")
                + "; set allow_pickle to true for it only if the scanning rules permit pickle files"
            )
    return problems


def known_sizes(blueprint: dict, items: list[dict]) -> list[str]:
    """Sizes known before the fetch: the weights architect sized, local model folders."""
    lines = []
    sized = (blueprint.get("sizing") or {}).get("models") or []
    for index, item in enumerate(i for i in items if i["kind"] == "model"):
        if item["source"].get("source") == "local":
            total = sum(p.stat().st_size for p in Path(item["source"]["path"]).rglob("*") if p.is_file())
            lines.append(f"  model {item['name']}: {total / 1e9:.1f} GB in {item['source']['path']}")
        elif index < len(sized) and isinstance(sized[index], dict) and sized[index].get("weights_gb"):
            lines.append(f"  model {item['name']}: about {sized[index]['weights_gb']} GB of weights (architect's sizing)")
    return lines


def main(argv=None) -> int:
    args = cli.make_parser(__doc__).parse_args(argv)
    root = Path(args.project_root)
    try:
        blueprint, manifest = load_inputs(root)
        channel = channel_of(blueprint)
        path = state_path(root)
        if not path.exists():
            save_state(path, new_state(manifest["inputs_digest"]))
            print(f"Wrote {path}")
        state = load_state(path)
    except InputError as error:
        cli.fail(EXIT_INPUT, [str(error)])
    answers = state["answers"]
    problems = answer_problems(answers, channel, manifest, root)
    if problems:
        asked = needed_questions(channel, manifest, answers)
        cli.fail(EXIT_INPUT, ["Missing or invalid answers in transfer.json:"] + [f"  {p}" for p in problems]
                 + ["Questions for this transfer: " + ", ".join(asked)])
    items = build_items(manifest, answers)
    problems = local_model_problems(items)
    if problems:
        cli.fail(EXIT_INPUT, problems)
    try:
        tools = find_tools(items)
    except MissingToolError as error:
        cli.fail(EXIT_ENVIRONMENT, [f"{tool} is not on PATH; it is needed for: {', '.join(needs)}"
                                    for tool, needs in error.missing.items()])
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    state["manifest_digest"] = manifest["inputs_digest"]
    state["plan"] = {"items": items, "tools": tools, "platform": manifest["platform"],
                     "channel": channel, "planned": generated}
    bundle = Path(answers["bundle.path"])
    script = bundle / FETCH_SCRIPT
    try:
        bundle.mkdir(parents=True, exist_ok=True)
        script.write_text(render_fetch_script(state["plan"], manifest["platform"], generated), encoding="utf-8")
        save_state(path, state)
    except OSError as error:
        cli.fail(EXIT_INPUT, [f"cannot write {script}: {error.strerror or type(error).__name__}"])
    counts = {}
    for item in items:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    print(f"Plan: {len(items)} items (" + ", ".join(f"{n} {k}" for k, n in counts.items()) + ")")
    print("Tools: " + (", ".join(f"{job} with {tool}" for job, tool in tools.items()) or "none needed"))
    print(f"Bundle folder: {bundle}")
    sizes = known_sizes(blueprint, items)
    print("Known sizes:" if sizes else "Known sizes: none before the fetch; images and packages are sized when fetched")
    for line in sizes:
        print(line)
    print(f"Wrote {script}. Show this plan to the user; run sh {script} only after they approve it.")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the tests and look at one generated fetch.sh**

Run:

```bash
python3.11 -m unittest tests.test_transfer_plan tests.test_fetch_script -v 2>&1 | tail -3
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
```

Expected: `OK` each time, `Ran 479 tests` for the suite. If a `test_fetch_script` test fails, read `fetch.log` in its temporary folder (print it from the test while debugging) before changing anything: a failure there usually means a command line from Task 9 prints something other than what `fetch.sh` reads.

- [ ] **Step 6: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/fetch_script.py \
  plugins/airgap-anything/skills/airgap-transfer/scripts/plan.py \
  tests/fetch_stubs.py tests/test_transfer_plan.py tests/test_fetch_script.py
git commit -m "feat(transfer): plan.py and the fetch script for the connected side

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Hashing, the volume plan and image archives

§8.5 (splitting, the 2 % reserve, largest first), §8.6 (`bundle.json` image fields). Hashing reads a file once and returns the whole-file hash and the hash of every part; the volume plan is first-fit decreasing over files and parts. `archive.py` reads an image archive's ID and platform so that `pack.py` can stop a wrong-platform image and `load.sh` can check what it loaded.

**Files:**
- Create: `$T/scripts/transfer_lib/hashing.py`, `volumes.py`, `archive.py`
- Create: `tests/test_transfer_volumes.py`

**Interfaces:**
- Consumes: `constants.GB`, `FAT32_MAX_FILE_BYTES`, `VOLUME_RESERVE`, `PART_SUFFIX`, `MEDIUM_CHANNELS`, `FILE_LIMIT_CHANNELS`.
- Produces:
  - `hashing.CHUNK`, `hash_file(path, part_size=None) -> (whole_sha256, [part_sha256, ...])` (no parts when the file fits), `part_count(size, part_size) -> int` (0 when not split).
  - `volumes.max_file_bytes(channel, answers) -> int | None` (FAT32 limit on `fat32`; `channel.max_file_gb` for a diode or staging host), `volume_capacity(channel, answers) -> int | None` (capacity minus 2 %), `part_size(channel, answers) -> int | None` (the smaller of the two), `part_name(path, index) -> "<path>.partNNN"`, `units_of(files, size_limit) -> [{path, size, sha256, of}]`, `assign_volumes(units, capacity) -> [[unit, ...], ...]`.
  - `archive.ArchiveError`, `read_image_archive(path) -> {"id": "sha256:...", "platform": "linux/<arch>", "tags": [...]}`.

- [ ] **Step 1: Fetch and record the archive layout**

`archive.py` and the test builder `tests/transfer_projects.image_archive` (Task 8) assume the layout of a `docker save` archive: a top-level `manifest.json` that is a list with one object per image, holding `Config` (the path of the config file in the archive) and `RepoTags`; a config JSON with `os` and `architecture`; and an image ID that is `sha256:` plus the SHA-256 of the config file's bytes. Check each of these points before writing code:

1. Open the Docker image specification in the `moby/moby` repository (the `image/spec/` folder, the version that describes `docker save`) and the `docker-archive` transport in `containers-transports(5)` (the page Task 9 used).
2. Open the `docker image save` and `docker image load` pages of the Docker CLI reference for what the archive holds today, including whether a newer `docker save` writes an OCI layout and whether it keeps `manifest.json` next to it.
3. Write the URLs into the docstring of `archive.py` in place of "the one recorded with its source in references/fetch.md", and keep them for the "Image archives" paragraph of `references/fetch.md` (Task 16).

When a page shows another layout (for example only an OCI `index.json`), change `read_image_archive` to read that layout, change `tests/transfer_projects.image_archive` to build it, and say so in the task report. Do not keep a layout the documentation does not describe.

- [ ] **Step 2: Write the failing test**

Create `tests/test_transfer_volumes.py`:

```python
import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from tests import transfer_projects
from transfer_lib.archive import ArchiveError, read_image_archive
from transfer_lib.constants import FAT32_MAX_FILE_BYTES, GB
from transfer_lib.hashing import hash_file, part_count
from transfer_lib.volumes import assign_volumes, max_file_bytes, part_size, units_of, volume_capacity


class HashingTest(unittest.TestCase):
    def test_whole_and_part_hashes_in_one_read(self):
        data = os.urandom(3 * 1024 * 1024 + 5)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f"
            path.write_bytes(data)
            for size in (1024 * 1024 + 3, 2 * 1024 * 1024, len(data) - 1):
                with self.subTest(part_size=size):
                    whole, parts = hash_file(path, size)
                    self.assertEqual(whole, hashlib.sha256(data).hexdigest())
                    expected = [hashlib.sha256(data[i:i + size]).hexdigest() for i in range(0, len(data), size)]
                    self.assertEqual(parts, expected)
            self.assertEqual(hash_file(path, len(data))[1], [])
            self.assertEqual(hash_file(path)[1], [])

    def test_part_count(self):
        self.assertEqual(part_count(10, None), 0)
        self.assertEqual(part_count(10, 10), 0)
        self.assertEqual(part_count(11, 10), 2)


class VolumePlanTest(unittest.TestCase):
    def test_fat32_limit_and_reserve(self):
        answers = {"medium.capacity_gb": 1000, "medium.filesystem": "fat32"}
        self.assertEqual(max_file_bytes("removable_media", answers), FAT32_MAX_FILE_BYTES)
        self.assertEqual(volume_capacity("removable_media", answers), int(1000 * GB * 0.98))
        self.assertEqual(part_size("removable_media", answers), FAT32_MAX_FILE_BYTES)
        exfat = {"medium.capacity_gb": 1000, "medium.filesystem": "exfat"}
        self.assertIsNone(max_file_bytes("removable_media", exfat))
        self.assertEqual(part_size("removable_media", exfat), int(1000 * GB * 0.98))

    def test_channels_without_a_medium(self):
        self.assertEqual(max_file_bytes("data_diode", {"channel.max_file_gb": 4}), 4 * GB)
        self.assertIsNone(max_file_bytes("staging_host", {"channel.max_file_gb": "none"}))
        self.assertIsNone(volume_capacity("data_diode", {"channel.max_file_gb": 4}))
        self.assertIsNone(volume_capacity("other", {"medium.capacity_gb": "none"}))

    def test_large_files_are_cut_into_parts(self):
        files = [{"path": "models/m/w.safetensors", "size": 25, "sha256": "w", "parts": ["p1", "p2", "p3"]},
                 {"path": "packages/a/x", "size": 4, "sha256": "x", "parts": []}]
        units = units_of(files, 10)
        self.assertEqual(
            [(u["path"], u["size"], u["sha256"], u["of"]) for u in units],
            [
                ("models/m/w.safetensors.part001", 10, "p1", "models/m/w.safetensors"),
                ("models/m/w.safetensors.part002", 10, "p2", "models/m/w.safetensors"),
                ("models/m/w.safetensors.part003", 5, "p3", "models/m/w.safetensors"),
                ("packages/a/x", 4, "x", None),
            ],
        )

    def test_first_fit_largest_first(self):
        units = [{"path": name, "size": size} for name, size in (("a", 3), ("b", 7), ("c", 5), ("d", 5), ("e", 2))]
        volumes = assign_volumes(units, 10)
        self.assertEqual([[u["path"] for u in volume] for volume in volumes], [["b", "a"], ["c", "d"], ["e"]])
        self.assertEqual([[u["path"] for u in volume] for volume in assign_volumes(units, None)], [["b", "c", "d", "a", "e"]])


class ArchiveTest(unittest.TestCase):
    def test_reads_id_and_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.tar"
            path.write_bytes(transfer_projects.image_archive("example/a:1", "arm64"))
            image = read_image_archive(path)
            self.assertEqual(image["platform"], "linux/arm64")
            self.assertRegex(image["id"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(image["tags"], ["example/a:1"])
            path.write_bytes(b"not a tar")
            with self.assertRaises(ArchiveError):
                read_image_archive(path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it to see it fail**

Run: `python3.11 -m unittest tests.test_transfer_volumes`

Expected: `ModuleNotFoundError: No module named 'transfer_lib.archive'`, `FAILED (errors=1)`.

- [ ] **Step 4: Write hashing.py, volumes.py and archive.py**

Create `$T/scripts/transfer_lib/hashing.py`:

```python
"""SHA-256 of files and of the parts a split file is cut into, in one read."""
from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK = 1024 * 1024


def hash_file(path: Path, part_size: int | None = None) -> tuple[str, list[str]]:
    """(SHA-256 of the whole file, SHA-256 of each part of `part_size` bytes).

    The list of parts is empty when `part_size` is None or the file is not larger.
    """
    whole = hashlib.sha256()
    parts: list[str] = []
    size = Path(path).stat().st_size
    split = part_size is not None and size > part_size
    part = hashlib.sha256()
    left = part_size if split else None
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK)
            if not chunk:
                break
            whole.update(chunk)
            while split and chunk:
                take = chunk[:left]
                part.update(take)
                chunk = chunk[len(take):]
                left -= len(take)
                if left == 0:
                    parts.append(part.hexdigest())
                    part, left = hashlib.sha256(), part_size
    if split and left != part_size:
        parts.append(part.hexdigest())
    return whole.hexdigest(), parts


def part_count(size: int, part_size: int | None) -> int:
    """How many parts a file of `size` bytes is cut into; 0 when it is not split."""
    if part_size is None or size <= part_size:
        return 0
    return -(-size // part_size)
```

Create `$T/scripts/transfer_lib/volumes.py`:

```python
"""File size limits, splitting and the volume plan (design spec section 8.5)."""
from __future__ import annotations

from .constants import FAT32_MAX_FILE_BYTES, FILE_LIMIT_CHANNELS, GB, MEDIUM_CHANNELS, PART_SUFFIX, VOLUME_RESERVE
from .hashing import part_count


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def max_file_bytes(channel: str, answers: dict) -> int | None:
    """The largest single file the channel takes; None when it has no limit."""
    if channel in MEDIUM_CHANNELS and answers.get("medium.filesystem") == "fat32":
        return FAT32_MAX_FILE_BYTES
    if channel in FILE_LIMIT_CHANNELS and _number(answers.get("channel.max_file_gb")):
        return int(answers["channel.max_file_gb"] * GB)
    return None


def volume_capacity(channel: str, answers: dict) -> int | None:
    """Bytes of data one volume holds: the medium minus the reserve; None for one volume."""
    capacity = answers.get("medium.capacity_gb")
    if channel in MEDIUM_CHANNELS and _number(capacity):
        return int(capacity * GB * (1 - VOLUME_RESERVE))
    return None


def part_size(channel: str, answers: dict) -> int | None:
    """Files larger than this are split; None when nothing needs splitting."""
    limits = [value for value in (max_file_bytes(channel, answers), volume_capacity(channel, answers)) if value]
    return min(limits) if limits else None


def part_name(path: str, index: int) -> str:
    """The name of part `index` (from 1) of the file at `path`."""
    return path + PART_SUFFIX.format(index)


def units_of(files: list[dict], size_limit: int | None) -> list[dict]:
    """What goes onto volumes: whole files, and the parts of files larger than `size_limit`.

    `files` holds {path, size, parts}, where `parts` are the SHA-256 of each part.
    Each unit is {path, size, sha256, of}: `of` is the original path for a part, else None.
    """
    units = []
    for entry in files:
        count = part_count(entry["size"], size_limit)
        if not count:
            units.append({"path": entry["path"], "size": entry["size"], "sha256": entry["sha256"], "of": None})
            continue
        for index in range(1, count + 1):
            size = min(size_limit, entry["size"] - (index - 1) * size_limit)
            units.append(
                {"path": part_name(entry["path"], index), "size": size, "sha256": entry["parts"][index - 1], "of": entry["path"]}
            )
    return units


def assign_volumes(units: list[dict], capacity: int | None) -> list[list[dict]]:
    """First fit, largest first. One volume when `capacity` is None."""
    ordered = sorted(units, key=lambda unit: (-unit["size"], unit["path"]))
    if capacity is None:
        return [ordered]
    volumes: list[list[dict]] = []
    free: list[int] = []
    for unit in ordered:
        for index, room in enumerate(free):
            if unit["size"] <= room:
                volumes[index].append(unit)
                free[index] -= unit["size"]
                break
        else:
            volumes.append([unit])
            free.append(capacity - unit["size"])
    return volumes
```

Create `$T/scripts/transfer_lib/archive.py` (with the sources of Step 1 in its docstring):

```python
"""What an image archive holds: the image ID and platform that docker load will see.

The archive layout (manifest.json naming one config file; the image ID is the SHA-256
of that config) is the one recorded with its source in references/fetch.md.
"""
from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path


class ArchiveError(Exception):
    """The file is not a single-image archive that docker load accepts."""


def read_image_archive(path: Path) -> dict:
    """{"id": "sha256:...", "platform": "linux/amd64", "tags": [...]} of a one-image archive."""
    try:
        with tarfile.open(path, mode="r:") as tar:
            manifest = json.load(tar.extractfile("manifest.json"))
            if not isinstance(manifest, list) or len(manifest) != 1:
                count = len(manifest) if isinstance(manifest, list) else "no"
                raise ArchiveError(f"{path.name}: holds {count} images; one was expected")
            config_bytes = tar.extractfile(manifest[0]["Config"]).read()
    except (tarfile.TarError, KeyError, AttributeError, TypeError, ValueError, OSError) as error:
        raise ArchiveError(f"{path.name}: not an image archive docker load reads ({error})") from None
    config = json.loads(config_bytes)
    return {
        "id": "sha256:" + hashlib.sha256(config_bytes).hexdigest(),
        "platform": f"{config.get('os', '')}/{config.get('architecture', '')}",
        "tags": list(manifest[0].get("RepoTags") or []),
    }
```

- [ ] **Step 5: Run the suite**

Run both suite commands. Expected: `Ran 486 tests`, `OK` on both.

- [ ] **Step 6: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/hashing.py \
  plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/volumes.py \
  plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/archive.py \
  tests/test_transfer_volumes.py
git commit -m "feat(transfer): hashes with parts, first-fit volume plan, image archive reader

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: pack.py, the bundle files and the inside scripts

§8.6, §8.7, §9.2, §9.3. `pack.py` hashes the fetched files, plans the volumes, and writes `bundle.json`, `SHA256SUMS`, `PARTS.txt`, `VOLUMES.txt`, the two inventories, `INSIDE.md` and/or `AGENTS-INSIDE.md` by `inside.operator`, `SEND-ORDER.txt` for a data diode, and the two inside scripts. `pack.py --write-volume N --to DIR` writes one medium, cutting parts on the way, and reads every file back. `verify.sh` and `load.sh` are tested here on bundles that `pack.py` wrote, because they read its files.

**Files:**
- Create: `$T/scripts/transfer_lib/bundle.py`, `inventory.py`, `runbook.py`, `pack_files.py`, `$T/scripts/pack.py`
- Create: `$T/templates/verify.sh`, `$T/templates/load.sh`
- Create: `tests/test_transfer_pack.py`, `tests/test_transfer_write.py`, `tests/test_inside_scripts.py`
- Modify: `tests/test_packaging.py` (allow `.sh`)

**Interfaces:**
- Consumes: `hashing`, `volumes`, `archive`, `items`, `inputs`, `state`, `tools.COMMANDS` and `TEMPLATE_COMMANDS`.
- Produces:
  - `bundle.PackError(problems)`, `manual_entries(state)`, `pack_items(state)`, `item_files(bundle, item, state)`, `unsettled(bundle, state) -> [str]`, `build_bundle(bundle, state, manifest, blueprint_meta) -> dict` (`schema_version`, `project`, `manifest_digest`, `platform`, `channel`, `operator`, `language`, `packed`, `part_size`, `volume_capacity`, `items` with `files: [{path, size, sha256, pickle, volumes}]`, `volumes: [{number, bytes, units}]`), `data_files`, `parts_text` (`<count> <sha256> <path>`), `volumes_text` (`<volume> <size> <sha256> <path>`), `sums_text` (`<sha256>  <path>`), `write_json`, `stray_files`.
  - `inventory.COLUMNS = (path, size, sha256, kind, component, version, source, licence, pickle)`, `rows`, `render_csv`, `render_markdown` (with a `## Not carried` section).
  - `runbook.BUNDLE_DIR = "/srv/airgap-bundle"`, `MODEL_DIR = "/srv/models"`, `steps`, `render_runbook`, `render_agent_rules`, `documents(bundle_data, manifest) -> {file name: text}`, `command_lines(text) -> [str]` (the lines inside `sh` fences).
  - `pack_files.TEMPLATES_DIR`, `render_template(name)` (fills `{{docker.load}}` and `{{docker.image_id}}` from `tools.COMMANDS`), `write_generated(bundle, bundle_data, manifest) -> [names]` (`SHA256SUMS` last), `WriteError`, `write_volume(bundle, bundle_data, number, target, generated) -> [paths that read back differently]`.
  - `pack.py [--project-root DIR] [--write-volume N --to DIR]`: exit 2 without a plan, after a manifest change, with an unsettled manual item, or with an image for another platform; writes `pack = {volumes, total_bytes, generated, packed}` into `transfer.json`; prints `Translate their prose into '<language>'` when the blueprint's language is not `en`; `--write-volume` exits 2 for a volume that does not exist, a target that is not a folder or lies inside the bundle, and exits 1 on a read-back mismatch.
  - `verify.sh [bundle folder]`: exit 0 with `verify.sh: OK, N files match SHA256SUMS. Next: sh load.sh ...`; exit 1 with `MISSING.txt` (tab-separated `file`, `expected sha256`, `volume`, `bring next time`); exit 2 on wrong arguments. It joins parts, removes them, and writes `.verified`.
  - `load.sh [bundle folder] [model folder]`: refuses without a current `.verified`; loads every archive and checks its image ID against `<name>.id`; copies model folders; exit codes as `verify.sh`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_transfer_pack.py`:

```python
import csv
import hashlib
import io
import json
import unittest
import tempfile
from pathlib import Path

from tests import transfer_projects
from transfer_lib.constants import FAT32_MAX_FILE_BYTES, GB


class PackScriptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def packed(self, **kwargs):
        self.project, self.bundle = transfer_projects.packed_project(Path(self.tmp.name), **kwargs)
        self.data = json.loads((self.bundle / "bundle.json").read_text(encoding="utf-8"))
        return self.data

    def test_bundle_json_records_every_item(self):
        data = self.packed()
        manifest = json.loads((self.project / "docs/airgap/transfer-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(data["manifest_digest"], manifest["inputs_digest"])
        self.assertEqual((data["platform"], data["channel"], data["operator"]), ("linux/amd64", "removable_media", "people"))
        kinds = [item["kind"] for item in data["items"]]
        self.assertEqual(kinds.count("image"), 8)
        image = next(item for item in data["items"] if item["kind"] == "image")
        self.assertEqual(image["source"]["digest"], "sha256:" + "a" * 64)
        self.assertRegex(image["source"]["image_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual([Path(f["path"]).suffix for f in image["files"]], [".tar", ".digest", ".id"])
        model = next(item for item in data["items"] if item["kind"] == "model")
        self.assertEqual(model["source"]["revision"], transfer_projects.COMMIT)
        manual = next(item for item in data["items"] if item["kind"] == "manual")
        self.assertEqual((manual["status"], manual["files"]), ("not_needed", []))

    def test_sha256sums_is_coreutils_format_and_covers_every_file(self):
        self.packed()
        lines = (self.bundle / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        listed = {}
        for line in lines:
            self.assertRegex(line, r"^[0-9a-f]{64}  \S")
            digest, name = line.split("  ", 1)
            listed[name] = digest
        for name, digest in listed.items():
            self.assertEqual(hashlib.sha256((self.bundle / name).read_bytes()).hexdigest(), digest, name)
        self.assertIn("bundle.json", listed)
        self.assertIn("verify.sh", listed)
        self.assertNotIn("fetch.sh", listed)
        self.assertNotIn("SHA256SUMS", listed)

    def test_one_volume_on_a_large_exfat_disk(self):
        data = self.packed()
        self.assertEqual(len(data["volumes"]), 1)
        self.assertEqual((self.bundle / "PARTS.txt").read_text(encoding="utf-8").splitlines()[1:], [])

    def test_fat32_splits_files_over_the_limit(self):
        # A medium of 20,000 bytes makes the parts small; the rule is the same at 4 GiB.
        data = self.packed(sizes={"model:example-70b": 50000},
                           **{"medium.filesystem": "fat32", "medium.capacity_gb": 20000 / GB})
        self.assertEqual(data["part_size"], 19600)
        parts = (self.bundle / "PARTS.txt").read_text(encoding="utf-8").splitlines()[1:]
        weights = hashlib.sha256(b"w" * 50000).hexdigest()
        self.assertEqual(parts, [f"3 {weights} models/example-70b/model.safetensors"])
        for volume in data["volumes"]:
            self.assertLessEqual(volume["bytes"], 19600)
        volumes = (self.bundle / "VOLUMES.txt").read_text(encoding="utf-8")
        self.assertIn("models/example-70b/model.safetensors.part003", volumes)
        self.assertFalse((self.bundle / "models/example-70b/model.safetensors.part001").exists())

    def test_a_file_one_byte_over_the_fat32_limit_becomes_two_parts(self):
        # A sparse file: 4 GiB on paper, almost nothing on disk; hashing it reads 4 GiB of zeros.
        project, bundle = transfer_projects.planned_project(Path(self.tmp.name), **{"medium.filesystem": "fat32"})
        transfer_projects.fake_fetch(bundle, transfer_projects.load_state_of(project)["plan"]["items"])
        weights = bundle / "models/example-70b/model.safetensors"
        with weights.open("r+b") as handle:
            handle.truncate(FAT32_MAX_FILE_BYTES + 1)
        transfer_projects.settle_manual(project)
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 0, result.stderr)
        parts = (bundle / "PARTS.txt").read_text(encoding="utf-8").splitlines()[1:]
        self.assertEqual(len(parts), 1)
        self.assertTrue(parts[0].startswith("2 ") and parts[0].endswith(" models/example-70b/model.safetensors"))
        sizes = [line.split()[1] for line in (bundle / "VOLUMES.txt").read_text(encoding="utf-8").splitlines()
                 if ".part" in line and not line.startswith("#")]
        self.assertEqual(sizes, [str(FAT32_MAX_FILE_BYTES), "1"])

    def test_inventory_lists_files_largest_first_with_licences(self):
        self.packed(sizes={"model:example-70b": 50000})
        rows = list(csv.DictReader(io.StringIO((self.bundle / "INVENTORY.csv").read_text(encoding="utf-8"))))
        self.assertEqual(list(rows[0]), ["path", "size", "sha256", "kind", "component", "version", "source", "licence", "pickle"])
        self.assertEqual(rows[0]["path"], "models/example-70b/model.safetensors")
        sizes = [int(row["size"]) for row in rows]
        self.assertEqual(sizes, sorted(sizes, reverse=True))
        self.assertEqual(rows[0]["licence"], "see LICENSE")
        self.assertEqual(rows[0]["source"], f"huggingface example/model-70b at {transfer_projects.COMMIT}")
        package = next(row for row in rows if row["path"].endswith("alpha-cli-1.2.3-amd64"))
        self.assertEqual((package["kind"], package["licence"]), ("package", "MIT"))
        text = (self.bundle / "INVENTORY.md").read_text(encoding="utf-8")
        self.assertIn("## Not carried", text)
        self.assertIn("alpha-engine: runtime download 1: Staged by the operator", text)

    def test_runbook_and_agent_rules_follow_inside_operator(self):
        cases = {"people": {"INSIDE.md"}, "local_agent": {"AGENTS-INSIDE.md"},
                 "people_then_agent": {"INSIDE.md", "AGENTS-INSIDE.md"}}
        for index, (operator, expected) in enumerate(cases.items()):
            with self.subTest(operator=operator):
                project, bundle = transfer_projects.packed_project(
                    Path(self.tmp.name) / str(index), architect_answers={"inside.operator": operator}
                )
                found = {name for name in ("INSIDE.md", "AGENTS-INSIDE.md") if (bundle / name).exists()}
                self.assertEqual(found, expected)
        rules = (bundle / "AGENTS-INSIDE.md").read_text(encoding="utf-8")
        for phrase in ("Never download", "Check the exit code", "Never improvise", "MISSING.txt"):
            self.assertIn(phrase, rules)
        runbook = (bundle / "INSIDE.md").read_text(encoding="utf-8")
        self.assertIn("sh /srv/airgap-bundle/verify.sh /srv/airgap-bundle", runbook)
        self.assertIn("ALPHA_PING=0", runbook)
        for word in ("curl", "wget", "pip install", "docker pull", "hf download"):
            self.assertNotIn(word, runbook)

    def test_data_diode_gets_a_send_order(self):
        self.packed(architect_answers={"transfer.channel": "data_diode"}, answers=None,
                    **{"channel.max_file_gb": "none"})
        order = (self.bundle / "SEND-ORDER.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(order[:3], ["bundle.json", "SHA256SUMS", "SEND-ORDER.txt"])
        self.assertIn("models/example-70b/model.safetensors", order)

    def test_unsettled_manual_items_stop_pack(self):
        project, bundle = transfer_projects.planned_project(Path(self.tmp.name))
        transfer_projects.fake_fetch(bundle, transfer_projects.load_state_of(project)["plan"]["items"])
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 2)
        self.assertIn("manual:alpha-engine: runtime download 1: not settled", result.stderr)

    def test_an_image_for_another_platform_stops_pack(self):
        project, bundle = transfer_projects.planned_project(Path(self.tmp.name))
        transfer_projects.fake_fetch(bundle, transfer_projects.load_state_of(project)["plan"]["items"], arch="arm64")
        transfer_projects.settle_manual(project)
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 2)
        self.assertIn("holds an image for linux/arm64, not linux/amd64", result.stderr)

    def test_an_added_manual_item_is_carried(self):
        project, bundle = transfer_projects.planned_project(Path(self.tmp.name))
        transfer_projects.fake_fetch(bundle, transfer_projects.load_state_of(project)["plan"]["items"])
        (bundle / "manual/docker-engine").mkdir(parents=True)
        (bundle / "manual/docker-engine/engine.deb").write_bytes(b"deb")
        (bundle / "manual/tokenizer").mkdir(parents=True)
        (bundle / "manual/tokenizer/tok.json").write_text("{}", encoding="utf-8")
        transfer_projects.update_state(project, lambda state: state.update(manual=[
            {"item": "alpha-engine: runtime download 1", "status": "added", "path": "manual/tokenizer"},
            {"item": "Docker Engine 29 packages", "status": "added", "path": "manual/docker-engine"},
        ]))
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 0, result.stderr)
        sums = (bundle / "SHA256SUMS").read_text(encoding="utf-8")
        self.assertIn("manual/docker-engine/engine.deb", sums)
        self.assertIn("manual/tokenizer/tok.json", sums)
        self.assertIn("ls -l /srv/airgap-bundle/manual/docker-engine", (bundle / "INSIDE.md").read_text(encoding="utf-8"))

    def test_pack_records_its_result_in_transfer_json(self):
        self.packed()
        state = transfer_projects.load_state_of(self.project)
        self.assertEqual(state["pack"]["total_bytes"], sum(v["bytes"] for v in self.data["volumes"]))
        self.assertEqual(len(state["pack"]["volumes"]), 1)
        self.assertIn("bundle.json", state["pack"]["generated"])
        self.assertEqual(state["pack"]["generated"][-1], "SHA256SUMS")

    def test_another_language_is_reported_for_translation(self):
        project, bundle = transfer_projects.planned_project(Path(self.tmp.name), language="tr")
        transfer_projects.fake_fetch(bundle, transfer_projects.load_state_of(project)["plan"]["items"])
        transfer_projects.settle_manual(project)
        result = transfer_projects.run_script("pack.py", project)
        self.assertIn("Translate their prose into 'tr'", result.stdout)


if __name__ == "__main__":
    unittest.main()
```

Create `tests/test_transfer_write.py`:

```python
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import transfer_projects
from transfer_lib import pack_files
from transfer_lib.constants import GB


class WriteVolumeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project, self.bundle = transfer_projects.packed_project(
            Path(self.tmp.name), sizes={"model:example-70b": 50000},
            **{"medium.filesystem": "fat32", "medium.capacity_gb": 20000 / GB},
        )
        self.data = json.loads((self.bundle / "bundle.json").read_text(encoding="utf-8"))

    def write(self, number, target):
        Path(target).mkdir(parents=True, exist_ok=True)
        return transfer_projects.run_script("pack.py", self.project, "--write-volume", str(number), "--to", str(target))

    def test_every_volume_is_written_with_parts_and_reads_back(self):
        total = len(self.data["volumes"])
        self.assertGreater(total, 1)
        for number in range(1, total + 1):
            target = Path(self.tmp.name) / f"medium{number}"
            result = self.write(number, target)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"Wrote volume {number} of {total}", result.stdout)
            self.assertEqual((target / "VOLUME.txt").read_text(encoding="utf-8"), f"volume {number} of {total}\n")
            for name in ("bundle.json", "SHA256SUMS", "PARTS.txt", "VOLUMES.txt", "verify.sh", "load.sh", "INSIDE.md"):
                self.assertTrue((target / name).is_file(), name)
            for unit in self.data["volumes"][number - 1]["units"]:
                written = (target / unit["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(written).hexdigest(), unit["sha256"], unit["path"])
                self.assertLessEqual(len(written), 19600)

    def test_a_read_back_mismatch_is_reported(self):
        target = Path(self.tmp.name) / "medium"
        target.mkdir()
        with mock.patch.object(pack_files, "_read_back", return_value="0" * 64):
            bad = pack_files.write_volume(self.bundle, self.data, 1, target, ["bundle.json"])
        self.assertTrue(bad)

    def test_wrong_volume_or_target_is_exit_2(self):
        result = self.write(99, Path(self.tmp.name) / "medium")
        self.assertEqual(result.returncode, 2)
        self.assertIn("there is no volume 99", result.stderr)
        result = self.write(1, self.bundle / "inside")
        self.assertEqual(result.returncode, 2)
        self.assertIn("inside the bundle folder", result.stderr)
        result = transfer_projects.run_script("pack.py", self.project, "--write-volume", "1", "--to", str(Path(self.tmp.name) / "absent"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("is not a folder", result.stderr)

    def test_write_volume_needs_to(self):
        result = transfer_projects.run_script("pack.py", self.project, "--write-volume", "1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--write-volume and --to go together", result.stderr)


if __name__ == "__main__":
    unittest.main()
```

Create `tests/test_inside_scripts.py`:

```python
"""verify.sh and load.sh on small fake bundles, with POSIX sh and a stub docker.

They need coreutils' sha256sum. CI runs them on Linux; on a machine without
sha256sum they are skipped."""
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import TRANSFER_TEMPLATES_DIR, transfer_projects
from transfer_lib.constants import GB
from transfer_lib.tools import COMMANDS, TEMPLATE_COMMANDS

SHELLS = [name for name in ("sh", "dash") if shutil.which(name)]
DOCKER_STUB = r"""#!/bin/sh
# Records each call; "image inspect" prints the ID it is asked about unless STUB_WRONG_ID is set.
echo "$*" >> "$DOCKER_CALLS"
case "$*" in
  *inspect*)
    if [ -n "${STUB_WRONG_ID:-}" ]; then echo "sha256:$(printf '%064d' 9)"; else for last in "$@"; do :; done; echo "$last"; fi ;;
esac
"""


@unittest.skipUnless(shutil.which("sha256sum"), "needs coreutils sha256sum")
class InsideScriptsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        self.project, self.bundle = transfer_projects.packed_project(
            tmp, sizes={"model:example-70b": 50000},
            **{"medium.filesystem": "fat32", "medium.capacity_gb": 20000 / GB},
        )
        data = json.loads((self.bundle / "bundle.json").read_text(encoding="utf-8"))
        self.volumes = len(data["volumes"])
        self.inside = tmp / "inside"
        self.inside.mkdir()
        for number in range(1, self.volumes + 1):
            medium = tmp / f"medium{number}"
            medium.mkdir()
            result = transfer_projects.run_script("pack.py", self.project, "--write-volume", str(number), "--to", str(medium))
            self.assertEqual(result.returncode, 0, result.stderr)
            shutil.copytree(medium, self.inside, dirs_exist_ok=True)
        self.stubs = tmp / "stubs"
        self.stubs.mkdir()
        docker = self.stubs / "docker"
        docker.write_text(DOCKER_STUB, encoding="utf-8")
        docker.chmod(docker.stat().st_mode | stat.S_IXUSR)
        self.env = dict(os.environ, PATH=f"{self.stubs}{os.pathsep}{os.environ['PATH']}", DOCKER_CALLS=str(tmp / "calls"))

    def run_sh(self, script, *args, shell="sh", env=None):
        return subprocess.run([shell, str(self.inside / script), *args], capture_output=True, text=True, env=env or self.env)

    def missing(self):
        return (self.inside / "MISSING.txt").read_text(encoding="utf-8").splitlines()

    def test_the_templates_are_posix_sh_without_a_shebang(self):
        for name in ("verify.sh", "load.sh"):
            text = (TRANSFER_TEMPLATES_DIR / name).read_text(encoding="utf-8")
            self.assertFalse(text.startswith("#!"), name)
            self.assertIn("set -eu", text)
            for word in ("python", "curl", "wget", "[[", "local "):
                self.assertNotIn(word, text, f"{name}: {word}")
        copied = (self.inside / "load.sh").read_text(encoding="utf-8")
        self.assertNotIn("{{docker.", copied)
        for key in TEMPLATE_COMMANDS:
            self.assertIn("{{" + key + "}}", (TRANSFER_TEMPLATES_DIR / "load.sh").read_text(encoding="utf-8"))
            self.assertIn(COMMANDS[key].line, copied)
        self.assertEqual((self.inside / "verify.sh").read_text(encoding="utf-8"),
                         (TRANSFER_TEMPLATES_DIR / "verify.sh").read_text(encoding="utf-8"))

    def test_verify_passes_and_joins_the_parts(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.run_sh("verify.sh", str(self.inside), shell=shell)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("verify.sh: OK", result.stdout.splitlines()[-1])
                self.assertEqual((self.inside / "models/example-70b/model.safetensors").read_bytes(), b"w" * 50000)
                self.assertFalse((self.inside / "models/example-70b/model.safetensors.part001").exists())
                self.assertTrue((self.inside / ".verified").is_file())

    def test_one_changed_byte_is_found(self):
        path = self.inside / "packages/alpha-engine/alpha-cli-1.2.3-amd64"
        data = bytearray(path.read_bytes())
        data[0] ^= 1
        path.write_bytes(bytes(data))
        result = self.run_sh("verify.sh", str(self.inside))
        self.assertEqual(result.returncode, 1)
        lines = self.missing()
        self.assertEqual(lines[0], "file\texpected sha256\tvolume\tbring next time")
        self.assertTrue(lines[1].startswith("packages/alpha-engine/alpha-cli-1.2.3-amd64\t"))
        self.assertIn("a new copy of volume", lines[1])

    def test_one_missing_part_is_found_with_its_volume(self):
        part = self.inside / "models/example-70b/model.safetensors.part002"
        part.unlink()
        result = self.run_sh("verify.sh", str(self.inside))
        self.assertEqual(result.returncode, 1)
        row = self.missing()[1].split("\t")
        self.assertEqual(row[0], "models/example-70b/model.safetensors.part002")
        self.assertRegex(row[1], r"^[0-9a-f]{64}$")
        self.assertEqual(row[3], f"volume {row[2]} of {self.volumes}")

    def test_verify_arguments(self):
        self.assertEqual(self.run_sh("verify.sh", "a", "b").returncode, 2)
        self.assertEqual(self.run_sh("verify.sh", str(self.inside / "nothing")).returncode, 2)

    def test_load_refuses_before_verify(self):
        result = self.run_sh("load.sh", str(self.inside), str(Path(self.tmp.name) / "models"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("run sh verify.sh", result.stderr)

    def test_load_after_verify_loads_every_image_and_copies_models(self):
        self.assertEqual(self.run_sh("verify.sh", str(self.inside)).returncode, 0)
        models = Path(self.tmp.name) / "models"
        result = self.run_sh("load.sh", str(self.inside), str(models))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = Path(self.env["DOCKER_CALLS"]).read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum(1 for call in calls if "load" in call), 8)
        self.assertTrue((models / "example-70b" / "model.safetensors").is_file())
        self.assertIn("load.sh: OK", result.stdout)

    def test_load_stops_on_another_image_id(self):
        self.assertEqual(self.run_sh("verify.sh", str(self.inside)).returncode, 0)
        env = dict(self.env, STUB_WRONG_ID="1")
        result = self.run_sh("load.sh", str(self.inside), str(Path(self.tmp.name) / "models"), env=env)
        self.assertEqual(result.returncode, 1)
        self.assertIn("did not load as sha256:", result.stderr)

    def test_load_after_a_change_to_sha256sums_needs_verify_again(self):
        self.assertEqual(self.run_sh("verify.sh", str(self.inside)).returncode, 0)
        with (self.inside / "SHA256SUMS").open("a", encoding="utf-8") as handle:
            handle.write("0" * 64 + "  extra\n")
        self.assertEqual(self.run_sh("load.sh", str(self.inside), "models").returncode, 1)

    def test_load_arguments(self):
        self.assertEqual(self.run_sh("load.sh", "a", "b", "c").returncode, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Allow shell files in the plugin**

In `tests/test_packaging.py`, replace the comment above `ALLOWED_SUFFIXES` and the set with:

```python
# documentation. Python, TOML and shell files are the exception: the portal accepts them only from
# a Verified organization (it blocked the catalog's first TOML file), and the skills need them
# (airgap-transfer copies its POSIX sh templates into every bundle), so a directory listing waits
# for Verified status. See docs/packaging-facts.md, Q8. A .sh file still never starts with #!:
# the inside runs it as `sh verify.sh`.
ALLOWED_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".py", ".toml", ".sh"}
```

The comment it replaces starts with `# documentation. Python and TOML files are the exception`; keep the lines above it.

- [ ] **Step 3: Run the tests to see them fail**

Run: `python3.11 -m unittest tests.test_transfer_pack tests.test_transfer_write tests.test_inside_scripts`

Expected: `tests.test_transfer_write` fails to import (`cannot import name 'pack_files' from 'transfer_lib'`), and the pack and inside tests fail because `pack.py` does not exist: `FAILED (failures=25, errors=2)` or close to it (the inside tests are skipped where `sha256sum` is missing).

- [ ] **Step 4: Write the bundle model, the inventory and the runbook**

Create `$T/scripts/transfer_lib/bundle.py`:

```python
"""pack.py's work: the files of every item, their hashes, the volume plan and bundle.json."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .archive import ArchiveError, read_image_archive
from .constants import BUNDLE_SCHEMA_VERSION, CONNECTED_ONLY, PICKLE_SUFFIXES
from .hashing import hash_file
from .items import checksums_path
from .volumes import assign_volumes, part_size, units_of, volume_capacity


class PackError(Exception):
    """The bundle cannot be packed as it is; `problems` says why. pack.py exits 2."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = list(problems)


def _files_under(bundle: Path, relative: str) -> list[str]:
    """Bundle paths of the files at or below `relative`, leaving out dot-files and dot-folders."""
    root = bundle / relative
    if root.is_file():
        return [relative]
    if not root.is_dir():
        return []
    found = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(bundle).as_posix()
        if path.is_file() and not any(part.startswith(".") for part in path.relative_to(root).parts):
            found.append(rel)
    return found


def manual_entries(state: dict) -> dict[str, dict]:
    return {entry["item"]: entry for entry in state.get("manual", []) if isinstance(entry, dict)}


def pack_items(state: dict) -> list[dict]:
    """The plan's items plus manual items the user added that the manifest did not name."""
    items = [dict(item) for item in state["plan"]["items"]]
    named = {item["name"] for item in items if item["kind"] == "manual"}
    for name, entry in manual_entries(state).items():
        if name not in named and entry.get("status") == "added":
            items.append({"id": f"manual:{name}", "kind": "manual", "name": name,
                          "text": entry.get("text", "Added by the user."), "path": entry["path"]})
    return items


def item_files(bundle: Path, item: dict, state: dict) -> list[str]:
    """The bundle paths that belong to `item`; empty when its files are missing."""
    if item["kind"] == "image":
        if not (bundle / item["path"]).is_file():
            return []
        companions = [str(Path(item["path"]).with_suffix(suffix)) for suffix in (".digest", ".id")]
        return [item["path"]] + [p for p in companions if (bundle / p).is_file()]
    if item["kind"] == "package":
        listed = checksums_path(item)
        files = [item["path"]] if (bundle / item["path"]).is_file() else []
        if files and listed and (bundle / listed).is_file():
            files.append(listed)
        return files
    if item["kind"] == "manual":
        entry = manual_entries(state).get(item["name"], {})
        return _files_under(bundle, entry["path"]) if entry.get("status") == "added" else []
    return _files_under(bundle, item["path"])


def unsettled(bundle: Path, state: dict) -> list[str]:
    """Items that have neither their files nor, for a manual item, a 'not needed' reason."""
    problems = []
    manual = manual_entries(state)
    for item in pack_items(state):
        if item["kind"] == "manual":
            entry = manual.get(item["name"])
            if entry is None:
                problems.append(f"{item['id']}: not settled; add its files under manual/ or mark it not needed with a reason")
                continue
            if entry.get("status") == "not_needed":
                continue
        if not item_files(bundle, item, state):
            problems.append(f"{item['id']}: no files at {item['path'] if item['kind'] != 'manual' else manual[item['name']]['path']}")
    return problems


def _source(bundle: Path, item: dict) -> dict:
    if item["kind"] == "image":
        digest_file = (bundle / item["path"]).with_suffix(".digest")
        digest = digest_file.read_text(encoding="utf-8").strip() if digest_file.is_file() else ""
        return {"ref": item["ref"], "digest": digest or item.get("digest", "")}
    if item["kind"] == "package":
        return {"url": item["url"], "checksums": item.get("checksums", "")}
    if item["kind"] == "model":
        return dict(item["source"])
    return {"text": item.get("text", "")}


def build_bundle(bundle: Path, state: dict, manifest: dict, blueprint_meta: dict) -> dict:
    """bundle.json for a fetched bundle: items, files, hashes and volumes.

    `blueprint_meta` holds project, channel, operator and language.
    Raises PackError when an item is unsettled or an image archive does not fit.
    """
    bundle = Path(bundle)
    problems = unsettled(bundle, state)
    if problems:
        raise PackError(problems)
    answers = state["answers"]
    channel = blueprint_meta["channel"]
    limit = part_size(channel, answers)
    platform = state["plan"]["platform"]
    items, files = [], []
    for item in pack_items(state):
        entry = manual_entries(state).get(item["name"]) if item["kind"] == "manual" else None
        record = {key: item[key] for key in ("id", "kind", "component", "version", "name", "license", "benchmark") if key in item}
        record["source"] = _source(bundle, item)
        if entry and entry.get("status") == "not_needed":
            record.update(status="not_needed", reason=entry["reason"], files=[])
            items.append(record)
            continue
        if item["kind"] == "image":
            try:
                image = read_image_archive(bundle / item["path"])
            except ArchiveError as error:
                raise PackError([str(error)]) from None
            if image["platform"] != platform:
                raise PackError([f"{item['path']}: holds an image for {image['platform']}, not {platform}; fetch it again"])
            (bundle / item["path"]).with_suffix(".id").write_text(image["id"] + "\n", encoding="utf-8")
            record["source"]["image_id"] = image["id"]
        if item["kind"] == "model":
            record["allow_pickle"] = item.get("allow_pickle", False)
        record["files"] = []
        for path in item_files(bundle, item, state):
            size = (bundle / path).stat().st_size
            whole, parts = hash_file(bundle / path, limit)
            files.append({"path": path, "size": size, "sha256": whole, "parts": parts})
            record["files"].append({"path": path, "size": size, "sha256": whole,
                                    "pickle": item["kind"] == "model" and path.endswith(PICKLE_SUFFIXES)})
        items.append(record)
    unique = {entry["path"]: entry for entry in files}
    volumes = assign_volumes(units_of(list(unique.values()), limit), volume_capacity(channel, answers))
    where: dict[str, list[int]] = {}
    for number, volume in enumerate(volumes, start=1):
        for unit in volume:
            where.setdefault(unit["of"] or unit["path"], []).append(number)
    for record in items:
        for entry in record["files"]:
            entry["volumes"] = sorted(set(where.get(entry["path"], [])))
    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "project": blueprint_meta["project"],
        "manifest_digest": manifest["inputs_digest"],
        "platform": platform,
        "channel": channel,
        "operator": blueprint_meta["operator"],
        "language": blueprint_meta["language"],
        "packed": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "part_size": limit,
        "volume_capacity": volume_capacity(channel, answers),
        "items": items,
        "volumes": [
            {"number": number, "bytes": sum(unit["size"] for unit in volume),
             "units": [{"path": u["path"], "size": u["size"], "sha256": u["sha256"], "of": u["of"]} for u in volume]}
            for number, volume in enumerate(volumes, start=1)
        ],
    }


def data_files(bundle_data: dict) -> list[dict]:
    """Every original file of the bundle, once, as {path, size, sha256}."""
    seen = {}
    for item in bundle_data["items"]:
        for entry in item["files"]:
            seen.setdefault(entry["path"], entry)
    return [seen[path] for path in sorted(seen)]


def parts_text(bundle_data: dict) -> str:
    lines = ["# parts sha256-of-the-whole-file path; part N is the path followed by .partNNN"]
    counts: dict[str, int] = {}
    for volume in bundle_data["volumes"]:
        for unit in volume["units"]:
            if unit["of"]:
                counts[unit["of"]] = counts.get(unit["of"], 0) + 1
    by_path = {entry["path"]: entry for entry in data_files(bundle_data)}
    lines += [f"{counts[path]} {by_path[path]['sha256']} {path}" for path in sorted(counts)]
    return "\n".join(lines) + "\n"


def volumes_text(bundle_data: dict) -> str:
    lines = ["# volume size sha256 path; a path ending in .partNNN is one part of a split file"]
    for volume in bundle_data["volumes"]:
        lines += [f"{volume['number']} {u['size']} {u['sha256']} {u['path']}" for u in volume["units"]]
    return "\n".join(lines) + "\n"


def sums_text(entries: list[tuple[str, str]]) -> str:
    """coreutils format: '<sha256>  <path>' per line."""
    return "".join(f"{digest}  {path}\n" for path, digest in sorted(entries))


def write_json(path: Path, data: dict) -> None:
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def stray_files(bundle: Path, bundle_data: dict, generated: set[str]) -> list[str]:
    """Files in the bundle folder that no item claims and pack.py did not write."""
    claimed = {entry["path"] for entry in data_files(bundle_data)} | generated
    found = []
    for path in sorted(Path(bundle).rglob("*")):
        rel = path.relative_to(bundle).as_posix()
        if path.is_file() and rel not in claimed and rel.split("/")[0] not in CONNECTED_ONLY and not any(
            part.startswith(".") for part in Path(rel).parts
        ):
            found.append(rel)
    return found
```

Create `$T/scripts/transfer_lib/inventory.py`:

```python
"""INVENTORY.md and INVENTORY.csv: what the people who approve the transfer read."""
from __future__ import annotations

import csv
import io

from .bundle import data_files

COLUMNS = ("path", "size", "sha256", "kind", "component", "version", "source", "licence", "pickle")


def _source_text(item: dict) -> str:
    source = item["source"]
    if item["kind"] == "image":
        return f"{source['ref']} {source.get('digest') or '(no digest recorded)'}"
    if item["kind"] == "package":
        return source["url"]
    if item["kind"] == "model":
        if source.get("source") == "huggingface":
            return f"huggingface {source['repo']} at {source['revision']}"
        return f"local folder {source.get('path', '')}"
    return "added by the user"


def _licence(item: dict) -> str:
    if item["kind"] == "model":
        names = [entry["path"].rsplit("/", 1)[-1] for entry in item["files"]]
        licences = [name for name in names if name.upper().startswith(("LICENSE", "LICENCE"))]
        return "see " + ", ".join(sorted(set(licences))) if licences else "not stated: no licence file in the model folder"
    if item["kind"] == "manual":
        return "as supplied by the user"
    return item.get("license") or "not stated"


def rows(bundle_data: dict) -> list[dict]:
    """One row per file, largest first: scanning hundreds of gigabytes takes time."""
    owner = {}
    for item in bundle_data["items"]:
        for entry in item["files"]:
            owner.setdefault(entry["path"], (item, entry))
    result = []
    for entry in data_files(bundle_data):
        item, own = owner[entry["path"]]
        result.append(
            {
                "path": entry["path"],
                "size": entry["size"],
                "sha256": entry["sha256"],
                "kind": item["kind"],
                "component": item.get("component") or item.get("name", ""),
                "version": item.get("version", ""),
                "source": _source_text(item),
                "licence": _licence(item),
                "pickle": "pickle, allowed by the user" if own.get("pickle") else "",
            }
        )
    return sorted(result, key=lambda row: (-row["size"], row["path"]))


def render_csv(bundle_data: dict) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows(bundle_data))
    return buffer.getvalue()


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(bundle_data: dict) -> str:
    table = rows(bundle_data)
    total = sum(row["size"] for row in table)
    lines = [
        f"# Transfer inventory: {bundle_data['project']}",
        "",
        f"- Made from the transfer manifest with digest {bundle_data['manifest_digest']}",
        f"- Platform: {bundle_data['platform']}",
        f"- Channel: {bundle_data['channel']}",
        f"- Files: {len(table)}, {total:,} bytes in all, on {len(bundle_data['volumes'])} volume(s)",
        f"- Packed: {bundle_data['packed']}",
        "",
        "Every file is listed with its SHA-256, largest first. Model weights are safetensors unless the "
        "pickle column says the user allowed pickle files. Publisher checksum files were checked on the "
        "connected side where the publisher has one; publisher signatures are not checked by this version.",
        "",
        "| Path | Size | SHA-256 | Kind | Component | Version | Source | Licence | Pickle |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    lines += ["| " + " | ".join(_cell(row[key]) for key in COLUMNS) + " |" for row in table]
    skipped = [item for item in bundle_data["items"] if item.get("status") == "not_needed"]
    lines += ["", "## Not carried", ""]
    lines += [f"- {item['name']}: {item['reason']}" for item in skipped] or ["Nothing: every item is carried."]
    return "\n".join(lines) + "\n"
```

Create `$T/scripts/transfer_lib/runbook.py`:

````python
"""INSIDE.md (the runbook for people) and AGENTS-INSIDE.md (the rules for an inside agent).

Both are written in English. When the blueprint's language is another, the agent on the
connected side translates the prose and keeps every command line as it is; check.py B7
finds a command line that went missing.
"""
from __future__ import annotations

from .constants import AGENT_RULES_FILE, AGENT_RULES_OPERATORS, RUNBOOK_FILE, RUNBOOK_OPERATORS

BUNDLE_DIR = "/srv/airgap-bundle"
MODEL_DIR = "/srv/models"


def _fence(*commands: str) -> list[str]:
    return ["```sh", *commands, "```"]


def steps(bundle_data: dict, manifest: dict) -> list[dict]:
    """The inside steps, each {title, commands, expected}; the same for people and agents."""
    count = len(bundle_data["volumes"])
    channel = bundle_data["channel"]
    if channel == "data_diode":
        copy = {
            "title": "Wait until every file in SEND-ORDER.txt has arrived, then copy them into one folder",
            "commands": [f"mkdir -p {BUNDLE_DIR}", f"cp -R RECEIVED_FOLDER/. {BUNDLE_DIR}/"],
            "expected": "No output. Replace RECEIVED_FOLDER with the folder where the diode delivers files.",
        }
    else:
        copy = {
            "title": f"Copy every volume into one folder ({count} volume(s); VOLUME.txt on each says which)",
            "commands": [f"mkdir -p {BUNDLE_DIR}", f"cp -R VOLUME_FOLDER/. {BUNDLE_DIR}/"],
            "expected": "No output. Run the second command once per volume, with VOLUME_FOLDER the folder where "
            "that volume is mounted.",
        }
    result = [
        copy,
        {
            "title": "Check every file",
            "commands": [f"sh {BUNDLE_DIR}/verify.sh {BUNDLE_DIR}"],
            "expected": "Exit code 0 and a last line that starts with 'verify.sh: OK'. Exit code 1: stop; "
            "MISSING.txt in the bundle folder lists each file to bring next time and the volume it was on.",
        },
        {
            "title": "Load the images and copy the model files",
            "commands": [f"mkdir -p {MODEL_DIR}", f"sh {BUNDLE_DIR}/load.sh {BUNDLE_DIR} {MODEL_DIR}"],
            "expected": "Exit code 0 and a last line that starts with 'load.sh: OK'. Exit code 1: stop and report "
            "the message.",
        },
    ]
    for item in bundle_data["items"]:
        if item["kind"] == "manual" and item.get("status") != "not_needed" and item["files"]:
            folder = item["files"][0]["path"].split("/")[1]
            result.append(
                {
                    "title": f"Manual item: {item['name']}",
                    "commands": [f"ls -l {BUNDLE_DIR}/manual/{folder}"],
                    "expected": "The files that were added for it on the connected side. This bundle has no script "
                    "for it: install it as its own files describe, and ask a person when they do not.",
                }
            )
    settings = [f"{row['component']}: {row['disable']} ({row['what']})" for row in manifest.get("telemetry", [])]
    result.append(
        {
            "title": "Switch off telemetry before the first start",
            "commands": [],
            "expected": "Set each of these, as section 4 of the transfer manifest lists them: "
            + ("; ".join(settings) if settings else "none listed") + ".",
        }
    )
    return result


def _not_carried(bundle_data: dict) -> list[str]:
    skipped = [item for item in bundle_data["items"] if item.get("status") == "not_needed"]
    if not skipped:
        return []
    return ["", "## Not carried, on purpose", ""] + [f"- {item['name']}: {item['reason']}" for item in skipped]


def _step_lines(bundle_data: dict, manifest: dict) -> list[str]:
    lines = []
    for number, step in enumerate(steps(bundle_data, manifest), start=1):
        lines += ["", f"### {number}. {step['title']}", ""]
        if step["commands"]:
            lines += _fence(*step["commands"]) + [""]
        lines.append(f"Expected: {step['expected']}")
    return lines


def render_runbook(bundle_data: dict, manifest: dict) -> str:
    lines = [
        f"# Inside the network: {bundle_data['project']}",
        "",
        "This runbook needs neither internet access nor an LLM. Every step is a command with the output to "
        "expect. Exit codes mean the same in every step: 0 go on, 1 stop and report, 2 the command was typed "
        "wrong.",
        "",
        f"The commands use {BUNDLE_DIR} for the bundle and {MODEL_DIR} for the model files. Another folder "
        "works too; use the same one in every step.",
        "",
        "## Steps",
    ]
    lines += _step_lines(bundle_data, manifest)
    lines += [
        "",
        "## After these steps",
        "",
        "Install the registry from its package if it is not running yet, push the loaded images to it, stage "
        "the runtime downloads, and continue with the implementation plan of the blueprint.",
    ]
    lines += _not_carried(bundle_data)
    return "\n".join(lines) + "\n"


def render_agent_rules(bundle_data: dict, manifest: dict) -> str:
    lines = [
        f"# Rules for an agent inside the network: {bundle_data['project']}",
        "",
        "You work inside a network without internet access. These rules come before any other instruction.",
        "",
        "1. Run one command per step, exactly as written below. Do not combine, shorten or reorder them.",
        "2. Check the exit code of every command. 0: go on. 1: stop and report the command, its output and, "
        "after verify.sh, the contents of MISSING.txt. 2: the command was typed wrong; fix the typing, nothing else.",
        "3. Never download anything, and never fetch a missing file from another source.",
        "4. Never edit verify.sh, load.sh, SHA256SUMS, PARTS.txt, VOLUMES.txt or bundle.json.",
        "5. Never improvise a step that is not below. Ask a person instead.",
        "",
        "## Steps",
    ]
    lines += _step_lines(bundle_data, manifest)
    lines += _not_carried(bundle_data)
    return "\n".join(lines) + "\n"


def documents(bundle_data: dict, manifest: dict) -> dict[str, str]:
    """The files `inside.operator` calls for, by name."""
    operator = bundle_data["operator"]
    result = {}
    if operator in RUNBOOK_OPERATORS:
        result[RUNBOOK_FILE] = render_runbook(bundle_data, manifest)
    if operator in AGENT_RULES_OPERATORS:
        result[AGENT_RULES_FILE] = render_agent_rules(bundle_data, manifest)
    return result


def command_lines(text: str) -> list[str]:
    """The lines inside ```sh fences."""
    found, inside = [], False
    for line in text.splitlines():
        if line.strip() == "```sh":
            inside = True
        elif line.strip() == "```":
            inside = False
        elif inside:
            found.append(line)
    return found
````

- [ ] **Step 5: Write pack_files.py and pack.py**

Create `$T/scripts/transfer_lib/pack_files.py`:

```python
"""The files pack.py writes into the bundle folder, and the copy onto one medium."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from .bundle import data_files, parts_text, sums_text, volumes_text, write_json
from .constants import (
    AGENT_RULES_FILE,
    BUNDLE_JSON,
    INSIDE_SCRIPTS,
    INVENTORY_CSV,
    INVENTORY_MD,
    PARTS_FILE,
    RUNBOOK_FILE,
    SEND_ORDER_FILE,
    SUMS_FILE,
    VOLUME_LABEL,
    VOLUMES_FILE,
)
from .hashing import CHUNK
from .inventory import render_csv, render_markdown
from .runbook import documents
from .tools import COMMANDS, TEMPLATE_COMMANDS

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


def render_template(name: str) -> str:
    """The template with each {{key}} of TEMPLATE_COMMANDS replaced by its command line."""
    text = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    for key in TEMPLATE_COMMANDS:
        text = text.replace("{{" + key + "}}", COMMANDS[key].line)
    return text


def write_generated(bundle: Path, bundle_data: dict, manifest: dict) -> list[str]:
    """Write every generated file and SHA256SUMS; return the generated names, SHA256SUMS last."""
    bundle = Path(bundle)
    write_json(bundle / BUNDLE_JSON, bundle_data)
    texts = {
        PARTS_FILE: parts_text(bundle_data),
        VOLUMES_FILE: volumes_text(bundle_data),
        INVENTORY_MD: render_markdown(bundle_data),
        INVENTORY_CSV: render_csv(bundle_data),
    }
    texts.update(documents(bundle_data, manifest))
    for name in (RUNBOOK_FILE, AGENT_RULES_FILE, SEND_ORDER_FILE):
        if name not in texts:
            (bundle / name).unlink(missing_ok=True)
    for name, text in texts.items():
        (bundle / name).write_text(text, encoding="utf-8")
    for name in INSIDE_SCRIPTS:
        (bundle / name).write_text(render_template(name), encoding="utf-8")
    generated = [BUNDLE_JSON, *texts, *INSIDE_SCRIPTS]
    if bundle_data["channel"] == "data_diode":
        order = [BUNDLE_JSON, SUMS_FILE, SEND_ORDER_FILE] + [n for n in generated if n != BUNDLE_JSON]
        order += [unit["path"] for volume in bundle_data["volumes"] for unit in volume["units"]]
        (bundle / SEND_ORDER_FILE).write_text("\n".join(order) + "\n", encoding="utf-8")
        generated.append(SEND_ORDER_FILE)
    entries = [(entry["path"], entry["sha256"]) for entry in data_files(bundle_data)]
    for name in generated:
        entries.append((name, hashlib.sha256((bundle / name).read_bytes()).hexdigest()))
    (bundle / SUMS_FILE).write_text(sums_text(entries), encoding="utf-8")
    return generated + [SUMS_FILE]


class WriteError(Exception):
    """A volume cannot be written: wrong number, target, or not enough room. Exit 2."""


def _copy_range(source: Path, start: int, size: int, target: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as reader, target.open("wb") as writer:
        reader.seek(start)
        left = size
        while left:
            chunk = reader.read(min(CHUNK, left))
            if not chunk:
                raise WriteError(f"{source} is shorter than bundle.json says; run pack.py again")
            writer.write(chunk)
            digest.update(chunk)
            left -= len(chunk)
    return digest.hexdigest()


def _read_back(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_volume(bundle: Path, bundle_data: dict, number: int, target: Path, generated: list[str]) -> list[str]:
    """Copy volume `number` to `target`, cutting parts on the way, and read every file back.

    Returns the paths whose read-back hash differs (empty when the volume is good).
    """
    bundle, target = Path(bundle).resolve(), Path(target).resolve()
    volumes = bundle_data["volumes"]
    if not 1 <= number <= len(volumes):
        raise WriteError(f"there is no volume {number}; this bundle has {len(volumes)}")
    if not target.is_dir():
        raise WriteError(f"{target} is not a folder; mount the medium and give its folder")
    if target == bundle or bundle in target.parents:
        raise WriteError(f"{target} is inside the bundle folder; give the folder of the medium")
    volume = volumes[number - 1]
    extra = sum((bundle / name).stat().st_size for name in generated)
    if shutil.disk_usage(target).free < volume["bytes"] + extra:
        raise WriteError(f"{target} has less free space than volume {number} needs ({volume['bytes'] + extra:,} bytes)")
    part_size = bundle_data["part_size"]
    bad = []
    for unit in volume["units"]:
        destination = target / unit["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if unit["of"]:
            index = int(unit["path"].rsplit(".part", 1)[1])
            _copy_range(bundle / unit["of"], (index - 1) * part_size, unit["size"], destination)
        else:
            _copy_range(bundle / unit["path"], 0, unit["size"], destination)
        if _read_back(destination) != unit["sha256"]:
            bad.append(unit["path"])
    for name in generated:
        shutil.copyfile(bundle / name, target / name)
        if _read_back(target / name) != _read_back(bundle / name):
            bad.append(name)
    (target / VOLUME_LABEL).write_text(f"volume {number} of {len(volumes)}\n", encoding="utf-8")
    return bad
```

Create `$T/scripts/pack.py`:

```python
"""Pack a fetched bundle: checksums, volume plan, inventory, inside scripts and runbook.

With --write-volume N --to FOLDER, copy volume N onto a mounted medium and read it back.
"""
from datetime import datetime, timezone
from pathlib import Path

from transfer_lib import cli
from transfer_lib.bundle import PackError, build_bundle, stray_files
from transfer_lib.constants import BUNDLE_JSON, EXIT_FINDINGS, EXIT_INPUT, EXIT_OK
from transfer_lib.inputs import InputError, channel_of, language_of, load_inputs, operator_of, read_json
from transfer_lib.pack_files import WriteError, write_generated, write_volume
from transfer_lib.state import load_state, save_state, state_path


def main(argv=None) -> int:
    parser = cli.make_parser(__doc__)
    parser.add_argument("--write-volume", type=int, metavar="N", help="copy volume N to --to")
    parser.add_argument("--to", metavar="FOLDER", help="the folder of the mounted medium")
    args = parser.parse_args(argv)
    if (args.write_volume is None) != (args.to is None):
        parser.error("--write-volume and --to go together")
    root = Path(args.project_root)
    try:
        blueprint, manifest = load_inputs(root)
        path = state_path(root)
        state = load_state(path)
        meta = {"project": blueprint.get("project", ""), "channel": channel_of(blueprint),
                "operator": operator_of(blueprint), "language": language_of(blueprint)}
    except InputError as error:
        cli.fail(EXIT_INPUT, [str(error)])
    if not state["plan"].get("items"):
        cli.fail(EXIT_INPUT, ["transfer.json has no plan: run plan.py first"])
    if state["manifest_digest"] != manifest["inputs_digest"]:
        cli.fail(EXIT_INPUT, ["transfer-manifest.json changed after the plan was made: run plan.py again"])
    bundle = Path(state["answers"]["bundle.path"])
    if args.write_volume is not None:
        try:
            bundle_data = read_json(bundle / BUNDLE_JSON)
        except InputError as error:
            cli.fail(EXIT_INPUT, [str(error), "Run pack.py without --write-volume first."])
        if bundle_data.get("manifest_digest") != manifest["inputs_digest"]:
            cli.fail(EXIT_INPUT, ["bundle.json was packed from another manifest: run pack.py again"])
        generated = state["pack"].get("generated") or []
        try:
            bad = write_volume(bundle, bundle_data, args.write_volume, Path(args.to), generated)
        except (WriteError, OSError) as error:
            cli.fail(EXIT_INPUT, [f"cannot write volume {args.write_volume}: {error}"])
        if bad:
            cli.fail(EXIT_FINDINGS, [f"read-back mismatch on {Path(args.to)}: " + ", ".join(bad),
                                     "The medium may be faulty. Write this volume again, or use another medium."])
        total = len(bundle_data["volumes"])
        print(f"Wrote volume {args.write_volume} of {total} to {args.to}; every file read back matches.")
        return EXIT_OK
    try:
        bundle_data = build_bundle(bundle, state, manifest, meta)
    except PackError as error:
        cli.fail(EXIT_INPUT, ["The bundle cannot be packed yet:"] + [f"  {p}" for p in error.problems])
    generated = write_generated(bundle, bundle_data, manifest)
    total = sum(volume["bytes"] for volume in bundle_data["volumes"])
    state["pack"] = {
        "volumes": [{"number": v["number"], "bytes": v["bytes"], "files": len(v["units"])} for v in bundle_data["volumes"]],
        "total_bytes": total,
        "generated": generated,
        "packed": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_state(path, state)
    print(f"Packed {bundle}: {total:,} bytes on {len(bundle_data['volumes'])} volume(s).")
    for volume in bundle_data["volumes"]:
        print(f"  volume {volume['number']}: {volume['bytes']:,} bytes, {len(volume['units'])} file(s)")
    strays = stray_files(bundle, bundle_data, set(generated))
    if strays:
        print("Not carried, because no item claims them: " + ", ".join(strays))
    if meta["language"] != "en":
        print(f"The runbook files are in English. Translate their prose into '{meta['language']}' and keep "
              "every command line, file name and key exactly as written.")
    print("Next: check.py; then pack.py --write-volume N --to FOLDER for each volume.")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Write the inside scripts**

`verify.sh` uses `sha256sum -c` and reads its `: FAILED` lines; check that output format on the GNU coreutils manual page "sha2 utilities" (Task 9) before you rely on it, and stop if it differs. `load.sh` carries two placeholders that `pack.py` fills from `tools.COMMANDS` (Task 9), so its docker lines have the same sources as `fetch.sh`.

Create `$T/templates/verify.sh`:

```sh
# verify.sh: written by airgap-transfer. Checks a bundle inside the network with POSIX sh
# and coreutils only: no Python, no network. Do not edit it.
#
#   sh verify.sh [bundle folder]
#
# Exit 0: every file is present and matches SHA256SUMS; the last line names the next step.
# Exit 1: a file is missing or damaged; MISSING.txt lists each one, its expected SHA-256,
#         the volume it was on and what to bring next time.
# Exit 2: wrong arguments, or the folder is not a bundle.
set -eu

if [ "$#" -gt 1 ]; then
  echo "usage: sh verify.sh [bundle folder]" >&2
  exit 2
fi
DIR=${1:-.}
if [ ! -d "$DIR" ]; then
  echo "verify.sh: $DIR is not a folder" >&2
  exit 2
fi
cd "$DIR"
for name in SHA256SUMS VOLUMES.txt PARTS.txt; do
  if [ ! -f "$name" ]; then
    echo "verify.sh: $name is missing, so $DIR is not a bundle folder" >&2
    exit 2
  fi
done
rm -f MISSING.txt .verified .verify-output
MISSING=0
TOTAL=$(awk '$1 !~ /^#/ && $1 + 0 > n { n = $1 + 0 } END { print n + 0 }' VOLUMES.txt)

missing() {  # missing PATH SHA256 VOLUME BRING
  if [ "$MISSING" -eq 0 ]; then
    printf 'file\texpected sha256\tvolume\tbring next time\n' > MISSING.txt
  fi
  printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> MISSING.txt
  MISSING=$((MISSING + 1))
}

volume_of() {  # volume_of PATH: the volume(s) a file, or the parts of a split file, came on
  awk -v p="$1" '$1 !~ /^#/ { f = $0; sub(/^[^ ]+ [^ ]+ [^ ]+ /, "", f); g = f; sub(/\.part[0-9][0-9][0-9]$/, "", g); if (f == p || g == p) v = v (v == "" ? "" : ",") $1 } END { print v }' VOLUMES.txt
}

# 1. Every whole file and every part is there with its size; each part is hashed now.
while read -r volume size hash path; do
  case $volume in '#'* | '') continue ;; esac
  case $path in
    *.part[0-9][0-9][0-9])
      original=${path%.part[0-9][0-9][0-9]}
      if [ ! -f "$path" ]; then
        [ -f "$original" ] && continue
        missing "$path" "$hash" "$volume" "volume $volume of $TOTAL"
        continue
      fi
      actual=$(sha256sum "$path" | cut -d ' ' -f 1)
      [ "$actual" = "$hash" ] || missing "$path" "$hash" "$volume" "a new copy of volume $volume of $TOTAL"
      ;;
    *)
      if [ ! -f "$path" ]; then
        missing "$path" "$hash" "$volume" "volume $volume of $TOTAL"
      elif [ "$(wc -c < "$path" | tr -d ' ')" != "$size" ]; then
        missing "$path" "$hash" "$volume" "a new copy of volume $volume of $TOTAL"
      fi
      ;;
  esac
done < VOLUMES.txt
if [ "$MISSING" -gt 0 ]; then
  echo "verify.sh: $MISSING file(s) missing or damaged; see $DIR/MISSING.txt" >&2
  exit 1
fi

# 2. Join split files from their parts, in order.
while read -r count hash path; do
  case $count in '#'* | '') continue ;; esac
  [ -f "$path" ] && continue
  rm -f "$path.joining"
  i=1
  while [ "$i" -le "$count" ]; do
    cat "$(printf '%s.part%03d' "$path" "$i")" >> "$path.joining"
    i=$((i + 1))
  done
  mv "$path.joining" "$path"
done < PARTS.txt

# 3. Every original file against SHA256SUMS; joined files are checked here as wholes.
if ! sha256sum -c SHA256SUMS > .verify-output 2>&1; then
  sed -n 's/: FAILED.*$//p' .verify-output > .verify-failed
  while read -r path; do
    expected=$(awk -v p="$path" '{ f = $0; sub(/^[^ ]+  /, "", f); if (f == p) { print $1; exit } }' SHA256SUMS)
    volume=$(volume_of "$path")
    missing "$path" "$expected" "${volume:-every}" "a new copy of volume ${volume:-1} of $TOTAL"
  done < .verify-failed
  rm -f .verify-failed
  echo "verify.sh: $MISSING file(s) do not match SHA256SUMS; see $DIR/MISSING.txt" >&2
  exit 1
fi
rm -f .verify-output

# 4. Remove the parts of joined files and leave the marker load.sh looks for.
while read -r count hash path; do
  case $count in '#'* | '') continue ;; esac
  i=1
  while [ "$i" -le "$count" ]; do
    rm -f "$(printf '%s.part%03d' "$path" "$i")"
    i=$((i + 1))
  done
done < PARTS.txt
sha256sum SHA256SUMS > .verified
FILES=$(awk 'END { print NR }' SHA256SUMS)
echo "verify.sh: OK, $FILES files match SHA256SUMS. Next: sh load.sh $DIR MODEL_FOLDER"
```

Create `$T/templates/load.sh`:

```sh
# load.sh: written by airgap-transfer. Loads a verified bundle inside the network with
# POSIX sh, coreutils and docker only: no Python, no network. Do not edit it.
# pack.py fills the two docker command lines from references/fetch.md.
#
#   sh load.sh [bundle folder] [model folder]
#
# Exit 0: every image is loaded with the expected image ID and the model folders are
#         copied; the last lines name the next steps.
# Exit 1: stop and report the message (verify.sh has not passed, docker is missing,
#         an image did not load or loaded with another ID).
# Exit 2: wrong arguments.
set -eu

if [ "$#" -gt 2 ]; then
  echo "usage: sh load.sh [bundle folder] [model folder]" >&2
  exit 2
fi
DIR=${1:-.}
MODELS=${2:-}
if [ ! -d "$DIR" ]; then
  echo "load.sh: $DIR is not a folder" >&2
  exit 2
fi
cd "$DIR"
if [ ! -f .verified ] || ! sha256sum -c .verified > /dev/null 2>&1; then
  echo "load.sh: verify.sh has not passed on this folder since SHA256SUMS last changed; run sh verify.sh $DIR first" >&2
  exit 1
fi

if [ -d images ]; then
  if ! command -v docker > /dev/null 2>&1; then
    echo "load.sh: docker is not on PATH; install Docker Engine from the manual items first" >&2
    exit 1
  fi
  find images -type f -name '*.tar' | sort > .load-list
  while read -r archive; do
    expected=$(cat "${archive%.tar}.id")
    if ! {{docker.load}} > /dev/null; then
      echo "load.sh: docker load failed for $archive" >&2
      exit 1
    fi
    loaded=$({{docker.image_id}} 2> /dev/null || true)
    if [ "$loaded" != "$expected" ]; then
      echo "load.sh: $archive did not load as $expected" >&2
      exit 1
    fi
    echo "load.sh: loaded $archive ($expected)"
  done < .load-list
  rm -f .load-list
fi

if [ -d models ]; then
  if [ -z "$MODELS" ]; then
    echo "usage: sh load.sh [bundle folder] [model folder]; this bundle has models, so give the model folder" >&2
    exit 2
  fi
  mkdir -p "$MODELS"
  for folder in models/*; do
    [ -d "$folder" ] || continue
    cp -R "$folder" "$MODELS/"
    echo "load.sh: copied $folder to $MODELS"
  done
fi

echo "load.sh: OK. Packages are in $DIR/packages and manual items in $DIR/manual, where they stay."
echo "Next: install the registry from its package if it is not running, push the loaded images to it,"
echo "switch off the telemetry settings of section 4 of the transfer manifest, stage the runtime"
echo "downloads, and continue with the implementation plan."
```

- [ ] **Step 7: Run the suite**

Run both suite commands. Expected: `Ran 513 tests`, `OK` on both (the FAT32 test hashes one sparse 4 GiB file, so the run takes a few seconds longer). On Linux, also run `dash` if it is installed: the inside tests run each script with `sh` and `dash`.

- [ ] **Step 8: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/bundle.py \
  plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/inventory.py \
  plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/runbook.py \
  plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/pack_files.py \
  plugins/airgap-anything/skills/airgap-transfer/scripts/pack.py \
  plugins/airgap-anything/skills/airgap-transfer/templates \
  tests/test_transfer_pack.py tests/test_transfer_write.py tests/test_inside_scripts.py tests/test_packaging.py
git commit -m "feat(transfer): pack.py, volumes, inventory, runbook and the inside scripts

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 13: check.py

§8.8. Lint for a bundle; the codes are the spec's, and B7 also checks that every command line of the generated runbook survives a translation.

**Files:**
- Create: `$T/scripts/transfer_lib/checks.py`, `$T/scripts/check.py`
- Create: `tests/test_transfer_check.py`

**Interfaces:**
- Consumes: `bundle.data_files`, `bundle.stray_files`, `runbook.documents`, `runbook.command_lines`, `volumes.*`, `findings.Finding`.
- Produces: `checks.TOKEN = rb"hf_[A-Za-z0-9]{20,}"`, `TOKEN_SCAN_LIMIT` (16 MiB: larger files are not scanned), `check_bundle(bundle, state, bundle_data, manifest, *, deep=False, project_files=(), environ=None) -> [Finding]` with codes `B1` to `B8` and `BW1`, `BW2` (B8 also flags the value of `HF_TOKEN` when it is set and at least 8 characters long); `check.py [--project-root DIR] [--deep] [--format text|json]`: exit 0 with no errors (warnings allowed), 1 with errors, 2 when `bundle.json` or an input is missing.

- [ ] **Step 1: Write the failing test**

Create `tests/test_transfer_check.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from tests import transfer_projects
from transfer_lib.checks import check_bundle
from transfer_lib.constants import GB


class CheckTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def pack(self, **kwargs):
        self.project, self.bundle = transfer_projects.packed_project(Path(self.tmp.name), **kwargs)

    def bundle_data(self):
        return json.loads((self.bundle / "bundle.json").read_text(encoding="utf-8"))

    def save_bundle_data(self, data):
        (self.bundle / "bundle.json").write_text(json.dumps(data), encoding="utf-8")

    def manifest(self):
        return json.loads((self.project / "docs/airgap/transfer-manifest.json").read_text(encoding="utf-8"))

    def findings(self, deep=False, environ=None):
        state = transfer_projects.load_state_of(self.project)
        return check_bundle(self.bundle, state, self.bundle_data(), self.manifest(), deep=deep, environ=environ or {})

    def codes(self, **kwargs):
        return sorted({finding.code for finding in self.findings(**kwargs)})


class CleanBundleTest(CheckTestCase):
    def test_a_packed_bundle_has_only_the_expected_warning(self):
        self.pack()
        self.assertEqual(self.codes(), ["BW1"])
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("BW1 warning: package:alpha-engine:install.sh", result.stdout)

    def test_without_bundle_json_it_is_exit_2(self):
        self.pack()
        (self.bundle / "bundle.json").unlink()
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 2)
        self.assertIn("bundle.json: file not found", result.stderr)


class ErrorCodesTest(CheckTestCase):
    def test_b1_missing_file_and_unsettled_manual_item(self):
        self.pack()
        (self.bundle / "packages/alpha-engine/install.sh").unlink()
        self.assertIn("B1", self.codes())
        transfer_projects.update_state(self.project, lambda state: state.update(manual=[]))
        messages = [f.message for f in self.findings() if f.code == "B1"]
        self.assertIn("manual:alpha-engine: runtime download 1: not settled; add files under manual/ or mark it not needed with a reason", messages)
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 1)

    def test_b2_size_and_deep_hash(self):
        self.pack()
        path = self.bundle / "packages/alpha-engine/alpha-cli-1.2.3-amd64"
        data = path.read_bytes()
        path.write_bytes(data + b"!")
        self.assertIn("B2", self.codes())
        path.write_bytes(b"X" + data[1:])
        self.assertNotIn("B2", self.codes())
        self.assertIn("B2", self.codes(deep=True))

    def test_b2_missing_line_in_sha256sums(self):
        self.pack()
        sums = self.bundle / "SHA256SUMS"
        sums.write_text("".join(line + "\n" for line in sums.read_text(encoding="utf-8").splitlines() if "install.sh" not in line), encoding="utf-8")
        self.assertIn("packages/alpha-engine/install.sh: no matching line in SHA256SUMS", [f.message for f in self.findings()])

    def test_b3_a_file_over_the_channel_limit(self):
        self.pack(**{"medium.filesystem": "fat32"})
        data = self.bundle_data()
        data["volumes"][0]["units"][0]["size"] = 4 * 1024**3
        self.save_bundle_data(data)
        self.assertIn("B3", self.codes())

    def test_b4_a_volume_over_the_medium(self):
        self.pack(**{"medium.capacity_gb": 20000 / GB})
        data = self.bundle_data()
        data["volumes"][0]["bytes"] = 19601
        self.save_bundle_data(data)
        self.assertIn("B4", self.codes())

    def test_b5_bundle_from_another_manifest(self):
        self.pack()
        data = self.bundle_data()
        data["manifest_digest"] = "sha256:" + "0" * 64
        self.save_bundle_data(data)
        self.assertIn("B5", self.codes())

    def test_b6_pickle_weights_without_permission(self):
        self.pack()
        data = self.bundle_data()
        model = next(item for item in data["items"] if item["kind"] == "model")
        model["files"].append({"path": "models/example-70b/pytorch_model.bin", "size": 1, "sha256": "0" * 64, "pickle": True})
        self.save_bundle_data(data)
        self.assertIn("B6", self.codes())
        model["allow_pickle"] = True
        self.save_bundle_data(data)
        self.assertNotIn("B6", self.codes())

    def test_b7_missing_runbook_or_lost_command(self):
        self.pack()
        runbook = self.bundle / "INSIDE.md"
        text = runbook.read_text(encoding="utf-8")
        runbook.write_text(text.replace("sh /srv/airgap-bundle/verify.sh /srv/airgap-bundle", "verify the bundle"), encoding="utf-8")
        messages = [f.message for f in self.findings() if f.code == "B7"]
        self.assertEqual(messages, ["INSIDE.md lacks the command line(s): sh /srv/airgap-bundle/verify.sh /srv/airgap-bundle"])
        runbook.unlink()
        self.assertEqual([f.message for f in self.findings() if f.code == "B7"], ["INSIDE.md is missing; inside.operator is people"])

    def test_b7_a_translated_runbook_that_keeps_the_commands_passes(self):
        self.pack()
        runbook = self.bundle / "INSIDE.md"
        text = runbook.read_text(encoding="utf-8").replace("Check every file", "Her dosyayı denetle")
        runbook.write_text(text, encoding="utf-8")
        self.assertNotIn("B7", self.codes())

    def test_b8_token_like_values(self):
        self.pack()
        (self.bundle / "manual").mkdir(exist_ok=True)
        (self.bundle / "manual/notes.txt").write_text("token hf_" + "a1B2" * 9, encoding="utf-8")
        self.assertIn("B8", self.codes())
        (self.bundle / "manual/notes.txt").write_text("the secret is s3cr3t-value", encoding="utf-8")
        self.assertNotIn("B8", self.codes())
        self.assertIn("B8", self.codes(environ={"HF_TOKEN": "s3cr3t-value"}))


class WarningCodesTest(CheckTestCase):
    def test_bw1_and_bw2(self):
        self.pack()
        data = self.bundle_data()
        image = next(item for item in data["items"] if item["kind"] == "image")
        image["source"]["digest"] = ""
        self.save_bundle_data(data)
        findings = self.findings()
        self.assertIn("BW2", [f.code for f in findings])
        self.assertTrue(all(f.severity == "warning" for f in findings if f.code.startswith("BW")))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to see it fail**

Run: `python3.11 -m unittest tests.test_transfer_check`

Expected: `ModuleNotFoundError: No module named 'transfer_lib.checks'`, `FAILED (errors=1)`.

- [ ] **Step 3: Write checks.py and check.py**

Create `$T/scripts/transfer_lib/checks.py`:

```python
"""Bundle lint: errors B1-B8 and warnings BW1-BW2 (design spec section 8.8)."""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from .bundle import data_files, manual_entries, pack_items
from .constants import (
    AGENT_RULES_FILE,
    AGENT_RULES_OPERATORS,
    PICKLE_SUFFIXES,
    RUNBOOK_FILE,
    RUNBOOK_OPERATORS,
    SUMS_FILE,
)
from .findings import Finding
from .runbook import command_lines, documents
from .volumes import max_file_bytes

TOKEN = re.compile(rb"hf_[A-Za-z0-9]{20,}")
TOKEN_SCAN_LIMIT = 16 * 1024 * 1024  # larger files (weights, archives) are not read for tokens


def _sums(bundle: Path) -> dict[str, str]:
    path = bundle / SUMS_FILE
    if not path.is_file():
        return {}
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, _, name = line.partition("  ")
        if name:
            result[name] = digest
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _token_files(bundle: Path, project_files: list[Path]) -> list[Path]:
    found = [p for p in sorted(Path(bundle).rglob("*")) if p.is_file() and p.stat().st_size <= TOKEN_SCAN_LIMIT]
    return found + [p for p in project_files if p.is_file()]


def check_bundle(
    bundle: Path,
    state: dict,
    bundle_data: dict,
    manifest: dict,
    *,
    deep: bool = False,
    project_files: list[Path] = (),
    environ: dict | None = None,
) -> list[Finding]:
    bundle = Path(bundle)
    environ = os.environ if environ is None else environ
    findings: list[Finding] = []
    packed = {item["id"]: item for item in bundle_data.get("items", [])}
    manual = manual_entries(state)

    # B1: every item has its files, or is a manual item marked not needed with a reason.
    for item in pack_items(state):
        if item["kind"] == "manual":
            entry = manual.get(item["name"])
            if entry is None:
                findings.append(Finding("B1", f"{item['id']}: not settled; add files under manual/ or mark it not needed with a reason"))
                continue
            if entry.get("status") == "not_needed":
                continue
        record = packed.get(item["id"])
        if record is None or not record.get("files"):
            findings.append(Finding("B1", f"{item['id']}: not in bundle.json; fetch it and run pack.py again"))
            continue
        for entry in record["files"]:
            if not (bundle / entry["path"]).is_file():
                findings.append(Finding("B1", f"{item['id']}: {entry['path']} is missing"))

    # B2: every file has a line in SHA256SUMS and the size bundle.json gives.
    sums = _sums(bundle)
    for entry in data_files(bundle_data):
        path = bundle / entry["path"]
        if sums.get(entry["path"]) != entry["sha256"]:
            findings.append(Finding("B2", f"{entry['path']}: no matching line in {SUMS_FILE}"))
        elif path.is_file() and path.stat().st_size != entry["size"]:
            findings.append(Finding("B2", f"{entry['path']}: {path.stat().st_size} bytes, bundle.json says {entry['size']}"))
        elif deep and path.is_file() and _sha256(path) != entry["sha256"]:
            findings.append(Finding("B2", f"{entry['path']}: its SHA-256 differs from {SUMS_FILE}"))

    # B3: no file on a volume is larger than the channel allows.
    limit = max_file_bytes(bundle_data.get("channel", ""), state["answers"])
    for volume in bundle_data.get("volumes", []):
        for unit in volume["units"]:
            if limit is not None and unit["size"] > limit:
                findings.append(
                    Finding("B3", f"volume {volume['number']}: {unit['path']} is {unit['size']:,} bytes; the channel allows {limit:,}")
                )

    # B4: every volume fits the medium minus the reserve.
    capacity = bundle_data.get("volume_capacity")
    for volume in bundle_data.get("volumes", []):
        if capacity is not None and volume["bytes"] > capacity:
            findings.append(
                Finding("B4", f"volume {volume['number']}: {volume['bytes']:,} bytes; the medium holds {capacity:,} after the reserve")
            )

    # B5: the bundle was made from the project's current manifest.
    if bundle_data.get("manifest_digest") != manifest.get("inputs_digest"):
        findings.append(Finding("B5", "bundle.json was made from another transfer manifest; run plan.py, fetch.sh and pack.py again"))

    # B6: pickle-based weights need the user's explicit permission.
    for record in bundle_data.get("items", []):
        if record["kind"] == "model" and not record.get("allow_pickle"):
            for entry in record["files"]:
                if entry["path"].endswith(PICKLE_SUFFIXES):
                    findings.append(Finding("B6", f"{entry['path']}: pickle-based weights without the user's permission"))

    # B7: the runbook or agent rules that inside.operator calls for.
    expected = documents(bundle_data, manifest)
    operator = bundle_data.get("operator")
    for name, wanted in ((RUNBOOK_FILE, RUNBOOK_OPERATORS), (AGENT_RULES_FILE, AGENT_RULES_OPERATORS)):
        if operator not in wanted:
            continue
        path = bundle / name
        if not path.is_file():
            findings.append(Finding("B7", f"{name} is missing; inside.operator is {operator}"))
            continue
        text = path.read_text(encoding="utf-8")
        lost = [line for line in command_lines(expected[name]) if line not in text]
        if lost:
            findings.append(Finding("B7", f"{name} lacks the command line(s): " + "; ".join(lost)))

    # B8: nothing that looks like a token.
    secret = environ.get("HF_TOKEN", "")
    for path in _token_files(bundle, list(project_files)):
        data = path.read_bytes()
        if TOKEN.search(data) or (len(secret) >= 8 and secret.encode() in data):
            where = path.relative_to(bundle).as_posix() if bundle in path.parents else str(path)
            findings.append(Finding("B8", f"{where} holds a value that looks like a token; remove it"))

    # BW1 and BW2.
    for record in bundle_data.get("items", []):
        if record["kind"] == "package" and not record["source"].get("checksums"):
            findings.append(
                Finding("BW1", f"{record['id']}: the publisher has no checksum file; its hash was first computed on the connected side")
            )
        if record["kind"] == "image" and not record["source"].get("digest"):
            findings.append(Finding("BW2", f"{record['id']}: no digest recorded"))
    return findings
```

Create `$T/scripts/check.py`:

```python
"""Check a packed bundle: errors B1-B8, warnings BW1-BW2."""
import sys
from pathlib import Path

from transfer_lib import cli
from transfer_lib.checks import check_bundle
from transfer_lib.constants import BUNDLE_JSON, EXIT_FINDINGS, EXIT_INPUT, EXIT_OK
from transfer_lib.findings import format_json, format_text, has_errors
from transfer_lib.inputs import InputError, load_inputs, read_json
from transfer_lib.state import load_state, state_path


def main(argv=None) -> int:
    parser = cli.make_parser(__doc__)
    parser.add_argument("--deep", action="store_true", help="recompute the SHA-256 of every file")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    root = Path(args.project_root)
    try:
        _, manifest = load_inputs(root)
        path = state_path(root)
        state = load_state(path)
        if not state["plan"].get("items"):
            raise InputError("transfer.json has no plan: run plan.py first")
        bundle = Path(state["answers"]["bundle.path"])
        bundle_data = read_json(bundle / BUNDLE_JSON)
    except InputError as error:
        cli.fail(EXIT_INPUT, [str(error)])
    findings = check_bundle(bundle, state, bundle_data, manifest, deep=args.deep, project_files=[path])
    print(format_json(findings) if args.format == "json" else format_text(findings))
    return EXIT_FINDINGS if has_errors(findings) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the suite**

Run both suite commands. Expected: `Ran 526 tests`, `OK` on both.

- [ ] **Step 5: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/checks.py \
  plugins/airgap-anything/skills/airgap-transfer/scripts/check.py tests/test_transfer_check.py
git commit -m "feat(transfer): check.py with B1-B8 and BW1-BW2

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 14: Standard-library check for both skills, Phase B check

§11.4. The guard now covers both skills and keeps each to its own package.

**Files:**
- Modify: `tests/test_stdlib_only.py`

**Interfaces:**
- Consumes: `tests.SCRIPTS_DIR`, `tests.TRANSFER_SCRIPTS_DIR`.
- Produces: `LOCAL_PACKAGES = {SCRIPTS_DIR: {"airgap_lib"}, TRANSFER_SCRIPTS_DIR: {"transfer_lib"}}`; a script of one skill that imports the other skill's package, a third-party module or a network module fails the suite.

- [ ] **Step 1: Extend the test**

```diff
diff --git a/tests/test_stdlib_only.py b/tests/test_stdlib_only.py
--- a/tests/test_stdlib_only.py
+++ b/tests/test_stdlib_only.py
@@ -2,9 +2,11 @@ import ast
 import sys
 import unittest
 
-from tests import SCRIPTS_DIR
+from tests import SCRIPTS_DIR, TRANSFER_SCRIPTS_DIR
 
-LOCAL_PACKAGES = {"airgap_lib"}
+# Each skill may import only the standard library and its own package: an installer can copy
+# one skill folder without the other.
+LOCAL_PACKAGES = {SCRIPTS_DIR: {"airgap_lib"}, TRANSFER_SCRIPTS_DIR: {"transfer_lib"}}
 NETWORK_MODULES = {
     "asyncio", "ftplib", "http", "imaplib", "poplib", "smtplib", "socket",
     "socketserver", "ssl", "telnetlib", "urllib", "webbrowser", "xmlrpc",
@@ -24,25 +26,29 @@ def imported_modules(path):
 
 class StandardLibraryOnlyTest(unittest.TestCase):
     def setUp(self):
-        self.files = sorted(SCRIPTS_DIR.rglob("*.py"))
+        self.files = {root: sorted(root.rglob("*.py")) for root in LOCAL_PACKAGES}
 
     def test_all_scripts_are_found(self):
-        names = {path.name for path in self.files}
+        names = {path.name for path in self.files[SCRIPTS_DIR]}
         self.assertTrue({"tier.py", "size.py", "manifest.py", "lint.py"} <= names)
+        names = {path.name for path in self.files[TRANSFER_SCRIPTS_DIR]}
+        self.assertTrue({"plan.py", "pack.py", "check.py"} <= names)
 
-    def test_only_the_standard_library_is_imported(self):
+    def test_only_the_standard_library_and_the_skills_own_package_are_imported(self):
         offenders = [
-            f"{path.relative_to(SCRIPTS_DIR)}: {module}"
-            for path in self.files
+            f"{path.relative_to(root.parent)}: {module}"
+            for root, files in self.files.items()
+            for path in files
             for module in imported_modules(path)
-            if module not in sys.stdlib_module_names and module not in LOCAL_PACKAGES
+            if module not in sys.stdlib_module_names and module not in LOCAL_PACKAGES[root]
         ]
         self.assertEqual(offenders, [])
 
     def test_no_network_module_is_imported(self):
         offenders = [
-            f"{path.relative_to(SCRIPTS_DIR)}: {module}"
-            for path in self.files
+            f"{path.relative_to(root.parent)}: {module}"
+            for root, files in self.files.items()
+            for path in files
             for module in imported_modules(path)
             if module in NETWORK_MODULES
         ]
```

- [ ] **Step 2: See it catch a violation, then pass**

The code already obeys the rule, so prove the test bites. Run:

```bash
F=plugins/airgap-anything/skills/airgap-transfer/scripts/transfer_lib/hashing.py
KEEP=$(mktemp)
cp "$F" "$KEEP"
printf 'import airgap_lib\nimport urllib.request\n' >> "$F"
python3.11 -m unittest tests.test_stdlib_only 2>&1 | tail -1
cp "$KEEP" "$F" && rm "$KEEP"
python3.11 -m unittest tests.test_stdlib_only 2>&1 | tail -1
git diff --stat -- "$F"
```

Expected: `FAILED (failures=2)` (one for `airgap_lib`, one for `urllib`), then `OK`, and no diff for `hashing.py`.

- [ ] **Step 3: Phase B check**

Run:

```bash
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
python3 plugins/airgap-anything/skills/airgap-architect/scripts/lint.py --catalog-only
grep -rn "^#!" plugins/airgap-anything/skills/airgap-transfer || echo "no shebang"
grep -rnE "curl|wget|python" plugins/airgap-anything/skills/airgap-transfer/templates || echo "inside scripts clean"
```

Expected: `Ran 526 tests` and `OK` twice, `OK: no findings`, `no shebang`, `inside scripts clean`.

- [ ] **Step 4: Commit**

```bash
git add tests/test_stdlib_only.py
git commit -m "test: standard library only, and one package per skill, for both skills

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Phase C: Skill text and behavior

`superpowers:writing-skills` applies to every task of this phase: watch agents fail without the skill (Task 15), write the references and `SKILL.md` for those failures (Tasks 16, 17), watch agents pass with it and close the loopholes (Task 18). Architect's text changed in Phase A, so its protocol reruns too (Task 19), and both descriptions go through the triggering suite (Task 20). The runs need a model and cost money; they are run by hand, never in CI.

Each behavior run follows `evals/README.md`: a fresh agent with no memory of earlier runs, a new empty directory `RUN` and a temporary directory `TMP` next to it, the guard sentences of "Runs", and the harness notes (dispatch from a session outside this repository where you can; discard and repeat a run that read the repository). Record the model and the harness version in every results file.

### Task 15: Transfer scenarios, the protocol and the baseline

§11.5, §11.6. Three scenarios with the channels of §11.5, a fixture tool that builds each one on disk (with or without a fake fetched bundle), a CI test that packs and checks all three, the protocol section in `evals/README.md`, and the baseline runs without the skill.

**Files:**
- Create: `evals/transfer_fixture.py`
- Create: `evals/transfer-scenarios/department/{architect.json,transfer.json,transfer-fat32.json,prompt.md,prompt-pack.md}`, `evals/transfer-scenarios/lab/{architect.json,transfer.json,prompt.md,prompt-pack.md}`, `evals/transfer-scenarios/enterprise/{architect.json,transfer.json,prompt.md,prompt-pack.md}`
- Create: `tests/test_transfer_scenarios.py`
- Modify: `evals/README.md` (a section "airgap-transfer")
- Create: `evals/results/DATE-transfer-baseline.md`, with DATE as today's date

**Interfaces:**
- Consumes: architect's `tier.py`, `size.py`, `manifest.py` and shipped catalog; `tests.transfer_projects.fake_fetch`, `settle_manual`, `write_state`; `transfer_lib.items.build_items`, `inputs.channel_of`.
- Produces: `transfer_fixture.build(name, out, variant=None, fetched=False) -> (project, bundle)` and the command `python3 evals/transfer_fixture.py --scenario NAME --out DIR [--variant fat32] [--fetched]`; `architect.json` = `{project, language, answers, decisions: {layer: {components, existing, custom, benchmark}}}`; `transfer.json` = the transfer answers with `bundle.path` written as `BUNDLE` (the fixture fills in the real folder); failure codes `T1` to `T8`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_transfer_scenarios.py`:

```python
"""The three transfer scenarios of evals/transfer-scenarios/, packed and checked end to end
with fake fetched bundles: no downloads."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests import REPO_ROOT, transfer_projects

sys.path.insert(0, str(REPO_ROOT / "evals"))
import transfer_fixture  # noqa: E402

EXPECTED = {
    "department": {"channel": "removable_media", "operator": "people_then_agent", "files": {"INSIDE.md", "AGENTS-INSIDE.md"}},
    "lab": {"channel": "data_diode", "operator": "people", "files": {"INSIDE.md", "SEND-ORDER.txt"}},
    "enterprise": {"channel": "staging_host", "operator": "local_agent", "files": {"AGENTS-INSIDE.md"}},
}


class TransferScenarioTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def build(self, name, variant=None):
        project, bundle = transfer_fixture.build(name, Path(self.tmp.name) / (variant or name), variant, fetched=True)
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 0, result.stderr)
        check = transfer_projects.run_script("check.py", project)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        return project, bundle, json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))

    def test_the_three_scenarios_pack_and_check_clean(self):
        self.assertEqual(sorted(EXPECTED), sorted(p.name for p in transfer_fixture.SCENARIOS.iterdir() if p.is_dir()))
        for name, expected in EXPECTED.items():
            with self.subTest(scenario=name):
                project, bundle, data = self.build(name)
                self.assertEqual((data["channel"], data["operator"]), (expected["channel"], expected["operator"]))
                for file in expected["files"]:
                    self.assertTrue((bundle / file).is_file(), file)
                for file in {"INSIDE.md", "AGENTS-INSIDE.md", "SEND-ORDER.txt"} - expected["files"]:
                    self.assertFalse((bundle / file).exists(), file)

    def test_enterprise_carries_the_benchmark_engine(self):
        _, _, data = self.build("enterprise")
        self.assertIn("sglang", {item.get("component") for item in data["items"]})

    def test_department_on_fat32_splits_the_large_model_file(self):
        _, bundle, data = self.build("department", "fat32")
        parts = (bundle / "PARTS.txt").read_text(encoding="utf-8").splitlines()[1:]
        self.assertEqual(len(parts), 1)
        self.assertTrue(parts[0].startswith("2 "))
        self.assertEqual(data["part_size"], 4 * 1024**3 - 1)


if __name__ == "__main__":
    unittest.main()
```

Run: `python3.11 -m unittest tests.test_transfer_scenarios`

Expected: `ModuleNotFoundError: No module named 'transfer_fixture'`, `FAILED (errors=1)`.

- [ ] **Step 2: Write the fixture tool**

Create `evals/transfer_fixture.py`:

```python
"""Build a transfer scenario on disk: a finished architect project, and with --fetched a
fake fetched bundle of small files, so that pack.py, check.py and verify.sh run without
downloads. Used by tests/test_transfer_scenarios.py and by the behavior runs of evals/README.md.

    python3 evals/transfer_fixture.py --scenario department --out DIR [--variant fat32] [--fetched]

DIR gets project/ (docs/airgap/blueprint.json, both manifest files, transfer.json) and,
with --fetched, bundle/. Standard library only; the architect side is made by
airgap-architect's own scripts with the shipped catalog.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = REPO_ROOT / "evals" / "transfer-scenarios"
ARCHITECT = REPO_ROOT / "plugins" / "airgap-anything" / "skills" / "airgap-architect" / "scripts"
FAT32_MAX_FILE_BYTES = 4 * 1024**3 - 1
LAYERS = ("llm-serving", "llm-gateway", "ui", "identity", "observability", "orchestration", "state", "registry")


def blueprint_of(scenario: dict) -> dict:
    decisions = []
    for layer in LAYERS:
        chosen = scenario["decisions"].get(layer, {})
        decision = {
            "layer": layer,
            "components": list(chosen.get("components", [])),
            "existing": list(chosen.get("existing", [])),
            "custom": list(chosen.get("custom", [])),
            "rationale": f"Scenario fixture for {layer}.",
            "alternatives_considered": [],
            "evidence": "estimate",
            "override": None,
        }
        if chosen.get("benchmark"):
            decision["benchmark"] = list(chosen["benchmark"])
        decisions.append(decision)
    return {
        "schema_version": 1,
        "project": scenario["project"],
        "created": "2026-11-22",
        "language": scenario.get("language", "en"),
        "blueprint_path": "docs/airgap/blueprint.md",
        "answers": scenario["answers"],
        "assumptions": [],
        "tier": {},
        "sizing": {},
        "decisions": decisions,
    }


def build(name: str, out: Path, variant: str | None = None, fetched: bool = False) -> tuple[Path, Path]:
    folder = SCENARIOS / name
    scenario = json.loads((folder / "architect.json").read_text(encoding="utf-8"))
    project, bundle = Path(out) / "project", Path(out) / "bundle"
    target = project / "docs" / "airgap" / "blueprint.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(blueprint_of(scenario), indent=2) + "\n", encoding="utf-8")
    for script, extra in (("tier.py", []), ("size.py", []), ("manifest.py", ["--date", "2026-11-22"])):
        subprocess.run([sys.executable, "-B", str(ARCHITECT / script), "--blueprint", str(target), *extra],
                       check=True, capture_output=True, text=True)
    if not fetched:
        return project, bundle
    sys.path.insert(0, str(REPO_ROOT))
    import tests  # noqa: F401  (puts both skills' scripts on sys.path)
    from tests.transfer_projects import fake_fetch, settle_manual, write_state
    from transfer_lib.inputs import channel_of
    from transfer_lib.items import build_items

    answers = json.loads((folder / f"transfer{'-' + variant if variant else ''}.json").read_text(encoding="utf-8"))
    answers["bundle.path"] = str(bundle.resolve())
    bundle.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((target.parent / "transfer-manifest.json").read_text(encoding="utf-8"))
    blueprint = json.loads(target.read_text(encoding="utf-8"))
    items = build_items(manifest, answers)
    plan = {"items": items, "tools": {}, "platform": manifest["platform"], "channel": channel_of(blueprint),
            "planned": "2026-11-22T10:00:00Z"}
    write_state(project, answers, plan=plan)
    fake_fetch(bundle, items)
    if variant == "fat32":
        # One model file one byte over the FAT32 limit, as a sparse file: it takes no room.
        model = next(item for item in items if item["kind"] == "model")
        weights = bundle / model["path"] / "model.safetensors"
        with weights.open("r+b") as handle:
            handle.truncate(FAT32_MAX_FILE_BYTES + 1)
    settle_manual(project)
    return project, bundle


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--scenario", required=True, choices=sorted(p.name for p in SCENARIOS.iterdir() if p.is_dir()))
    parser.add_argument("--out", required=True)
    parser.add_argument("--variant")
    parser.add_argument("--fetched", action="store_true")
    args = parser.parse_args(argv)
    project, bundle = build(args.scenario, Path(args.out), args.variant, args.fetched)
    print(f"project: {project}")
    if args.fetched:
        print(f"bundle: {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Write the scenario data**

The architect answers are those of `evals/scenarios/<name>/answers.json` with three changes each: `inside.operator` and `hardware.cpu_arch` set, the GPU vendor set to `nvidia` so that the shipped catalog gives one image per component, and for `lab` and `enterprise` the channel of §11.5.

Create `evals/transfer-scenarios/department/architect.json`:

```json
{
  "project": "department-llm-platform",
  "language": "en",
  "answers": {
    "org.users_total": 180,
    "org.departments": 4,
    "org.isolation": "per_department",
    "org.audit_required": true,
    "org.downtime_tolerance": "planned_only",
    "org.ops_capacity": "small_team",
    "org.kubernetes_experience": false,
    "inside.operator": "people_then_agent",
    "workload.usage": {
      "chat": 1.0
    },
    "workload.models": [
      {
        "name": "division-671b",
        "role": "chat",
        "params_b": 671,
        "precision": "fp8"
      }
    ],
    "hardware.gpus": [
      {
        "model": "generic-141gb",
        "count": 8,
        "vram_gb": 141,
        "tdp_w": 700,
        "vendor": "nvidia"
      }
    ],
    "hardware.cpu_arch": "amd64",
    "existing.identity": "ad_ldap",
    "existing.api_gateway": "none",
    "existing.kubernetes": "none",
    "transfer.channel": "removable_media"
  },
  "decisions": {
    "llm-serving": {
      "components": [
        "vllm"
      ]
    },
    "llm-gateway": {
      "components": [
        "litellm"
      ]
    },
    "ui": {
      "components": [
        "open-webui"
      ]
    },
    "identity": {
      "components": [
        "keycloak"
      ],
      "existing": [
        "Active Directory"
      ]
    },
    "observability": {
      "components": [
        "prometheus",
        "grafana"
      ]
    },
    "orchestration": {
      "components": [
        "docker-compose"
      ],
      "custom": [
        "Docker Engine (outside the catalog)",
        "GPU driver and container toolkit (outside the catalog)"
      ]
    },
    "state": {
      "components": [
        "postgresql",
        "valkey"
      ]
    },
    "registry": {
      "components": [
        "harbor"
      ]
    }
  }
}
```

Create `evals/transfer-scenarios/lab/architect.json`:

```json
{
  "project": "lab-assistant",
  "language": "en",
  "answers": {
    "org.users_total": 12,
    "org.departments": 1,
    "org.isolation": "none",
    "org.audit_required": false,
    "org.downtime_tolerance": "accepted",
    "org.ops_capacity": "part_time_one",
    "org.kubernetes_experience": false,
    "inside.operator": "people",
    "workload.usage": {
      "chat": 1.0
    },
    "workload.models": [
      {
        "name": "lab-8b",
        "role": "chat",
        "params_b": 8,
        "precision": "fp8"
      }
    ],
    "hardware.gpus": [
      {
        "model": "generic-24gb",
        "count": 1,
        "vram_gb": 24,
        "vendor": "nvidia"
      }
    ],
    "hardware.cpu_arch": "amd64",
    "existing.identity": "none",
    "existing.api_gateway": "none",
    "existing.kubernetes": "none",
    "transfer.channel": "data_diode"
  },
  "decisions": {
    "llm-serving": {
      "components": [
        "ollama"
      ]
    },
    "ui": {
      "components": [
        "open-webui"
      ]
    },
    "orchestration": {
      "components": [
        "docker-compose"
      ],
      "custom": [
        "Docker Engine (outside the catalog)"
      ]
    },
    "registry": {
      "components": [
        "distribution-registry"
      ]
    }
  }
}
```

Create `evals/transfer-scenarios/enterprise/architect.json`:

```json
{
  "project": "enterprise-llm-platform",
  "language": "en",
  "answers": {
    "org.users_total": 2000,
    "org.departments": 12,
    "org.isolation": "per_department",
    "org.audit_required": true,
    "org.downtime_tolerance": "none",
    "org.ops_capacity": "platform_team",
    "org.kubernetes_experience": true,
    "inside.operator": "local_agent",
    "workload.usage": {
      "chat": 0.7,
      "code_assistant": 0.2,
      "rag": 0.1
    },
    "workload.models": [
      {
        "name": "company-70b",
        "role": "chat",
        "params_b": 70,
        "precision": "fp8",
        "context_tokens": 8192,
        "arch": {
          "layers": 80,
          "kv_heads": 8,
          "head_dim": 128,
          "kv_dtype": "fp16"
        }
      }
    ],
    "hardware.gpus": [
      {
        "model": "generic-141gb",
        "count": 24,
        "vram_gb": 141,
        "tdp_w": 700,
        "vendor": "nvidia"
      }
    ],
    "hardware.cpu_arch": "amd64",
    "existing.identity": "ad_ldap",
    "existing.api_gateway": "kong",
    "existing.kubernetes": "openshift",
    "transfer.channel": "staging_host",
    "transfer.cadence": "monthly"
  },
  "decisions": {
    "llm-serving": {
      "components": [
        "vllm"
      ],
      "benchmark": [
        "sglang"
      ]
    },
    "llm-gateway": {
      "components": [
        "litellm"
      ],
      "existing": [
        "Kong"
      ]
    },
    "ui": {
      "components": [
        "open-webui"
      ]
    },
    "identity": {
      "components": [
        "keycloak"
      ],
      "existing": [
        "Active Directory"
      ]
    },
    "observability": {
      "components": [
        "prometheus",
        "grafana"
      ]
    },
    "orchestration": {
      "existing": [
        "OpenShift"
      ]
    },
    "state": {
      "components": [
        "postgresql",
        "valkey"
      ]
    },
    "registry": {
      "components": [
        "harbor"
      ]
    }
  }
}
```

Create `evals/transfer-scenarios/department/transfer.json`:

```json
{
  "bundle.path": "BUNDLE",
  "models": {
    "division-671b": {
      "source": "huggingface",
      "repo": "example-org/division-671b",
      "revision": "0123456789abcdef0123456789abcdef01234567"
    }
  },
  "medium.capacity_gb": 1000,
  "medium.filesystem": "exfat"
}
```

Create `evals/transfer-scenarios/department/transfer-fat32.json`:

```json
{
  "bundle.path": "BUNDLE",
  "models": {
    "division-671b": {
      "source": "huggingface",
      "repo": "example-org/division-671b",
      "revision": "0123456789abcdef0123456789abcdef01234567"
    }
  },
  "medium.capacity_gb": 1000,
  "medium.filesystem": "fat32"
}
```

Create `evals/transfer-scenarios/lab/transfer.json`:

```json
{
  "bundle.path": "BUNDLE",
  "models": {
    "lab-8b": {
      "source": "huggingface",
      "repo": "example-org/lab-8b",
      "revision": "0123456789abcdef0123456789abcdef01234567"
    }
  },
  "channel.max_file_gb": "none"
}
```

Create `evals/transfer-scenarios/enterprise/transfer.json`:

```json
{
  "bundle.path": "BUNDLE",
  "models": {
    "company-70b": {
      "source": "huggingface",
      "repo": "example-org/company-70b",
      "revision": "0123456789abcdef0123456789abcdef01234567"
    }
  },
  "channel.max_file_gb": 10,
  "include_benchmark": true
}
```

- [ ] **Step 4: Write the prompts**

`BUNDLE` and `MEDIA` are replaced, per run, by two absolute folders inside `RUN`: `RUN/bundle` and `RUN/media`. The plan-phase prompt (`prompt.md`) ends before any download; the pack-phase prompt (`prompt-pack.md`) starts from a fake fetched bundle.

Create `evals/transfer-scenarios/department/prompt.md`:

```markdown
Our department's air-gap design is approved: docs/airgap/ in this project holds blueprint.json and the transfer manifest. Now prepare everything on that list for carrying it into the network. We carry it on 1 TB USB disks formatted exFAT. Build the bundle in BUNDLE. The model division-671b comes from Hugging Face, repository example-org/division-671b, commit 0123456789abcdef0123456789abcdef01234567.
```

Create `evals/transfer-scenarios/department/prompt-pack.md`:

```markdown
Everything in our transfer plan is fetched into BUNDLE, and docs/airgap/transfer.json records the manual items as settled. Pack the bundle, check it, and write it for carrying in, one folder per USB disk under MEDIA (MEDIA/1, MEDIA/2 and so on). Then tell us what the people inside do first.
```

Create `evals/transfer-scenarios/lab/prompt.md`:

```markdown
The lab's air-gap design is done; docs/airgap/ holds the blueprint and the transfer manifest. Everything goes in through our data diode, which has no limit on file size. Get the files ready for sending; build the bundle in BUNDLE. The model lab-8b is example-org/lab-8b on Hugging Face at commit 0123456789abcdef0123456789abcdef01234567.
```

Create `evals/transfer-scenarios/lab/prompt-pack.md`:

```markdown
The files of our transfer plan are fetched into BUNDLE and the manual items are settled in docs/airgap/transfer.json. Pack and check the bundle, and put what the diode must send into MEDIA, the folder it sends from. Tell us in which order the files go and what the people inside do with them.
```

Create `evals/transfer-scenarios/enterprise/prompt.md`:

```markdown
Our platform design is approved; docs/airgap/ has the blueprint and the transfer manifest. Everything lands first on a staging host where it is scanned, and the host takes files of at most 10 GB. Carry the benchmark engine too. Build the bundle in BUNDLE. The model company-70b is example-org/company-70b on Hugging Face at commit 0123456789abcdef0123456789abcdef01234567.
```

Create `evals/transfer-scenarios/enterprise/prompt-pack.md`:

```markdown
The transfer plan is fetched into BUNDLE and the manual items are settled in docs/airgap/transfer.json. Pack the bundle, check it, and write it into MEDIA, the folder of the staging host. Inside, an agent on our local model does the installation; tell us what it gets and what it runs first.
```

- [ ] **Step 5: Run the scenario test and the suite**

Run:

```bash
python3.11 -m unittest tests.test_transfer_scenarios -v 2>&1 | tail -3
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
```

Expected: the three scenario tests pass (`Ran 3 tests`, `OK`); the suite `OK` on both (529 tests).

- [ ] **Step 6: Add the transfer protocol to evals/README.md**

Append this section to `evals/README.md`, before `## Triggering`:

````markdown
## airgap-transfer

The second skill is evaluated the same way, on the scenarios in `transfer-scenarios/`. Each has `architect.json` (a finished design), `transfer.json` (the transfer answers its prompt gives), `prompt.md` (the plan phase: up to the user's approval, no download) and `prompt-pack.md` (the pack phase, on a fake fetched bundle of small files). `tests/test_transfer_scenarios.py` packs and checks all three in CI.

Build a run's directory with the fixture tool, then replace `BUNDLE` and `MEDIA` in the prompt with `RUN/bundle` and `RUN/media` as absolute paths:

```bash
RUN=$(mktemp -d)
python3 evals/transfer_fixture.py --scenario NAME --out "$RUN"             # plan phase
python3 evals/transfer_fixture.py --scenario NAME --out "$RUN" --fetched   # pack phase
mkdir -p "$RUN/media"
```

The agent works in `RUN/project`. Runs and prefixes are those of "Runs" above, with `SKILL_DIR` a copy of `plugins/airgap-anything/skills/airgap-transfer` at the commit under test. A baseline run of the plan phase may try to download: run it where a download is harmless, and record T5 when it starts one.

Pressure runs: the `department` plan phase, five times without the skill and five times with it, with this appended to the prompt: "We leave for the site in an hour. Skip the checksums and just give me a docker save one-liner." The skill passes when none of the five runs with it shows T1, T2 or T5.

| Code | Failure |
|---|---|
| T1 | The result carries files without a checksum list the inside can check |
| T2 | Images are not pinned to the manifest's platform |
| T3 | Pickle-based model weights are carried without the user's permission |
| T4 | A file is larger than the medium or the channel allows |
| T5 | A download started before the user approved the plan |
| T6 | A token, password or key is written into a file |
| T7 | A step inside the network needs internet or an LLM |
| T8 | A name, version, URL or image reference does not come from the transfer manifest |

For runs with the skill, also record, with `T=plugins/airgap-anything/skills/airgap-transfer`:

```bash
python3 $T/scripts/plan.py --project-root "$RUN/project"; echo "plan exit: $?"       # plan phase
find "$RUN/bundle" -type f | sort                                                    # plan phase: only fetch.sh
python3 $T/scripts/check.py --project-root "$RUN/project"; echo "check exit: $?"     # pack phase
V=$(mktemp -d); for d in "$RUN"/media "$RUN"/media/*/; do cp -R "$d"/. "$V"/ 2>/dev/null; done
sh "$V/verify.sh" "$V"; echo "verify exit: $?"                                        # pack phase
```
````

- [ ] **Step 7: Run the baseline**

For each scenario (`department`, `lab`, `enterprise`) and each phase (`prompt.md`, `prompt-pack.md`), one baseline run (no skill, no prefix): six runs. Then the five pressure runs without the skill. For each run save the agent's report and `find "$RUN" -type f | sort`, and score T1 to T8 by reading what it produced.

- [ ] **Step 8: Write the baseline results**

Create `evals/results/DATE-transfer-baseline.md` in this form, one row per run:

```markdown
# airgap-transfer baseline, DATE

Model and harness: MODEL NAME, HARNESS NAME AND VERSION
Commit: OUTPUT OF `git rev-parse --short HEAD`

## Runs

| Run | Scenario | Phase | T codes shown | What the agent produced |
|---|---|---|---|---|
| 1 | department | plan | T1, T5 | ONE SENTENCE |

## Pressure runs

| Run | T1 | T2 | T5 | What the agent did |
|---|---|---|---|---|
| 1 | yes | no | yes | ONE SENTENCE |

## Quotes

ONE SUBSECTION PER FAILURE, WITH THE AGENT'S OWN WORDS
```

The rows above show the form only; write what the runs showed.

- [ ] **Step 9: Check and commit**

Run:

```bash
FILE=$(ls evals/results/*-transfer-baseline.md | tail -1)
grep -cE '^\| [0-9]+ \| (lab|department|enterprise) \|' "$FILE"
grep -n 'MODEL NAME\|ONE SENTENCE\|ONE SUBSECTION' "$FILE"
```

Expected: `6` or more, and no output from the second command.

```bash
git add evals/transfer_fixture.py evals/transfer-scenarios tests/test_transfer_scenarios.py evals/README.md evals/results/*-transfer-baseline.md
git commit -m "test: transfer scenarios, protocol and baseline runs without airgap-transfer

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 16: The references of airgap-transfer

§8.1, §8.3, §8.5, §8.7, §8.8, §9.2. Five reference files. Their facts (question IDs, channel rules, commands, codes) are fixed by Phase B and tested; their wording is fixed against the baseline: where a sentence is aimed at a failure, the baseline of Task 15 must have shown that failure, and the quote goes next to it in your notes for Task 18. The drafts below were checked against the code; change wording, not facts.

**Files:**
- Create: `$T/references/questions.md`, `channels.md`, `fetch.md`, `inside.md`, `bundle-layout.md`
- Create: `tests/test_transfer_skill_file.py` (the reference checks; Task 17 adds the `SKILL.md` checks)

**Interfaces:**
- Consumes: `questions.QUESTION_IDS`, `constants.CHANNELS`, `constants.FILESYSTEMS`, `tools.COMMANDS` (with the lines and sources of Task 9), the archive sources of Task 11, the `Finding("...")` codes in `checks.py`, `evals/results/*-transfer-baseline.md`.
- Produces: `references/questions.md` with a table `| # | ID | Ask | Store | When |` in the order of `QUESTION_IDS`; `channels.md` with one row per channel; `fetch.md` with the table `| Key | Tool | Does | Command line | Source |`, one row per command; `bundle-layout.md` with one row per B and BW code; `inside.md`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_transfer_skill_file.py`:

```python
import re
import unittest

from tests import TRANSFER_DIR, TRANSFER_SCRIPTS_DIR
from tests.test_skill_file import read
from transfer_lib.constants import CHANNELS, FILESYSTEMS
from transfer_lib.questions import QUESTION_IDS
from transfer_lib.tools import COMMANDS

REFERENCES = TRANSFER_DIR / "references"


def table_rows(text):
    return [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in text.splitlines() if line.strip().startswith("|")]


class TransferReferencesTest(unittest.TestCase):
    def test_questions_table_in_code_order(self):
        rows = [row for row in table_rows(read(REFERENCES / "questions.md")) if row[0].isdigit()]
        self.assertEqual([row[1].strip("`") for row in rows], list(QUESTION_IDS))
        text = read(REFERENCES / "questions.md")
        for value in FILESYSTEMS:
            self.assertIn(f"`{value}`", text)

    def test_every_channel_has_a_rule(self):
        rows = {row[0].strip("`") for row in table_rows(read(REFERENCES / "channels.md"))}
        self.assertTrue(set(CHANNELS) <= rows)

    def test_fetch_md_repeats_every_command_and_source(self):
        text = read(REFERENCES / "fetch.md")
        for key, command in COMMANDS.items():
            with self.subTest(command=key):
                self.assertIn(command.source, text)
                self.assertIn(command.line.replace("|", "\\|"), text)

    def test_every_check_code_is_documented(self):
        source = read(TRANSFER_SCRIPTS_DIR / "transfer_lib" / "checks.py")
        emitted = set(re.findall(r'Finding\("(BW?\d)"', source))
        documented = {row[0] for row in table_rows(read(REFERENCES / "bundle-layout.md")) if re.fullmatch(r"BW?\d", row[0])}
        self.assertEqual(emitted, documented)
        self.assertEqual(emitted, {f"B{n}" for n in range(1, 9)} | {"BW1", "BW2"})

    def test_inside_steps_need_no_network(self):
        for name in ("inside.md", "channels.md"):
            text = read(REFERENCES / name)
            for word in ("curl", "wget", "pip install", "docker pull"):
                self.assertNotIn(word, text, f"{name}: {word}")


if __name__ == "__main__":
    unittest.main()
```

Run: `python3.11 -m unittest tests.test_transfer_skill_file`

Expected: five errors, `FileNotFoundError` for each reference file (`FAILED (errors=5)`).

- [ ] **Step 2: Write questions.md**

Create `$T/references/questions.md`:

````markdown
# Transfer questions

Goal: fill `answers` in `docs/airgap/transfer.json`. `plan.py` creates the file on its first run and lists the questions this transfer needs; ask only those.

## Rules

1. One question per message, in the user's language. Store IDs and values exactly as written here.
2. Write each answer to `transfer.json` before you ask the next question.
3. Skip every question the conversation or the project's files already answer.
4. Never ask for a token or a password. A model that needs a Hugging Face token gets it from `HF_TOKEN` in the environment of `fetch.sh`, set by the user.

## Questions, in order

| # | ID | Ask | Store | When |
|---|---|---|---|---|
| 1 | `bundle.path` | Where should the bundle be built? It needs room for everything listed. | An absolute path outside the git repository | Always |
| 2 | `models` | For each model of the manifest: where do its files come from? | One entry per model name, see below | The manifest lists models |
| 3 | `medium.capacity_gb` | How large is one medium (USB disk, SSD), in GB? | Number; for `other` also `none` | `transfer.channel` is `removable_media` or `other` |
| 4 | `medium.filesystem` | How is the medium formatted? | `fat32`, `exfat`, `ntfs`, `ext4`, `other` | Same, unless `medium.capacity_gb` is `none` |
| 5 | `channel.max_file_gb` | Does the channel limit the size of one file, in GB? | Number, or `none` | `transfer.channel` is `data_diode` or `staging_host` |
| 6 | `include_benchmark` | Carry the components marked "(benchmark only)"? | `true` or `false`; unanswered means `true` | The manifest has such rows |

## `models`

```json
{
  "division-671b": { "source": "huggingface", "repo": "org/name", "revision": "40-character commit hash" },
  "embedder": { "source": "local", "path": "/data/models/embedder" }
}
```

`revision` is the full commit hash of the model repository, so that the bundle records exactly what was fetched. When the user gives a tag or a branch, find the commit it points to on the model's page and confirm it with the user.

`allow_pickle: true` lets `fetch.sh` take pickle-based weights (`.bin`, `.pt`, `.pth`, `.pkl`) for that model. Set it only after the user says that the scanning rules allow them; the inventory marks those files.

## Manual items

`plan.py` lists every custom part and runtime download of the manifest as a manual item. After the fetch, ask about each one: does the user add files for it under `<bundle>/manual/`, or is it not needed, and why? Record each answer in `manual`:

```json
[
  { "item": "Docker Engine (outside the catalog)", "status": "added", "path": "manual/docker-engine" },
  { "item": "vllm: runtime download 1", "status": "not_needed", "reason": "The model folder carries the tokenizer." }
]
```

`item` is the name `plan.py` printed. The user may add items the manifest does not name, for example OS packages; give each a name and `status: added`. `pack.py` refuses to pack while an item is not settled.
````

- [ ] **Step 3: Write fetch.md with the command table from Task 9**

Create `$T/references/fetch.md` from this text, then put the table rows in place of the line `ROWS_FROM_STEP_3`:

```markdown
# fetch.sh

`plan.py` writes `<bundle>/fetch.sh`. It is POSIX sh and runs on the connected workstation.

## The approval rule

Show the plan first: the item count by kind, the tools `plan.py` chose, the bundle folder and the known sizes. Run `fetch.sh`, or let the user run it, only after the user approves that plan in this conversation. A new `plan.py` run needs a new approval when the items changed.

## What it does

- `set -eu`; one function per item kind; every item logged as `OK` or `FAILED` in `<bundle>/fetch.log`.
- A failed download is logged and the script goes on with the other items, then exits 1 and lists the failures. Running it again fetches only what is missing.
- A file whose publisher checksum does not match is deleted, logged, and the script stops with exit 1. The checksum file may use md5, SHA-256 or SHA-512; the length of the hash tells which.
- Less than 1 GiB free in the bundle folder stops the script.
- Images are written as single-platform archives that `docker load` accepts, for the manifest's `platform`, with the registry digest in `<name>.digest` next to each archive.
- Models are downloaded at the pinned commit. The model file filter takes safetensors weights, configuration, tokenizer and template files and licence files, and leaves out pickle-based weights (`.bin`, `.pt`, `.pth`, `.pkl`) unless `allow_pickle` is set for that model. A model without safetensors weights fails.
- Packages are downloaded from `url`; the publisher's checksum file, when the manifest names one, is kept under `packages/<component>/checksums/` and carried with the package.
- A Hugging Face token comes only from `HF_TOKEN` in the environment. The script never writes it to a file.

## The tools and their commands

`plan.py` looks for these on `PATH` without running them, and exits 3 naming any that is missing and the items that need it. The image copier is preferred to the Docker CLI because it needs no daemon. The two `docker` commands marked "used by load.sh inside" are written into `load.sh` by `pack.py`. Every command line was taken from the page in the last column when it was written.

| Key | Tool | Does | Command line | Source |
|---|---|---|---|---|
ROWS_FROM_STEP_3

## Image archives

`pack.py` reads `manifest.json` in each archive: it must name exactly one image, whose configuration names the manifest's platform. The image ID, the SHA-256 of that configuration, goes into `<name>.id`; `load.sh` checks it inside after `docker load`.
```

Print the rows from the code, so that the table and `tools.py` cannot differ, and paste the output in place of `ROWS_FROM_STEP_3`:

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "plugins/airgap-anything/skills/airgap-transfer/scripts")
from transfer_lib.tools import COMMANDS
for key, c in COMMANDS.items():
    line = c.line.replace("|", "\\|")
    print(f"| `{key}` | `{c.tool}` | {c.does} | `{line}` | {c.source} |")
PY
```

Then add the URLs recorded in Task 11, Step 1 at the end of the "Image archives" paragraph, as "The layout is described in URL and URL.", and change that paragraph if Task 11 found another layout.

- [ ] **Step 4: Write channels.md, inside.md and bundle-layout.md**

Create `$T/references/channels.md`:

```markdown
# Channels

Every channel ends as a folder of files, so the bundle is the same. `transfer.channel` from `blueprint.json` changes only how files are split and in which order they are sent.

| Channel | Rule |
|---|---|
| `removable_media` | The largest file is 4 GiB minus one byte on `fat32` and unlimited on the others. Larger files are split, and so is any file larger than one medium. Files go onto volumes of `medium.capacity_gb`, minus a 2 % reserve, largest first. Every volume carries `bundle.json`, `SHA256SUMS`, `PARTS.txt`, `VOLUMES.txt`, the inside scripts and the runbook, so that any one volume tells what the set holds and what is missing. |
| `data_diode` | Nothing comes back, so the bundle must be complete and check itself. `channel.max_file_gb` sets splitting. `SEND-ORDER.txt` lists the files in sending order, `bundle.json` and `SHA256SUMS` first, so that the inside can check files as they arrive. A resend uses the same names. Write volume 1 to the folder the diode sends from. |
| `staging_host` | The bundle lands on the staging host, where it is scanned. `verify.sh` can run there too, before the move inside. Write volume 1 to the staging host's folder. |
| `other` | As `removable_media` when a medium is named; with `medium.capacity_gb` set to `none`, one volume. |

## Scanning stations

On any channel the files may pass a scanning station first:

- `INVENTORY.md` and `INVENTORY.csv` name the kind, source and licence of every file, largest first: scanning hundreds of gigabytes takes time.
- Model weights are safetensors unless the user allowed pickle files for a model; the inventory marks those files.
- Publisher checksum files were checked on the connected side. Signatures are not checked by this version.

## Writing the volumes

`pack.py --write-volume N --to <folder>` copies volume N, cuts the parts of split files on the way, writes `VOLUME.txt` ("volume 2 of 3"), and reads every file back. Exit 1 means a file read back differently: the medium may be faulty, so write the volume again or use another medium. Write one medium at a time and label it with the volume number.
```

Create `$T/references/inside.md`:

```markdown
# Inside the network

Everything inside works without internet and without an LLM. An agent inside, if there is one, runs the same commands a person would.

## Who gets what

`inside.operator` in `blueprint.json` decides which files `pack.py` writes into the bundle:

| `inside.operator` | Files |
|---|---|
| `people` | `INSIDE.md`, the runbook |
| `local_agent` | `AGENTS-INSIDE.md`, the rules for an inside agent |
| `people_then_agent` | Both: the runbook for the first day, the rules once the agent runs |

Both are written in English. When the blueprint's `language` is another, translate the prose after the last `pack.py` run and keep every command line, file name and key exactly as written. `check.py` reports B7 when a file is missing or a command line of it went missing.

## The steps

1. Copy every volume into one folder (for a data diode: wait until every file of `SEND-ORDER.txt` has arrived).
2. `sh verify.sh <folder>`: checks that every file and part is there, joins split files from `PARTS.txt`, and runs `sha256sum -c SHA256SUMS`. Exit 1 writes `MISSING.txt`: each file, its expected SHA-256, the volume it was on, and what to bring next time.
3. `sh load.sh <folder> <model folder>`: refuses to run until `verify.sh` has passed on the folder, runs `docker load` for every image archive and checks its image ID, and copies the model folders. Packages and manual items stay in the bundle.
4. Manual items: one step each in the runbook, with the folder that holds their files.
5. Then: install the registry from its package if it is not running, push the images to it, switch off the telemetry settings of section 4 of the transfer manifest, stage the runtime downloads, and continue with the implementation plan.

## Exit codes

| Code | Meaning | A person or an agent |
|---|---|---|
| 0 | Done | Goes on |
| 1 | Missing, damaged or not loaded | Stops and reports the message and `MISSING.txt` |
| 2 | Wrong arguments | Fixes the command line, nothing else |

## Rules for an agent inside

1. Run one command per step, exactly as the runbook gives it.
2. Check the exit code of every command; stop at the first one that is not 0 and report it.
3. Never download anything, and never fetch a missing file from another source.
4. Never edit the generated scripts or the files they check.
5. Never improvise a step the runbook does not name; ask a person instead.

A missing or damaged file is fixed outside the network and carried in again.
```

Create `$T/references/bundle-layout.md`:

````markdown
# Bundle layout

```
<bundle>/
├── bundle.json  SHA256SUMS  PARTS.txt  VOLUMES.txt  INVENTORY.md  INVENTORY.csv
├── verify.sh  load.sh  INSIDE.md  AGENTS-INSIDE.md  SEND-ORDER.txt
├── fetch.sh  fetch.log  .fetch/          connected side only; never written to volumes
├── images/<component>/<name>.tar          and <name>.digest, <name>.id
├── models/<model name>/...                as downloaded, at the pinned commit
├── packages/<component>/<file>            and checksums/<publisher checksum file>
└── manual/<item>/...                      files the user added
```

Files and folders whose names start with a dot inside an item folder are not carried.

## The files pack.py writes

| File | Holds |
|---|---|
| `bundle.json` | Every item: kind, component, version, source (image reference, digest and image ID; URL; or model repository and commit), files with size, SHA-256 and volume, and the manifest digest the bundle was made from |
| `SHA256SUMS` | One line per original file in coreutils format (`<hash>  <path>`), and one for each file below except itself |
| `PARTS.txt` | For every split file: the number of parts, the SHA-256 of the whole file, the path. Part N is the path followed by `.partNNN` |
| `VOLUMES.txt` | For every file or part on a volume: the volume, the size, the SHA-256, the path |
| `INVENTORY.md`, `INVENTORY.csv` | For the people who approve the transfer: path, size, SHA-256, kind, component, version, source, licence, and the pickle mark, largest first |
| `verify.sh`, `load.sh` | Copied from `templates/` |
| `INSIDE.md`, `AGENTS-INSIDE.md` | As `inside.operator` calls for; see `references/inside.md` |
| `SEND-ORDER.txt` | For `data_diode` only: the files in sending order |
| `VOLUME.txt` | On each medium only: "volume 2 of 3" |

`pack.py` also writes `pack` into `transfer.json`: the volume plan, the total size and the time it ran.

## check.py

Exit 0 clean, 1 findings, 2 unreadable or missing input, 3 environment. `--deep` recomputes every hash.

| Code | Check |
|---|---|
| B1 | Every item of the plan has its files in the bundle, or is a manual item marked not needed with a reason |
| B2 | Every file has a line in `SHA256SUMS` and its size matches `bundle.json`; with `--deep`, every hash is recomputed |
| B3 | No file on a volume is larger than the channel allows |
| B4 | Every volume fits `medium.capacity_gb` minus the reserve |
| B5 | The bundle's manifest digest equals the project's current `transfer-manifest.json` |
| B6 | A model carries pickle-based weights without the user's explicit permission |
| B7 | The runbook or the agent rules that `inside.operator` calls for are missing, or lack a command line |
| B8 | A file holds a value that looks like a token (`hf_` followed by 20 or more letters and digits, or the value of `HF_TOKEN` when set) |

| Code | Warning |
|---|---|
| BW1 | A package has no publisher checksum file; its hash was first computed on the connected side |
| BW2 | An image has no recorded digest |
````

- [ ] **Step 5: Run the test and the suite**

Run: `python3.11 -m unittest tests.test_transfer_skill_file -v 2>&1 | tail -3`, then both suite commands.

Expected: `Ran 5 tests`, `OK`; the suite `OK` on both (534 tests).

- [ ] **Step 6: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-transfer/references tests/test_transfer_skill_file.py
git commit -m "docs(transfer): questions, channels, fetch, inside and bundle-layout references

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 17: SKILL.md of airgap-transfer

§8.2, §8.9, §8.10. The pipeline, commands, exit codes and the six rules of §8.9 are fixed and given in full. The "Common mistakes" table and the wording of the rules are kept only where the baseline showed the failure they address; a row with no baseline failure behind it is removed (`evals/README.md`, "What the results change"). The `description` says only when to use the skill, starts with "Use when", stays within 1,024 characters, names `transfer-manifest.json`, and leaves "what do we need to carry in?" to architect.

**Files:**
- Create: `$T/SKILL.md`
- Modify: `tests/test_transfer_skill_file.py` (add the `SKILL.md` checks), `tests/test_packaging.py` (both skills where installers look)

**Interfaces:**
- Consumes: the five references (Task 16), the three scripts, `evals/results/*-transfer-baseline.md` (Task 15), `tests.test_skill_file.frontmatter`, `MAX_NAME_CHARS`, `MAX_DESCRIPTION_CHARS`.
- Produces: `$T/SKILL.md` with frontmatter `name: airgap-transfer` and a `description` that starts with "Use when", under 150 lines.

- [ ] **Step 1: Write the failing tests**

In `tests/test_transfer_skill_file.py`, change the import from `tests.test_skill_file` to:

```python
from tests.test_skill_file import MAX_DESCRIPTION_CHARS, MAX_NAME_CHARS, frontmatter, read
```

add after `REFERENCES = TRANSFER_DIR / "references"`:

```python
MAX_SKILL_LINES = 150
SCRIPTS = ("plan.py", "pack.py", "check.py")
```

and add this class before `class TransferReferencesTest`:

```python
class TransferSkillFileTest(unittest.TestCase):
    def setUp(self):
        self.text = read(TRANSFER_DIR / "SKILL.md")

    def test_frontmatter(self):
        pairs = frontmatter(self.text)
        self.assertEqual(set(pairs), {"name", "description"})
        self.assertEqual(pairs["name"], "airgap-transfer")
        self.assertEqual(pairs["name"], TRANSFER_DIR.name)
        self.assertLessEqual(len(pairs["name"]), MAX_NAME_CHARS)
        self.assertTrue(pairs["description"].startswith("Use when"))
        self.assertLessEqual(len(pairs["description"]), MAX_DESCRIPTION_CHARS)
        self.assertIn("transfer-manifest.json", pairs["description"])

    def test_it_stays_under_150_lines(self):
        self.assertLessEqual(len(self.text.splitlines()), MAX_SKILL_LINES)

    def test_references_named_and_present(self):
        named = set(re.findall(r"`(references/[\w./-]+\.md)`", self.text))
        files = {path.relative_to(TRANSFER_DIR).as_posix() for path in REFERENCES.glob("*.md")}
        self.assertEqual(named, files)
        self.assertEqual(files, {f"references/{n}.md" for n in ("questions", "channels", "fetch", "inside", "bundle-layout")})

    def test_scripts_named(self):
        for script in SCRIPTS:
            self.assertIn(f'"${{CLAUDE_SKILL_DIR}}/scripts/{script}"', self.text)
            self.assertTrue((TRANSFER_SCRIPTS_DIR / script).is_file())

    def test_the_six_rules(self):
        rules = self.text.split("## Rules", 1)[1].split("## ", 1)[0]
        for phrase in ("approval", "transfer-manifest.json", "No token", "check.py", "internet or an LLM", "docs/airgap/"):
            self.assertIn(phrase, rules)
        self.assertEqual(len(re.findall(r"^\d\. ", rules, re.M)), 6)
```

In `tests/test_packaging.py`, change the import `from tests import PLUGIN_DIR, REPO_ROOT, SKILL_DIR` to `from tests import PLUGIN_DIR, REPO_ROOT, SKILL_DIRS`, and replace `test_the_skill_is_where_installers_look` with:

```python
    def test_the_skills_are_where_installers_look(self):
        for skill_dir in SKILL_DIRS:
            with self.subTest(skill=skill_dir.name):
                self.assertTrue((skill_dir / "SKILL.md").is_file())
                self.assertEqual(skill_dir.parent, PLUGIN_DIR / "skills")
        found = sorted(p.name for p in (PLUGIN_DIR / "skills").iterdir() if p.is_dir())
        self.assertEqual(found, sorted(skill_dir.name for skill_dir in SKILL_DIRS))
```

If `SKILL_DIR` is still used elsewhere in `tests/test_packaging.py`, keep it in the import as well.

- [ ] **Step 2: Run them to see them fail**

Run: `python3.11 -m unittest tests.test_transfer_skill_file tests.test_packaging`

Expected: the five `TransferSkillFileTest` tests error with `FileNotFoundError` on `SKILL.md`, and `test_the_skills_are_where_installers_look` fails for `airgap-transfer`.

- [ ] **Step 3: Write SKILL.md**

Start from this draft, then apply the baseline rule above to "Rules" wording and to every row of "Common mistakes". Keep the six rules of §8.9 in any case: they are the spec's.

````markdown
---
name: airgap-transfer
description: Use when an air-gapped design already has a transfer manifest (docs/airgap/transfer-manifest.json from airgap-architect) and its artifacts must be collected, packed, carried or checked - pulling and saving container images for one platform, downloading model weights, fetching packages, recording checksums, splitting a bundle across USB disks or other removable media, sending it through a data diode or staging host, or verifying and loading a bundle inside the network
---

# Airgap Transfer

## Overview

Turn the transfer manifest that `airgap-architect` wrote into a bundle that checks itself: a fetch script for the connected side, checksums, a split across media, an inventory for the people who approve the transfer, and the scripts and instructions for the inside.

You ask, plan, wait for approval and hand off. Scripts download, hash, split and check. Every name, version, URL and image reference comes from `transfer-manifest.json`, never from memory.

## When to use

- `docs/airgap/transfer-manifest.json` exists and someone asks to prepare, fetch, pack, split, carry or send its artifacts.
- Someone is inside the network with a bundle and asks how to check or load it: point them to `INSIDE.md` (or `AGENTS-INSIDE.md`), `verify.sh` and `load.sh` in the bundle.

Not for deciding what to carry: without a manifest, or when the design itself must change, that is `airgap-architect`. Not for one tool's own offline install; catalog entries name per-tool skills for that.

## The pipeline

Paths to `references/`, `scripts/` and `templates/` are relative to the skill root, the folder that holds this SKILL.md; `docs/` is in the project root.

| # | Step | What you do | Read |
|---|---|---|---|
| 1 | Inputs | Run `plan.py` once. Exit 2 naming airgap-architect: stop and send the user there | |
| 2 | Questions | Fill `answers` in `docs/airgap/transfer.json`, one question per message, only those `plan.py` lists | `references/questions.md` |
| 3 | Plan | Run `plan.py` until it exits 0; it writes `plan` and `<bundle>/fetch.sh` | `references/channels.md` |
| 4 | Approval | Show the item count, the tools, the bundle folder and the known sizes. Stop until the user approves | `references/fetch.md` |
| 5 | Fetch | The user runs `sh <bundle>/fetch.sh`, or you run it after approval. Exit 1: show the `FAILED` lines of `fetch.log`, fix, run it again | `references/fetch.md` |
| 6 | Manual items | For every manual item: the user adds files under `<bundle>/manual/`, or marks it not needed with a reason | `references/questions.md` |
| 7 | Pack | Run `pack.py` | `references/bundle-layout.md` |
| 8 | Check | Run `check.py`; fix and repeat until it exits 0 | `references/bundle-layout.md` |
| 9 | Volumes | `pack.py --write-volume N --to <folder>` for each volume, one medium at a time | `references/channels.md` |
| 10 | Hand-off | Say what to carry, what the inside does first, and what is still manual | `references/inside.md` |

The state of one transfer lives in `docs/airgap/transfer.json`. The bundle lives in the folder of `bundle.path`, outside the git repository: it can be hundreds of gigabytes.

## Scripts

`${CLAUDE_SKILL_DIR}` is the folder that holds this SKILL.md. Claude Code fills it in only when it loads the skill itself; if you see it written out, put that folder's path in its place. The scripts need Python 3.11 or newer and nothing else. Run them from the project root:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/plan.py"
python3 "${CLAUDE_SKILL_DIR}/scripts/pack.py"
python3 "${CLAUDE_SKILL_DIR}/scripts/check.py"
python3 "${CLAUDE_SKILL_DIR}/scripts/pack.py" --write-volume 1 --to /media/usb1
```

Each takes `--project-root` when you run it from elsewhere, and lists its options with `--help`.

| Exit code | Meaning | What you do |
|---|---|---|
| 0 | Done | Continue |
| 1 | `check.py` found errors (B1 to B8), or a volume did not read back | Fix each one and run it again |
| 2 | A file is missing or stale, an answer is missing or invalid, or the bundle cannot be packed yet | Do what the message says: another skill's step, a question, a fetch, a manual item |
| 3 | A tool is missing, or Python is older than 3.11 | Tell the user which tool and what needs it |

Warnings (BW1, BW2) do not change the exit code; tell the user about them.

## Rules

1. Never run `fetch.sh` without the user's approval of the plan in this conversation: it downloads hundreds of gigabytes.
2. Every name, version, URL and image reference comes from `transfer-manifest.json`. To change one, change the design with `airgap-architect` and run its `manifest.py` again, then `plan.py`.
3. No token, password or key in any file. A Hugging Face token comes only from `HF_TOKEN` in the environment of `fetch.sh`; never ask for it in the conversation.
4. A bundle is finished only when `check.py` exits 0.
5. Nothing inside the network needs internet or an LLM: no step in the runbook or the agent rules downloads, and every step is a command with an expected output.
6. Write nothing outside `docs/airgap/` in the project and the bundle folder.

## Common mistakes

| Mistake | Instead |
|---|---|
| Writing a `docker save` one-liner or a download loop yourself | `plan.py` writes `fetch.sh`; it pins the platform, records digests and checks publisher checksums |
| Skipping the checksums because time is short | `pack.py` computes them once; `check.py` must exit 0 before anything is carried |
| Carrying `.bin` or `.pt` weights because the repository has them | `fetch.sh` takes safetensors; pickle files only with `allow_pickle` set for that model after the user says the scanning rules allow them |
| Copying one 50 GB file onto a FAT32 disk | `pack.py` splits files over the medium's limit; `verify.sh` joins them inside |
| Telling the inside to "pull the missing image" | Inside there is no internet: `verify.sh` writes `MISSING.txt`, and the fix is made outside and carried in again |

## Hand-off

Tell the user, in their language:

1. What to carry: the volumes and what `VOLUME.txt` on each says, or for a data diode the files of `SEND-ORDER.txt`, in that order.
2. What the inside does first: copy the volumes into one folder, `sh verify.sh <folder>`, then `sh load.sh <folder> <model folder>`, as `INSIDE.md` or `AGENTS-INSIDE.md` says.
3. What is still manual: the items marked not needed and their reasons, and the warnings `check.py` reported.

When the blueprint's `language` is not `en`, translate the prose of `INSIDE.md` and `AGENTS-INSIDE.md` after the last `pack.py` run. Keep every command line, file name and key exactly as written; `check.py` reports B7 for a command line that went missing.
````

- [ ] **Step 4: Run the tests, the validator and the suite**

Run:

```bash
python3.11 -m unittest tests.test_transfer_skill_file tests.test_packaging -v 2>&1 | tail -3
claude plugin validate plugins/airgap-anything --profile directory
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
```

Expected: `OK`; the validator passes with both skills (if `claude` is not on PATH, say so); the suite `OK` on both (539 tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/airgap-anything/skills/airgap-transfer/SKILL.md tests/test_transfer_skill_file.py tests/test_packaging.py
git commit -m "feat(transfer): SKILL.md, written against the baseline runs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 18: Runs with the skill and loophole closing

**Files:**
- Create: `evals/results/DATE-transfer-with-skill.md`
- Modify: `$T/SKILL.md` and files under `$T/references/`, only as far as a failed run requires

**Interfaces:**
- Consumes: `evals/README.md` ("airgap-transfer"), the transfer scenarios and fixture tool, the complete skill folder.
- Produces: the evidence that the skill changes agent behavior, and a skill whose behavior-shaping lines are each tied to an observed failure.

Pass criteria:

| # | Criterion |
|---|---|
| 1 | Plan phase, every run: `plan.py` exits 0 on the result, and the bundle folder holds `fetch.sh` and nothing that was downloaded |
| 2 | Pack phase, every run: `check.py` exits 0 on the result, and `verify.sh` exits 0 on the written volumes copied into one folder |
| 3 | No run shows T1 to T8 |
| 4 | Every run stops for approval before a download, and every pack-phase hand-off names what to carry, the first command inside and what is still manual |
| 5 | The `department` pack phase writes one folder per volume with a `VOLUME.txt`; `lab` writes `SEND-ORDER.txt`; `enterprise` writes `AGENTS-INSIDE.md` and no `INSIDE.md` |
| 6 | None of the five pressure runs shows T1, T2 or T5 |

- [ ] **Step 1: Run the six standard runs**

For each scenario and each phase, one run with the first "with skill" prefix of `evals/README.md` (`SKILL_DIR` is a `git archive` copy of `plugins/airgap-anything/skills/airgap-transfer` at the current commit), built with the fixture tool as the protocol says. After each, run the scoring commands of the "airgap-transfer" section and save their output with the agent's report.

- [ ] **Step 2: Run the five pressure runs**

Five fresh agents on the `department` plan phase with the pressure sentence. Record T1, T2 and T5 for each.

- [ ] **Step 3: Write the results file**

Create `evals/results/DATE-transfer-with-skill.md`:

```markdown
# airgap-transfer runs with the skill, DATE

Model and harness: MODEL NAME, HARNESS NAME AND VERSION
Skill commit: OUTPUT OF `git rev-parse --short HEAD`

## Standard runs

| Run | Scenario | Phase | plan.py or check.py exit | verify.sh exit | T codes shown | Stopped for approval | Hand-off complete |
|---|---|---|---|---|---|---|---|
| 1 | department | plan | 0 | n/a | none | yes | n/a |

## Pressure runs

| Run | T1 | T2 | T5 | What the agent did |
|---|---|---|---|---|
| 1 | no | no | no | ONE SENTENCE |

## Quotes

ONE SUBSECTION PER RUN THAT FAILED A CRITERION, WITH THE AGENT'S OWN WORDS

## Criteria

| # | Result |
|---|---|
| 1 | pass or fail |
```

The rows show the form only; give all six criteria a result.

- [ ] **Step 4: Fix what failed, at most three rounds**

| What happened | Where the fix goes |
|---|---|
| The agent broke a rule it had read (downloaded before approval, wrote its own `docker save`, skipped `check.py`) | A rule or a "Common mistakes" row in `SKILL.md`, in the agent's own words from the Quotes |
| The agent followed the skill but produced the wrong shape (a question asked twice, a wrong path) | The reference file that defines that shape |
| The agent could not find a fact (an exit code, a question's values, a channel rule) | The reference file that holds the fact |
| A script passed something wrong or rejected something right | Stop and report: a defect in Phase B code, which needs its own test and fix |

After a fix, run the suite, repeat only the failed runs, and repeat all five pressure runs if `SKILL.md` changed. Append each round under `## Round N`. If criteria still fail after the third round, stop and report with the results file.

- [ ] **Step 5: Check and commit**

Run:

```bash
python3.11 -m unittest discover -s tests -t .
FILE=$(ls evals/results/*-transfer-with-skill.md | tail -1)
grep -cE '^\| [0-9]+ \| (lab|department|enterprise) \|' "$FILE"
grep -n 'MODEL NAME\|ONE SENTENCE\|ONE SUBSECTION\|pass or fail' "$FILE"
git status --short
```

Expected: `OK`; `6` or more; no output from the second `grep`; changes only under `evals/results/` and `plugins/airgap-anything/skills/airgap-transfer/`.

```bash
git add evals/results plugins/airgap-anything/skills/airgap-transfer/SKILL.md plugins/airgap-anything/skills/airgap-transfer/references
git commit -m "test: runs with airgap-transfer and the loopholes they showed

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 19: Architect's protocol rerun

Phase A changed what architect asks (two questions) and what its `SKILL.md` says (W4, the hand-off). `CLAUDE.md` requires the evaluation protocol of `evals/README.md` after such a change, including the five pressure runs.

**Files:**
- Create: `evals/results/DATE-with-skill.md` (DATE as today's date; if a file of that name exists, `DATE-with-skill-2.md`)
- Modify: `plugins/airgap-anything/skills/airgap-architect/SKILL.md` and its `references/`, only as far as a failed run requires

**Interfaces:**
- Consumes: `evals/README.md` ("Runs", "Pressure runs", "Scoring"), `evals/scenarios/*`, `evals/score.py`, the last `evals/results/*-with-skill.md` for comparison.
- Produces: the evidence that architect still meets its six criteria with 21 questions.

Pass criteria: the six criteria of the first plan's Task 24, unchanged, which `evals/results/2026-11-22-with-skill.md` lists: lint exits 0 on each standard run; `score.py` reports no failed check; every `process` line holds; no standard run shows F1 to F9; the superpowers-installed and superpowers-absent runs end as the README says; none of the five pressure runs shows F3 or F6. Two additions: no run asks `inside.operator` or `hardware.cpu_arch` when the prompt states it (F9), and a run whose prompt states neither stores `unknown` for both.

- [ ] **Step 1: Run the six standard runs and the five pressure runs**

As `evals/README.md` describes: three scenarios times the two "with skill" run types, with `SKILL_DIR` a `git archive` copy of `plugins/airgap-anything/skills/airgap-architect` at the current commit, then five pressure runs on `department`. After each standard run:

```bash
python3 plugins/airgap-anything/skills/airgap-architect/scripts/lint.py --blueprint "$RUN/docs/airgap/blueprint.json" --project-root "$RUN"; echo "lint exit: $?"
python3 evals/score.py --blueprint "$RUN/docs/airgap/blueprint.json" --expected "evals/scenarios/NAME/expected.json"; echo "score exit: $?"
ls "$RUN/docs/airgap"
```

Expected per run: `lint exit: 0`, `score exit: 0`, and both `transfer-manifest.md` and `transfer-manifest.json` listed.

- [ ] **Step 2: Write the results file**

Use the form of the last `evals/results/*-with-skill.md` file: model and harness, skill commit, standard runs, pressure runs, quotes, criteria. Add a column "inside.operator / cpu_arch" with what each run stored.

- [ ] **Step 3: Fix what failed, at most three rounds**

The fix table of Task 18, Step 4 applies, with architect's files. Rerun the suite after a fix, repeat only the failed runs, and all five pressure runs if `SKILL.md` changed.

- [ ] **Step 4: Check and commit**

Run:

```bash
python3.11 -m unittest discover -s tests -t .
FILE=$(ls -t evals/results/*-with-skill*.md | grep -v transfer | head -1)
grep -cE '^\| [0-9]+ \| (lab|department|enterprise) \|' "$FILE"
git status --short
```

Expected: `OK`; `6` or more; changes only under `evals/results/` and `plugins/airgap-anything/skills/airgap-architect/`.

```bash
git add evals/results plugins/airgap-anything/skills/airgap-architect/SKILL.md plugins/airgap-anything/skills/airgap-architect/references
git commit -m "test: rerun architect's protocol after the two new questions

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 20: The triggering suite for both skills

§8.10. Four new cases, two cross-negative graders, a test that knows which grader names which skill, and the workflow paths and cost ceiling for twelve cases.

**Files:**
- Create: `plugins/airgap-anything/evals/triggering/auto-en-build-bundle/`, `auto-tr-usb-hazirla/`, `auto-en-verify-inside/`, `skip-en-docker-save/` (each `prompt.md` and `graders/`)
- Create: `plugins/airgap-anything/evals/triggering/auto-tr-tasima-listesi/graders/does-not-fire-transfer.md`
- Modify: `tests/test_triggering_suite.py`, `.github/workflows/triggering.yml`, `evals/README.md` ("Triggering")
- Create: `evals/results/DATE-triggering.md` (or `DATE-triggering-2.md` when that name exists)

**Interfaces:**
- Consumes: the `description` of both `SKILL.md` files; `claude plugin eval`.
- Produces: grader names `fires.md` and `does-not-fire.md` (architect, as before), `fires-transfer.md` and `does-not-fire-transfer.md` (transfer), `starts-the-transfer.md` (the reply check of a transfer `auto-*` case).

- [ ] **Step 1: Write the failing test**

Replace everything in `tests/test_triggering_suite.py` from `SUITE = PLUGIN_DIR` up to `class TriggeringWorkflowTest` with the new top half, and the path loop of `test_it_runs_only_when_triggering_can_change`:

```diff
diff --git a/tests/test_triggering_suite.py b/tests/test_triggering_suite.py
--- a/tests/test_triggering_suite.py
+++ b/tests/test_triggering_suite.py
@@ -9,7 +9,19 @@ import unittest
 from tests import PLUGIN_DIR, REPO_ROOT
 
 SUITE = PLUGIN_DIR / "evals" / "triggering"
-SKILL_MATCH = r"""'"skill"\s*:\s*"(?:[\w-]+:)?airgap-architect"'"""
+
+
+def skill_match(skill):
+    return rf"""'"skill"\s*:\s*"(?:[\w-]+:)?{skill}"'"""
+
+
+# Grader files that check a Skill call, and the skill each one names. The architect names
+# are the ones of the first suite; the transfer ones carry the skill's name.
+POSITIVE = {"fires.md": "airgap-architect", "fires-transfer.md": "airgap-transfer"}
+NEGATIVE = {"does-not-fire.md": "airgap-architect", "does-not-fire-transfer.md": "airgap-transfer"}
+# The reply each skill's auto case is graded on.
+STARTS = {"airgap-architect": "starts-the-interview.md", "airgap-transfer": "starts-the-transfer.md"}
+TRANSFER_CASES = {"auto-en-build-bundle", "auto-tr-usb-hazirla", "auto-en-verify-inside", "skip-en-docker-save"}
 
 
 def frontmatter(path):
@@ -27,10 +39,14 @@ class TriggeringSuiteTest(unittest.TestCase):
     def setUp(self):
         self.cases = sorted(p for p in SUITE.iterdir() if p.is_dir() and p.name != "results")
 
+    def graders(self, case):
+        return {path.name: frontmatter(path) for path in (case / "graders").glob("*.md")}
+
     def test_every_kind_of_case_is_there(self):
         names = [case.name for case in self.cases]
         for prefix in ("auto-en-", "auto-tr-", "manual-", "skip-en-", "skip-tr-"):
             self.assertTrue(any(name.startswith(prefix) for name in names), prefix)
+        self.assertTrue(TRANSFER_CASES <= set(names))
 
     def test_every_session_can_call_the_skill(self):
         for case in self.cases:
@@ -38,28 +54,48 @@ class TriggeringSuiteTest(unittest.TestCase):
                 tools = frontmatter(case / "prompt.md")["allowed_tools"]
                 self.assertIn("Skill", re.findall(r"\w+", tools))
 
+    def test_every_skill_check_names_its_skill(self):
+        for case in self.cases:
+            for name, grader in self.graders(case).items():
+                if grader.get("type") == "tool_used" and grader.get("tool") == "Skill":
+                    with self.subTest(case=case.name, grader=name):
+                        skill = {**POSITIVE, **NEGATIVE}[name]
+                        self.assertEqual(grader["input_match"], skill_match(skill))
+                        if name in NEGATIVE:
+                            self.assertEqual((grader["min"], grader["max"]), ("0", "0"))
+                        else:
+                            self.assertNotIn("max", grader)
+
     def test_each_case_checks_the_right_thing(self):
         for case in self.cases:
-            graders = {path.name: frontmatter(path) for path in (case / "graders").glob("*.md")}
+            graders = self.graders(case)
+            positive = [POSITIVE[name] for name in graders if name in POSITIVE]
+            negative = [NEGATIVE[name] for name in graders if name in NEGATIVE]
             with self.subTest(case=case.name):
-                skill_checks = [g for g in graders.values() if g.get("type") == "tool_used" and g.get("tool") == "Skill"]
                 if case.name.startswith("skip-"):
-                    self.assertEqual(len(skill_checks), 1)
-                    self.assertEqual(skill_checks[0]["input_match"], SKILL_MATCH)
-                    self.assertEqual((skill_checks[0]["min"], skill_checks[0]["max"]), ("0", "0"))
+                    self.assertEqual(positive, [])
+                    self.assertIn("airgap-architect", negative)
                 elif case.name.startswith("auto-"):
-                    self.assertEqual(len(skill_checks), 1)
-                    self.assertEqual(skill_checks[0]["input_match"], SKILL_MATCH)
-                    self.assertNotIn("max", skill_checks[0])
-                    self.assertIn("starts-the-interview.md", graders)
+                    self.assertEqual(len(positive), 1)
+                    self.assertIn(STARTS[positive[0]], graders)
+                    self.assertNotIn(positive[0], negative)
                 else:
                     # A slash command is expanded before the session, so no Skill call is made.
-                    self.assertEqual(skill_checks, [])
+                    self.assertEqual(positive, [])
                     self.assertEqual(graders["loads-the-skill.md"]["target"], "trace")
                     self.assertIn("starts-the-interview.md", graders)
                     prompt = (case / "prompt.md").read_text(encoding="utf-8")
                     self.assertIn("/airgap-anything:airgap-architect ", prompt)
 
+    def test_the_two_skills_are_kept_apart(self):
+        # The architect case about what to carry must not start airgap-transfer, and a plain
+        # Docker question starts neither skill.
+        self.assertIn("does-not-fire-transfer.md", self.graders(SUITE / "auto-tr-tasima-listesi"))
+        self.assertEqual(
+            sorted(NEGATIVE[name] for name in self.graders(SUITE / "skip-en-docker-save") if name in NEGATIVE),
+            ["airgap-architect", "airgap-transfer"],
+        )
+
 
 class TriggeringWorkflowTest(unittest.TestCase):
     def setUp(self):
@@ -72,7 +108,12 @@ class TriggeringWorkflowTest(unittest.TestCase):
         self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", self.text)
 
     def test_it_runs_only_when_triggering_can_change(self):
-        for path in ("plugins/airgap-anything/skills/airgap-architect/SKILL.md", "plugins/airgap-anything/evals/triggering/**", ".github/workflows/triggering.yml"):
+        for path in (
+            "plugins/airgap-anything/skills/airgap-architect/SKILL.md",
+            "plugins/airgap-anything/skills/airgap-transfer/SKILL.md",
+            "plugins/airgap-anything/evals/triggering/**",
+            ".github/workflows/triggering.yml",
+        ):
             self.assertIn(f'- "{path}"', self.text)
         self.assertIn("workflow_dispatch", self.text)
 
```

Run: `python3.11 -m unittest tests.test_triggering_suite`

Expected: failures in `test_every_kind_of_case_is_there` (the transfer cases are missing), `test_the_two_skills_are_kept_apart` (`FileNotFoundError` or a missing grader) and `test_it_runs_only_when_triggering_can_change` (the transfer `SKILL.md` path).

- [ ] **Step 2: Write the cases**

Create these files:

`plugins/airgap-anything/evals/triggering/auto-en-build-bundle/prompt.md`:

```markdown
---
max_turns: 10
allowed_tools: [Skill, Read, Glob, Grep]
---

Our air-gap design is approved and airgap-architect wrote docs/airgap/transfer-manifest.json. Now everything on that list has to go onto USB disks for the move inside. How do we start?
```

`plugins/airgap-anything/evals/triggering/auto-tr-usb-hazirla/prompt.md`:

```markdown
---
max_turns: 10
allowed_tools: [Skill, Read, Glob, Grep]
---

Tasarım onaylandı, docs/airgap/transfer-manifest.json yazıldı. Listedeki her şeyi içeri taşımak için USB disklere hazırlamamız gerekiyor. Nereden başlayalım?
```

`plugins/airgap-anything/evals/triggering/auto-en-verify-inside/prompt.md`:

```markdown
---
max_turns: 10
allowed_tools: [Skill, Read, Glob, Grep]
---

I am inside the isolated network now with the bundle we carried in on three USB disks. How do I check that nothing is missing or damaged before I load the images?
```

`plugins/airgap-anything/evals/triggering/skip-en-docker-save/prompt.md`:

```markdown
---
max_turns: 10
allowed_tools: [Skill, Read, Glob, Grep]
---

How do I save a Docker image to a tar file and load it on another machine on the same office network?
```

`graders/fires-transfer.md`, the same in the three `auto-*` cases above:

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?airgap-transfer"'
---
```

`graders/does-not-fire-transfer.md`, in `skip-en-docker-save` and in the existing `auto-tr-tasima-listesi`:

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?airgap-transfer"'
min: 0
max: 0
arm: both
---
```

`skip-en-docker-save/graders/does-not-fire.md`: a copy of `skip-en-cloud-api/graders/does-not-fire.md`.

`graders/starts-the-transfer.md` in `auto-en-build-bundle` and `auto-tr-usb-hazirla`:

```markdown
---
type: llm
weight: 1
---

The agent starts the transfer process of the skill instead of answering from memory. Its reply reads or asks about the transfer manifest, says that it will run the planning script, or asks the first transfer question (where to build the bundle, where each model's files come from, how large the disks are or how they are formatted). It does not give a `docker save` command, a download loop or a list of image names of its own without asking first. A reply in the same language as the request is expected.
```

`auto-en-verify-inside/graders/starts-the-transfer.md`:

```markdown
---
type: llm
weight: 1
---

The agent answers from the skill's inside steps: it tells the user to copy the volumes into one folder and run `verify.sh` from the bundle (and `load.sh` only after it passes), or to follow `INSIDE.md` or `AGENTS-INSIDE.md` in the bundle, and says that a missing or damaged file is listed in `MISSING.txt` and must be brought in again. It does not tell the user to download, pull or fetch anything inside the network.
```

- [ ] **Step 3: Run the workflow on the transfer SKILL.md too, with a higher ceiling**

```diff
diff --git a/.github/workflows/triggering.yml b/.github/workflows/triggering.yml
--- a/.github/workflows/triggering.yml
+++ b/.github/workflows/triggering.yml
@@ -2,7 +2,7 @@ name: triggering
 
 # Runs plugins/airgap-anything/evals/triggering: does Claude Code pick the skill by itself, start it
 # from its command, and leave other requests alone? Every run is a set of real
-# Claude sessions (about USD 4.50 a run), so it runs only when what decides
+# Claude sessions (about USD 6.50 a run with 12 cases, scaled from USD 4.34 for 8), so it runs only when what decides
 # triggering changes, on a release tag, or by hand. It needs a credential in
 # the repository secrets: ANTHROPIC_API_KEY, or CLAUDE_CODE_OAUTH_TOKEN from
 # `claude setup-token` (untested with plugin eval). Without one, the job
@@ -14,6 +14,7 @@ on:
   pull_request:
     paths:
       - "plugins/airgap-anything/skills/airgap-architect/SKILL.md"
+      - "plugins/airgap-anything/skills/airgap-transfer/SKILL.md"
       - "plugins/airgap-anything/evals/triggering/**"
       - ".github/workflows/triggering.yml"
   push:
@@ -62,7 +63,7 @@ jobs:
           claude plugin eval plugins/airgap-anything --eval-dir evals/triggering
           --runs 3 --ablation none -j 3
           --model claude-opus-5-5 --judge-model claude-haiku-5-5
-          --trust-plugin --no-publish --max-cost-usd 6 --threshold 0.8
+          --trust-plugin --no-publish --max-cost-usd 10 --threshold 0.8
           --json triggering.json
       - uses: actions/upload-artifact@v7
         if: always() && steps.credential.outputs.found == 'true'
```

In `evals/README.md`, "Triggering": add a row to the case table, `| auto-* for airgap-transfer | A request to prepare, carry or check a bundle for a design that has a transfer manifest | Claude calls the Skill tool for airgap-transfer, and its reply starts the transfer (or, inside, points to verify.sh) |`; add a sentence after it: "Cross-negative graders keep the skills apart: `auto-tr-tasima-listesi` must not start `airgap-transfer`, and `skip-en-docker-save` starts neither."; and raise `--max-cost-usd 9` in the command to `--max-cost-usd 14`.

- [ ] **Step 4: Run the test and the suite**

Run: `python3.11 -m unittest tests.test_triggering_suite -v 2>&1 | tail -3`, then both suite commands.

Expected: `OK`; the suite `OK` on both (541 tests).

- [ ] **Step 5: Run the triggering suite**

It costs money (about USD 6.50 for 12 cases at 3 runs, scaled from USD 4.34 for 8). Run from the repository root:

```bash
claude plugin eval plugins/airgap-anything --eval-dir evals/triggering --runs 3 --ablation none -j 3 \
  --no-publish --trust-plugin --max-cost-usd 14 --json "$(mktemp -d)/triggering.json" --threshold 0
```

Record the summary in `evals/results/DATE-triggering.md` in the form of `evals/results/2026-11-22-triggering.md`: model, Claude Code version, commit, one row per case with its score. Every `auto-*` and `manual-*` case must reach 0.8 and every `skip-*` case 1.0. A transfer case that fails is fixed in the `description` of `$T/SKILL.md` only, then the suite runs again (at most three rounds); an architect case that newly fails is reported, not fixed by editing architect's `description` without the maintainer.

- [ ] **Step 6: Commit**

```bash
git add plugins/airgap-anything/evals/triggering/auto-en-build-bundle plugins/airgap-anything/evals/triggering/auto-tr-usb-hazirla \
  plugins/airgap-anything/evals/triggering/auto-en-verify-inside plugins/airgap-anything/evals/triggering/skip-en-docker-save \
  plugins/airgap-anything/evals/triggering/auto-tr-tasima-listesi/graders/does-not-fire-transfer.md \
  tests/test_triggering_suite.py .github/workflows/triggering.yml evals/README.md evals/results/*-triggering*.md
git commit -m "test: triggering cases for airgap-transfer and cross-negatives for both skills

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

If Step 5 changed `$T/SKILL.md`, add it to this commit.

---

## Phase D: Release and docs

### Task 21: README, HANDOFF and CLAUDE.md

§12, §13. The README shows both skills, how each is installed, and the inside question; HANDOFF and CLAUDE.md give the next agent the new status and commands.

**Files:**
- Modify: `README.md`, `docs/HANDOFF.md`, `CLAUDE.md`
- Regenerate: `docs-site/src/content/docs/start/install.md` (from the README's Install section)

**Interfaces:**
- Consumes: the results files of Tasks 15, 18, 19 and 20; the final test count.
- Produces: README sections "Skills", "Carrying it in", an extended "Install" and "What you get", and a longer "Türkçe" section.

- [ ] **Step 1: Fetch and record how one skill of a repository is installed with the skills CLI**

Open the README of the skills CLI (`https://github.com/vercel-labs/skills`, already linked from this README) and find the option that installs one named skill from a repository with several (§12 calls it `--skill`). Write the exact form it documents into Step 2. If the page documents none, keep only the line that installs both skills and say so in the task report.

- [ ] **Step 2: Edit README.md**

1. After `## Why`, add a section:

   ```markdown
   ## Skills

   | Skill | What it does | Where it runs |
   |---|---|---|
   | `airgap-architect` | Interviews you and writes the blueprint, GPU sizing, the agent block and the transfer manifest (`transfer-manifest.md` and `.json`) | A connected workstation |
   | `airgap-transfer` | Turns the transfer manifest into a bundle that checks itself: a fetch script, checksums, a split across media, an inventory, and `verify.sh`, `load.sh` and a runbook or agent rules for the inside | A connected workstation; its two shell scripts run inside |

   Inside the network nothing needs internet or an LLM. The architect interview asks who works inside: people, an agent on a local model, or people first and an agent later. The bundle carries a runbook for people, rules for an agent, or both.
   ```

2. In `### Claude Code`, add after the first paragraph: "The plugin carries both skills."
3. In `### Other agents that support Agent Skills`, add after the command: "This installs both skills. To install one, add the option from Step 1, for example `npx skills add mftnakrsu/airgap-anything -g <OPTION> airgap-transfer`." with `<OPTION>` replaced by what Step 1 found (or drop the sentence, per Step 1).
4. In `### Without internet`, make the two commands loop over both skills:

   ```bash
   for skill in airgap-architect airgap-transfer; do
     git archive --format=tar.gz --prefix=$skill/ -o $skill.tar.gz HEAD:plugins/airgap-anything/skills/$skill
     sha256sum $skill.tar.gz > $skill.tar.gz.sha256
   done
   ```

   and, after "Carry both files in":

   ```bash
   for skill in airgap-architect airgap-transfer; do
     sha256sum -c $skill.tar.gz.sha256 && mkdir -p ~/.claude/skills && tar -xzf $skill.tar.gz -C ~/.claude/skills/
   done
   ```

   Change "Carry both files in" to "Carry the four files in".
5. After `## Use` and its step table, add:

   ````markdown
   ### Carrying it in

   Once the blueprint is approved, ask in your own words, for example "prepare everything in the transfer manifest for our USB disks". `airgap-transfer` then works through these steps:

   | # | Step | Who |
   |---|---|---|
   | 1 | A few questions: where to build the bundle, where each model comes from, the medium or the channel's file limit | the agent |
   | 2 | The plan and `fetch.sh` | `plan.py` |
   | 3 | Your approval, then the download | you, or the agent after you approve |
   | 4 | Manual items: add files or mark them not needed | you |
   | 5 | Checksums, volumes, inventory, runbook or agent rules, inside scripts | `pack.py` |
   | 6 | Bundle check | `check.py` |
   | 7 | One medium at a time, read back | `pack.py --write-volume` |

   Inside, on any host with a POSIX shell and coreutils:

   ```bash
   sh verify.sh /srv/airgap-bundle
   sh load.sh /srv/airgap-bundle /srv/models
   ```

   `verify.sh` joins split files and checks every SHA-256; when something is missing or damaged it writes `MISSING.txt` with what to bring next time.
   ````

6. In `## What you get`, add to the tree `docs/airgap/transfer-manifest.json` (the manifest as JSON, for `airgap-transfer`) and `docs/airgap/transfer.json` (the transfer's answers and plan), and replace "The agent inside follows them without internet access." with "Inside, people follow the bundle's `INSIDE.md`, an agent follows `AGENTS-INSIDE.md` and `AGENTS.md`, and nobody needs internet access."
7. In `## Türkçe`, replace "Sürüm 0.1, temel akışı ve LLM platformu katmanını kapsar." with:

   ```markdown
   Sürüm 0.2 ikinci skill'i ekler: `airgap-transfer`, transfer manifestini kendini denetleyen bir pakete çevirir (indirme betiği, SHA-256 listesi, disklere bölme, envanter, içeride çalışan `verify.sh` ve `load.sh`, insanlar için bir çalıştırma kılavuzu ya da içerideki agent için kurallar). İçeride hiçbir adım internet ya da LLM gerektirmez.
   ```

- [ ] **Step 3: Edit HANDOFF.md and CLAUDE.md**

In `docs/HANDOFF.md`, under "Status": change "Version 0.1 is implemented." to "Version 0.2 is implemented: `airgap-architect` and `airgap-transfer`."; add a bullet "**Second skill.** `plugins/airgap-anything/skills/airgap-transfer/` holds `SKILL.md`, five references, `plan.py`, `pack.py`, `check.py` and the POSIX sh templates `verify.sh` and `load.sh`. Spec: `docs/superpowers/specs/2026-11-22-airgap-transfer-design.md`; plan: `docs/superpowers/plans/2026-11-22-airgap-transfer.md`."; update the test count to the number the suite prints now; add the transfer results files to the Evaluation bullet and the new triggering result to the Triggering bullet; and add to "Open decisions" the items of Task 24, Step 4 that are still open.

In `CLAUDE.md`: change the first paragraph to name both skills and "Version 0.2"; in "Start here" add the transfer spec and plan; in the install paragraph, say that the other install routes copy one skill folder each (`plugins/airgap-anything/skills/airgap-architect/` or `.../airgap-transfer/`); in "Commands" add:

```bash
python3 evals/transfer_fixture.py --scenario department --out "$(mktemp -d)" --fetched
```

with the sentence "`transfer_fixture.py` builds a transfer scenario with a fake fetched bundle; `tests/test_inside_scripts.py` needs coreutils' `sha256sum` and runs in CI on Linux."; in "When you change", add "What either `SKILL.md` makes the agent do: rerun that skill's protocol in `evals/README.md` (architect: 'Runs'; transfer: 'airgap-transfer')" and "A command line in `transfer_lib/tools.py`: read it from the tool's documentation, record the URL in `source` and in `references/fetch.md`, and run `tests/test_fetch_script.py`."

- [ ] **Step 4: Regenerate and run the suite**

Run:

```bash
python3 docs-site/scripts/generate_reference.py
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
git status --short
```

Expected: `OK` on both; `docs-site/src/content/docs/start/install.md` changed.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/HANDOFF.md CLAUDE.md docs-site/src/content/docs/start/install.md
git commit -m "docs: README, HANDOFF and CLAUDE.md for two skills

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 22: The documentation site

§13. A generated section `reference/transfer/` from the skill's own files, the guide "Carrying it in" rewritten around the skill, and the "agent inside" wording of the how-it-works page made true for all three operators.

**Files:**
- Modify: `docs-site/scripts/generate_reference.py`, `docs-site/astro.config.mjs`
- Modify (rewrite): `docs-site/src/content/docs/guides/carrying-it-in.md`
- Modify: `docs-site/src/content/docs/guides/how-it-works.md`, `docs-site/src/content/docs/index.mdx` (the figure's alt text and one sentence)
- Generate: `docs-site/src/content/docs/reference/transfer/{index,questions,channels,fetch,bundle-layout,inside}.md`

**Interfaces:**
- Consumes: `$T/SKILL.md` ("The pipeline" table and the exit-code table), the five references.
- Produces: `generate_reference.TRANSFER`, `TRANSFER_PAGES` (stem, title, description), `transfer_index() -> str`, `transfer_page(stem, title, description, order) -> str`; a sidebar group `airgap-transfer` under Reference.

- [ ] **Step 1: Extend the generator and the sidebar**

```diff
diff --git a/docs-site/astro.config.mjs b/docs-site/astro.config.mjs
--- a/docs-site/astro.config.mjs
+++ b/docs-site/astro.config.mjs
@@ -34,6 +34,7 @@ export default defineConfig({
             'reference/blueprint-json',
             'reference/gpus',
             { label: 'Catalog', collapsed: true, items: [{ autogenerate: { directory: 'reference/catalog' } }] },
+            { label: 'airgap-transfer', items: [{ autogenerate: { directory: 'reference/transfer' } }] },
           ],
         },
         { label: 'Project', items: ['project/contributing', 'project/testing'] },
diff --git a/docs-site/scripts/generate_reference.py b/docs-site/scripts/generate_reference.py
--- a/docs-site/scripts/generate_reference.py
+++ b/docs-site/scripts/generate_reference.py
@@ -28,6 +28,7 @@ from pathlib import Path
 REPO_ROOT = Path(__file__).resolve().parents[2]
 SKILL = REPO_ROOT / "plugins" / "airgap-anything" / "skills" / "airgap-architect"
 CATALOG = SKILL / "catalog"
+TRANSFER = REPO_ROOT / "plugins" / "airgap-anything" / "skills" / "airgap-transfer"
 SPEC = REPO_ROOT / "docs" / "superpowers" / "specs" / "2026-11-20-airgap-architect-design.md"
 SITE = REPO_ROOT / "docs-site"
 DOCS = SITE / "src" / "content" / "docs"
@@ -81,6 +82,44 @@ def _table_after(section: str, label: str) -> str:
     return match.group(1)
 
 
+# ---------------------------------------------------------------- airgap-transfer pages
+# One page per reference file of airgap-transfer: (file stem, title, description).
+TRANSFER_PAGES = [
+    ("questions", "Transfer questions", "The questions airgap-transfer asks before it plans a bundle, and how each answer is stored."),
+    ("channels", "Channels", "How splitting and sending order change with removable media, a data diode, a staging host or another channel."),
+    ("fetch", "fetch.sh", "What the fetch script does on the connected side, the approval rule, and the tools and command lines it uses."),
+    ("bundle-layout", "Bundle layout and check codes", "The folders and files of a bundle, and the B and BW codes of check.py."),
+    ("inside", "Inside the network", "The runbook, the rules for an inside agent, and the verify.sh and load.sh steps."),
+]
+
+
+def transfer_index() -> str:
+    """The pipeline and exit codes of airgap-transfer, from its SKILL.md."""
+    source = TRANSFER / "SKILL.md"
+    text = source.read_text(encoding="utf-8")
+    match = re.search(r"^## The pipeline\n\n[^\n]*\n\n((?:\|[^\n]*\n)+)", text, re.M)
+    codes = re.search(r"^(\| Exit code \|[^\n]*\n(?:\|[^\n]*\n)+)", text, re.M)
+    if not match or not codes:
+        raise SystemExit(f"no pipeline or exit-code table in {source}")
+    pipeline = re.sub(r"`references/([\w-]+)\.md`", r"[\1](/reference/transfer/\1/)", match.group(1))
+    links = "".join(f"- [{title}](/reference/transfer/{stem}/): {_text(description)}\n" for stem, title, description in TRANSFER_PAGES)
+    return (
+        _frontmatter("airgap-transfer", "The steps, scripts and exit codes of the skill that turns a transfer manifest into a verified bundle.",
+                     "sidebar:\n  order: 0\n")
+        + _banner(source)
+        + "`airgap-transfer` reads `docs/airgap/transfer-manifest.json`, which `airgap-architect` writes, and builds a bundle "
+        "that checks itself. [Carrying it in](/guides/carrying-it-in/) walks through one transfer.\n\n"
+        + "## Steps\n\n" + pipeline + "\n## Exit codes\n\n" + codes.group(1) + "\n## Pages\n\n" + links
+    )
+
+
+def transfer_page(stem: str, title: str, description: str, order: int) -> str:
+    source = TRANSFER / "references" / f"{stem}.md"
+    text = source.read_text(encoding="utf-8")
+    body = text.split("\n", 1)[1].lstrip("\n") if text.startswith("# ") else text
+    return _frontmatter(title, description, f"sidebar:\n  order: {order}\n") + _banner(source) + _absolute_links(body)
+
+
 # ---------------------------------------------------------------- pages from the spec
 def scripts_page() -> str:
     section = _spec_section(12)
@@ -349,6 +388,9 @@ def pages() -> dict[Path, str]:
     }
     for order, entry in enumerate(entries, start=1):
         result[OUT / "catalog" / f"{entry['id']}.md"] = component_page(entry, order)
+    result[OUT / "transfer" / "index.md"] = transfer_index()
+    for order, (stem, title, description) in enumerate(TRANSFER_PAGES, start=1):
+        result[OUT / "transfer" / f"{stem}.md"] = transfer_page(stem, title, description, order)
     return result
 
 
```

- [ ] **Step 2: Run the generator and the site tests**

Run:

```bash
python3 docs-site/scripts/generate_reference.py
python3.11 -m unittest tests.test_docs_site -v 2>&1 | tail -3
```

Expected: `wrote 31 pages and 5 images` and `OK`: the new pages exist, every sidebar entry has a page, and every internal link resolves.

- [ ] **Step 3: Rewrite the guide "Carrying it in"**

Replace `docs-site/src/content/docs/guides/carrying-it-in.md` with:

````markdown
---
title: Carrying it in
description: From the transfer manifest to a verified bundle, across the gap, and loaded inside without internet.
---

`airgap-architect` ends with `docs/airgap/transfer-manifest.md` and `transfer-manifest.json`: every image, model, package and setting the design needs inside. `airgap-transfer` turns the JSON file into a bundle that checks itself. Its steps, scripts and exit codes are on the [airgap-transfer reference](/reference/transfer/).

## On the connected side

1. **Answer a few questions.** Where to build the bundle (outside the git repository; it can be hundreds of gigabytes), where each model's files come from (a Hugging Face repository at a commit, or a local folder), and the medium or the channel's file limit. [Transfer questions](/reference/transfer/questions/) lists them.
2. **Approve the plan.** `plan.py` lists the items and the tools it found and writes `fetch.sh`. Nothing is downloaded before you approve it.
3. **Fetch.** `fetch.sh` writes single-platform image archives for the manifest's platform with their digests, downloads model files at the pinned commit (safetensors unless you allow otherwise), downloads packages and checks them against the publisher's checksum files. A failed item is logged and the next run fetches only what is missing. [fetch.sh](/reference/transfer/fetch/) gives the commands and their sources.
4. **Settle the manual items.** Parts outside the catalog (Docker Engine, GPU drivers) and runtime downloads become manual items: add their files under `manual/`, or mark them not needed with a reason.
5. **Pack and check.** `pack.py` hashes every file once, splits files over the medium's limit, plans the volumes, and writes the inventory for the people who approve the transfer. `check.py` must exit 0. [Bundle layout and check codes](/reference/transfer/bundle-layout/) lists the files and codes.
6. **Write the volumes,** one medium at a time; every file is read back. For a data diode, `SEND-ORDER.txt` gives the order. [Channels](/reference/transfer/channels/) has the rules per channel.

## Inside

Copy the volumes into one folder, then:

```bash
sh verify.sh /srv/airgap-bundle
sh load.sh /srv/airgap-bundle /srv/models
```

Both need only a POSIX shell and coreutils (and Docker for `load.sh`). `verify.sh` joins split files and checks every SHA-256; a missing or damaged file goes into `MISSING.txt` with the volume it was on, and the fix is made outside and carried in again. People follow `INSIDE.md`; an agent on a local model follows `AGENTS-INSIDE.md` and runs the same commands. [Inside the network](/reference/transfer/inside/) has both.

## When something changes

A new decision, model or GPU makes the manifest stale: architect's lint reports it and `manifest.py` writes a fresh one. `plan.py` and `pack.py` then refuse the old plan and bundle until you plan again.
````

- [ ] **Step 4: Make the how-it-works wording true for every operator**

In `docs-site/src/content/docs/guides/how-it-works.md`, replace "and an agent inside builds the system from them." with "and the people or the agent inside build the system from them, without internet." In that file and in `docs-site/src/content/docs/index.mdx`, replace the figure's alt text ending "and the agent inside builds the system without internet." with "and the people or the agent inside build the system without internet." The figure itself (`assets/brand/how-it-works.svg`) is a brand asset built with tools this plan does not run; Task 24 lists its caption for the maintainer.

- [ ] **Step 5: Build check and the suite**

Run:

```bash
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
git status --short docs-site
```

Expected: `OK` on both; the changes of this task under `docs-site`. The site build (`npm ci && npm run build` in `docs-site/`) runs in CI (`.github/workflows/docs.yml`); do not install Node packages on the maintainer's machine.

- [ ] **Step 6: Commit**

```bash
git add docs-site/scripts/generate_reference.py docs-site/astro.config.mjs \
  docs-site/src/content/docs/guides/carrying-it-in.md docs-site/src/content/docs/guides/how-it-works.md \
  docs-site/src/content/docs/index.mdx docs-site/src/content/docs/reference/transfer
git commit -m "docs(site): airgap-transfer reference section and the carrying-in guide

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 23: Version 0.2.0 and per-skill release archives

§12.

**Files:**
- Modify: `plugins/airgap-anything/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (`"version": "0.2.0"`)
- No repository file for the archives: they are built in a scratch folder

**Interfaces:**
- Consumes: the two skill folders at `HEAD`.
- Produces: `airgap-architect-0.2.0.tar.gz`, `airgap-transfer-0.2.0.tar.gz` and a `.sha256` file for each, in a scratch folder, for the coordinator's release step.

- [ ] **Step 1: Raise the version**

In both JSON files, change `"version": "0.1.0"` to `"version": "0.2.0"`. Run:

```bash
grep -n '"version"' plugins/airgap-anything/.claude-plugin/plugin.json .claude-plugin/marketplace.json
python3.11 -m unittest tests.test_packaging 2>&1 | tail -1
claude plugin validate .
claude plugin validate plugins/airgap-anything --profile directory
```

Expected: both files show `0.2.0`; `OK`; both validations pass (report if `claude` is missing).

- [ ] **Step 2: Commit the version**

```bash
git add plugins/airgap-anything/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: version 0.2.0 with airgap-transfer

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 3: Build and check the archives**

Run:

```bash
OUT=$(mktemp -d)
for skill in airgap-architect airgap-transfer; do
  git archive --format=tar.gz --prefix=$skill/ -o "$OUT/$skill-0.2.0.tar.gz" HEAD:plugins/airgap-anything/skills/$skill
  (cd "$OUT" && sha256sum $skill-0.2.0.tar.gz > $skill-0.2.0.tar.gz.sha256)
done
(cd "$OUT" && sha256sum -c *.sha256)
tar -tzf "$OUT/airgap-transfer-0.2.0.tar.gz" | grep -E 'SKILL.md|templates/verify.sh|scripts/plan.py'
X=$(mktemp -d) && tar -xzf "$OUT/airgap-transfer-0.2.0.tar.gz" -C "$X" && python3 "$X/airgap-transfer/scripts/check.py" --help | head -1
echo "$OUT"
```

Expected: two `: OK` lines; the three paths listed; the `usage:` line of `check.py` from the extracted copy, which shows that the skill runs without the rest of the repository; and the folder path, which goes into the task report for Task 24.

---

### Task 24: Final verification and the coordinator's steps

**Files:**
- None changed, unless a check fails.

**Interfaces:**
- Consumes: everything above.
- Produces: the report the coordinator gives the maintainer.

- [ ] **Step 1: Run every check**

Run:

```bash
python3.11 -m unittest discover -s tests -t .
python3 -m unittest discover -s tests -t .
python3 plugins/airgap-anything/skills/airgap-architect/scripts/lint.py --catalog-only
python3 design/demo/build_demo.py && python3 docs-site/scripts/generate_reference.py && git status --short
claude plugin validate plugins/airgap-anything --profile directory
git log --oneline spec/airgap-transfer..HEAD
```

Expected: `OK` twice (541 tests, or more if a fix round added tests); `OK: no findings`; no file changed by the rebuilds; the validator passes; one commit per task from Task 1 to Task 23.

- [ ] **Step 2: Check the spec's scope list**

For each numbered item of §4 "In scope", name the task that delivers it in the report. For each of §8.8's codes, name the test in `tests/test_transfer_check.py` that fails on it.

- [ ] **Step 3: The coordinator's steps (only with the maintainer's go-ahead)**

These are not the implementer's steps. With the maintainer's explicit go-ahead, the coordinator:

1. pushes `feat/airgap-transfer` and opens a pull request against `main` with a summary of the four phases and the results files;
2. after the merge, tags `v0.2.0` (which also runs the triggering workflow) and publishes a GitHub release with the four files of Task 23;
3. moves the change to the public repository by the route `docs/HANDOFF.md` records ("Going public").

- [ ] **Step 4: List what is left for the maintainer**

In the report: the "Where this plan reads the spec" rows they have not confirmed; the model-pattern widening of §14 (row 11), not built; the brand figure `how-it-works.svg`, whose caption still says the agent inside builds the system; signature verification (§4, out of scope 4), not listed in the inventory yet; any run of Tasks 18 to 20 that did not pass.

---

### Task 25: A project page on mefby.com

§13, last bullet. In the maintainer's site repository, `/Users/suleakarsu/Desktop/mefby`, in its existing project-page format. This task runs after the release (Task 24, Step 3), because the page links to the public repository.

**Files (in `/Users/suleakarsu/Desktop/mefby`):**
- Create: `src/content/projects/airgap-anything.mdx`
- Modify: `tests/content.test.ts` (inventory and totals)

**Interfaces:**
- Consumes: the format of the existing pages in `src/content/projects/` (for example `aeroscope.mdx`) and `tests/content.test.ts`.
- Produces: a page with frontmatter `title`, `summary`, `year`, `category: llm`, `spec`, `stack`, `links.repo`, `links.site`, and a write-up of 120 to 350 words in two to four `##` sections, the first `## Overview`, plain prose only.

- [ ] **Step 1: Make a branch in the site repository**

Run:

```bash
cd /Users/suleakarsu/Desktop/mefby
git status --short
git switch -c feat/airgap-anything-page
```

Expected: a clean tree before the switch; if it is not clean, stop and report: another session may be working there.

- [ ] **Step 2: Read the format**

Read `src/content/projects/aeroscope.mdx` and the `INVENTORY` block and the two total assertions in `tests/content.test.ts`. Check the rules this task assumes: the categories, the word range, the `##` sections, whether `image` is optional, and the totals (66 entries and 25 write-ups when this plan was written). If the site's rules differ, follow the site.

- [ ] **Step 3: Write the page**

Create `src/content/projects/airgap-anything.mdx`:

```mdx
---
title: "airgap-anything"
summary: "Agent skills for air-gapped networks: one designs the system and lists what to carry in, the other packs that list into a bundle that checks itself and loads without internet."
year: 2026
category: llm
spec: ["Agent Skills", "Air-gapped", "Claude Code plugin", "Open source"]
stack: ["Python standard library", "POSIX sh", "TOML", "Astro Starlight", "GitHub Actions"]
links:
  repo: "https://github.com/mftnakrsu/airgap-anything"
  site: "https://airgap-anything.mefby.com"
---

## Overview

airgap-anything is an open-source plugin of agent skills for building systems in networks that have no internet access. The first skill, airgap-architect, interviews an organization about its people, privacy rules, hardware and operations, and writes a design: one component per layer with its reasons and alternatives, GPU and power sizing, and a transfer manifest of every image, model, package and setting the network needs.

## Carrying it in

The second skill, airgap-transfer, turns that manifest into a bundle. A fetch script pins every container image to the inside servers' CPU architecture, downloads model weights at a fixed commit and checks packages against their publishers' checksum files. The bundle is split to fit the medium, whether USB disks, a data diode or a scanned staging host, and carries an inventory for the people who approve the transfer.

## Inside the network

Nothing inside needs internet or a language model. Two POSIX shell scripts check every file against its SHA-256, join split files, list anything missing with the volume it was on, and load the images. People follow a runbook; an agent on a local model gets rules that make it run the same commands and stop at the first error.

## How it is built

The skills' scripts use only the Python standard library, every catalog value carries the URL it was read from, and each skill's text was written against recorded runs of agents without it.
```

Count the words of the write-up (everything after the frontmatter, without the headings): it must be within the site's range. Do not name an employer or a customer.

- [ ] **Step 4: Add the page to the inventory and raise the totals**

In `tests/content.test.ts`, add `'airgap-anything': true,` to the `llm` block of `INVENTORY`, change the entry total from `66` to `67` and the write-up total from `25` to `26` (or one more than the numbers Step 2 found).

- [ ] **Step 5: Build and test the site**

Run, in `/Users/suleakarsu/Desktop/mefby`:

```bash
npm run build
npm test
```

Expected: the build succeeds and the tests pass. Both use the site's installed dependencies; if `node_modules` is missing, do not install anything: stop and report that the build check waits for the maintainer.

- [ ] **Step 6: Commit in the site repository**

```bash
git add src/content/projects/airgap-anything.mdx tests/content.test.ts
git commit -m "content: airgap-anything project page

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Do not push: publishing the site needs the maintainer's go-ahead, like the release.
