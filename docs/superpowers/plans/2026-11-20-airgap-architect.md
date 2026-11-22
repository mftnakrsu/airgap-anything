# airgap-architect Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `airgap-architect`, an Agent Skill that interviews a person about their organization and produces a lint-clean design blueprint, GPU sizing and a transfer manifest for an air-gapped system, published in the `airgap-anything` repository.

**Architecture:** A hybrid skill. Markdown decision tables and a TOML catalog hold the knowledge; the model interviews and decides; four standard-library Python scripts (`tier.py`, `size.py`, `manifest.py`, `lint.py`) compute and verify, writing their results into one state file, `docs/airgap/blueprint.json`. The deterministic code is built test-first. Catalog content is researched with recorded sources. The skill text is written only after baseline runs without it.

**Tech Stack:** Python 3.11+ (standard library only: `tomllib`, `json`, `argparse`, `unittest`), TOML, Markdown, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-20-airgap-architect-design.md`. Read it before any task. Section numbers written as §N refer to it.

**How the code in this plan was checked:** every Python file, `rules.toml`, the scenario fixtures and the skill documents below were run together in a scratch copy of this layout on Python 3.12.3. The plan itself was then replayed: each file was extracted from this document in task order and the suite was run after every task (206 tests passing at the end, with synthetic stand-ins for the sixteen catalog entries and one GPU row). The catalog entries themselves are not in this plan; they are research tasks. Nothing was run on Python 3.11; CI in Task 27 covers it.

## Global Constraints

- **Names.** Repository and plugin: `airgap-anything`. Skill: `airgap-architect`. Marketplace: `airgap-anything-marketplace`. Tagline: "Design any system for air-gapped environments".
- **Python.** 3.11 or newer. Scripts import only standard-library modules and the local package `airgap_lib`. No `pip install`, no network modules, no network calls. Tests use `unittest`.
- **Test command,** always from the repository root: `python3 -m unittest discover -s tests -t . -v`. One module: `python3 -m unittest tests.test_NAME -v`.
- **The skill is self-contained.** Everything an installed skill needs lives under `skills/airgap-architect/`.
- **Nothing from memory (§6.3, principle 4).** No catalog value, version, image reference, license, telemetry setting, GPU figure or decision-table evidence is written from the implementing agent's memory. Each one has a URL that was opened while writing it, or a field note; otherwise it is labeled `estimate` with the basis in `notes`. Tasks 14 to 19 and 22 are research tasks for this reason. Do not shortcut them, and do not "improve" a value you believe you know.
- **Evidence labels:** `field`, `docs`, `estimate`. Weakest to strongest: `estimate`, `docs`, `field`.
- **Tiers:** `T1`, `T2`, `T3`. **Layers,** exact IDs in this order: `llm-serving`, `llm-gateway`, `ui`, `identity`, `observability`, `orchestration`, `state`, `registry`.
- **Exit codes:** 0 success; 1 lint errors; 2 missing or invalid answers, unreadable `blueprint.json`, or an unknown component; 3 environment problem (Python older than 3.11, unreadable catalog).
- **Finding codes:** blueprint lint errors `E1` to `E11` and warnings `W1` to `W3` (§12), plus note `N1`, which reports an override (§8.2). Catalog checks: `C1` schema, `C2` identity, `C3` references, `C4` evidence policy. Only errors make lint exit with 1.
- **Fixed strings.** Section marker: `<!-- airgap:section NAME -->`, with NAME one of `context`, `tier`, `architecture`, `decisions`, `sizing`, `transfer`, `data-flow`, `operations`, `verification`, `out-of-scope` (in this order), plus `isolation-design`. Agent block markers: `<!-- airgap-architect:start -->` and `<!-- airgap-architect:end -->`.
- **Paths in a target project:** `docs/airgap/blueprint.json`, `docs/airgap/transfer-manifest.md`, and the blueprint at `docs/superpowers/specs/<date>-<project>-airgap-blueprint-design.md` with superpowers, otherwise `docs/airgap/blueprint.md`.
- **Language and license:** repository content in English; MIT.
- **Brand assets are a separate workstream.** No task in this plan creates or modifies anything under `design/` or `assets/`.
- **Files that may already exist.** The handoff pull request adds `.gitignore`, `README.md` (a design-phase page), `CLAUDE.md`, `docs/HANDOFF.md`, `assets/brand/` and `design/brand/`. Task 2 extends `.gitignore`, Task 26 replaces the text of `README.md` and keeps its images, and no task touches the others. Every task also works when these files are absent.
- **Git.** One commit per task. Stage the listed files by path; never `git add -A`, `git add .` or `git commit -a`. End commit messages with the attribution trailer your session prescribes. Do not push and do not create a GitHub repository; both need the owner's explicit go-ahead.
- **When blocked.** If a step cannot be done as written (a source cannot be found, a command fails for a reason the step does not cover), stop and report. Do not invent a value to get past it.

## File Structure

```
airgap-anything/
├── .gitignore                                   Task 2 (extended if it exists)
├── LICENSE                                      Task 2
├── README.md                                    Task 26 (replaces the design-phase page)
├── CONTRIBUTING.md                              Task 13
├── .claude-plugin/
│   ├── plugin.json                              Task 25
│   └── marketplace.json                         Task 25
├── .github/workflows/ci.yml                     Task 27
├── docs/packaging-facts.md                      Task 1
├── skills/airgap-architect/
│   ├── SKILL.md                                 Task 23
│   ├── references/
│   │   ├── interview.md                         Task 21
│   │   ├── tiers.md                             Task 21
│   │   ├── sizing.md                            Task 21
│   │   ├── blueprint-template.md                Task 21
│   │   ├── agents-snippet.md                    Task 21
│   │   └── layers/
│   │       ├── llm-serving.md                   Task 22
│   │       ├── llm-gateway.md                   Task 22
│   │       └── supporting-defaults.md           Task 22
│   ├── catalog/
│   │   ├── rules.toml                           Task 3 (evidence review in Task 19)
│   │   ├── gpus.toml                            Task 4 (rows in Task 19)
│   │   └── components/*.toml                    Tasks 14 to 18, sixteen files
│   └── scripts/
│       ├── tier.py  size.py  manifest.py  lint.py    Task 11
│       └── airgap_lib/
│           ├── __init__.py     Python version guard                  Task 2
│           ├── constants.py    names shared by every module          Task 2
│           ├── findings.py     Finding and report formats            Task 2
│           ├── evidence.py     the evidence policy                   Task 2
│           ├── rules.py        rules.toml access and validation      Task 3
│           ├── catalog.py      catalog loading and validation        Task 4
│           ├── answers.py      question table, "unknown" handling    Task 5
│           ├── tiering.py      base tier, floors, requirements       Task 6
│           ├── sizing.py       concurrency, memory, totals           Task 7
│           ├── blueprint.py    blueprint.json I/O, schema, digest    Task 8
│           ├── transfer.py     transfer manifest                     Task 9
│           ├── checks.py       lint rules E1-E11, W1-W3, N1          Task 10
│           └── cli.py          argument parsing and exit codes       Task 11
├── tests/
│   ├── __init__.py             path setup                            Task 2
│   ├── support.py              synthetic catalog and answers         Task 4
│   ├── projects.py             synthetic complete projects           Task 10
│   └── test_*.py               one file per module                   Tasks 2 to 12, 19 to 23, 25, 26
└── evals/
    ├── README.md               eval protocol                         Task 20
    ├── score.py                scores decisions against expectations Task 20
    ├── scenarios/{lab,department,enterprise}/                        Task 12
    └── results/                                                      Tasks 20 and 24
```

Module boundaries: each `airgap_lib` module has one job and depends only on modules above it in the list. `checks.py` is the only module that uses all of them. The four scripts are thin: parse arguments, call the library, write a file, print a summary.

Phases:

| Phase | Tasks | Nature |
|---|---|---|
| 0. Facts | 1 | Verify packaging facts against current documentation |
| 1. Deterministic core | 2 to 12 | Test-first Python, complete code below |
| 2. Catalog content | 13 to 19 | Research with recorded sources |
| 3. The skill | 20 to 24 | `superpowers:writing-skills`: baseline first, then documents, then runs |
| 4. Packaging | 25 to 28 | Manifests, README, CI, final verification |

---

## Phase 0: Facts

### Task 1: Verify packaging facts against current documentation

Nothing about plugin manifests, skill discovery or frontmatter limits is taken from memory. This task writes those facts down once, with sources, and later tasks read them.

**Files:**
- Create: `docs/packaging-facts.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `docs/packaging-facts.md` with a `## Facts` section answering Q1 to Q7 and a `## Deviations` section. Task 21 and Task 23 read Q5 and Q7. Task 25 reads Q1 to Q4. Task 26 reads Q3 and Q6.

- [ ] **Step 1: Read a working plugin on disk**

Run:

```bash
REF=~/.claude/plugins/cache/superpowers-dev/superpowers/6.3.0
cat "$REF/.claude-plugin/plugin.json" "$REF/.claude-plugin/marketplace.json"
head -5 "$REF/skills/writing-plans/SKILL.md"
ls "$REF/skills"
```

Expected: two JSON objects, a frontmatter block with `name` and `description`, and a list of skill folders. If that directory does not exist, run `ls ~/.claude/plugins/cache/*/*/` and use any installed plugin that has both `.claude-plugin/plugin.json` and a `skills/` folder. If there is none, note "no reference plugin on disk" in the file and continue.

- [ ] **Step 2: Open the current documentation**

Open each source and keep the final URL of every page you read.

1. Claude Code plugin documentation: the plugin manifest reference and the plugin marketplace page. If a `claude-code-guide` agent is available, ask it: "Give me the current documentation URLs and the exact required and optional fields for `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, the commands to add a GitHub-hosted marketplace and install a plugin from it, where Claude Code looks for skills inside a plugin, and how a skill learns its own base directory at run time." Otherwise search the web for `Claude Code plugins reference plugin.json` and `Claude Code plugin marketplaces marketplace.json` and open the official pages.
2. The Agent Skills specification: `https://agentskills.io/specification`.
3. The `skills` command-line tool:

```bash
gh api repos/vercel-labs/skills/readme -H "Accept: application/vnd.github.raw" | head -200
```

- [ ] **Step 3: Write `docs/packaging-facts.md`**

Use this structure. Replace each line in capitals with what the source says, in your own words, followed by the URL.

```markdown
# Packaging facts

Checked on DATE. Every answer names the page it came from.

## Facts

### Q1. `.claude-plugin/plugin.json`
REQUIRED FIELDS. OPTIONAL FIELDS. Source: URL

### Q2. `.claude-plugin/marketplace.json`
REQUIRED FIELDS. HOW A REPOSITORY THAT IS ITSELF THE PLUGIN WRITES `source`. Source: URL

### Q3. Install commands
THE EXACT COMMAND TO ADD A GITHUB-HOSTED MARKETPLACE. THE EXACT COMMAND TO INSTALL A PLUGIN FROM IT. WHERE THE NAME AFTER `@` COMES FROM. Source: URL

### Q4. Skills inside a plugin
THE FOLDER AND FILE NAMES CLAUDE CODE LOOKS FOR. Source: URL

### Q5. Agent Skills frontmatter
REQUIRED FIELDS. LIMITS AND ALLOWED CHARACTERS FOR `name`. WHETHER `name` MUST EQUAL THE FOLDER NAME. LIMIT FOR `description`. OPTIONAL FIELDS. Source: URL

### Q6. `npx skills add`
WHICH FOLDERS IT SEARCHES. WHETHER IT COPIES THE WHOLE SKILL FOLDER, INCLUDING `scripts/` AND `catalog/`. HOW ONE SKILL IS SELECTED. Source: URL

### Q7. A skill's own files at run time
HOW AN AGENT LEARNS THE SKILL'S BASE DIRECTORY IN CLAUDE CODE. WHAT THE AGENT SKILLS SPECIFICATION SAYS ABOUT RELATIVE PATHS FOR OTHER AGENTS. Source: URL

## Deviations

ONE LINE PER FACT THAT CONTRADICTS THE PLAN OR THE SPEC, OR "None."
```

Compare the facts with these values, which the plan and the spec assume, and list every difference under `## Deviations` together with the value to use instead:

| Assumed | Where it is used |
|---|---|
| Layout `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `skills/airgap-architect/SKILL.md` | §6.1, Tasks 23 and 25 |
| `"source": "./"` for a plugin at the repository root | Task 25 |
| `/plugin marketplace add OWNER/airgap-anything` then `/plugin install airgap-anything@airgap-anything-marketplace` | §18, Task 26 |
| `npx skills add OWNER/airgap-anything` finds `skills/airgap-architect/` and copies the whole folder | §18, Task 26 |
| Frontmatter with exactly `name` and `description`; `name` at most 64 characters and equal to the folder name; `description` at most 1024 characters | Task 23 |
| Skill documents refer to bundled files as `<skill-dir>/scripts/...`, where `<skill-dir>` is the folder the skill was loaded from | Tasks 21 and 23 |

- [ ] **Step 4: Check the file**

Run:

```bash
grep -c '^### Q' docs/packaging-facts.md
grep -c 'https://' docs/packaging-facts.md
grep -n '^## Deviations' docs/packaging-facts.md
grep -nE 'REQUIRED FIELDS|OPTIONAL FIELDS|HOW A REPOSITORY|THE EXACT COMMAND|WHERE THE NAME|THE FOLDER AND FILE|LIMITS AND ALLOWED|WHICH FOLDERS|HOW AN AGENT|ONE LINE PER FACT|Source: URL|Checked on DATE' docs/packaging-facts.md
```

Expected: `7`; a number of 7 or more; one matching line; and no output from the last command (no stand-in text is left).

- [ ] **Step 5: Commit**

```bash
git add docs/packaging-facts.md
git commit -m "docs: record packaging facts with sources"
```

---

## Phase 1: Deterministic core

Every task in this phase follows the same rhythm: write the test file, watch it fail, write the module, watch the whole suite pass, commit. Write each file exactly as given. Do not add features, flags or abstractions the tests do not ask for.

### Task 2: Repository scaffold, Python guard and shared names

**Files:**
- Create or extend: `.gitignore`
- Create: `LICENSE`
- Create: `tests/__init__.py`
- Create: `tests/test_python_guard.py`
- Create: `tests/test_foundation.py`
- Create: `skills/airgap-architect/scripts/airgap_lib/__init__.py`
- Create: `skills/airgap-architect/scripts/airgap_lib/constants.py`
- Create: `skills/airgap-architect/scripts/airgap_lib/findings.py`
- Create: `skills/airgap-architect/scripts/airgap_lib/evidence.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `tests/__init__.py`: `REPO_ROOT`, `SKILL_DIR`, `SCRIPTS_DIR`, `CATALOG_DIR`, `SCENARIOS_DIR` (all `pathlib.Path`); importing `tests` puts `SCRIPTS_DIR` on `sys.path`.
  - `airgap_lib`: `check_python(version_info=None) -> str | None`, `MINIMUM_PYTHON = (3, 11)`, `EXIT_ENVIRONMENT = 3`. Importing the package on an older interpreter prints a message and exits with 3.
  - `airgap_lib.constants`: `SCHEMA_VERSION`, `TIERS`, `LAYERS`, `EVIDENCE_LEVELS`, `USAGE_TYPES`, `INTERACTIVE_USAGE`, `MODEL_ROLES`, `GENERATIVE_ROLES`, `SIZE_CLASSES`, `ESCALATOR_REQUIREMENTS`, `REQUIREMENTS`, `SECTION_MARKERS`, `ISOLATION_MARKER`, `AGENT_BLOCK_START`, `AGENT_BLOCK_END`, `UNKNOWN`; `tier_index(tier: str) -> int`, `max_tier(a: str, b: str) -> str`, `weakest(levels) -> str`, `section_marker(name: str) -> str`.
  - `airgap_lib.findings`: `SEVERITIES = ("error", "warning", "note")`; `Finding(code: str, message: str)` with property `severity` (`"warning"` for codes starting with `W`, `"note"` for `N`, otherwise `"error"`); `has_errors(findings) -> bool`; `format_text(findings) -> str`; `format_json(findings) -> str`.
  - `airgap_lib.evidence`: `evidence_problems(level, sources, verified_by, notes) -> list[str]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/__init__.py`:

```python
"""Test package. Importing it puts the skill's scripts on sys.path."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "airgap-architect"
SCRIPTS_DIR = SKILL_DIR / "scripts"
CATALOG_DIR = SKILL_DIR / "catalog"
SCENARIOS_DIR = REPO_ROOT / "evals" / "scenarios"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
```

Create `tests/test_python_guard.py`:

```python
import unittest

import tests  # noqa: F401  (puts the scripts directory on sys.path)
import airgap_lib


class PythonGuardTest(unittest.TestCase):
    def test_old_interpreter_gets_a_message_naming_both_versions(self):
        message = airgap_lib.check_python((3, 10, 12))
        self.assertIn("3.11", message)
        self.assertIn("3.10", message)

    def test_supported_interpreters_pass(self):
        self.assertIsNone(airgap_lib.check_python((3, 11, 0)))
        self.assertIsNone(airgap_lib.check_python((3, 13, 1)))


if __name__ == "__main__":
    unittest.main()
```

Create `tests/test_foundation.py`:

```python
import json
import unittest

import tests  # noqa: F401  (puts the scripts directory on sys.path)
from airgap_lib.constants import (
    LAYERS,
    SECTION_MARKERS,
    TIERS,
    max_tier,
    section_marker,
    tier_index,
    weakest,
)
from airgap_lib.evidence import evidence_problems
from airgap_lib.findings import Finding, format_json, format_text, has_errors


class ConstantsTest(unittest.TestCase):
    def test_tiers_and_layers_of_the_spec(self):
        self.assertEqual(TIERS, ("T1", "T2", "T3"))
        self.assertEqual(
            LAYERS,
            (
                "llm-serving", "llm-gateway", "ui", "identity",
                "observability", "orchestration", "state", "registry",
            ),
        )
        self.assertEqual(len(SECTION_MARKERS), 10)

    def test_tier_order(self):
        self.assertEqual(tier_index("T2"), 1)
        self.assertEqual(max_tier("T1", "T3"), "T3")
        self.assertEqual(max_tier("T2", "T2"), "T2")
        self.assertEqual(max_tier("T3", "T1"), "T3")

    def test_weakest_evidence_label(self):
        self.assertEqual(weakest(["docs", "field"]), "docs")
        self.assertEqual(weakest(["field", "estimate", "docs"]), "estimate")
        self.assertEqual(weakest(["field"]), "field")
        self.assertEqual(weakest([]), "field")

    def test_section_marker_text(self):
        self.assertEqual(section_marker("sizing"), "<!-- airgap:section sizing -->")


class EvidencePolicyTest(unittest.TestCase):
    def test_docs_needs_a_url(self):
        self.assertEqual(evidence_problems("docs", ["https://example.test/a"], "", ""), [])
        self.assertEqual(len(evidence_problems("docs", [], "", "")), 1)
        self.assertEqual(len(evidence_problems("docs", ["not a url"], "", "")), 1)
        self.assertEqual(len(evidence_problems("docs", None, "", "")), 1)

    def test_field_needs_a_verifier_and_notes(self):
        self.assertEqual(evidence_problems("field", [], "someone", "2x GPU, lab"), [])
        self.assertEqual(len(evidence_problems("field", [], "", "")), 2)

    def test_estimate_needs_notes(self):
        self.assertEqual(evidence_problems("estimate", [], "", "reasoned from X"), [])
        self.assertEqual(len(evidence_problems("estimate", [], "", "  ")), 1)

    def test_unknown_level(self):
        problems = evidence_problems("rumour", [], "", "")
        self.assertEqual(problems, ["evidence level must be one of estimate, docs, field"])


class FindingsTest(unittest.TestCase):
    def setUp(self):
        self.findings = [Finding("E3", "broken"), Finding("W1", "old"), Finding("C1", "bad")]

    def test_severity_comes_from_the_code_letter(self):
        self.assertEqual([f.severity for f in self.findings], ["error", "warning", "error"])

    def test_notes_are_a_third_severity(self):
        self.assertEqual(Finding("N1", "override").severity, "note")

    def test_has_errors(self):
        self.assertTrue(has_errors(self.findings))
        self.assertFalse(has_errors([Finding("W2", "unknown answer"), Finding("N1", "override")]))
        self.assertFalse(has_errors([]))

    def test_text_report(self):
        self.assertEqual(format_text([]), "OK: no findings")
        lines = format_text(self.findings).splitlines()
        self.assertEqual(lines[0], "E3 error: broken")
        self.assertEqual(lines[1], "W1 warning: old")
        self.assertEqual(lines[-1], "2 error(s), 1 warning(s), 0 note(s)")

    def test_json_report(self):
        report = json.loads(format_json(self.findings))
        self.assertEqual(report[1], {"code": "W1", "severity": "warning", "message": "old"})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: both test modules fail to import with `ModuleNotFoundError: No module named 'airgap_lib'`.

- [ ] **Step 3: Write the scaffold and the modules**

Make sure `.gitignore` ignores Python caches. The file may already exist with other entries; keep them.

```bash
touch .gitignore
for line in '__pycache__/' '*.pyc'; do
  grep -qxF -- "$line" .gitignore || echo "$line" >> .gitignore
done
grep -c -xF -e '__pycache__/' -e '*.pyc' .gitignore
```

Expected: `2`.

Create `LICENSE`:

```text
MIT License

Copyright (c) 2026 airgap-anything contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Create `skills/airgap-architect/scripts/airgap_lib/__init__.py`:

```python
"""Shared code for the airgap-architect scripts.

Importing this package checks the Python version first, so every script
fails with a clear message on an interpreter older than 3.11.
"""
import sys

MINIMUM_PYTHON = (3, 11)
EXIT_ENVIRONMENT = 3


def check_python(version_info=None):
    """Return an error message when the interpreter is too old, else None."""
    version = tuple((version_info or sys.version_info)[:2])
    if version < MINIMUM_PYTHON:
        return "airgap-architect needs Python %d.%d or newer (found %d.%d)." % (
            MINIMUM_PYTHON + version
        )
    return None


_message = check_python()
if _message:
    sys.stderr.write(_message + "\n")
    raise SystemExit(EXIT_ENVIRONMENT)
```

Create `skills/airgap-architect/scripts/airgap_lib/constants.py`:

```python
"""Names shared by every module."""
from __future__ import annotations

from collections.abc import Iterable

SCHEMA_VERSION = 1

TIERS = ("T1", "T2", "T3")
LAYERS = (
    "llm-serving",
    "llm-gateway",
    "ui",
    "identity",
    "observability",
    "orchestration",
    "state",
    "registry",
)
# Weakest first: a decision carries the weakest label among its inputs.
EVIDENCE_LEVELS = ("estimate", "docs", "field")

USAGE_TYPES = ("chat", "code_assistant", "rag", "batch")
INTERACTIVE_USAGE = ("chat", "code_assistant", "rag")
MODEL_ROLES = ("chat", "code", "embedding", "rerank")
GENERATIVE_ROLES = ("chat", "code")
SIZE_CLASSES = ("S", "M", "L", "XL")

# Requirements an escalator in rules.toml may switch on.
ESCALATOR_REQUIREMENTS = (
    "gateway_non_empty",
    "isolation_design_section",
    "two_engine_replicas",
)
REQUIREMENTS = ESCALATOR_REQUIREMENTS + ("kubernetes_risk_note",)

# Language-independent anchors in the blueprint Markdown file.
SECTION_MARKERS = (
    "context",
    "tier",
    "architecture",
    "decisions",
    "sizing",
    "transfer",
    "data-flow",
    "operations",
    "verification",
    "out-of-scope",
)
ISOLATION_MARKER = "isolation-design"
AGENT_BLOCK_START = "<!-- airgap-architect:start -->"
AGENT_BLOCK_END = "<!-- airgap-architect:end -->"

UNKNOWN = "unknown"


def tier_index(tier: str) -> int:
    return TIERS.index(tier)


def max_tier(a: str, b: str) -> str:
    return a if tier_index(a) >= tier_index(b) else b


def weakest(levels: Iterable[str]) -> str:
    """Weakest evidence label in `levels`; 'field' when `levels` is empty."""
    found = [EVIDENCE_LEVELS.index(level) for level in levels]
    return EVIDENCE_LEVELS[min(found)] if found else "field"


def section_marker(name: str) -> str:
    return f"<!-- airgap:section {name} -->"
```

Create `skills/airgap-architect/scripts/airgap_lib/findings.py`:

```python
"""Lint findings and how they are printed."""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass

# Report order. Only errors make lint fail.
SEVERITIES = ("error", "warning", "note")


@dataclass(frozen=True)
class Finding:
    code: str
    message: str

    @property
    def severity(self) -> str:
        return {"W": "warning", "N": "note"}.get(self.code[:1], "error")


def has_errors(findings: Iterable[Finding]) -> bool:
    return any(finding.severity == "error" for finding in findings)


def format_text(findings: list[Finding]) -> str:
    if not findings:
        return "OK: no findings"
    lines = [f"{f.code} {f.severity}: {f.message}" for f in findings]
    counts = {
        severity: sum(1 for f in findings if f.severity == severity)
        for severity in SEVERITIES
    }
    lines.append(
        f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['note']} note(s)"
    )
    return "\n".join(lines)


def format_json(findings: list[Finding]) -> str:
    return json.dumps(
        [
            {"code": f.code, "severity": f.severity, "message": f.message}
            for f in findings
        ],
        indent=2,
    )
```

Create `skills/airgap-architect/scripts/airgap_lib/evidence.py`:

```python
"""The evidence policy shared by rules, GPU rows and component entries."""
from __future__ import annotations

from .constants import EVIDENCE_LEVELS


def _has_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def evidence_problems(level, sources, verified_by, notes) -> list[str]:
    """Problems with one evidence record; empty when it follows the policy."""
    if level not in EVIDENCE_LEVELS:
        return ["evidence level must be one of " + ", ".join(EVIDENCE_LEVELS)]
    if level == "docs":
        urls_ok = (
            isinstance(sources, list)
            and bool(sources)
            and all(
                isinstance(url, str) and url.startswith(("http://", "https://"))
                for url in sources
            )
        )
        return [] if urls_ok else ["evidence 'docs' needs at least one URL in sources"]
    if level == "field":
        problems = []
        if not _has_text(verified_by):
            problems.append("evidence 'field' needs verified_by")
        if not _has_text(notes):
            problems.append("evidence 'field' needs notes with hardware and context")
        return problems
    if not _has_text(notes):
        return ["evidence 'estimate' needs notes stating the basis"]
    return []
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: `Ran 15 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
git add .gitignore LICENSE tests/__init__.py tests/test_python_guard.py tests/test_foundation.py \
  skills/airgap-architect/scripts/airgap_lib/__init__.py \
  skills/airgap-architect/scripts/airgap_lib/constants.py \
  skills/airgap-architect/scripts/airgap_lib/findings.py \
  skills/airgap-architect/scripts/airgap_lib/evidence.py
git commit -m "feat: add scaffold, Python version guard and shared names"
```

---

### Task 3: Rules file and loader

`rules.toml` holds every threshold and default (§8, §10). Its starting values come from the spec and are labeled `estimate`. The loader flattens the nested tables: a table that has a `value` key is a constant, and its ID is its path.

**Files:**
- Create: `tests/test_rules.py`
- Create: `skills/airgap-architect/catalog/rules.toml`
- Create: `skills/airgap-architect/scripts/airgap_lib/rules.py`

**Interfaces:**
- Consumes: `Finding` from `airgap_lib.findings`; `evidence_problems` from `airgap_lib.evidence`; `ESCALATOR_REQUIREMENTS`, `LAYERS`, `SCHEMA_VERSION`, `TIERS` from `airgap_lib.constants`; `CATALOG_DIR` from `tests`.
- Produces, in `airgap_lib.rules`:
  - `REQUIRED_CONSTANTS: tuple[str, ...]`, `BYTES_PREFIX = "sizing.bytes_per_param."`
  - `class Rules(data: dict)` with `has(key) -> bool`, `constant_keys() -> list[str]`, `entry(key) -> dict`, `value(key)`, `use(key, sink=None)` (returns the value and appends `{"id", "value", "evidence", "note"}` to `sink` once per key), `precisions() -> tuple[str, ...]`, property `escalators -> list[dict]`, `default_answer(question_id) -> dict | None`
  - `load_rules(path) -> Rules`
  - `validate_rules(rules) -> list[Finding]`
- Constant IDs later tasks read: `tiers.t1_max_users`, `tiers.t2_max_users`, `tiers.t1_max_departments`, `tiers.t2_max_departments`, `sizing.<usage>.active`, `sizing.<usage>.duty_low`, `sizing.<usage>.duty_high` for `chat`, `rag`, `code_assistant`, `sizing.bytes_per_param.<precision>`, `sizing.gpu_memory_utilization`, `sizing.overhead`, `sizing.gpu_group_sizes`, `sizing.default_precision`, `sizing.default_context_tokens`, `sizing.default_output_tokens`, `sizing.default_kv_dtype`, `sizing.size_class.<S|M|L|XL>`, `sizing.gpus_per_server`, `sizing.power_system_factor`, `sizing.ha_min_replicas`, `lint.freshness_days`, `defaults.<question ID>`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_rules.py`:

```python
import unittest

from tests import CATALOG_DIR
from airgap_lib.rules import REQUIRED_CONSTANTS, Rules, load_rules, validate_rules


def codes(findings):
    return [finding.code for finding in findings]


class ShippedRulesTest(unittest.TestCase):
    def setUp(self):
        self.rules = load_rules(CATALOG_DIR / "rules.toml")

    def test_shipped_rules_are_valid(self):
        self.assertEqual(validate_rules(self.rules), [])

    def test_every_required_constant_is_present(self):
        for key in REQUIRED_CONSTANTS:
            self.assertTrue(self.rules.has(key), key)

    def test_spec_thresholds(self):
        self.assertEqual(self.rules.value("tiers.t1_max_users"), 25)
        self.assertEqual(self.rules.value("tiers.t2_max_users"), 300)
        self.assertEqual(self.rules.value("tiers.t1_max_departments"), 1)
        self.assertEqual(self.rules.value("tiers.t2_max_departments"), 5)

    def test_precisions_come_from_bytes_per_param(self):
        self.assertEqual(
            set(self.rules.precisions()), {"fp32", "bf16", "fp16", "fp8", "int8", "int4"}
        )

    def test_use_records_a_constant_once(self):
        sink = []
        self.assertEqual(self.rules.use("sizing.overhead", sink), 0.10)
        self.rules.use("sizing.overhead", sink)
        self.assertEqual(len(sink), 1)
        self.assertEqual(set(sink[0]), {"id", "value", "evidence", "note"})
        self.assertEqual(sink[0]["id"], "sizing.overhead")
        self.assertTrue(sink[0]["note"])

    def test_default_answer(self):
        self.assertEqual(self.rules.default_answer("org.audit_required")["value"], True)
        self.assertEqual(self.rules.default_answer("workload.usage")["value"], {"chat": 1.0})
        self.assertIsNone(self.rules.default_answer("org.users_total"))

    def test_four_escalators(self):
        self.assertEqual(
            [escalator["id"] for escalator in self.rules.escalators],
            ["audit", "isolation-per-department", "isolation-multi-level", "no-downtime"],
        )


class RulesValidationTest(unittest.TestCase):
    def test_missing_constants_are_c1(self):
        findings = validate_rules(Rules({"schema_version": 1}))
        self.assertIn("C1", codes(findings))
        self.assertTrue(any("tiers.t1_max_users" in f.message for f in findings))

    def test_estimate_without_notes_is_c4(self):
        rules = Rules({"schema_version": 1, "x": {"y": {"value": 1, "evidence": "estimate"}}})
        messages = [f.message for f in validate_rules(rules) if f.code == "C4"]
        self.assertTrue(any("x.y" in message for message in messages))

    def test_docs_without_sources_is_c4(self):
        rules = Rules({"schema_version": 1, "x": {"value": 1, "evidence": "docs", "notes": "n"}})
        self.assertIn("C4", codes(validate_rules(rules)))

    def test_escalator_with_unknown_layer_is_c1(self):
        rules = Rules(
            {
                "schema_version": 1,
                "escalators": [
                    {
                        "answer": "org.audit_required",
                        "equals": True,
                        "floors": {"no-such-layer": "T2"},
                        "requires": [],
                        "reason": "r",
                        "evidence": "estimate",
                        "notes": "n",
                    }
                ],
            }
        )
        self.assertTrue(
            any(f.code == "C1" and "escalators[0]" in f.message for f in validate_rules(rules))
        )

    def test_escalator_with_unknown_requirement_is_c1(self):
        rules = Rules(
            {
                "schema_version": 1,
                "escalators": [
                    {
                        "answer": "org.audit_required",
                        "equals": True,
                        "floors": {},
                        "requires": ["no_such_requirement"],
                        "reason": "r",
                        "evidence": "estimate",
                        "notes": "n",
                    }
                ],
            }
        )
        self.assertTrue(
            any(f.code == "C1" and "requires" in f.message for f in validate_rules(rules))
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_rules -v`

Expected: `ModuleNotFoundError: No module named 'airgap_lib.rules'`.

- [ ] **Step 3: Write the rules file and the loader**

Create `skills/airgap-architect/catalog/rules.toml`. The values are the spec's starting content plus the defaults listed under "Open questions" at the end of this plan. Do not change a value.

```toml
# Thresholds, escalators and defaults for airgap-architect.
#
# Every constant is a table with `value`, `evidence` and `notes`.
#   evidence = "field"    also needs `verified_by`
#   evidence = "docs"     also needs `sources` (list of URLs)
#   evidence = "estimate" needs `notes` stating the basis
# A constant's ID is its table path, for example `tiers.t1_max_users`.

schema_version = 1

# --- Base tier (design spec section 8.1) ------------------------------------

[tiers.t1_max_users]
value = 25
evidence = "estimate"
notes = "Starting threshold from the design spec; replace with field data."

[tiers.t2_max_users]
value = 300
evidence = "estimate"
notes = "Starting threshold from the design spec; replace with field data."

[tiers.t1_max_departments]
value = 1
evidence = "estimate"
notes = "Starting threshold from the design spec; replace with field data."

[tiers.t2_max_departments]
value = 5
evidence = "estimate"
notes = "Starting threshold from the design spec; replace with field data."

# --- Escalators (design spec section 8.2) -----------------------------------
# An escalator applies when answers[answer] == equals. It raises the listed
# floors to at least the given tier and switches the listed requirements on.

[[escalators]]
id = "audit"
answer = "org.audit_required"
equals = true
floors = { "llm-gateway" = "T2" }
requires = ["gateway_non_empty"]
reason = "org.audit_required sets the llm-gateway floor to at least T2 and requires a gateway"
evidence = "estimate"
notes = "Design spec section 8.2."

[[escalators]]
id = "isolation-per-department"
answer = "org.isolation"
equals = "per_department"
floors = { "llm-gateway" = "T2", "identity" = "T2" }
requires = ["gateway_non_empty"]
reason = "org.isolation = per_department sets the llm-gateway and identity floors to at least T2 and requires a gateway"
evidence = "estimate"
notes = "Design spec section 8.2."

[[escalators]]
id = "isolation-multi-level"
answer = "org.isolation"
equals = "multi_level"
floors = { "llm-gateway" = "T3", "identity" = "T3" }
requires = ["gateway_non_empty", "isolation_design_section"]
reason = "org.isolation = multi_level sets the llm-gateway and identity floors to T3, requires a gateway and an Isolation design subsection"
evidence = "estimate"
notes = "Design spec section 8.2. The gateway requirement follows from section 9.2 (isolation other than none)."

[[escalators]]
id = "no-downtime"
answer = "org.downtime_tolerance"
equals = "none"
floors = { "orchestration" = "T3", "llm-serving" = "T3", "state" = "T3" }
requires = ["two_engine_replicas"]
reason = "org.downtime_tolerance = none sets the orchestration, llm-serving and state floors to T3 and requires at least two engine replicas"
evidence = "estimate"
notes = "Design spec section 8.2."

# --- Concurrency (design spec section 10.1) ---------------------------------

[sizing.chat.active]
value = 0.20
evidence = "estimate"
notes = "Share of users active in the peak hour. Starting default from the design spec."

[sizing.chat.duty_low]
value = 0.15
evidence = "estimate"
notes = "Share of time an active user has a request in flight, low end. Starting default from the design spec."

[sizing.chat.duty_high]
value = 0.30
evidence = "estimate"
notes = "Share of time an active user has a request in flight, high end. Starting default from the design spec."

[sizing.rag.active]
value = 0.20
evidence = "estimate"
notes = "Share of users active in the peak hour. Starting default from the design spec."

[sizing.rag.duty_low]
value = 0.15
evidence = "estimate"
notes = "Share of time an active user has a request in flight, low end. Starting default from the design spec."

[sizing.rag.duty_high]
value = 0.30
evidence = "estimate"
notes = "Share of time an active user has a request in flight, high end. Starting default from the design spec."

[sizing.code_assistant.active]
value = 0.30
evidence = "estimate"
notes = "Share of users active in the peak hour. Starting default from the design spec."

[sizing.code_assistant.duty_low]
value = 0.70
evidence = "estimate"
notes = "Share of time an active user has a request in flight, low end. Starting default from the design spec."

[sizing.code_assistant.duty_high]
value = 1.00
evidence = "estimate"
notes = "Share of time an active user has a request in flight, high end. Starting default from the design spec."

# --- Memory (design spec section 10.2) --------------------------------------

[sizing.bytes_per_param.fp32]
value = 4
evidence = "estimate"
notes = "Arithmetic: 32 bits per parameter."

[sizing.bytes_per_param.bf16]
value = 2
evidence = "estimate"
notes = "Arithmetic: 16 bits per parameter."

[sizing.bytes_per_param.fp16]
value = 2
evidence = "estimate"
notes = "Arithmetic: 16 bits per parameter."

[sizing.bytes_per_param.fp8]
value = 1
evidence = "estimate"
notes = "Arithmetic: 8 bits per parameter."

[sizing.bytes_per_param.int8]
value = 1
evidence = "estimate"
notes = "Arithmetic: 8 bits per parameter."

[sizing.bytes_per_param.int4]
value = 0.5
evidence = "estimate"
notes = "Arithmetic: 4 bits per parameter; ignores quantization metadata."

[sizing.gpu_memory_utilization]
value = 0.90
evidence = "estimate"
notes = "Share of GPU memory the engine may use. Starting default from the design spec."

[sizing.overhead]
value = 0.10
evidence = "estimate"
notes = "Extra memory on top of the weights. Starting default from the design spec."

[sizing.gpu_group_sizes]
value = [1, 2, 4, 8]
evidence = "estimate"
notes = "GPU counts one replica may span. Starting default from the design spec."

[sizing.default_precision]
value = "bf16"
evidence = "estimate"
notes = "Used when a model is given as a size class without a precision. Unquantized, so sizing errs on the large side."

[sizing.default_context_tokens]
value = 8192
evidence = "estimate"
notes = "Used when a model entry has no context_tokens. Chosen by the implementation plan, not measured."

[sizing.default_output_tokens]
value = 1024
evidence = "estimate"
notes = "Tokens generated per request for KV-cache sizing. Chosen by the implementation plan, not measured."

[sizing.default_kv_dtype]
value = "fp16"
evidence = "estimate"
notes = "KV-cache element type when the architecture numbers do not state one."

[sizing.size_class.S]
value = 8
evidence = "estimate"
notes = "Representative parameter count in billions for class S (up to 15B)."

[sizing.size_class.M]
value = 32
evidence = "estimate"
notes = "Representative parameter count in billions for class M (16B to 80B)."

[sizing.size_class.L]
value = 120
evidence = "estimate"
notes = "Representative parameter count in billions for class L (81B to 300B)."

[sizing.size_class.XL]
value = 671
evidence = "estimate"
notes = "Representative parameter count in billions for class XL (above 300B)."

# --- Totals (design spec section 10.3) --------------------------------------

[sizing.gpus_per_server]
value = 8
evidence = "estimate"
notes = "GPUs per server chassis. Starting default from the design spec."

[sizing.power_system_factor]
value = 1.8
evidence = "estimate"
notes = "Whole-system power divided by GPU power. Starting default from the design spec."

[sizing.ha_min_replicas]
value = 2
evidence = "estimate"
notes = "Minimum engine replicas when no downtime is accepted. Design spec section 10.2."

# --- Lint --------------------------------------------------------------------

[lint.freshness_days]
value = 180
evidence = "estimate"
notes = "Catalog entries older than this trigger warning W1. Design spec section 11.3."

# --- Defaults for answers given as "unknown" (design spec section 7) ---------
# No default exists for org.users_total, org.departments, workload.models and
# hardware.gpus: those must be answered.

[defaults.org.isolation]
value = "per_department"
evidence = "estimate"
notes = "Unknown privacy rules are treated as the stricter common case."

[defaults.org.audit_required]
value = true
evidence = "estimate"
notes = "Unknown audit rules are treated as required."

[defaults.org.downtime_tolerance]
value = "planned_only"
evidence = "estimate"
notes = "Middle option."

[defaults.org.ops_capacity]
value = "part_time_one"
evidence = "estimate"
notes = "Smallest operating capacity, so the design stays simple."

[defaults.org.kubernetes_experience]
value = false
evidence = "estimate"
notes = "Kubernetes experience is not assumed."

[defaults.workload.usage]
value = { chat = 1.0 }
evidence = "estimate"
notes = "Chat only."

[defaults.existing.identity]
value = "none"
evidence = "estimate"
notes = "No existing infrastructure is assumed."

[defaults.existing.api_gateway]
value = "none"
evidence = "estimate"
notes = "No existing infrastructure is assumed."

[defaults.existing.kubernetes]
value = "none"
evidence = "estimate"
notes = "No existing infrastructure is assumed."

[defaults.transfer.channel]
value = "removable_media"
evidence = "estimate"
notes = "The most restrictive common transfer channel."
```

Create `skills/airgap-architect/scripts/airgap_lib/rules.py`:

```python
"""rules.toml: thresholds, escalators, sizing defaults and answer defaults."""
from __future__ import annotations

import tomllib
from pathlib import Path

from .constants import ESCALATOR_REQUIREMENTS, LAYERS, SCHEMA_VERSION, TIERS
from .evidence import evidence_problems
from .findings import Finding

REQUIRED_CONSTANTS = (
    "tiers.t1_max_users",
    "tiers.t2_max_users",
    "tiers.t1_max_departments",
    "tiers.t2_max_departments",
    "sizing.chat.active",
    "sizing.chat.duty_low",
    "sizing.chat.duty_high",
    "sizing.rag.active",
    "sizing.rag.duty_low",
    "sizing.rag.duty_high",
    "sizing.code_assistant.active",
    "sizing.code_assistant.duty_low",
    "sizing.code_assistant.duty_high",
    "sizing.gpu_memory_utilization",
    "sizing.overhead",
    "sizing.gpu_group_sizes",
    "sizing.default_precision",
    "sizing.default_context_tokens",
    "sizing.default_output_tokens",
    "sizing.default_kv_dtype",
    "sizing.size_class.S",
    "sizing.size_class.M",
    "sizing.size_class.L",
    "sizing.size_class.XL",
    "sizing.gpus_per_server",
    "sizing.power_system_factor",
    "sizing.ha_min_replicas",
    "lint.freshness_days",
)
BYTES_PREFIX = "sizing.bytes_per_param."
_RESERVED_TOP_LEVEL = ("schema_version", "escalators")


class Rules:
    """Read access to rules.toml. A constant's ID is its table path."""

    def __init__(self, data: dict):
        self.data = data
        self._constants: dict[str, dict] = {}
        self._collect("", data)

    def _collect(self, prefix: str, table: dict) -> None:
        for key, value in table.items():
            if not prefix and key in _RESERVED_TOP_LEVEL:
                continue
            if not isinstance(value, dict):
                continue
            path = f"{prefix}.{key}" if prefix else key
            if "value" in value:
                self._constants[path] = value
            else:
                self._collect(path, value)

    def has(self, key: str) -> bool:
        return key in self._constants

    def constant_keys(self) -> list[str]:
        return sorted(self._constants)

    def entry(self, key: str) -> dict:
        return self._constants[key]

    def value(self, key: str):
        return self._constants[key]["value"]

    def use(self, key: str, sink: list[dict] | None = None):
        """Return a constant's value and record it once in `sink`."""
        entry = self._constants[key]
        if sink is not None and not any(item["id"] == key for item in sink):
            sink.append(
                {
                    "id": key,
                    "value": entry["value"],
                    "evidence": entry.get("evidence", "estimate"),
                    "note": entry.get("notes", ""),
                }
            )
        return entry["value"]

    def precisions(self) -> tuple[str, ...]:
        return tuple(
            key[len(BYTES_PREFIX):]
            for key in self.constant_keys()
            if key.startswith(BYTES_PREFIX)
        )

    @property
    def escalators(self) -> list[dict]:
        return list(self.data.get("escalators", []))

    def default_answer(self, question_id: str) -> dict | None:
        """The default entry for an answer given as 'unknown', or None."""
        return self._constants.get(f"defaults.{question_id}")


def load_rules(path: Path) -> Rules:
    with Path(path).open("rb") as handle:
        return Rules(tomllib.load(handle))


def validate_rules(rules: Rules) -> list[Finding]:
    findings: list[Finding] = []
    if rules.data.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            Finding("C1", f"rules.toml: schema_version must be {SCHEMA_VERSION}")
        )
    for key in REQUIRED_CONSTANTS:
        if not rules.has(key):
            findings.append(Finding("C1", f"rules.toml: missing constant '{key}'"))
    precisions = rules.precisions()
    if not precisions:
        findings.append(
            Finding("C1", f"rules.toml: no '{BYTES_PREFIX}<precision>' constants")
        )
    for key in ("sizing.default_precision", "sizing.default_kv_dtype"):
        if rules.has(key) and rules.value(key) not in precisions:
            findings.append(
                Finding("C1", f"rules.toml: {key} must name a known precision")
            )
    for key in rules.constant_keys():
        entry = rules.entry(key)
        for problem in evidence_problems(
            entry.get("evidence"),
            entry.get("sources"),
            entry.get("verified_by"),
            entry.get("notes"),
        ):
            findings.append(Finding("C4", f"rules.toml: {key}: {problem}"))
    for index, escalator in enumerate(rules.escalators):
        where = f"rules.toml: escalators[{index}]"
        if not isinstance(escalator.get("answer"), str) or "equals" not in escalator:
            findings.append(Finding("C1", f"{where}: needs 'answer' and 'equals'"))
        if not isinstance(escalator.get("reason"), str) or not escalator["reason"]:
            findings.append(Finding("C1", f"{where}: needs a 'reason'"))
        floors = escalator.get("floors", {})
        if not isinstance(floors, dict) or any(
            layer not in LAYERS or tier not in TIERS for layer, tier in floors.items()
        ):
            findings.append(
                Finding("C1", f"{where}: floors must map known layers to T1, T2 or T3")
            )
        requires = escalator.get("requires", [])
        if not isinstance(requires, list) or any(
            name not in ESCALATOR_REQUIREMENTS for name in requires
        ):
            findings.append(
                Finding(
                    "C1",
                    f"{where}: requires must be a list drawn from "
                    + ", ".join(ESCALATOR_REQUIREMENTS),
                )
            )
        for problem in evidence_problems(
            escalator.get("evidence"),
            escalator.get("sources"),
            escalator.get("verified_by"),
            escalator.get("notes"),
        ):
            findings.append(Finding("C4", f"{where}: {problem}"))
    return findings
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: `Ran 27 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_rules.py skills/airgap-architect/catalog/rules.toml \
  skills/airgap-architect/scripts/airgap_lib/rules.py
git commit -m "feat: add rules.toml and its loader"
```

---

### Task 4: Catalog loader and validation

The loader reads `rules.toml`, `gpus.toml` and `components/*.toml`. Validation implements the catalog checks C1 to C4 and the freshness warning W1 (§11). The tests in this phase build synthetic catalogs in temporary directories and name no real product.

**Files:**
- Create: `tests/support.py`
- Create: `tests/test_catalog.py`
- Create: `tests/test_real_catalog.py`
- Create: `skills/airgap-architect/catalog/gpus.toml`
- Create: `skills/airgap-architect/scripts/airgap_lib/catalog.py`

**Interfaces:**
- Consumes: `Rules`, `load_rules`, `validate_rules` from `airgap_lib.rules`; `Finding`; `evidence_problems`; `LAYERS`, `SCHEMA_VERSION`, `TIERS`.
- Produces, in `airgap_lib.catalog`:
  - `@dataclass(frozen=True) class Catalog` with fields `rules: Rules`, `gpus: list[dict]`, `components: dict[str, dict]` and method `gpu(model: str) -> dict | None`
  - `default_catalog_dir() -> Path` (the `catalog/` folder next to `scripts/`)
  - `load_gpus(path) -> list[dict]`
  - `load_components(directory) -> tuple[dict[str, dict], list[Finding]]`
  - `load_catalog(root) -> tuple[Catalog, list[Finding]]`
  - `validate_component(entry: dict, known_ids: set[str]) -> list[Finding]`
  - `validate_gpus(gpus) -> list[Finding]`
  - `is_stale(last_verified, today: date, freshness_days: int) -> bool`
  - `validate_catalog(catalog, today: date) -> list[Finding]`
- Produces, in `tests/support.py`: `TODAY`, `GPUS_TOML`, `component(component_id, layer, **overrides) -> dict`, `fixture_components() -> list[dict]`, `component_toml(entry) -> str`, `make_catalog(root, components=None, gpus_toml=GPUS_TOML, rules_toml=None) -> Path`, `load_fixture_catalog(root, components=None) -> Catalog`, `base_answers(**overrides) -> dict`, `base_decisions() -> list[dict]`.
- The synthetic catalog has nine components: `alpha-engine` and `beta-engine` (`llm-serving`; `beta-engine` allows only T1 and T2 and is labeled `estimate`), `gamma-gateway` (`llm-gateway`, requires `delta-db`), `delta-db` (`state`), `epsilon-ui` (`ui`), `zeta-idp` (`identity`), `eta-metrics` (`observability`), `theta-orch` (`orchestration`), `iota-registry` (`registry`). All have version `1.2.3`. The synthetic GPU is `Test GPU 141` (alias `TG141`, 141 GB, 700 W).

- [ ] **Step 1: Write the failing tests**

Create `tests/support.py`:

```python
"""Builders for synthetic catalogs and answers. No real product is named here."""
from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

from airgap_lib.catalog import Catalog, load_catalog
from airgap_lib.constants import LAYERS
from tests import CATALOG_DIR

TODAY = date(2026, 11, 20)

GPUS_TOML = """schema_version = 1

[[gpu]]
model = "Test GPU 141"
aliases = ["TG141"]
vram_gb = 141
tdp_w = 700
evidence = "estimate"
notes = "Synthetic row for tests."
last_verified = 2026-11-20
"""


def component(component_id: str, layer: str, **overrides) -> dict:
    """A valid synthetic component entry. Dict overrides merge into sub-tables."""
    entry = {
        "schema_version": 1,
        "id": component_id,
        "name": component_id.title(),
        "layer": layer,
        "summary": f"Synthetic {layer} component for tests.",
        "tiers": ["T1", "T2", "T3"],
        "requires": [],
        "version": "1.2.3",
        "license": "MIT",
        "last_verified": TODAY,
        "evidence": {
            "level": "docs",
            "sources": ["https://example.test/docs"],
            "verified_by": "",
            "notes": "",
        },
        "airgap": {
            "images": [
                {"ref": f"registry.example.test/synthetic/{component_id}:1.2.3", "digest": ""}
            ],
            "packages": [],
            "runtime_downloads": [],
            "telemetry": [],
            "license_server": False,
            "notes": "",
        },
        "choose": {
            "when": ["always in tests"],
            "avoid_when": [],
            "alternatives": [],
            "caveats": [],
        },
        "deeper_skills": [],
    }
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(entry.get(key), dict):
            entry[key] = {**entry[key], **value}
        else:
            entry[key] = value
    return entry


def fixture_components() -> list[dict]:
    return [
        component("alpha-engine", "llm-serving"),
        component(
            "beta-engine",
            "llm-serving",
            tiers=["T1", "T2"],
            evidence={"level": "estimate", "sources": [], "notes": "Synthetic estimate."},
        ),
        component("gamma-gateway", "llm-gateway", requires=["delta-db"]),
        component("delta-db", "state"),
        component("epsilon-ui", "ui"),
        component("zeta-idp", "identity"),
        component("eta-metrics", "observability"),
        component("theta-orch", "orchestration"),
        component("iota-registry", "registry"),
    ]


def _toml(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{key} = {_toml(item)}" for key, item in value.items()) + " }"
    raise TypeError(f"cannot write {type(value).__name__} as TOML")


def component_toml(entry: dict) -> str:
    """Serialize a component entry the way catalog files are written."""
    lines: list[str] = []
    tables = {key: value for key, value in entry.items() if isinstance(value, dict)}
    for key, value in entry.items():
        if key != "deeper_skills" and key not in tables:
            lines.append(f"{key} = {_toml(value)}")
    for name, table in tables.items():
        lines += ["", f"[{name}]"]
        lines += [f"{key} = {_toml(value)}" for key, value in table.items()]
    for row in entry.get("deeper_skills", []):
        lines += ["", "[[deeper_skills]]"]
        lines += [f"{key} = {_toml(value)}" for key, value in row.items()]
    return "\n".join(lines) + "\n"


def make_catalog(root: Path, components=None, gpus_toml: str = GPUS_TOML, rules_toml=None) -> Path:
    """Write a catalog directory. Rules default to the shipped rules.toml."""
    root = Path(root)
    (root / "components").mkdir(parents=True, exist_ok=True)
    if rules_toml is None:
        shutil.copy(CATALOG_DIR / "rules.toml", root / "rules.toml")
    else:
        (root / "rules.toml").write_text(rules_toml, encoding="utf-8")
    (root / "gpus.toml").write_text(gpus_toml, encoding="utf-8")
    for entry in fixture_components() if components is None else components:
        path = root / "components" / f"{entry['id']}.toml"
        path.write_text(component_toml(entry), encoding="utf-8")
    return root


def load_fixture_catalog(root: Path, components=None) -> Catalog:
    catalog, findings = load_catalog(make_catalog(root, components))
    assert not findings, findings
    return catalog


def base_answers(**overrides) -> dict:
    """Complete, valid answers for a 180-person, four-department organization."""
    answers = {
        "org.users_total": 180,
        "org.departments": 4,
        "org.isolation": "per_department",
        "org.audit_required": True,
        "org.downtime_tolerance": "planned_only",
        "org.ops_capacity": "small_team",
        "org.kubernetes_experience": False,
        "workload.usage": {"chat": 1.0},
        "workload.models": [
            {"name": "example-70b", "role": "chat", "params_b": 70, "precision": "fp8"}
        ],
        "hardware.gpus": [{"model": "TG141", "count": 8}],
        "existing.identity": "ad_ldap",
        "existing.api_gateway": "none",
        "existing.kubernetes": "none",
        "transfer.channel": "removable_media",
    }
    answers.update(overrides)
    return answers


def base_decisions() -> list[dict]:
    chosen = {
        "llm-serving": ["alpha-engine"],
        "llm-gateway": ["gamma-gateway"],
        "ui": ["epsilon-ui"],
        "identity": ["zeta-idp"],
        "observability": ["eta-metrics"],
        "orchestration": ["theta-orch"],
        "state": ["delta-db"],
        "registry": ["iota-registry"],
    }
    return [
        {
            "layer": layer,
            "components": list(chosen[layer]),
            "existing": [],
            "custom": [],
            "rationale": f"Synthetic rationale for {layer}.",
            "alternatives_considered": [],
            "evidence": "docs",
            "override": None,
        }
        for layer in LAYERS
    ]
```

Create `tests/test_catalog.py`:

```python
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tests import support
from airgap_lib.catalog import load_catalog, validate_catalog, validate_component


def codes(findings):
    return [finding.code for finding in findings]


class CatalogLoadingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_fixture_catalog_loads_and_validates(self):
        catalog, findings = load_catalog(support.make_catalog(self.root))
        self.assertEqual(findings, [])
        self.assertEqual(len(catalog.components), 9)
        self.assertEqual(validate_catalog(catalog, support.TODAY), [])

    def test_gpu_lookup_ignores_case_and_punctuation(self):
        catalog = support.load_fixture_catalog(self.root)
        self.assertEqual(catalog.gpu("tg-141")["vram_gb"], 141)
        self.assertEqual(catalog.gpu("TEST GPU 141")["tdp_w"], 700)
        self.assertIsNone(catalog.gpu("no such gpu"))

    def test_file_name_must_match_id(self):
        support.make_catalog(self.root)
        entry = support.component("mismatch", "ui")
        (self.root / "components" / "other-name.toml").write_text(
            support.component_toml(entry), encoding="utf-8"
        )
        catalog, findings = load_catalog(self.root)
        self.assertEqual(codes(findings), ["C2"])
        self.assertNotIn("mismatch", catalog.components)

    def test_unparsable_file_is_c2(self):
        support.make_catalog(self.root)
        (self.root / "components" / "broken.toml").write_text("id = = 1\n", encoding="utf-8")
        _, findings = load_catalog(self.root)
        self.assertEqual(codes(findings), ["C2"])

    def test_stale_entry_is_w1(self):
        old = support.component("epsilon-ui", "ui", last_verified=date(2026, 1, 1))
        components = [c for c in support.fixture_components() if c["id"] != "epsilon-ui"] + [old]
        catalog = support.load_fixture_catalog(self.root, components)
        findings = validate_catalog(catalog, support.TODAY)
        self.assertEqual(codes(findings), ["W1"])
        self.assertIn("epsilon-ui", findings[0].message)


class ComponentValidationTest(unittest.TestCase):
    def check(self, entry, known=("x",)):
        return validate_component(entry, set(known))

    def test_valid_component(self):
        self.assertEqual(self.check(support.component("x", "ui")), [])

    def test_latest_is_not_a_version(self):
        self.assertIn("C1", codes(self.check(support.component("x", "ui", version="latest"))))

    def test_placeholder_values_are_rejected(self):
        findings = self.check(support.component("x", "ui", version="<exact version>"))
        self.assertTrue(any(f.code == "C1" and "placeholder" in f.message for f in findings))

    def test_nested_placeholder_is_rejected(self):
        entry = support.component("x", "ui", airgap={"images": [{"ref": "<registry/repository:tag>", "digest": ""}]})
        findings = self.check(entry)
        self.assertTrue(any("airgap.images[0].ref" in f.message for f in findings))

    def test_unknown_layer_and_tier(self):
        self.assertIn("C1", codes(self.check(support.component("x", "no-such-layer"))))
        self.assertIn("C1", codes(self.check(support.component("x", "ui", tiers=["T4"]))))
        self.assertIn("C1", codes(self.check(support.component("x", "ui", tiers=[]))))

    def test_unknown_key_is_c1(self):
        entry = support.component("x", "ui")
        entry["telemetery"] = []
        findings = self.check(entry)
        self.assertTrue(any("unknown key 'telemetery'" in f.message for f in findings))

    def test_missing_table_is_c1(self):
        entry = support.component("x", "ui")
        del entry["airgap"]
        self.assertTrue(any("[airgap]" in f.message for f in self.check(entry)))

    def test_quoted_date_is_c1(self):
        entry = support.component("x", "ui", last_verified="2026-11-20")
        self.assertTrue(any("last_verified" in f.message for f in self.check(entry)))

    def test_docs_needs_a_url(self):
        entry = support.component("x", "ui", evidence={"level": "docs", "sources": []})
        self.assertEqual(codes(self.check(entry)), ["C4"])

    def test_field_needs_verifier_and_notes(self):
        entry = support.component("x", "ui", evidence={"level": "field", "sources": []})
        self.assertEqual(codes(self.check(entry)), ["C4", "C4"])

    def test_estimate_needs_notes(self):
        entry = support.component("x", "ui", evidence={"level": "estimate", "sources": [], "notes": " "})
        self.assertEqual(codes(self.check(entry)), ["C4"])

    def test_unknown_reference_is_c3(self):
        entry = support.component("x", "ui", requires=["ghost"], choose={"alternatives": ["phantom"]})
        self.assertEqual(codes(self.check(entry)), ["C3", "C3"])

    def test_bad_id_is_c1(self):
        self.assertIn("C1", codes(self.check(support.component("Bad_ID", "ui"), known=("Bad_ID",))))


if __name__ == "__main__":
    unittest.main()
```

Create `tests/test_real_catalog.py`:

```python
import unittest
from datetime import date

from tests import CATALOG_DIR
from airgap_lib.catalog import load_catalog, validate_catalog


class ShippedCatalogTest(unittest.TestCase):
    def test_the_shipped_catalog_has_no_errors(self):
        catalog, findings = load_catalog(CATALOG_DIR)
        findings = findings + validate_catalog(catalog, date.today())
        errors = [f"{f.code} {f.message}" for f in findings if f.severity == "error"]
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `python3 -m unittest tests.test_catalog tests.test_real_catalog -v`

Expected: `ModuleNotFoundError: No module named 'airgap_lib.catalog'`.

- [ ] **Step 3: Write the GPU table and the loader**

Create `skills/airgap-architect/catalog/gpus.toml`. It has no rows yet; Task 19 adds them from vendor pages.

```toml
# GPU table used by sizing. One [[gpu]] row per GPU model.
# Rows are added by research with a source URL; nothing here comes from memory.
#
# [[gpu]]
# model = "<model name>"
# aliases = ["<other spellings>"]
# vram_gb = <number>
# tdp_w = <number>            # optional
# evidence = "docs"           # field | docs | estimate
# sources = ["<URL>"]
# notes = ""
# last_verified = <YYYY-MM-DD>

schema_version = 1
```

Create `skills/airgap-architect/scripts/airgap_lib/catalog.py`:

```python
"""Loading and validating the catalog: rules, GPU table, component entries."""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .constants import LAYERS, SCHEMA_VERSION, TIERS
from .evidence import evidence_problems
from .findings import Finding
from .rules import Rules, load_rules, validate_rules

_ID_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
_PLACEHOLDER = re.compile(r"<[^<>]+>")

_TOP_KEYS = {
    "schema_version", "id", "name", "layer", "summary", "tiers", "requires",
    "version", "license", "last_verified", "evidence", "airgap", "choose",
    "deeper_skills",
}
_EVIDENCE_KEYS = {"level", "sources", "verified_by", "notes"}
_AIRGAP_KEYS = {
    "images", "packages", "runtime_downloads", "telemetry", "license_server",
    "notes",
}
_CHOOSE_KEYS = {"when", "avoid_when", "alternatives", "caveats"}
_GPU_KEYS = {
    "model", "aliases", "vram_gb", "tdp_w", "evidence", "sources",
    "verified_by", "notes", "last_verified",
}


@dataclass(frozen=True)
class Catalog:
    rules: Rules
    gpus: list[dict]
    components: dict[str, dict]

    def gpu(self, model: str) -> dict | None:
        """Look a GPU up by model name or alias, ignoring case and punctuation."""
        wanted = _normalize(model)
        for row in self.gpus:
            names = [row.get("model", "")] + list(row.get("aliases", []))
            if wanted in {_normalize(name) for name in names}:
                return row
        return None


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def default_catalog_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "catalog"


def load_gpus(path: Path) -> list[dict]:
    with Path(path).open("rb") as handle:
        return list(tomllib.load(handle).get("gpu", []))


def load_components(directory: Path) -> tuple[dict[str, dict], list[Finding]]:
    """Read every *.toml file. Unreadable or misnamed files become C2 findings."""
    components: dict[str, dict] = {}
    findings: list[Finding] = []
    for path in sorted(Path(directory).glob("*.toml")):
        try:
            with path.open("rb") as handle:
                entry = tomllib.load(handle)
        except tomllib.TOMLDecodeError as error:
            findings.append(Finding("C2", f"{path.name}: cannot parse ({error})"))
            continue
        if entry.get("id") != path.stem:
            findings.append(
                Finding("C2", f"{path.name}: id must equal the file name '{path.stem}'")
            )
            continue
        components[path.stem] = entry
    return components, findings


def load_catalog(root: Path) -> tuple[Catalog, list[Finding]]:
    root = Path(root)
    components, findings = load_components(root / "components")
    catalog = Catalog(
        rules=load_rules(root / "rules.toml"),
        gpus=load_gpus(root / "gpus.toml"),
        components=components,
    )
    return catalog, findings


def _strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _placeholders(value, path: str) -> list[str]:
    """Paths of string values still holding an <angle-bracket> template token."""
    if isinstance(value, str):
        return [path] if _PLACEHOLDER.fullmatch(value.strip()) else []
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found += _placeholders(item, f"{path}[{index}]")
        return found
    if isinstance(value, dict):
        found = []
        for key, item in value.items():
            found += _placeholders(item, f"{path}.{key}" if path else key)
        return found
    return []


def validate_component(entry: dict, known_ids: set[str]) -> list[Finding]:
    name = entry.get("id", "?")
    findings: list[Finding] = []

    def c1(message: str) -> None:
        findings.append(Finding("C1", f"{name}: {message}"))

    for key in sorted(set(entry) - _TOP_KEYS):
        c1(f"unknown key '{key}'")
    if entry.get("schema_version") != SCHEMA_VERSION:
        c1(f"schema_version must be {SCHEMA_VERSION}")
    if not isinstance(entry.get("id"), str) or not _ID_PATTERN.fullmatch(entry["id"]):
        c1("id must be lower-case words joined by hyphens")
    for key in ("name", "summary", "license", "version"):
        if not isinstance(entry.get(key), str) or not entry[key].strip():
            c1(f"{key} must be a non-empty string")
    if isinstance(entry.get("version"), str) and entry["version"].strip().lower() == "latest":
        c1("version must be an exact version, never 'latest'")
    if entry.get("layer") not in LAYERS:
        c1("layer must be one of " + ", ".join(LAYERS))
    tiers = entry.get("tiers")
    if (
        not _strings(tiers)
        or not tiers
        or len(set(tiers)) != len(tiers)
        or any(tier not in TIERS for tier in tiers)
    ):
        c1("tiers must be a non-empty list drawn from T1, T2, T3")
    if not _strings(entry.get("requires")):
        c1("requires must be a list of component IDs")
    if not isinstance(entry.get("last_verified"), date):
        c1("last_verified must be a date (YYYY-MM-DD, unquoted)")

    evidence = entry.get("evidence")
    if not isinstance(evidence, dict):
        c1("missing [evidence] table")
    else:
        for key in sorted(set(evidence) - _EVIDENCE_KEYS):
            c1(f"unknown key 'evidence.{key}'")
        for problem in evidence_problems(
            evidence.get("level"),
            evidence.get("sources"),
            evidence.get("verified_by"),
            evidence.get("notes"),
        ):
            findings.append(Finding("C4", f"{name}: {problem}"))

    airgap = entry.get("airgap")
    if not isinstance(airgap, dict):
        c1("missing [airgap] table")
    else:
        for key in sorted(set(airgap) - _AIRGAP_KEYS):
            c1(f"unknown key 'airgap.{key}'")
        images = airgap.get("images")
        if not isinstance(images, list) or any(
            not isinstance(image, dict)
            or not isinstance(image.get("ref"), str)
            or not image["ref"].strip()
            or not isinstance(image.get("digest", ""), str)
            for image in images
        ):
            c1("airgap.images must be a list of { ref, digest } tables")
        for key in ("packages", "runtime_downloads"):
            if not _strings(airgap.get(key)):
                c1(f"airgap.{key} must be a list of strings")
        telemetry = airgap.get("telemetry")
        if not isinstance(telemetry, list) or any(
            not isinstance(item, dict)
            or not isinstance(item.get("what"), str)
            or not isinstance(item.get("disable"), str)
            for item in telemetry
        ):
            c1("airgap.telemetry must be a list of { what, disable } tables")
        if not isinstance(airgap.get("license_server"), bool):
            c1("airgap.license_server must be true or false")
        if not isinstance(airgap.get("notes", ""), str):
            c1("airgap.notes must be a string")

    choose = entry.get("choose")
    if not isinstance(choose, dict):
        c1("missing [choose] table")
    else:
        for key in sorted(set(choose) - _CHOOSE_KEYS):
            c1(f"unknown key 'choose.{key}'")
        for key in sorted(_CHOOSE_KEYS):
            if not _strings(choose.get(key)):
                c1(f"choose.{key} must be a list of strings")

    skills = entry.get("deeper_skills", [])
    if not isinstance(skills, list) or any(
        not isinstance(skill, dict)
        or not isinstance(skill.get("repo"), str)
        or not isinstance(skill.get("skill"), str)
        for skill in skills
    ):
        c1("deeper_skills must be a list of { repo, skill } tables")

    for path in _placeholders(entry, ""):
        c1(f"{path} still holds a placeholder")

    references = list(entry.get("requires") or [])
    if isinstance(choose, dict):
        references += list(choose.get("alternatives") or [])
    for reference in references:
        if isinstance(reference, str) and reference not in known_ids:
            findings.append(
                Finding("C3", f"{name}: refers to unknown component '{reference}'")
            )
    return findings


def validate_gpus(gpus: list[dict]) -> list[Finding]:
    findings: list[Finding] = []
    for index, row in enumerate(gpus):
        name = f"gpus.toml: gpu[{index}]"
        for key in sorted(set(row) - _GPU_KEYS):
            findings.append(Finding("C1", f"{name}: unknown key '{key}'"))
        if not isinstance(row.get("model"), str) or not row["model"].strip():
            findings.append(Finding("C1", f"{name}: model must be a non-empty string"))
        if not _strings(row.get("aliases", [])):
            findings.append(Finding("C1", f"{name}: aliases must be a list of strings"))
        for key, required in (("vram_gb", True), ("tdp_w", False)):
            value = row.get(key)
            if value is None and not required:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                findings.append(Finding("C1", f"{name}: {key} must be a number above 0"))
        if not isinstance(row.get("last_verified"), date):
            findings.append(Finding("C1", f"{name}: last_verified must be a date"))
        for problem in evidence_problems(
            row.get("evidence"),
            row.get("sources"),
            row.get("verified_by"),
            row.get("notes"),
        ):
            findings.append(Finding("C4", f"{name}: {problem}"))
    return findings


def is_stale(last_verified, today: date, freshness_days: int) -> bool:
    return isinstance(last_verified, date) and (today - last_verified).days > freshness_days


def validate_catalog(catalog: Catalog, today: date) -> list[Finding]:
    """Every check `lint.py --catalog-only` runs, apart from load errors."""
    findings = validate_rules(catalog.rules)
    findings += validate_gpus(catalog.gpus)
    known = set(catalog.components)
    for component_id in sorted(catalog.components):
        findings += validate_component(catalog.components[component_id], known)
    if catalog.rules.has("lint.freshness_days"):
        limit = catalog.rules.value("lint.freshness_days")
        for component_id in sorted(catalog.components):
            entry = catalog.components[component_id]
            if is_stale(entry.get("last_verified"), today, limit):
                findings.append(
                    Finding(
                        "W1",
                        f"{component_id}: last verified {entry['last_verified']}, "
                        f"more than {limit} days ago",
                    )
                )
    return findings
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: `Ran 46 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/support.py tests/test_catalog.py tests/test_real_catalog.py \
  skills/airgap-architect/catalog/gpus.toml \
  skills/airgap-architect/scripts/airgap_lib/catalog.py
git commit -m "feat: add catalog loader and catalog checks C1-C4"
```

---

### Task 5: Interview answers: validation and defaults

The eighteen questions of §7 as data. `resolve_answers` validates answers, replaces `"unknown"` with the default from `rules.toml` and reports what it replaced. `org.users_total`, `org.departments`, `workload.models` and `hardware.gpus` have no default.

**Files:**
- Create: `tests/test_answers.py`
- Create: `skills/airgap-architect/scripts/airgap_lib/answers.py`

**Interfaces:**
- Consumes: `Rules` (`default_answer`, `precisions`); `MODEL_ROLES`, `SIZE_CLASSES`, `UNKNOWN`, `USAGE_TYPES`; `support.base_answers`.
- Produces, in `airgap_lib.answers`:
  - `@dataclass(frozen=True) class Question` with fields `id: str`, `kind: str`, `required: bool`, `choices: tuple[str, ...]`
  - `QUESTIONS: tuple[Question, ...]` (18 entries, in interview order), `QUESTION_IDS`, `REQUIRED_IDS` (14 entries)
  - `resolve_answers(answers: dict, rules: Rules, needed=None) -> tuple[dict, list[dict], list[str]]` returning `(resolved, assumptions, problems)`. `problems` are strings of the form `"question.id: reason"`. With `needed=None` every question is checked; with a list of IDs only those are checked. Assumptions are recorded for every defaulted answer regardless of `needed`.
- Answer shapes: `workload.usage` is a map of usage type to share; `workload.models` is a list of objects with `role` and exactly one of `params_b` (with `precision`), `weights_gb`, `size_class`, plus optional `name`, `context_tokens`, `arch` (`layers`, `kv_heads`, `head_dim`, optional `kv_dtype`); `hardware.gpus` is a list of objects with `model`, `count` and optional `vram_gb`, `tdp_w`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_answers.py`:

```python
import unittest

from tests import CATALOG_DIR, support
from airgap_lib.answers import QUESTIONS, REQUIRED_IDS, resolve_answers
from airgap_lib.rules import load_rules


class ResolveAnswersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules(CATALOG_DIR / "rules.toml")

    def problems(self, answers, needed=None):
        return resolve_answers(answers, self.rules, needed)[2]

    def test_question_table_matches_the_spec(self):
        self.assertEqual(len(QUESTIONS), 18)
        self.assertEqual(len(REQUIRED_IDS), 14)

    def test_complete_answers_have_no_problems(self):
        resolved, assumptions, problems = resolve_answers(support.base_answers(), self.rules)
        self.assertEqual(problems, [])
        self.assertEqual(assumptions, [])
        self.assertEqual(resolved, support.base_answers())

    def test_missing_required_answer_is_listed_by_id(self):
        answers = support.base_answers()
        del answers["org.isolation"]
        self.assertEqual(self.problems(answers), ["org.isolation: missing"])

    def test_unknown_uses_the_documented_default(self):
        answers = support.base_answers(**{"org.audit_required": "unknown"})
        resolved, assumptions, problems = resolve_answers(answers, self.rules)
        self.assertEqual(problems, [])
        self.assertIs(resolved["org.audit_required"], True)
        self.assertEqual(
            assumptions,
            [
                {
                    "id": "answers.org.audit_required",
                    "value": True,
                    "evidence": "estimate",
                    "note": "answer was 'unknown'; default applied",
                }
            ],
        )

    def test_unknown_without_a_default_is_a_problem(self):
        answers = support.base_answers(**{"org.users_total": "unknown"})
        self.assertEqual(
            self.problems(answers),
            ["org.users_total: must be answered; 'unknown' has no default"],
        )

    def test_unknown_optional_answer_is_dropped(self):
        answers = support.base_answers(**{"transfer.cadence": "unknown"})
        resolved, assumptions, problems = resolve_answers(answers, self.rules)
        self.assertEqual(problems, [])
        self.assertEqual(assumptions, [])
        self.assertNotIn("transfer.cadence", resolved)

    def test_needed_limits_which_answers_are_checked(self):
        answers = {"org.users_total": 12, "org.departments": 1, "workload.usage": "nonsense"}
        self.assertEqual(self.problems(answers, ("org.users_total", "org.departments")), [])
        self.assertIn("org.isolation: missing", self.problems(answers))

    def test_assumptions_are_recorded_for_answers_outside_needed(self):
        answers = support.base_answers(**{"transfer.channel": "unknown"})
        _, assumptions, _ = resolve_answers(answers, self.rules, ("org.users_total",))
        self.assertEqual([item["id"] for item in assumptions], ["answers.transfer.channel"])

    def test_counts_reject_booleans_and_zero(self):
        self.assertTrue(self.problems(support.base_answers(**{"org.users_total": True})))
        self.assertTrue(self.problems(support.base_answers(**{"org.departments": 0})))

    def test_boolean_rejects_numbers(self):
        self.assertEqual(
            self.problems(support.base_answers(**{"org.audit_required": 1})),
            ["org.audit_required: must be true or false"],
        )

    def test_enum_lists_the_choices(self):
        problems = self.problems(support.base_answers(**{"org.isolation": "strict"}))
        self.assertEqual(
            problems, ["org.isolation: must be one of none, per_department, multi_level"]
        )

    def test_usage_shares_must_sum_to_one(self):
        problems = self.problems(support.base_answers(**{"workload.usage": {"chat": 0.5}}))
        self.assertEqual(problems, ["workload.usage: shares must sum to 1"])

    def test_usage_rejects_unknown_types(self):
        problems = self.problems(support.base_answers(**{"workload.usage": {"poetry": 1.0}}))
        self.assertEqual(problems, ["workload.usage: unknown usage type 'poetry'"])

    def test_model_needs_exactly_one_size(self):
        both = [{"role": "chat", "params_b": 70, "precision": "fp8", "weights_gb": 70}]
        neither = [{"role": "chat"}]
        for models in (both, neither):
            problems = self.problems(support.base_answers(**{"workload.models": models}))
            self.assertEqual(
                problems,
                ["workload.models: item 0: give exactly one of weights_gb, params_b, size_class"],
            )

    def test_model_with_params_needs_a_known_precision(self):
        models = [{"role": "chat", "params_b": 70, "precision": "fp12"}]
        problems = self.problems(support.base_answers(**{"workload.models": models}))
        self.assertEqual(len(problems), 1)
        self.assertIn("precision must be one of", problems[0])

    def test_size_class_and_weights_are_accepted(self):
        models = [
            {"role": "chat", "size_class": "M"},
            {"role": "embedding", "weights_gb": 2.5},
        ]
        self.assertEqual(self.problems(support.base_answers(**{"workload.models": models})), [])

    def test_arch_numbers_must_be_whole_and_positive(self):
        models = [
            {
                "role": "chat",
                "params_b": 70,
                "precision": "fp8",
                "arch": {"layers": 80, "kv_heads": 0, "head_dim": 128},
            }
        ]
        problems = self.problems(support.base_answers(**{"workload.models": models}))
        self.assertEqual(
            problems, ["workload.models: item 0: arch.kv_heads must be a whole number above 0"]
        )

    def test_gpu_entries_need_model_and_count(self):
        problems = self.problems(support.base_answers(**{"hardware.gpus": [{"model": "X"}]}))
        self.assertEqual(
            problems, ["hardware.gpus: item 0: count must be a whole number of 1 or more"]
        )

    def test_no_gpu_requires_ram(self):
        answers = support.base_answers(**{"hardware.gpus": []})
        self.assertEqual(
            self.problems(answers),
            ["hardware.ram_gb: missing (required when hardware.gpus is empty)"],
        )
        answers["hardware.ram_gb"] = 256
        self.assertEqual(self.problems(answers), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_answers -v`

Expected: `ModuleNotFoundError: No module named 'airgap_lib.answers'`.

- [ ] **Step 3: Write the module**

Create `skills/airgap-architect/scripts/airgap_lib/answers.py`:

```python
"""The interview's question table: validation and 'unknown' handling."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .constants import MODEL_ROLES, SIZE_CLASSES, UNKNOWN, USAGE_TYPES
from .rules import Rules


@dataclass(frozen=True)
class Question:
    id: str
    kind: str
    required: bool
    choices: tuple[str, ...] = ()


QUESTIONS = (
    Question("org.users_total", "count", True),
    Question("org.departments", "count", True),
    Question("org.isolation", "enum", True, ("none", "per_department", "multi_level")),
    Question("org.audit_required", "bool", True),
    Question("org.downtime_tolerance", "enum", True, ("accepted", "planned_only", "none")),
    Question("org.ops_capacity", "enum", True, ("part_time_one", "small_team", "platform_team")),
    Question("org.kubernetes_experience", "bool", True),
    Question("workload.usage", "usage", True),
    Question("workload.models", "models", True),
    Question("hardware.gpus", "gpus", True),
    Question("hardware.ram_gb", "number", False),
    Question("hardware.power_budget_kw", "number", False),
    Question("existing.identity", "enum", True, ("none", "ad_ldap", "oidc")),
    Question("existing.api_gateway", "enum", True, ("none", "kong", "other")),
    Question("existing.kubernetes", "enum", True, ("none", "kubernetes", "openshift")),
    Question("existing.registry", "enum", False, ("none", "harbor", "nexus", "artifactory", "other")),
    Question("transfer.channel", "enum", True, ("removable_media", "data_diode", "staging_host", "other")),
    Question("transfer.cadence", "enum", False, ("ad_hoc", "monthly", "quarterly")),
)
QUESTION_IDS = tuple(question.id for question in QUESTIONS)
REQUIRED_IDS = tuple(question.id for question in QUESTIONS if question.required)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_usage(value) -> list[str]:
    if not isinstance(value, dict) or not value:
        return ["must be a non-empty map of usage type to share"]
    errors = []
    for usage_type, share in value.items():
        if usage_type not in USAGE_TYPES:
            errors.append(f"unknown usage type '{usage_type}'")
        elif not _is_number(share) or share < 0:
            errors.append(f"share for '{usage_type}' must be a number of 0 or more")
    if not errors and abs(sum(value.values()) - 1.0) > 1e-6:
        errors.append("shares must sum to 1")
    return errors


def _check_models(value, rules: Rules) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["must be a non-empty list of models"]
    precisions = rules.precisions()
    errors = []
    for index, model in enumerate(value):
        where = f"item {index}"
        if not isinstance(model, dict):
            errors.append(f"{where}: must be an object")
            continue
        if model.get("role") not in MODEL_ROLES:
            errors.append(f"{where}: role must be one of " + ", ".join(MODEL_ROLES))
        given = [key for key in ("weights_gb", "params_b", "size_class") if model.get(key) is not None]
        if len(given) != 1:
            errors.append(f"{where}: give exactly one of weights_gb, params_b, size_class")
        elif given[0] == "size_class":
            if model["size_class"] not in SIZE_CLASSES:
                errors.append(f"{where}: size_class must be one of " + ", ".join(SIZE_CLASSES))
        elif not _is_number(model[given[0]]) or model[given[0]] <= 0:
            errors.append(f"{where}: {given[0]} must be a number above 0")
        precision = model.get("precision")
        if given == ["params_b"] and precision not in precisions:
            errors.append(f"{where}: precision must be one of " + ", ".join(precisions))
        elif precision is not None and precision not in precisions:
            errors.append(f"{where}: precision must be one of " + ", ".join(precisions))
        context = model.get("context_tokens")
        if context is not None and (not _is_int(context) or context <= 0):
            errors.append(f"{where}: context_tokens must be a whole number above 0")
        arch = model.get("arch")
        if arch is None:
            continue
        if not isinstance(arch, dict):
            errors.append(f"{where}: arch must be an object")
            continue
        for key in ("layers", "kv_heads", "head_dim"):
            if not _is_int(arch.get(key)) or arch[key] <= 0:
                errors.append(f"{where}: arch.{key} must be a whole number above 0")
        if arch.get("kv_dtype") is not None and arch["kv_dtype"] not in precisions:
            errors.append(f"{where}: arch.kv_dtype must be one of " + ", ".join(precisions))
    return errors


def _check_gpus(value) -> list[str]:
    if not isinstance(value, list):
        return ["must be a list (empty when there is no GPU)"]
    errors = []
    for index, gpu in enumerate(value):
        where = f"item {index}"
        if not isinstance(gpu, dict):
            errors.append(f"{where}: must be an object")
            continue
        if not isinstance(gpu.get("model"), str) or not gpu["model"].strip():
            errors.append(f"{where}: model must be a non-empty string")
        if not _is_int(gpu.get("count")) or gpu["count"] < 1:
            errors.append(f"{where}: count must be a whole number of 1 or more")
        for key in ("vram_gb", "tdp_w"):
            if gpu.get(key) is not None and (not _is_number(gpu[key]) or gpu[key] <= 0):
                errors.append(f"{where}: {key} must be a number above 0")
    return errors


def _check(question: Question, value, rules: Rules) -> list[str]:
    if question.kind == "count":
        return [] if _is_int(value) and value >= 1 else ["must be a whole number of 1 or more"]
    if question.kind == "bool":
        return [] if isinstance(value, bool) else ["must be true or false"]
    if question.kind == "enum":
        return [] if value in question.choices else ["must be one of " + ", ".join(question.choices)]
    if question.kind == "number":
        return [] if _is_number(value) and value > 0 else ["must be a number above 0"]
    if question.kind == "usage":
        return _check_usage(value)
    if question.kind == "models":
        return _check_models(value, rules)
    return _check_gpus(value)


def resolve_answers(
    answers: dict, rules: Rules, needed: Iterable[str] | None = None
) -> tuple[dict, list[dict], list[str]]:
    """Validate answers and replace 'unknown' with documented defaults.

    Returns (resolved, assumptions, problems).
    - resolved: a copy of `answers` with every defaultable 'unknown' replaced.
    - assumptions: one record per default that was applied (all questions).
    - problems: "question.id: reason" for missing or invalid answers.
      With `needed=None` every question is checked; otherwise only `needed`.
    """
    check_ids = set(QUESTION_IDS if needed is None else needed)
    resolved = dict(answers)
    assumptions: list[dict] = []
    problems: list[str] = []
    for question in QUESTIONS:
        checked = question.id in check_ids
        value = answers.get(question.id)
        if isinstance(value, str) and value == UNKNOWN:
            default = rules.default_answer(question.id)
            if default is not None:
                resolved[question.id] = default["value"]
                assumptions.append(
                    {
                        "id": f"answers.{question.id}",
                        "value": default["value"],
                        "evidence": default.get("evidence", "estimate"),
                        "note": "answer was 'unknown'; default applied",
                    }
                )
            elif question.required:
                if checked:
                    problems.append(f"{question.id}: must be answered; 'unknown' has no default")
            else:
                resolved.pop(question.id, None)
            continue
        if value is None:
            if checked and question.required:
                problems.append(f"{question.id}: missing")
            continue
        if checked:
            problems += [f"{question.id}: {error}" for error in _check(question, value, rules)]
    if (
        "hardware.ram_gb" in check_ids
        and resolved.get("hardware.gpus") == []
        and resolved.get("hardware.ram_gb") is None
    ):
        problems.append("hardware.ram_gb: missing (required when hardware.gpus is empty)")
    return resolved, assumptions, problems
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: `Ran 65 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_answers.py skills/airgap-architect/scripts/airgap_lib/answers.py
git commit -m "feat: add interview answer validation and defaults"
```

---

### Task 6: Tier and floors

Base tier from users and departments (§8.1), per-layer floors from the escalators in `rules.toml` (§8.2), and the requirements those escalators switch on. The test vectors are the ones in §17.

**Files:**
- Create: `tests/test_tiering.py`
- Create: `skills/airgap-architect/scripts/airgap_lib/tiering.py`

**Interfaces:**
- Consumes: `Rules` (`value`, `escalators`); `LAYERS`, `REQUIREMENTS`, `max_tier`.
- Produces, in `airgap_lib.tiering`:
  - `TIER_ANSWERS: tuple[str, ...]`, the six answers `tier.py` needs
  - `base_tier(users: int, departments: int, rules: Rules) -> str`
  - `compute_tier(answers: dict, rules: Rules) -> dict` returning `{"base": str, "floors": {layer: tier for all eight layers}, "requirements": {"gateway_non_empty": bool, "isolation_design_section": bool, "two_engine_replicas": bool, "kubernetes_risk_note": bool}, "reasons": list[str]}`. `answers` must already be resolved.

- [ ] **Step 1: Write the failing test**

Create `tests/test_tiering.py`:

```python
import unittest

from tests import CATALOG_DIR, support
from airgap_lib.constants import LAYERS, REQUIREMENTS
from airgap_lib.rules import load_rules
from airgap_lib.tiering import base_tier, compute_tier


class BaseTierTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules(CATALOG_DIR / "rules.toml")

    def test_spec_vectors(self):
        # (users, departments) -> base tier, from design spec section 17.
        vectors = {
            (25, 1): "T1",
            (26, 1): "T2",
            (20, 2): "T2",
            (300, 5): "T2",
            (301, 1): "T3",
            (50, 6): "T3",
        }
        for (users, departments), expected in vectors.items():
            with self.subTest(users=users, departments=departments):
                self.assertEqual(base_tier(users, departments, self.rules), expected)


class ComputeTierTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules(CATALOG_DIR / "rules.toml")

    def tier(self, **overrides):
        answers = {
            "org.users_total": 12,
            "org.departments": 1,
            "org.isolation": "none",
            "org.audit_required": False,
            "org.downtime_tolerance": "accepted",
            "org.kubernetes_experience": False,
        }
        answers.update(overrides)
        return compute_tier(answers, self.rules)

    def test_plain_small_team(self):
        tier = self.tier()
        self.assertEqual(tier["base"], "T1")
        self.assertEqual(tier["floors"], {layer: "T1" for layer in LAYERS})
        self.assertEqual(tier["requirements"], {name: False for name in REQUIREMENTS})
        self.assertEqual(tier["reasons"], [])

    def test_spec_vector_audit_raises_only_the_gateway(self):
        tier = self.tier(**{"org.audit_required": True})
        self.assertEqual(tier["base"], "T1")
        self.assertEqual(tier["floors"]["llm-gateway"], "T2")
        self.assertEqual(tier["floors"]["orchestration"], "T1")
        self.assertTrue(tier["requirements"]["gateway_non_empty"])
        self.assertEqual(len(tier["reasons"]), 1)
        self.assertIn("org.audit_required", tier["reasons"][0])

    def test_per_department_isolation(self):
        tier = self.tier(**{"org.isolation": "per_department"})
        self.assertEqual(tier["floors"]["llm-gateway"], "T2")
        self.assertEqual(tier["floors"]["identity"], "T2")
        self.assertTrue(tier["requirements"]["gateway_non_empty"])
        self.assertFalse(tier["requirements"]["isolation_design_section"])

    def test_multi_level_isolation(self):
        tier = self.tier(**{"org.isolation": "multi_level"})
        self.assertEqual(tier["floors"]["llm-gateway"], "T3")
        self.assertEqual(tier["floors"]["identity"], "T3")
        self.assertTrue(tier["requirements"]["isolation_design_section"])
        self.assertTrue(tier["requirements"]["gateway_non_empty"])

    def test_no_downtime_raises_three_layers_and_flags_kubernetes_risk(self):
        tier = self.tier(**{"org.downtime_tolerance": "none"})
        for layer in ("orchestration", "llm-serving", "state"):
            self.assertEqual(tier["floors"][layer], "T3", layer)
        self.assertEqual(tier["floors"]["ui"], "T1")
        self.assertTrue(tier["requirements"]["two_engine_replicas"])
        self.assertTrue(tier["requirements"]["kubernetes_risk_note"])

    def test_kubernetes_experience_removes_the_risk(self):
        tier = self.tier(**{"org.downtime_tolerance": "none", "org.kubernetes_experience": True})
        self.assertFalse(tier["requirements"]["kubernetes_risk_note"])

    def test_escalators_never_lower_a_floor(self):
        tier = self.tier(**{"org.users_total": 2000, "org.audit_required": True})
        self.assertEqual(tier["base"], "T3")
        self.assertEqual(tier["floors"]["llm-gateway"], "T3")

    def test_department_answers_from_support(self):
        tier = compute_tier(support.base_answers(), self.rules)
        self.assertEqual(tier["base"], "T2")
        self.assertEqual(set(tier["floors"].values()), {"T2"})
        self.assertTrue(tier["requirements"]["gateway_non_empty"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_tiering -v`

Expected: `ModuleNotFoundError: No module named 'airgap_lib.tiering'`.

- [ ] **Step 3: Write the module**

Create `skills/airgap-architect/scripts/airgap_lib/tiering.py`:

```python
"""Base tier, per-layer floors and the requirements escalators switch on."""
from __future__ import annotations

from .constants import LAYERS, REQUIREMENTS, max_tier
from .rules import Rules

# Answers tier.py needs. Everything else may still be unanswered.
TIER_ANSWERS = (
    "org.users_total",
    "org.departments",
    "org.isolation",
    "org.audit_required",
    "org.downtime_tolerance",
    "org.kubernetes_experience",
)


def base_tier(users: int, departments: int, rules: Rules) -> str:
    """The higher of the tier implied by users and by departments."""

    def implied(value: int, t1_key: str, t2_key: str) -> str:
        if value <= rules.value(t1_key):
            return "T1"
        if value <= rules.value(t2_key):
            return "T2"
        return "T3"

    return max_tier(
        implied(users, "tiers.t1_max_users", "tiers.t2_max_users"),
        implied(departments, "tiers.t1_max_departments", "tiers.t2_max_departments"),
    )


def compute_tier(answers: dict, rules: Rules) -> dict:
    """`answers` must be resolved and contain every ID in TIER_ANSWERS."""
    base = base_tier(answers["org.users_total"], answers["org.departments"], rules)
    floors = {layer: base for layer in LAYERS}
    requirements = {name: False for name in REQUIREMENTS}
    reasons: list[str] = []
    for escalator in rules.escalators:
        answer = answers.get(escalator["answer"])
        expected = escalator["equals"]
        if type(answer) is not type(expected) or answer != expected:
            continue
        for layer, tier in escalator.get("floors", {}).items():
            floors[layer] = max_tier(floors[layer], tier)
        for name in escalator.get("requires", []):
            requirements[name] = True
        reasons.append(escalator["reason"])
    if floors["orchestration"] == "T3" and answers.get("org.kubernetes_experience") is False:
        requirements["kubernetes_risk_note"] = True
        reasons.append(
            "the orchestration floor is T3 but org.kubernetes_experience is false"
        )
    return {
        "base": base,
        "floors": floors,
        "requirements": requirements,
        "reasons": reasons,
    }
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: `Ran 74 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_tiering.py skills/airgap-architect/scripts/airgap_lib/tiering.py
git commit -m "feat: add tier and per-layer floor computation"
```

---

### Task 7: Sizing

Concurrency, memory per model and totals (§10). The test vectors are the ones in §17: on 141 GB GPUs, 70B fp8 needs 1 GPU, 70B bf16 needs 2, 235B fp8 needs 4, 671B fp8 needs 8; on a 24 GB GPU, 30B int4 needs 1. Sizing never predicts throughput.

Three behaviors the spec leaves open are fixed here and listed under "Open questions": sizing uses only the GPU type with the most memory; every generative model is sized for the full interactive concurrency; and when one full-context sequence does not fit the KV cache, the next larger GPU group is tried.

**Files:**
- Create: `tests/test_sizing.py`
- Create: `skills/airgap-architect/scripts/airgap_lib/sizing.py`

**Interfaces:**
- Consumes: `Rules.use`; `GENERATIVE_ROLES`, `INTERACTIVE_USAGE`, `EVIDENCE_LEVELS`.
- Produces, in `airgap_lib.sizing`:
  - `SIZING_ANSWERS: tuple[str, ...]`, the answers `size.py` checks
  - `class SizingInputError(Exception)` with attribute `problems: list[str]`
  - `interactive_concurrency(users, usage, rules, sink=None) -> dict` returning `{"low": int, "high": int, "by_usage": {...}}`
  - `model_weights_gb(model, rules, sink=None) -> float`
  - `pick_primary_gpu(entries, gpu_lookup) -> dict | None` returning `{"model", "vram_gb", "tdp_w", "count"}`
  - `size_model(model, concurrency_high, gpu, min_replicas, rules, sink=None) -> dict`
  - `compute_sizing(answers, rules, gpu_lookup) -> tuple[dict, list[dict]]` returning `(sizing, assumptions)`. `gpu_lookup` is a callable from a model name to a GPU row or `None`; pass `catalog.gpu`.
- Keys of `sizing`: `concurrency`, `gpu`, `models` (each with `name`, `role`, `weights_gb`, `required_gb`, `gpus_per_replica`, `usable_gb`, `kv_headroom_gb`, `kv` (`status` is `computed`, `unknown`, `insufficient` or `not_applicable`), `replicas`, `gpus`, `notes`), `cpu_only`, `benchmark_required`, `total_gpus`, `servers`, `power_kw`, `power_within_budget`, `fits`, `warnings`, and `ram_required_gb` when there is no GPU.

- [ ] **Step 1: Write the failing test**

Create `tests/test_sizing.py`:

```python
import unittest

from tests import CATALOG_DIR
from airgap_lib.constants import EVIDENCE_LEVELS
from airgap_lib.rules import load_rules
from airgap_lib.sizing import (
    SizingInputError,
    compute_sizing,
    interactive_concurrency,
    model_weights_gb,
    pick_primary_gpu,
    size_model,
)


def no_gpu_table(model):
    return None


def answers(**overrides):
    base = {
        "org.users_total": 180,
        "org.downtime_tolerance": "planned_only",
        "workload.usage": {"chat": 1.0},
        "workload.models": [{"name": "m", "role": "chat", "params_b": 70, "precision": "fp8"}],
        "hardware.gpus": [{"model": "big", "count": 8, "vram_gb": 141, "tdp_w": 700}],
    }
    base.update(overrides)
    return base


class SizingTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules(CATALOG_DIR / "rules.toml")

    def size(self, **overrides):
        return compute_sizing(answers(**overrides), self.rules, no_gpu_table)


class ConcurrencyTest(SizingTestCase):
    def test_spec_example_180_chat_users(self):
        result = interactive_concurrency(180, {"chat": 1.0}, self.rules)
        self.assertEqual((result["low"], result["high"]), (6, 11))

    def test_exact_products_are_not_rounded_up_by_float_noise(self):
        result = interactive_concurrency(300, {"chat": 1.0}, self.rules)
        self.assertEqual((result["low"], result["high"]), (9, 18))

    def test_mixed_usage_adds_up(self):
        usage = {"chat": 0.7, "code_assistant": 0.2, "rag": 0.1}
        result = interactive_concurrency(2000, usage, self.rules)
        self.assertEqual((result["low"], result["high"]), (132, 216))
        self.assertEqual(set(result["by_usage"]), {"chat", "code_assistant", "rag"})

    def test_batch_is_excluded_and_the_minimum_is_one(self):
        result = interactive_concurrency(500, {"batch": 1.0}, self.rules)
        self.assertEqual((result["low"], result["high"]), (1, 1))
        self.assertEqual(result["by_usage"], {})

    def test_small_team_rounds_up_to_one(self):
        result = interactive_concurrency(12, {"chat": 1.0}, self.rules)
        self.assertEqual((result["low"], result["high"]), (1, 1))


class WeightsTest(SizingTestCase):
    def test_params_times_bytes(self):
        self.assertEqual(model_weights_gb({"params_b": 70, "precision": "bf16"}, self.rules), 140.0)
        self.assertEqual(model_weights_gb({"params_b": 30, "precision": "int4"}, self.rules), 15.0)

    def test_given_weight_size_wins(self):
        model = {"weights_gb": 42.5, "params_b": 70, "precision": "bf16"}
        self.assertEqual(model_weights_gb(model, self.rules), 42.5)

    def test_size_class_uses_the_default_precision_and_records_it(self):
        sink = []
        self.assertEqual(model_weights_gb({"size_class": "M"}, self.rules, sink), 64.0)
        self.assertEqual(
            [item["id"] for item in sink],
            ["sizing.size_class.M", "sizing.default_precision", "sizing.bytes_per_param.bf16"],
        )


class GpusPerReplicaTest(SizingTestCase):
    def group(self, params_b, precision, vram_gb):
        gpu = {"model": "x", "vram_gb": vram_gb, "tdp_w": None, "count": 8}
        model = {"role": "chat", "params_b": params_b, "precision": precision}
        return size_model(model, 1, gpu, 1, self.rules)["gpus_per_replica"]

    def test_spec_vectors_on_141_gb_gpus(self):
        self.assertEqual(self.group(70, "fp8", 141), 1)
        self.assertEqual(self.group(70, "bf16", 141), 2)
        self.assertEqual(self.group(235, "fp8", 141), 4)
        self.assertEqual(self.group(671, "fp8", 141), 8)

    def test_spec_vector_on_a_24_gb_gpu(self):
        self.assertEqual(self.group(30, "int4", 24), 1)

    def test_weights_that_fit_no_group(self):
        gpu = {"model": "x", "vram_gb": 24, "tdp_w": None, "count": 8}
        result = size_model({"role": "chat", "params_b": 671, "precision": "fp8"}, 1, gpu, 1, self.rules)
        self.assertIsNone(result["gpus_per_replica"])
        self.assertIsNone(result["gpus"])
        self.assertIn("do not fit", result["notes"][0])


class KvCacheTest(SizingTestCase):
    ARCH = {"layers": 80, "kv_heads": 8, "head_dim": 128, "kv_dtype": "fp16"}

    def test_unknown_without_architecture_numbers(self):
        sizing, _ = self.size()
        model = sizing["models"][0]
        self.assertEqual(model["kv"], {"status": "unknown"})
        self.assertEqual(model["replicas"], 1)
        self.assertIn("benchmark", model["notes"][0])

    def test_replicas_follow_kv_capacity(self):
        models = [{"role": "chat", "params_b": 70, "precision": "fp8", "arch": self.ARCH}]
        usage = {"chat": 0.7, "code_assistant": 0.2, "rag": 0.1}
        sizing, _ = self.size(
            **{
                "org.users_total": 2000,
                "workload.usage": usage,
                "workload.models": models,
                "hardware.gpus": [{"model": "big", "count": 16, "vram_gb": 141}],
            }
        )
        model = sizing["models"][0]
        self.assertEqual(model["kv"]["bytes_per_token"], 327680)
        self.assertEqual(model["kv"]["cached_tokens"], 152282)
        self.assertEqual(model["kv"]["sequences"], 16)
        self.assertEqual(model["replicas"], 14)
        self.assertEqual(sizing["total_gpus"], 14)
        self.assertEqual(sizing["servers"], 2)
        self.assertTrue(sizing["fits"])

    def test_group_grows_until_one_sequence_fits(self):
        # 115 GB of weights plus overhead leave no room for a 200k-token sequence on one GPU.
        models = [
            {
                "role": "chat",
                "weights_gb": 115,
                "context_tokens": 200000,
                "arch": self.ARCH,
            }
        ]
        sizing, _ = self.size(**{"workload.models": models})
        model = sizing["models"][0]
        self.assertEqual(model["gpus_per_replica"], 2)
        self.assertEqual(model["kv"]["status"], "computed")
        self.assertGreaterEqual(model["kv"]["sequences"], 1)

    def test_insufficient_kv_capacity_does_not_fit(self):
        models = [
            {
                "role": "chat",
                "weights_gb": 900,
                "context_tokens": 2000000,
                "arch": self.ARCH,
            }
        ]
        sizing, _ = self.size(**{"workload.models": models})
        self.assertEqual(sizing["models"][0]["kv"]["status"], "insufficient")
        self.assertFalse(sizing["fits"])

    def test_embedding_models_skip_kv_sizing(self):
        models = [{"role": "embedding", "weights_gb": 2.5, "arch": self.ARCH}]
        sizing, _ = self.size(**{"workload.models": models})
        self.assertEqual(sizing["models"][0]["kv"], {"status": "not_applicable"})


class TotalsTest(SizingTestCase):
    def test_spec_example_totals(self):
        models = [{"role": "chat", "params_b": 671, "precision": "fp8"}]
        sizing, _ = self.size(**{"workload.models": models})
        self.assertEqual(sizing["total_gpus"], 8)
        self.assertEqual(sizing["servers"], 1)
        self.assertEqual(sizing["power_kw"], 10.1)
        self.assertIs(sizing["fits"], True)
        self.assertIs(sizing["benchmark_required"], True)

    def test_too_few_gpus_do_not_fit(self):
        models = [{"role": "chat", "params_b": 671, "precision": "fp8"}]
        gpus = [{"model": "big", "count": 4, "vram_gb": 141}]
        sizing, _ = self.size(**{"workload.models": models, "hardware.gpus": gpus})
        self.assertIs(sizing["fits"], False)
        self.assertIsNone(sizing["power_kw"])

    def test_no_downtime_doubles_the_replicas(self):
        sizing, assumptions = self.size(**{"org.downtime_tolerance": "none"})
        self.assertEqual(sizing["models"][0]["replicas"], 2)
        self.assertEqual(sizing["total_gpus"], 2)
        self.assertIn("sizing.ha_min_replicas", [item["id"] for item in assumptions])

    def test_power_budget(self):
        sizing, _ = self.size(**{"hardware.power_budget_kw": 1.0})
        self.assertEqual(sizing["power_kw"], 1.3)
        self.assertIs(sizing["power_within_budget"], False)
        self.assertIn("power", sizing["warnings"][0])

    def test_assumptions_list_every_constant_used(self):
        _, assumptions = self.size()
        ids = [item["id"] for item in assumptions]
        self.assertEqual(len(ids), len(set(ids)))
        for expected in (
            "sizing.chat.active",
            "sizing.chat.duty_low",
            "sizing.chat.duty_high",
            "sizing.bytes_per_param.fp8",
            "sizing.overhead",
            "sizing.gpu_memory_utilization",
            "sizing.gpu_group_sizes",
            "sizing.gpus_per_server",
            "sizing.power_system_factor",
        ):
            self.assertIn(expected, ids)
        for item in assumptions:
            self.assertEqual(set(item), {"id", "value", "evidence", "note"})
            self.assertIn(item["evidence"], EVIDENCE_LEVELS)


class HardwareTest(SizingTestCase):
    def test_largest_vram_type_is_primary(self):
        entries = [
            {"model": "small", "count": 4, "vram_gb": 24},
            {"model": "big", "count": 2, "vram_gb": 141},
        ]
        self.assertEqual(pick_primary_gpu(entries, no_gpu_table)["model"], "big")
        sizing, _ = self.size(**{"hardware.gpus": entries})
        self.assertIn("several GPU types", sizing["warnings"][0])

    def test_table_supplies_missing_vram_and_tdp(self):
        table = {"known": {"vram_gb": 48, "tdp_w": 300}}
        gpu = pick_primary_gpu([{"model": "known", "count": 2}], table.get)
        self.assertEqual(gpu, {"model": "known", "vram_gb": 48, "tdp_w": 300, "count": 2})

    def test_unknown_gpu_without_vram_is_an_input_error(self):
        with self.assertRaises(SizingInputError) as caught:
            self.size(**{"hardware.gpus": [{"model": "mystery", "count": 1}]})
        self.assertEqual(
            caught.exception.problems,
            ["hardware.gpus: item 0: 'mystery' is not in gpus.toml; supply vram_gb"],
        )

    def test_cpu_only_compares_weights_with_ram(self):
        models = [{"role": "chat", "params_b": 8, "precision": "int4"}]
        sizing, _ = self.size(
            **{"hardware.gpus": [], "hardware.ram_gb": 64, "workload.models": models}
        )
        self.assertIs(sizing["cpu_only"], True)
        self.assertEqual(sizing["total_gpus"], 0)
        self.assertEqual(sizing["ram_required_gb"], 4.4)
        self.assertIs(sizing["fits"], True)
        self.assertIn("CPU inference", sizing["warnings"][0])

    def test_cpu_only_without_ram_is_an_input_error(self):
        with self.assertRaises(SizingInputError):
            self.size(**{"hardware.gpus": []})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_sizing -v`

Expected: `ModuleNotFoundError: No module named 'airgap_lib.sizing'`.

- [ ] **Step 3: Write the module**

Create `skills/airgap-architect/scripts/airgap_lib/sizing.py`:

```python
"""Organization answers to hardware numbers. Memory only; never throughput."""
from __future__ import annotations

import math
from collections.abc import Callable

from .constants import GENERATIVE_ROLES, INTERACTIVE_USAGE
from .rules import Rules

# Answers size.py checks. The last two are optional or conditional.
SIZING_ANSWERS = (
    "org.users_total",
    "org.downtime_tolerance",
    "workload.usage",
    "workload.models",
    "hardware.gpus",
    "hardware.ram_gb",
    "hardware.power_budget_kw",
)
BYTES_PER_GB = 1e9


class SizingInputError(Exception):
    """An answer is unusable for sizing; `problems` lists 'question.id: reason'."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = list(problems)


def _ceil(value: float) -> int:
    # Rounding first keeps 9.000000000000002 from becoming 10.
    return math.ceil(round(value, 9))


def interactive_concurrency(
    users: int, usage: dict, rules: Rules, sink: list[dict] | None = None
) -> dict:
    """Peak requests in flight as a low-high range. Batch is excluded."""
    low = high = 0.0
    by_usage: dict[str, dict] = {}
    for usage_type in INTERACTIVE_USAGE:
        share = usage.get(usage_type, 0)
        if share <= 0:
            continue
        active = rules.use(f"sizing.{usage_type}.active", sink)
        usage_low = users * share * active * rules.use(f"sizing.{usage_type}.duty_low", sink)
        usage_high = users * share * active * rules.use(f"sizing.{usage_type}.duty_high", sink)
        by_usage[usage_type] = {"low": round(usage_low, 3), "high": round(usage_high, 3)}
        low += usage_low
        high += usage_high
    return {"low": max(1, _ceil(low)), "high": max(1, _ceil(high)), "by_usage": by_usage}


def model_weights_gb(model: dict, rules: Rules, sink: list[dict] | None = None) -> float:
    if model.get("weights_gb") is not None:
        return float(model["weights_gb"])
    if model.get("size_class") is not None:
        params_b = rules.use(f"sizing.size_class.{model['size_class']}", sink)
        precision = model.get("precision") or rules.use("sizing.default_precision", sink)
    else:
        params_b = model["params_b"]
        precision = model["precision"]
    return float(params_b * rules.use(f"sizing.bytes_per_param.{precision}", sink))


def pick_primary_gpu(
    entries: list[dict], gpu_lookup: Callable[[str], dict | None]
) -> dict | None:
    """The GPU type sizing uses: the largest VRAM, then the larger count."""
    problems: list[str] = []
    candidates: list[dict] = []
    for index, entry in enumerate(entries):
        known = gpu_lookup(entry["model"]) or {}
        vram_gb = entry.get("vram_gb", known.get("vram_gb"))
        if vram_gb is None:
            problems.append(
                f"hardware.gpus: item {index}: '{entry['model']}' is not in gpus.toml; supply vram_gb"
            )
            continue
        candidates.append(
            {
                "model": entry["model"],
                "vram_gb": vram_gb,
                "tdp_w": entry.get("tdp_w", known.get("tdp_w")),
                "count": entry["count"],
            }
        )
    if problems:
        raise SizingInputError(problems)
    if not candidates:
        return None
    return max(candidates, key=lambda gpu: (gpu["vram_gb"], gpu["count"]))


def size_model(
    model: dict,
    concurrency_high: int,
    gpu: dict | None,
    min_replicas: int,
    rules: Rules,
    sink: list[dict] | None = None,
) -> dict:
    weights = model_weights_gb(model, rules, sink)
    required = weights * (1 + rules.use("sizing.overhead", sink))
    result = {
        "name": model.get("name", ""),
        "role": model["role"],
        "weights_gb": round(weights, 3),
        "required_gb": round(required, 3),
        "gpus_per_replica": None,
        "usable_gb": None,
        "kv_headroom_gb": None,
        "kv": {"status": "not_applicable"},
        "replicas": max(1, min_replicas),
        "gpus": None,
        "notes": [],
    }
    if gpu is None:
        result.update(gpus_per_replica=0, gpus=0)
        return result

    utilization = rules.use("sizing.gpu_memory_utilization", sink)

    def usable(group: int) -> float:
        return group * gpu["vram_gb"] * utilization

    fitting = [
        group
        for group in sorted(rules.use("sizing.gpu_group_sizes", sink))
        if usable(group) >= required
    ]
    if not fitting:
        result["notes"].append("the weights do not fit the largest allowed GPU group")
        return result

    group = fitting[0]
    arch = model.get("arch")
    if model["role"] in GENERATIVE_ROLES and arch is None:
        result["kv"] = {"status": "unknown"}
        result["notes"].append("KV-cache capacity is unknown; measure it with a benchmark")
    elif model["role"] in GENERATIVE_ROLES:
        dtype = arch.get("kv_dtype") or rules.use("sizing.default_kv_dtype", sink)
        bytes_per_token = (
            2
            * arch["layers"]
            * arch["kv_heads"]
            * arch["head_dim"]
            * rules.use(f"sizing.bytes_per_param.{dtype}", sink)
        )
        tokens_per_sequence = (
            model.get("context_tokens") or rules.use("sizing.default_context_tokens", sink)
        ) + rules.use("sizing.default_output_tokens", sink)
        cached_tokens = sequences = 0
        for candidate in fitting:
            group = candidate
            headroom_bytes = (usable(candidate) - required) * BYTES_PER_GB
            cached_tokens = int(headroom_bytes // bytes_per_token)
            sequences = cached_tokens // tokens_per_sequence
            if sequences >= 1:
                break
        result["kv"] = {
            "status": "computed" if sequences >= 1 else "insufficient",
            "bytes_per_token": bytes_per_token,
            "cached_tokens": cached_tokens,
            "sequences": sequences,
        }
        if sequences >= 1:
            result["replicas"] = max(
                result["replicas"], math.ceil(concurrency_high / sequences)
            )
        else:
            result["notes"].append(
                "the KV cache cannot hold one full-context sequence on the largest allowed GPU group"
            )
    result.update(
        gpus_per_replica=group,
        usable_gb=round(usable(group), 3),
        kv_headroom_gb=round(usable(group) - required, 3),
        gpus=result["replicas"] * group,
    )
    return result


def compute_sizing(
    answers: dict, rules: Rules, gpu_lookup: Callable[[str], dict | None]
) -> tuple[dict, list[dict]]:
    """Return (sizing, assumptions). `answers` must be resolved and valid."""
    sink: list[dict] = []
    concurrency = interactive_concurrency(
        answers["org.users_total"], answers["workload.usage"], rules, sink
    )
    min_replicas = 1
    if answers.get("org.downtime_tolerance") == "none":
        min_replicas = rules.use("sizing.ha_min_replicas", sink)
    entries = answers["hardware.gpus"]
    gpu = pick_primary_gpu(entries, gpu_lookup)
    warnings: list[str] = []
    if len(entries) > 1:
        warnings.append(
            "several GPU types were given; only the largest-VRAM type is used for sizing"
        )
    models = [
        size_model(model, concurrency["high"], gpu, min_replicas, rules, sink)
        for model in answers["workload.models"]
    ]
    sizing = {
        "concurrency": concurrency,
        "gpu": gpu,
        "models": models,
        "cpu_only": gpu is None,
        "benchmark_required": True,
    }
    if gpu is None:
        ram_gb = answers.get("hardware.ram_gb")
        if ram_gb is None:
            raise SizingInputError(
                ["hardware.ram_gb: missing (required when hardware.gpus is empty)"]
            )
        ram_required = round(sum(model["required_gb"] for model in models), 3)
        warnings.append(
            "CPU inference suits only a few concurrent users; benchmark before relying on it"
        )
        sizing.update(
            total_gpus=0,
            servers=1,
            power_kw=None,
            power_within_budget=None,
            ram_required_gb=ram_required,
            fits=ram_required <= ram_gb,
        )
    else:
        complete = all(
            model["gpus"] is not None and model["kv"]["status"] != "insufficient"
            for model in models
        )
        total_gpus = sum(model["gpus"] or 0 for model in models)
        servers = max(1, math.ceil(total_gpus / rules.use("sizing.gpus_per_server", sink)))
        power_kw = None
        if gpu["tdp_w"] is not None:
            factor = rules.use("sizing.power_system_factor", sink)
            power_kw = round(total_gpus * gpu["tdp_w"] * factor / 1000, 1)
        budget = answers.get("hardware.power_budget_kw")
        within_budget = None if power_kw is None or budget is None else power_kw <= budget
        if within_budget is False:
            warnings.append("the power estimate exceeds hardware.power_budget_kw")
        sizing.update(
            total_gpus=total_gpus,
            servers=servers,
            power_kw=power_kw,
            power_within_budget=within_budget,
            fits=complete and total_gpus <= gpu["count"],
        )
    sizing["warnings"] = warnings
    return sizing, sink
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: `Ran 100 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_sizing.py skills/airgap-architect/scripts/airgap_lib/sizing.py
git commit -m "feat: add sizing from organization answers"
```

---

### Task 8: `blueprint.json` state file

Reading, writing and structural validation of the state file (§13), and the digest that ties a transfer manifest to the decisions it was generated from.

**Files:**
- Create: `tests/test_blueprint.py`
- Create: `skills/airgap-architect/scripts/airgap_lib/blueprint.py`

**Interfaces:**
- Consumes: `EVIDENCE_LEVELS`, `LAYERS`, `SCHEMA_VERSION`; `support.base_answers`, `support.base_decisions`.
- Produces, in `airgap_lib.blueprint`:
  - `class BlueprintError(Exception)`
  - `load_blueprint(path) -> dict` (raises `BlueprintError` when the file is missing, is not JSON, or is not an object)
  - `save_blueprint(path, data) -> None` (creates parent folders; two-space indent; keeps non-ASCII text; ends with a newline)
  - `inputs_digest(data) -> str`, `"sha256:"` plus 64 hex characters, over `decisions` and `answers["workload.models"]`
  - `decisions_of(data) -> list[dict]`, `decision_for(data, layer) -> dict | None`, `chosen_components(data) -> list[str]`
  - `validate_schema(data) -> list[str]`, the structural problems of a finished file (lint error E1)
  - `has_override(decision) -> bool`
- Top-level keys of a finished `blueprint.json`: `schema_version`, `project`, `created`, `language`, `blueprint_path`, `answers`, `assumptions`, `tier`, `sizing`, `decisions`. A decision has `layer`, `components`, `existing`, `custom`, `rationale`, `alternatives_considered`, `evidence`, `override`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_blueprint.py`:

```python
import tempfile
import unittest
from pathlib import Path

from tests import support
from airgap_lib.blueprint import (
    BlueprintError,
    chosen_components,
    decision_for,
    has_override,
    inputs_digest,
    load_blueprint,
    save_blueprint,
    validate_schema,
)


class BlueprintFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_save_creates_directories_and_round_trips_unicode(self):
        path = self.root / "docs" / "airgap" / "blueprint.json"
        data = {"project": "örnek", "answers": {"org.users_total": 12}}
        save_blueprint(path, data)
        text = path.read_text(encoding="utf-8")
        self.assertIn("örnek", text)
        self.assertTrue(text.endswith("\n"))
        self.assertEqual(load_blueprint(path), data)

    def test_missing_file(self):
        with self.assertRaises(BlueprintError) as caught:
            load_blueprint(self.root / "nope.json")
        self.assertIn("file not found", str(caught.exception))

    def test_invalid_json(self):
        path = self.root / "blueprint.json"
        path.write_text("{ not json", encoding="utf-8")
        with self.assertRaises(BlueprintError) as caught:
            load_blueprint(path)
        self.assertIn("invalid JSON", str(caught.exception))

    def test_top_level_must_be_an_object(self):
        path = self.root / "blueprint.json"
        path.write_text("[]", encoding="utf-8")
        with self.assertRaises(BlueprintError):
            load_blueprint(path)


def valid_blueprint() -> dict:
    return {
        "schema_version": 1,
        "project": "example",
        "created": "2026-11-20",
        "language": "en",
        "blueprint_path": "docs/airgap/blueprint.md",
        "answers": support.base_answers(),
        "assumptions": [
            {"id": "sizing.overhead", "value": 0.1, "evidence": "estimate", "note": "default"}
        ],
        "tier": {},
        "sizing": {},
        "decisions": support.base_decisions(),
    }


class SchemaTest(unittest.TestCase):
    def setUp(self):
        self.data = valid_blueprint()

    def test_complete_blueprint_is_valid(self):
        self.assertEqual(validate_schema(self.data), [])

    def test_assumptions_need_id_value_and_evidence(self):
        self.data["assumptions"].append({"id": "x", "evidence": "docs"})
        self.assertEqual(
            validate_schema(self.data),
            ["assumptions[1] needs id, value and a valid evidence label"],
        )

    def test_missing_key(self):
        del self.data["decisions"]
        self.assertEqual(validate_schema(self.data), ["missing key 'decisions'"])

    def test_wrong_type(self):
        self.data["schema_version"] = True
        self.assertEqual(validate_schema(self.data), ["'schema_version' must be of type int"])

    def test_created_must_be_a_date(self):
        self.data["created"] = "yesterday"
        self.assertEqual(validate_schema(self.data), ["'created' must be a date like 2026-11-20"])

    def test_duplicate_layer(self):
        self.data["decisions"].append(dict(self.data["decisions"][0]))
        self.assertEqual(
            validate_schema(self.data), ["decisions[8]: second decision for layer 'llm-serving'"]
        )

    def test_decision_fields(self):
        decision = self.data["decisions"][0]
        decision["components"] = "alpha-engine"
        decision["evidence"] = "rumour"
        del decision["override"]
        problems = validate_schema(self.data)
        self.assertEqual(len(problems), 3)
        self.assertTrue(all(problem.startswith("decisions[0]") for problem in problems))

    def test_override_needs_a_reason(self):
        self.data["decisions"][0]["override"] = {"reason": " "}
        self.assertEqual(
            validate_schema(self.data),
            ["decisions[0].override must be null or an object with a reason"],
        )
        self.data["decisions"][0]["override"] = {"reason": "Pilot only."}
        self.assertEqual(validate_schema(self.data), [])
        self.assertTrue(has_override(self.data["decisions"][0]))


class DigestTest(unittest.TestCase):
    def setUp(self):
        self.data = {
            "answers": {"workload.models": [{"role": "chat", "weights_gb": 10}]},
            "decisions": support.base_decisions(),
        }

    def test_digest_is_stable_and_prefixed(self):
        digest = inputs_digest(self.data)
        self.assertTrue(digest.startswith("sha256:"))
        self.assertEqual(len(digest), len("sha256:") + 64)
        self.assertEqual(digest, inputs_digest(dict(self.data)))

    def test_digest_changes_with_decisions_and_models(self):
        before = inputs_digest(self.data)
        self.data["decisions"][0]["components"] = ["beta-engine"]
        after_decision = inputs_digest(self.data)
        self.assertNotEqual(before, after_decision)
        self.data["answers"]["workload.models"][0]["weights_gb"] = 20
        self.assertNotEqual(after_decision, inputs_digest(self.data))

    def test_digest_ignores_other_keys(self):
        before = inputs_digest(self.data)
        self.data["project"] = "renamed"
        self.assertEqual(before, inputs_digest(self.data))

    def test_chosen_components_keep_order_without_duplicates(self):
        self.data["decisions"][1]["components"] = ["gamma-gateway", "alpha-engine"]
        self.assertEqual(chosen_components(self.data)[:2], ["alpha-engine", "gamma-gateway"])
        self.assertEqual(decision_for(self.data, "state")["components"], ["delta-db"])
        self.assertIsNone(decision_for({"decisions": []}, "state"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_blueprint -v`

Expected: `ModuleNotFoundError: No module named 'airgap_lib.blueprint'`.

- [ ] **Step 3: Write the module**

Create `skills/airgap-architect/scripts/airgap_lib/blueprint.py`:

```python
"""blueprint.json: the single state file of one design."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from .constants import EVIDENCE_LEVELS, LAYERS, SCHEMA_VERSION

_TOP_LEVEL = (
    ("schema_version", int),
    ("project", str),
    ("created", str),
    ("language", str),
    ("blueprint_path", str),
    ("answers", dict),
    ("assumptions", list),
    ("tier", dict),
    ("sizing", dict),
    ("decisions", list),
)
_STRING_LISTS = ("components", "existing", "custom", "alternatives_considered")


class BlueprintError(Exception):
    """blueprint.json is missing or is not a JSON object."""


def load_blueprint(path: Path) -> dict:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise BlueprintError(f"{path}: file not found") from None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise BlueprintError(f"{path}: invalid JSON ({error})") from None
    if not isinstance(data, dict):
        raise BlueprintError(f"{path}: the top level must be an object")
    return data


def save_blueprint(path: Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def inputs_digest(data: dict) -> str:
    """Digest of what the transfer manifest is generated from."""
    payload = {
        "decisions": data.get("decisions", []),
        "models": (data.get("answers") or {}).get("workload.models", []),
    }
    canonical = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def decisions_of(data: dict) -> list[dict]:
    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        return []
    return [decision for decision in decisions if isinstance(decision, dict)]


def decision_for(data: dict, layer: str) -> dict | None:
    for decision in decisions_of(data):
        if decision.get("layer") == layer:
            return decision
    return None


def chosen_components(data: dict) -> list[str]:
    """Catalog IDs named in decisions, in order, without duplicates."""
    chosen: list[str] = []
    for decision in decisions_of(data):
        for component_id in decision.get("components") or []:
            if isinstance(component_id, str) and component_id not in chosen:
                chosen.append(component_id)
    return chosen


def validate_schema(data: dict) -> list[str]:
    """Structural problems of a finished blueprint.json (lint error E1)."""
    problems: list[str] = []
    for key, kind in _TOP_LEVEL:
        if key not in data:
            problems.append(f"missing key '{key}'")
        elif not isinstance(data[key], kind) or isinstance(data[key], bool):
            problems.append(f"'{key}' must be of type {kind.__name__}")
    if problems:
        return problems
    if data["schema_version"] != SCHEMA_VERSION:
        problems.append(f"'schema_version' must be {SCHEMA_VERSION}")
    if not data["project"].strip():
        problems.append("'project' is empty")
    if not data["blueprint_path"].strip():
        problems.append("'blueprint_path' is empty")
    try:
        date.fromisoformat(data["created"])
    except ValueError:
        problems.append("'created' must be a date like 2026-11-20")
    for index, item in enumerate(data["assumptions"]):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or "value" not in item
            or item.get("evidence") not in EVIDENCE_LEVELS
        ):
            problems.append(f"assumptions[{index}] needs id, value and a valid evidence label")
    seen: set[str] = set()
    for index, decision in enumerate(data["decisions"]):
        where = f"decisions[{index}]"
        if not isinstance(decision, dict):
            problems.append(f"{where} must be an object")
            continue
        layer = decision.get("layer")
        if layer not in LAYERS:
            problems.append(f"{where}.layer must be one of " + ", ".join(LAYERS))
        elif layer in seen:
            problems.append(f"{where}: second decision for layer '{layer}'")
        seen.add(layer)
        for key in _STRING_LISTS:
            value = decision.get(key)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                problems.append(f"{where}.{key} must be a list of strings")
        if not isinstance(decision.get("rationale"), str):
            problems.append(f"{where}.rationale must be a string")
        if decision.get("evidence") not in EVIDENCE_LEVELS:
            problems.append(f"{where}.evidence must be one of " + ", ".join(EVIDENCE_LEVELS))
        if "override" not in decision:
            problems.append(f"{where}.override must be null or an object with a reason")
        elif decision["override"] is not None and not has_override(decision):
            problems.append(f"{where}.override must be null or an object with a reason")
    return problems


def has_override(decision: dict) -> bool:
    override = decision.get("override")
    return (
        isinstance(override, dict)
        and isinstance(override.get("reason"), str)
        and bool(override["reason"].strip())
    )
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: `Ran 116 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_blueprint.py skills/airgap-architect/scripts/airgap_lib/blueprint.py
git commit -m "feat: add blueprint.json state file handling"
```

---

### Task 9: Transfer manifest

The list of everything that has to be carried into the network (§14.2), rendered from the chosen components' `[airgap]` tables and the models in `workload.models`. Its header records the digest from Task 8.

**Files:**
- Create: `tests/test_transfer.py`
- Create: `skills/airgap-architect/scripts/airgap_lib/transfer.py`

**Interfaces:**
- Consumes: `chosen_components`, `decisions_of`, `inputs_digest` from `airgap_lib.blueprint`; `Catalog`; `support` builders.
- Produces, in `airgap_lib.transfer`:
  - `MANIFEST_FILENAME = "transfer-manifest.md"`, `DIGEST_PREFIX = "- Decisions digest: "`, `REGISTRY_TOKEN = "REGISTRY_HOST"`
  - `class UnknownComponentError(Exception)` with attribute `component_ids: list[str]`
  - `split_image_ref(ref: str) -> tuple[str, str]`, registry host and the rest
  - `read_manifest_digest(text: str) -> str | None`
  - `render_manifest(blueprint: dict, catalog: Catalog, generated: str) -> str`, Markdown with seven numbered sections

- [ ] **Step 1: Write the failing test**

Create `tests/test_transfer.py`:

```python
import tempfile
import unittest
from pathlib import Path

from tests import support
from airgap_lib.blueprint import inputs_digest
from airgap_lib.transfer import (
    UnknownComponentError,
    read_manifest_digest,
    render_manifest,
    split_image_ref,
)


class ImageRefTest(unittest.TestCase):
    def test_registry_host_is_split_off(self):
        self.assertEqual(
            split_image_ref("registry.example.test/team/app:1.0"),
            ("registry.example.test", "team/app:1.0"),
        )
        self.assertEqual(split_image_ref("localhost:5000/app:1.0"), ("localhost:5000", "app:1.0"))

    def test_refs_without_a_registry_are_kept_whole(self):
        self.assertEqual(split_image_ref("team/app:1.0"), ("", "team/app:1.0"))
        self.assertEqual(split_image_ref("app:1.0"), ("", "app:1.0"))


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        components = support.fixture_components()
        components[0] = support.component(
            "alpha-engine",
            "llm-serving",
            airgap={
                "images": [
                    {"ref": "registry.example.test/synthetic/alpha-engine:1.2.3", "digest": "sha256:abc"}
                ],
                "packages": ["alpha-cli 1.2.3 binary"],
                "runtime_downloads": ["model weights"],
                "telemetry": [{"what": "usage statistics", "disable": "ALPHA_TELEMETRY=0"}],
            },
            deeper_skills=[{"repo": "example/skills", "skill": "alpha-deployment"}],
        )
        self.catalog = support.load_fixture_catalog(Path(self.tmp.name), components)
        self.blueprint = {
            "project": "example",
            "answers": support.base_answers(),
            "decisions": support.base_decisions(),
        }
        self.text = render_manifest(self.blueprint, self.catalog, "2026-11-20")

    def test_header_carries_date_and_digest(self):
        self.assertIn("# Transfer manifest: example", self.text)
        self.assertIn("- Generated: 2026-11-20", self.text)
        self.assertEqual(read_manifest_digest(self.text), inputs_digest(self.blueprint))

    def test_seven_sections_in_order(self):
        headings = [line for line in self.text.splitlines() if line.startswith("## ")]
        self.assertEqual([heading[3] for heading in headings], list("1234567"))

    def test_image_row_has_target_path_and_known_digest(self):
        self.assertIn(
            "| alpha-engine | 1.2.3 | registry.example.test/synthetic/alpha-engine:1.2.3 "
            "| sha256:abc |  | REGISTRY_HOST/synthetic/alpha-engine:1.2.3 |",
            self.text,
        )

    def test_other_tables_are_filled_from_the_catalog(self):
        self.assertIn("| example-70b | chat | weights, tokenizer and configuration files |  |", self.text)
        self.assertIn("| alpha-engine | 1.2.3 | alpha-cli 1.2.3 binary |", self.text)
        self.assertIn("| alpha-engine | usage statistics | ALPHA_TELEMETRY=0 |", self.text)
        self.assertIn("| alpha-engine | model weights |", self.text)
        self.assertIn("| alpha-engine | example/skills | alpha-deployment |", self.text)

    def test_every_chosen_component_appears(self):
        for decision in self.blueprint["decisions"]:
            for component_id in decision["components"]:
                self.assertIn(f"| {component_id} |", self.text)

    def test_custom_components_are_listed_for_manual_work(self):
        self.blueprint["decisions"][2]["custom"] = ["in-house portal"]
        text = render_manifest(self.blueprint, self.catalog, "2026-11-20")
        self.assertIn("| custom: in-house portal |  | enumerate artifacts manually |", text)

    def test_empty_tables_say_none(self):
        blueprint = dict(self.blueprint, decisions=[])
        text = render_manifest(blueprint, self.catalog, "2026-11-20")
        self.assertIn("## 1. Container images\n\nNone.", text)

    def test_unknown_component_is_an_error(self):
        self.blueprint["decisions"][0]["components"] = ["ghost"]
        with self.assertRaises(UnknownComponentError) as caught:
            render_manifest(self.blueprint, self.catalog, "2026-11-20")
        self.assertEqual(caught.exception.component_ids, ["ghost"])

    def test_output_is_deterministic(self):
        self.assertEqual(self.text, render_manifest(self.blueprint, self.catalog, "2026-11-20"))

    def test_digest_is_absent_from_other_text(self):
        self.assertIsNone(read_manifest_digest("# Something else\n"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_transfer -v`

Expected: `ModuleNotFoundError: No module named 'airgap_lib.transfer'`.

- [ ] **Step 3: Write the module**

Create `skills/airgap-architect/scripts/airgap_lib/transfer.py`:

```python
"""The transfer manifest: everything that has to be carried into the network."""
from __future__ import annotations

from .blueprint import chosen_components, decisions_of, inputs_digest
from .catalog import Catalog

MANIFEST_FILENAME = "transfer-manifest.md"
DIGEST_PREFIX = "- Decisions digest: "
REGISTRY_TOKEN = "REGISTRY_HOST"


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


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    if not rows:
        return ["None.", ""]
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(_cell(cell) for cell in row) + " |" for row in rows]
    lines.append("")
    return lines


def render_manifest(blueprint: dict, catalog: Catalog, generated: str) -> str:
    component_ids = chosen_components(blueprint)
    unknown = [cid for cid in component_ids if cid not in catalog.components]
    if unknown:
        raise UnknownComponentError(unknown)
    entries = [catalog.components[cid] for cid in component_ids]
    custom = [
        name for decision in decisions_of(blueprint) for name in decision.get("custom") or []
    ]
    models = (blueprint.get("answers") or {}).get("workload.models") or []

    images, packages, telemetry, downloads, skills = [], [], [], [], []
    for entry in entries:
        airgap = entry.get("airgap", {})
        for image in airgap.get("images", []):
            _, remainder = split_image_ref(image["ref"])
            images.append(
                [
                    entry["id"],
                    entry["version"],
                    image["ref"],
                    image.get("digest", ""),
                    "",
                    f"{REGISTRY_TOKEN}/{remainder}",
                ]
            )
        for package in airgap.get("packages", []):
            packages.append([entry["id"], entry["version"], package])
        for item in airgap.get("telemetry", []):
            telemetry.append([entry["id"], item["what"], item["disable"]])
        for download in airgap.get("runtime_downloads", []):
            downloads.append([entry["id"], download])
        for skill in entry.get("deeper_skills", []):
            skills.append([entry["id"], skill["repo"], skill["skill"]])
    for name in custom:
        packages.append([f"custom: {name}", "", "enumerate artifacts manually"])

    model_rows = [
        [
            model.get("name") or f"model {index + 1}",
            model.get("role", ""),
            "weights, tokenizer and configuration files",
            "",
        ]
        for index, model in enumerate(models)
        if isinstance(model, dict)
    ]

    lines = [
        f"# Transfer manifest: {blueprint.get('project', '')}",
        "",
        f"- Generated: {generated}",
        f"{DIGEST_PREFIX}{inputs_digest(blueprint)}",
        "",
        "Fill the digest, size and checksum columns when you pull each artifact. "
        f"Replace `{REGISTRY_TOKEN}` with the address of the registry inside the network.",
        "",
        "## 1. Container images",
        "",
    ]
    lines += _table(
        ["Component", "Version", "Image", "Digest", "Size", "Target path"], images
    )
    lines += ["## 2. Model artifacts", ""]
    lines += _table(["Model", "Role", "Files to carry", "SHA-256"], model_rows)
    lines += ["## 3. Packages and binaries", ""]
    lines += _table(["Component", "Version", "Artifact"], packages)
    lines += ["## 4. Telemetry and egress settings to switch off before first start", ""]
    lines += _table(["Component", "What", "Setting"], telemetry)
    lines += ["## 5. Runtime downloads to stage in advance", ""]
    lines += _table(["Component", "Download"], downloads)
    lines += ["## 6. Per-tool skills worth carrying inside", ""]
    lines += _table(["Component", "Repository", "Skill"], skills)
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
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: `Ran 128 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_transfer.py skills/airgap-architect/scripts/airgap_lib/transfer.py
git commit -m "feat: add transfer manifest rendering"
```

---

### Task 10: Blueprint lint

The eleven errors and three warnings of §12, and one note. Every rule has at least one test that builds a clean project, breaks one thing and expects exactly that code.

How each rule reads the spec:

| Code | Implementation |
|---|---|
| E1 | `validate_schema` plus `resolve_answers` over all questions. A structural problem stops the run, because later rules cannot work on a malformed file. |
| E2 | Component IDs exist in the catalog and belong to the decision's layer. |
| E3 | The component's `tiers` include the layer's floor, unless the decision has an override. |
| E4 | All eight layers have a decision with a non-empty rationale. |
| E5 | `gateway_non_empty`: the `llm-gateway` decision has a component, an existing gateway or a custom one, unless overridden. `two_engine_replicas`: every model in the stored `sizing` has at least `sizing.ha_min_replicas` replicas. |
| E6 | Stored `tier` and `sizing` equal a fresh computation. Later rules use the fresh tier. |
| E7 | The blueprint file exists, has the ten section markers in order, has one line in its decisions section naming each chosen component with its catalog version, and has the isolation marker when required. |
| E8 | `transfer-manifest.md` exists next to `blueprint.json` and its digest matches. |
| E9 | A decision's `evidence` equals the weakest label among its own label, its components' catalog labels and `estimate` for custom components; decisions that come out as `estimate` are named in the verification section; `org.kubernetes_experience` is named there when `kubernetes_risk_note` is true. |
| E10 | `sizing.fits` is true, or the `llm-serving` decision carries an override. |
| E11 | Each `requires` of a chosen component is chosen too, or its ID appears in some decision's `existing` text. |
| W1 | A chosen component's `last_verified` is older than `lint.freshness_days`. |
| W2 | A required answer is `"unknown"`. |
| W3 | `AGENTS.md` is missing or lacks the two block markers. |
| N1 | A decision carries an override. §8.2 says lint reports every override; a note does that without failing the run. |

Findings are returned errors first, then warnings, then notes, each group in numeric order.

**Files:**
- Create: `tests/projects.py`
- Create: `tests/test_checks.py`
- Create: `skills/airgap-architect/scripts/airgap_lib/checks.py`

**Interfaces:**
- Consumes: everything produced in Tasks 2 to 9.
- Produces, in `airgap_lib.checks`:
  - `split_sections(text: str) -> tuple[dict[str, str], list[str]]`
  - `lint_blueprint(*, blueprint: dict, catalog: Catalog, blueprint_text: str | None, manifest_text: str | None, agents_text: str | None, today: date) -> list[Finding]`
  - `lint_project(blueprint_path: Path, catalog: Catalog, project_root: Path, today: date) -> list[Finding]`, which reads the blueprint file at `project_root / blueprint_path`, the manifest next to `blueprint.json` and `project_root / "AGENTS.md"`
- Produces, in `tests/projects.py`: `AGENTS_TEXT`, `blueprint_markdown(blueprint, catalog, verification="", isolation=False) -> str`, `build_blueprint(catalog, answers=None, decisions=None) -> dict`, `write_project(root, catalog, blueprint, verification="", isolation=False) -> Path`, `make_project(root, catalog, answers=None, decisions=None, verification="", isolation=False) -> Path` (returns the path of `blueprint.json`), `edit_blueprint(path, change) -> dict`.

- [ ] **Step 1: Write the failing tests**

Create `tests/projects.py`:

```python
"""Builders for complete synthetic projects: blueprint.json and the files around it."""
from __future__ import annotations

from pathlib import Path

from airgap_lib.answers import resolve_answers
from airgap_lib.blueprint import load_blueprint, save_blueprint
from airgap_lib.catalog import Catalog
from airgap_lib.constants import (
    AGENT_BLOCK_END,
    AGENT_BLOCK_START,
    ISOLATION_MARKER,
    SECTION_MARKERS,
    section_marker,
)
from airgap_lib.sizing import compute_sizing
from airgap_lib.tiering import compute_tier
from airgap_lib.transfer import MANIFEST_FILENAME, render_manifest
from tests import support

AGENTS_TEXT = f"{AGENT_BLOCK_START}\nFollow the blueprint.\n{AGENT_BLOCK_END}\n"


def blueprint_markdown(blueprint: dict, catalog: Catalog, verification: str = "", isolation: bool = False) -> str:
    """The smallest blueprint file that satisfies lint."""
    lines: list[str] = []
    for name in SECTION_MARKERS:
        lines += [section_marker(name), f"## {name}", ""]
        if name == "decisions":
            for decision in blueprint["decisions"]:
                for component_id in decision["components"]:
                    entry = catalog.components.get(component_id)
                    version = entry["version"] if entry else "unknown"
                    lines.append(f"- {decision['layer']}: {component_id} {version}")
            if isolation:
                lines += ["", section_marker(ISOLATION_MARKER), "### Isolation design"]
        if name == "verification" and verification:
            lines.append(verification)
        lines.append("")
    return "\n".join(lines)


def build_blueprint(catalog: Catalog, answers=None, decisions=None) -> dict:
    answers = support.base_answers() if answers is None else answers
    resolved, defaults_used, problems = resolve_answers(answers, catalog.rules)
    assert not problems, problems
    sizing, constants_used = compute_sizing(resolved, catalog.rules, catalog.gpu)
    return {
        "schema_version": 1,
        "project": "example",
        "created": "2026-11-20",
        "language": "en",
        "blueprint_path": "docs/airgap/blueprint.md",
        "answers": answers,
        "assumptions": defaults_used + constants_used,
        "tier": compute_tier(resolved, catalog.rules),
        "sizing": sizing,
        "decisions": support.base_decisions() if decisions is None else decisions,
    }


def write_project(root: Path, catalog: Catalog, blueprint: dict, verification: str = "", isolation: bool = False) -> Path:
    """Write blueprint.json, the blueprint file, the manifest and AGENTS.md."""
    root = Path(root)
    path = root / "docs" / "airgap" / "blueprint.json"
    save_blueprint(path, blueprint)
    (path.parent / "blueprint.md").write_text(
        blueprint_markdown(blueprint, catalog, verification, isolation), encoding="utf-8"
    )
    (path.parent / MANIFEST_FILENAME).write_text(
        render_manifest(blueprint, catalog, "2026-11-20"), encoding="utf-8"
    )
    (root / "AGENTS.md").write_text(AGENTS_TEXT, encoding="utf-8")
    return path


def make_project(root: Path, catalog: Catalog, answers=None, decisions=None, verification: str = "", isolation: bool = False) -> Path:
    blueprint = build_blueprint(catalog, answers, decisions)
    return write_project(root, catalog, blueprint, verification, isolation)


def edit_blueprint(path: Path, change) -> dict:
    """Load blueprint.json, apply `change(data)`, save it and return it."""
    data = load_blueprint(path)
    change(data)
    save_blueprint(path, data)
    return data
```

Create `tests/test_checks.py`:

```python
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tests import projects, support
from airgap_lib.checks import lint_project, split_sections
from airgap_lib.constants import SECTION_MARKERS, section_marker
from airgap_lib.transfer import MANIFEST_FILENAME, render_manifest


class LintTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "project"
        self.catalog = support.load_fixture_catalog(Path(self.tmp.name) / "catalog")

    def project(self, answers=None, decisions=None, verification="", isolation=False):
        self.path = projects.make_project(
            self.root, self.catalog, answers, decisions, verification, isolation
        )
        return self.path

    def lint(self, today=support.TODAY):
        return lint_project(self.path, self.catalog, self.root, today)

    def codes(self, today=support.TODAY):
        return [finding.code for finding in self.lint(today)]

    def edit(self, change, refresh_manifest=True):
        data = projects.edit_blueprint(self.path, change)
        if refresh_manifest:
            (self.path.parent / MANIFEST_FILENAME).write_text(
                render_manifest(data, self.catalog, "2026-11-20"), encoding="utf-8"
            )
        return data

    def decision(self, data, layer):
        return next(d for d in data["decisions"] if d["layer"] == layer)


class CleanProjectTest(LintTestCase):
    def test_a_complete_project_has_no_findings(self):
        self.project()
        self.assertEqual(self.lint(), [])


class ErrorRulesTest(LintTestCase):
    def test_e1_schema_problem_stops_further_checks(self):
        self.project()
        self.edit(lambda data: data.pop("tier"), refresh_manifest=False)
        self.assertEqual(self.codes(), ["E1"])

    def test_e1_invalid_answer(self):
        self.project()
        self.edit(lambda data: data["answers"].update({"org.isolation": "strict"}))
        findings = self.lint()
        self.assertEqual(findings[0].code, "E1")
        self.assertIn("org.isolation", findings[0].message)

    def test_e2_unknown_component(self):
        self.project()
        self.edit(
            lambda data: self.decision(data, "ui").update(components=["ghost"]),
            refresh_manifest=False,
        )
        self.assertIn("E2", self.codes())

    def test_e2_component_from_another_layer(self):
        self.project()
        self.edit(lambda data: self.decision(data, "ui").update(components=["delta-db"]))
        messages = [f.message for f in self.lint() if f.code == "E2"]
        self.assertEqual(messages, ["ui: 'delta-db' belongs to layer 'state'"])

    def test_e3_component_below_the_floor(self):
        answers = support.base_answers(**{"org.downtime_tolerance": "none"})
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, "llm-serving").update(
            components=["beta-engine"], evidence="estimate"
        )
        self.project(answers, decisions, verification="llm-serving org.kubernetes_experience")
        self.assertEqual(self.codes(), ["E3"])

    def test_e3_override_is_reported_as_a_note_instead(self):
        answers = support.base_answers(**{"org.downtime_tolerance": "none"})
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, "llm-serving").update(
            components=["beta-engine"],
            evidence="estimate",
            override={"reason": "Pilot phase runs on the small engine."},
        )
        self.project(answers, decisions, verification="llm-serving org.kubernetes_experience")
        findings = self.lint()
        self.assertEqual([f.code for f in findings], ["N1"])
        self.assertEqual(findings[0].severity, "note")
        self.assertEqual(
            findings[0].message,
            "llm-serving: override in effect: Pilot phase runs on the small engine.",
        )

    def test_e4_missing_decision_and_empty_rationale(self):
        self.project()
        self.edit(lambda data: data["decisions"].pop())
        self.edit(lambda data: self.decision(data, "ui").update(rationale="  "))
        messages = [f.message for f in self.lint() if f.code == "E4"]
        self.assertEqual(
            messages, ["ui: the decision has no rationale", "registry: no decision"]
        )

    def test_e5_required_gateway_is_empty(self):
        self.project()
        self.edit(lambda data: self.decision(data, "llm-gateway").update(components=[]))
        self.assertEqual(self.codes(), ["E5"])

    def test_e5_existing_gateway_counts(self):
        self.project()
        self.edit(
            lambda data: self.decision(data, "llm-gateway").update(
                components=[], existing=["corporate API gateway"]
            )
        )
        self.assertEqual(self.codes(), [])

    def test_e5_too_few_replicas(self):
        self.project(support.base_answers(**{"org.downtime_tolerance": "none"}),
                     verification="org.kubernetes_experience")
        self.edit(lambda data: data["sizing"]["models"][0].update(replicas=1))
        self.assertEqual(self.codes(), ["E5", "E6"])

    def test_e6_stale_sizing(self):
        self.project()
        self.edit(lambda data: data["answers"].update({"org.users_total": 20}))
        findings = self.lint()
        self.assertEqual([f.code for f in findings], ["E6"])
        self.assertIn("sizing is stale", findings[0].message)

    def test_e6_stale_tier(self):
        self.project()
        self.edit(lambda data: data["tier"].update(base="T3"))
        findings = self.lint()
        self.assertEqual([f.code for f in findings], ["E6"])
        self.assertIn("tier is stale", findings[0].message)

    def test_e7_missing_blueprint_file(self):
        self.project()
        (self.path.parent / "blueprint.md").unlink()
        self.assertEqual(self.codes(), ["E7"])

    def test_e7_missing_marker_and_missing_version(self):
        self.project()
        target = self.path.parent / "blueprint.md"
        text = target.read_text(encoding="utf-8")
        text = text.replace(section_marker("transfer"), "").replace("epsilon-ui 1.2.3", "epsilon-ui")
        target.write_text(text, encoding="utf-8")
        messages = [f.message for f in self.lint() if f.code == "E7"]
        self.assertEqual(len(messages), 2)
        self.assertIn("transfer", messages[0])
        self.assertIn("epsilon-ui", messages[1])

    def test_e7_isolation_design_marker(self):
        answers = support.base_answers(**{"org.isolation": "multi_level"})
        self.project(answers)
        self.assertEqual(self.codes(), ["E7"])
        self.project(answers, isolation=True)
        self.assertEqual(self.codes(), [])

    def test_e8_missing_and_stale_manifest(self):
        self.project()
        self.edit(
            lambda data: self.decision(data, "ui").update(rationale="Changed."),
            refresh_manifest=False,
        )
        self.assertEqual(self.codes(), ["E8"])
        (self.path.parent / MANIFEST_FILENAME).unlink()
        self.assertEqual(self.codes(), ["E8"])

    def test_e9_estimate_decision_must_be_listed(self):
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, "llm-serving").update(
            components=["beta-engine"], evidence="estimate"
        )
        self.project(decisions=decisions)
        self.assertEqual(self.codes(), ["E9"])
        self.project(decisions=decisions, verification="Benchmark llm-serving before production.")
        self.assertEqual(self.codes(), [])

    def test_e9_label_must_be_the_weakest_input(self):
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, "llm-serving").update(components=["beta-engine"])
        self.project(decisions=decisions, verification="llm-serving")
        messages = [f.message for f in self.lint() if f.code == "E9"]
        self.assertEqual(len(messages), 1)
        self.assertIn("must be 'estimate'", messages[0])

    def test_e9_custom_components_count_as_estimates(self):
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, "ui").update(custom=["in-house portal"])
        self.project(decisions=decisions)
        self.assertEqual(self.codes(), ["E9", "E9"])

    def test_e9_kubernetes_risk_must_be_listed(self):
        self.project(support.base_answers(**{"org.downtime_tolerance": "none"}))
        self.assertEqual(self.codes(), ["E9"])

    def test_e10_hardware_does_not_fit(self):
        answers = support.base_answers(
            **{"workload.models": [{"role": "chat", "params_b": 671, "precision": "fp8"}],
               "hardware.gpus": [{"model": "TG141", "count": 4}]}
        )
        self.project(answers)
        self.assertEqual(self.codes(), ["E10"])
        self.edit(
            lambda data: self.decision(data, "llm-serving").update(
                override={"reason": "Four more GPUs are on order."}
            )
        )
        self.assertEqual(self.codes(), ["N1"])

    def test_e11_missing_required_component(self):
        self.project()
        self.edit(lambda data: self.decision(data, "state").update(components=[]))
        messages = [f.message for f in self.lint() if f.code == "E11"]
        self.assertEqual(len(messages), 1)
        self.assertIn("'gamma-gateway' requires 'delta-db'", messages[0])

    def test_e11_is_satisfied_by_existing_infrastructure(self):
        self.project()
        self.edit(
            lambda data: self.decision(data, "state").update(
                components=[], existing=["Delta-DB cluster run by the data team"]
            )
        )
        self.assertEqual(self.codes(), [])


class WarningRulesTest(LintTestCase):
    def test_w1_stale_component_in_use(self):
        self.project()
        self.assertEqual(self.codes(today=date(2027, 11, 20)), ["W1"] * 8)

    def test_w2_unknown_answer(self):
        self.project(support.base_answers(**{"transfer.channel": "unknown"}))
        findings = self.lint()
        self.assertEqual([f.code for f in findings], ["W2"])
        self.assertEqual(findings[0].severity, "warning")

    def test_w3_missing_agent_block(self):
        self.project()
        (self.root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        self.assertEqual(self.codes(), ["W3"])
        (self.root / "AGENTS.md").unlink()
        self.assertEqual(self.codes(), ["W3"])


class SectionsTest(unittest.TestCase):
    def test_sections_are_split_at_markers(self):
        text = "\n".join(f"{section_marker(name)}\nbody of {name}" for name in SECTION_MARKERS)
        sections, problems = split_sections(text)
        self.assertEqual(problems, [])
        self.assertEqual(list(sections), list(SECTION_MARKERS))
        self.assertIn("body of sizing", sections["sizing"])
        self.assertNotIn("body of transfer", sections["sizing"])

    def test_out_of_order_markers_are_reported(self):
        names = list(SECTION_MARKERS)
        names[0], names[1] = names[1], names[0]
        text = "\n".join(section_marker(name) for name in names)
        self.assertEqual(split_sections(text)[1], ["section markers are out of order"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_checks -v`

Expected: `ModuleNotFoundError: No module named 'airgap_lib.checks'`.

- [ ] **Step 3: Write the module**

Create `skills/airgap-architect/scripts/airgap_lib/checks.py`:

```python
"""Blueprint lint: errors E1-E11, warnings W1-W3 and note N1 of the design spec."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from .answers import QUESTIONS, resolve_answers
from .blueprint import (
    chosen_components,
    decision_for,
    decisions_of,
    has_override,
    inputs_digest,
    load_blueprint,
    validate_schema,
)
from .catalog import Catalog, is_stale
from .constants import (
    AGENT_BLOCK_END,
    AGENT_BLOCK_START,
    ISOLATION_MARKER,
    LAYERS,
    SECTION_MARKERS,
    UNKNOWN,
    section_marker,
    weakest,
)
from .findings import SEVERITIES, Finding
from .sizing import SizingInputError, compute_sizing
from .tiering import compute_tier
from .transfer import MANIFEST_FILENAME, read_manifest_digest


def split_sections(text: str) -> tuple[dict[str, str], list[str]]:
    """Map each section marker to the text that follows it; also return problems."""
    problems: list[str] = []
    positions: list[tuple[int, str]] = []
    for name in SECTION_MARKERS:
        position = text.find(section_marker(name))
        if position < 0:
            problems.append(f"section marker '{section_marker(name)}' is missing")
        else:
            positions.append((position, name))
    if [name for _, name in sorted(positions)] != [name for _, name in positions]:
        problems.append("section markers are out of order")
    ordered = sorted(positions)
    sections: dict[str, str] = {}
    for index, (position, name) in enumerate(ordered):
        end = ordered[index + 1][0] if index + 1 < len(ordered) else len(text)
        sections[name] = text[position:end]
    return sections, problems


def _report_order(finding: Finding) -> tuple[int, int]:
    """Errors, then warnings, then notes, each in numeric order; the sort is stable."""
    return (SEVERITIES.index(finding.severity), int(finding.code[1:]))


def _effective_evidence(decision: dict, catalog: Catalog) -> str:
    labels = [decision.get("evidence")]
    for component_id in decision.get("components") or []:
        entry = catalog.components.get(component_id)
        if entry:
            labels.append(entry.get("evidence", {}).get("level"))
    if decision.get("custom"):
        labels.append("estimate")
    return weakest(label for label in labels if isinstance(label, str))


def lint_blueprint(
    *,
    blueprint: dict,
    catalog: Catalog,
    blueprint_text: str | None,
    manifest_text: str | None,
    agents_text: str | None,
    today: date,
) -> list[Finding]:
    findings: list[Finding] = []
    rules = catalog.rules

    # E1: structure and answers.
    schema_problems = validate_schema(blueprint)
    findings += [Finding("E1", problem) for problem in schema_problems]
    if schema_problems:
        return findings
    answers = blueprint["answers"]
    resolved, _, answer_problems = resolve_answers(answers, rules)
    findings += [Finding("E1", problem) for problem in answer_problems]

    decisions = decisions_of(blueprint)

    # E2: components exist and belong to the decision's layer.
    for decision in decisions:
        for component_id in decision["components"]:
            entry = catalog.components.get(component_id)
            if entry is None:
                findings.append(
                    Finding("E2", f"{decision['layer']}: unknown component '{component_id}'")
                )
            elif entry.get("layer") != decision["layer"]:
                findings.append(
                    Finding(
                        "E2",
                        f"{decision['layer']}: '{component_id}' belongs to layer "
                        f"'{entry.get('layer')}'",
                    )
                )

    # E6: stored tier and sizing are fresh. Later checks use the fresh values.
    tier = sizing = None
    if not answer_problems:
        tier = compute_tier(resolved, rules)
        if blueprint["tier"] != tier:
            findings.append(Finding("E6", "tier is stale; run tier.py again"))
        try:
            sizing, _ = compute_sizing(resolved, rules, catalog.gpu)
        except SizingInputError as error:
            findings += [Finding("E1", problem) for problem in error.problems]
        else:
            if blueprint["sizing"] != sizing:
                findings.append(Finding("E6", "sizing is stale; run size.py again"))

    # E3: components allow the layer's floor tier.
    if tier:
        for decision in decisions:
            floor = tier["floors"].get(decision["layer"])
            for component_id in decision["components"]:
                entry = catalog.components.get(component_id)
                if entry and floor not in entry.get("tiers", []) and not has_override(decision):
                    findings.append(
                        Finding(
                            "E3",
                            f"{decision['layer']}: '{component_id}' does not allow floor {floor}; "
                            "choose another component or record an override",
                        )
                    )

    # E4: every layer has a decision with a rationale.
    for layer in LAYERS:
        decision = decision_for(blueprint, layer)
        if decision is None:
            findings.append(Finding("E4", f"{layer}: no decision"))
        elif not decision["rationale"].strip():
            findings.append(Finding("E4", f"{layer}: the decision has no rationale"))

    # E5: escalator requirements.
    if tier:
        requirements = tier["requirements"]
        gateway = decision_for(blueprint, "llm-gateway")
        if requirements["gateway_non_empty"] and gateway is not None:
            empty = not (gateway["components"] or gateway["existing"] or gateway["custom"])
            if empty and not has_override(gateway):
                findings.append(
                    Finding("E5", "llm-gateway: a gateway is required but the decision is empty")
                )
        if requirements["two_engine_replicas"] and sizing:
            minimum = rules.value("sizing.ha_min_replicas")
            for model in blueprint["sizing"].get("models", []):
                if isinstance(model, dict) and model.get("replicas", 0) < minimum:
                    findings.append(
                        Finding(
                            "E5",
                            f"llm-serving: model '{model.get('name', '')}' has fewer than "
                            f"{minimum} replicas",
                        )
                    )

    # E7 and E9 read the blueprint file.
    sections: dict[str, str] = {}
    if blueprint_text is None:
        findings.append(
            Finding("E7", f"blueprint file not found at '{blueprint['blueprint_path']}'")
        )
    else:
        sections, marker_problems = split_sections(blueprint_text)
        findings += [Finding("E7", problem) for problem in marker_problems]
        decision_lines = sections.get("decisions", "").splitlines()
        for component_id in chosen_components(blueprint):
            entry = catalog.components.get(component_id)
            if entry is None:
                continue
            if not any(
                component_id in line and entry["version"] in line for line in decision_lines
            ):
                findings.append(
                    Finding(
                        "E7",
                        f"the decisions section needs a line naming '{component_id}' with "
                        f"version {entry['version']}",
                    )
                )
        if (
            tier
            and tier["requirements"]["isolation_design_section"]
            and section_marker(ISOLATION_MARKER) not in blueprint_text
        ):
            findings.append(
                Finding("E7", f"marker '{section_marker(ISOLATION_MARKER)}' is missing")
            )

    # E8: transfer manifest exists and matches the decisions.
    if manifest_text is None:
        findings.append(Finding("E8", f"{MANIFEST_FILENAME} not found; run manifest.py"))
    elif read_manifest_digest(manifest_text) != inputs_digest(blueprint):
        findings.append(Finding("E8", f"{MANIFEST_FILENAME} is stale; run manifest.py again"))

    # E9: estimate-backed decisions are listed for verification.
    verification_text = sections.get("verification")
    for decision in decisions:
        effective = _effective_evidence(decision, catalog)
        if decision.get("evidence") != effective:
            findings.append(
                Finding(
                    "E9",
                    f"{decision['layer']}: evidence must be '{effective}', the weakest label "
                    "among the decision's inputs",
                )
            )
        if (
            effective == "estimate"
            and verification_text is not None
            and decision["layer"] not in verification_text
        ):
            findings.append(
                Finding(
                    "E9",
                    f"{decision['layer']}: the decision rests on an estimate and must be "
                    "listed in the verification section",
                )
            )
    if (
        tier
        and tier["requirements"]["kubernetes_risk_note"]
        and verification_text is not None
        and "org.kubernetes_experience" not in verification_text
    ):
        findings.append(
            Finding(
                "E9",
                "the verification section must list org.kubernetes_experience as a risk",
            )
        )

    # E10: the hardware covers the sizing.
    if blueprint["sizing"].get("fits") is not True:
        engine = decision_for(blueprint, "llm-serving")
        if engine is None or not has_override(engine):
            findings.append(
                Finding(
                    "E10",
                    "sizing.fits is not true; resolve it or record an override on the "
                    "llm-serving decision",
                )
            )

    # E11: required components are present.
    chosen = set(chosen_components(blueprint))
    existing_text = " ".join(
        name.lower() for decision in decisions for name in decision["existing"]
    )
    for component_id in sorted(chosen):
        entry = catalog.components.get(component_id)
        for required in (entry or {}).get("requires", []):
            if required not in chosen and required.lower() not in existing_text:
                findings.append(
                    Finding(
                        "E11",
                        f"'{component_id}' requires '{required}', which is neither chosen "
                        "nor named in existing",
                    )
                )

    # W1: stale catalog entries in use.
    limit = rules.value("lint.freshness_days")
    for component_id in sorted(chosen):
        entry = catalog.components.get(component_id)
        if entry and is_stale(entry.get("last_verified"), today, limit):
            findings.append(
                Finding(
                    "W1",
                    f"{component_id}: last verified {entry['last_verified']}, "
                    f"more than {limit} days ago",
                )
            )

    # W2: required answers given as "unknown".
    for question in QUESTIONS:
        if question.required and answers.get(question.id) == UNKNOWN:
            findings.append(Finding("W2", f"{question.id}: unknown; a default was used"))

    # W3: agent instruction block.
    if (
        agents_text is None
        or AGENT_BLOCK_START not in agents_text
        or AGENT_BLOCK_END not in agents_text
    ):
        findings.append(Finding("W3", "the agent instruction block is missing from AGENTS.md"))

    # N1: every override in effect is reported.
    for decision in decisions:
        if has_override(decision):
            reason = decision["override"]["reason"].strip()
            findings.append(
                Finding("N1", f"{decision['layer']}: override in effect: {reason}")
            )

    return sorted(findings, key=_report_order)


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError):
        return None


def lint_project(
    blueprint_path: Path, catalog: Catalog, project_root: Path, today: date
) -> list[Finding]:
    """Read the project's files from disk and lint them."""
    blueprint_path = Path(blueprint_path)
    project_root = Path(project_root)
    blueprint = load_blueprint(blueprint_path)
    relative = blueprint.get("blueprint_path")
    blueprint_text = None
    if isinstance(relative, str) and relative.strip():
        blueprint_text = _read(project_root / relative)
    return lint_blueprint(
        blueprint=blueprint,
        catalog=catalog,
        blueprint_text=blueprint_text,
        manifest_text=_read(blueprint_path.parent / MANIFEST_FILENAME),
        agents_text=_read(project_root / "AGENTS.md"),
        today=today,
    )
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: `Ran 157 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/projects.py tests/test_checks.py skills/airgap-architect/scripts/airgap_lib/checks.py
git commit -m "feat: add blueprint lint rules E1-E11, W1-W3 and N1"
```

---

### Task 11: The four scripts

Thin command-line wrappers (§12). They parse arguments, call the library, write into `blueprint.json` or next to it, and print a short summary. The tests run them as subprocesses and check exit codes and files.

**Files:**
- Create: `tests/test_cli.py`
- Create: `tests/test_stdlib_only.py`
- Create: `skills/airgap-architect/scripts/airgap_lib/cli.py`
- Create: `skills/airgap-architect/scripts/tier.py`
- Create: `skills/airgap-architect/scripts/size.py`
- Create: `skills/airgap-architect/scripts/manifest.py`
- Create: `skills/airgap-architect/scripts/lint.py`

**Interfaces:**
- Consumes: everything produced in Tasks 2 to 10.
- Produces, in `airgap_lib.cli`: `EXIT_OK = 0`, `EXIT_LINT_ERRORS = 1`, `EXIT_INPUT = 2`, `EXIT_ENVIRONMENT = 3`; `fail(code, lines)`; `make_parser(description, blueprint_required=True)`; `open_catalog(directory) -> Catalog`; `open_blueprint(path) -> dict`; `answers_of(blueprint) -> dict`; `fail_on_answer_problems(problems)`.
- Command lines:
  - `tier.py --blueprint PATH [--catalog DIR]` writes `tier`.
  - `size.py --blueprint PATH [--catalog DIR]` writes `sizing` and `assumptions`.
  - `manifest.py --blueprint PATH [--catalog DIR] [--out FILE] [--date YYYY-MM-DD]` writes `transfer-manifest.md` next to `blueprint.json`.
  - `lint.py --blueprint PATH [--catalog DIR] [--project-root DIR] [--format text|json] [--today YYYY-MM-DD]`, or `lint.py --catalog-only [--catalog DIR]`.
- Each script defines `main(argv=None) -> int`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cli.py`:

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import SCRIPTS_DIR, projects, support
from airgap_lib.blueprint import load_blueprint, save_blueprint
from airgap_lib.catalog import load_catalog
from airgap_lib.transfer import MANIFEST_FILENAME


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.catalog_dir = support.make_catalog(Path(self.tmp.name) / "catalog")
        self.root = Path(self.tmp.name) / "project"
        self.blueprint = self.root / "docs" / "airgap" / "blueprint.json"

    def start(self, answers=None):
        """Write the blueprint.json an interview leaves behind: answers only."""
        save_blueprint(
            self.blueprint,
            {
                "schema_version": 1,
                "project": "example",
                "created": "2026-11-20",
                "language": "en",
                "blueprint_path": "docs/airgap/blueprint.md",
                "answers": support.base_answers() if answers is None else answers,
                "assumptions": [],
                "tier": {},
                "sizing": {},
                "decisions": [],
            },
        )

    def run_script(self, name, *args, catalog=True):
        command = [sys.executable, str(SCRIPTS_DIR / name)]
        if catalog:
            command += ["--catalog", str(self.catalog_dir)]
        return subprocess.run(command + list(args), capture_output=True, text=True)

    def with_blueprint(self, name, *args):
        return self.run_script(name, "--blueprint", str(self.blueprint), *args)

    def lint(self, *args):
        return self.with_blueprint(
            "lint.py", "--project-root", str(self.root), "--today", "2026-11-20", *args
        )


class PipelineTest(CliTestCase):
    def test_tier_size_manifest_lint_in_order(self):
        self.start()

        tier = self.with_blueprint("tier.py")
        self.assertEqual(tier.returncode, 0, tier.stderr)
        self.assertIn("Base tier: T2", tier.stdout)
        self.assertEqual(load_blueprint(self.blueprint)["tier"]["base"], "T2")

        size = self.with_blueprint("size.py")
        self.assertEqual(size.returncode, 0, size.stderr)
        self.assertIn("Peak concurrency: 6-11", size.stdout)
        self.assertIn("benchmark before production", size.stdout)
        data = load_blueprint(self.blueprint)
        self.assertEqual(data["sizing"]["total_gpus"], 1)
        self.assertIn("sizing.overhead", [item["id"] for item in data["assumptions"]])

        data = projects.edit_blueprint(
            self.blueprint, lambda d: d.update(decisions=support.base_decisions())
        )
        manifest = self.with_blueprint("manifest.py", "--date", "2026-11-20")
        self.assertEqual(manifest.returncode, 0, manifest.stderr)
        self.assertTrue((self.blueprint.parent / MANIFEST_FILENAME).is_file())

        catalog, _ = load_catalog(self.catalog_dir)
        (self.blueprint.parent / "blueprint.md").write_text(
            projects.blueprint_markdown(data, catalog), encoding="utf-8"
        )
        (self.root / "AGENTS.md").write_text(projects.AGENTS_TEXT, encoding="utf-8")
        lint = self.lint()
        self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)
        self.assertIn("OK: no findings", lint.stdout)


class TierAndSizeExitCodesTest(CliTestCase):
    def test_missing_answers_exit_2_and_are_listed_by_id(self):
        answers = support.base_answers()
        del answers["org.isolation"]
        self.start(answers)
        result = self.with_blueprint("tier.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("org.isolation: missing", result.stderr)
        self.assertEqual(load_blueprint(self.blueprint)["tier"], {})

    def test_tier_ignores_answers_it_does_not_need(self):
        answers = support.base_answers()
        del answers["workload.models"]
        self.start(answers)
        self.assertEqual(self.with_blueprint("tier.py").returncode, 0)
        result = self.with_blueprint("size.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("workload.models: missing", result.stderr)

    def test_missing_blueprint_file_exits_2(self):
        result = self.with_blueprint("tier.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("file not found", result.stderr)

    def test_unknown_gpu_without_vram_exits_2(self):
        self.start(support.base_answers(**{"hardware.gpus": [{"model": "mystery", "count": 1}]}))
        result = self.with_blueprint("size.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("supply vram_gb", result.stderr)

    def test_unknown_answers_become_assumptions(self):
        self.start(support.base_answers(**{"org.audit_required": "unknown"}))
        self.assertEqual(self.with_blueprint("size.py").returncode, 0)
        ids = [item["id"] for item in load_blueprint(self.blueprint)["assumptions"]]
        self.assertEqual(ids[0], "answers.org.audit_required")

    def test_unreadable_catalog_exits_3(self):
        self.start()
        result = self.run_script(
            "tier.py", "--catalog", str(self.root / "nowhere"), "--blueprint", str(self.blueprint),
            catalog=False,
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("cannot read the catalog", result.stderr)


class ManifestCliTest(CliTestCase):
    def test_unknown_component_exits_2(self):
        self.start()
        decisions = support.base_decisions()
        decisions[0]["components"] = ["ghost"]
        projects.edit_blueprint(self.blueprint, lambda d: d.update(decisions=decisions))
        result = self.with_blueprint("manifest.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ghost", result.stderr)

    def test_out_option(self):
        self.start()
        target = self.root / "elsewhere" / "manifest.md"
        result = self.with_blueprint("manifest.py", "--out", str(target))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(target.is_file())


class LintCliTest(CliTestCase):
    def test_errors_exit_1_and_json_is_parseable(self):
        self.start()
        result = self.lint("--format", "json")
        self.assertEqual(result.returncode, 1)
        findings = json.loads(result.stdout)
        self.assertIn("E4", [finding["code"] for finding in findings])
        self.assertEqual(
            set(findings[0]), {"code", "severity", "message"}
        )

    def test_catalog_only_passes_on_a_valid_catalog(self):
        result = self.run_script("lint.py", "--catalog-only", "--today", "2026-11-20")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("OK: no findings", result.stdout)

    def test_catalog_only_fails_on_a_bad_entry(self):
        bad = support.component("bad-entry", "ui", version="latest")
        (self.catalog_dir / "components" / "bad-entry.toml").write_text(
            support.component_toml(bad), encoding="utf-8"
        )
        result = self.run_script("lint.py", "--catalog-only", "--today", "2026-11-20")
        self.assertEqual(result.returncode, 1)
        self.assertIn("C1 error: bad-entry", result.stdout)

    def test_blueprint_is_required_without_catalog_only(self):
        result = self.run_script("lint.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--blueprint is required", result.stderr)

    def test_default_catalog_is_the_shipped_one(self):
        result = self.run_script("lint.py", "--catalog-only", catalog=False)
        self.assertNotEqual(result.returncode, 3, result.stderr)


if __name__ == "__main__":
    unittest.main()
```

Create `tests/test_stdlib_only.py`:

```python
import ast
import sys
import unittest

from tests import SCRIPTS_DIR

LOCAL_PACKAGES = {"airgap_lib"}
NETWORK_MODULES = {
    "asyncio", "ftplib", "http", "imaplib", "poplib", "smtplib", "socket",
    "socketserver", "ssl", "telnetlib", "urllib", "webbrowser", "xmlrpc",
}


def imported_modules(path):
    """Top-level names of every absolute import in a Python file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".")[0]


class StandardLibraryOnlyTest(unittest.TestCase):
    def setUp(self):
        self.files = sorted(SCRIPTS_DIR.rglob("*.py"))

    def test_all_scripts_are_found(self):
        names = {path.name for path in self.files}
        self.assertTrue({"tier.py", "size.py", "manifest.py", "lint.py"} <= names)

    def test_only_the_standard_library_is_imported(self):
        offenders = [
            f"{path.relative_to(SCRIPTS_DIR)}: {module}"
            for path in self.files
            for module in imported_modules(path)
            if module not in sys.stdlib_module_names and module not in LOCAL_PACKAGES
        ]
        self.assertEqual(offenders, [])

    def test_no_network_module_is_imported(self):
        offenders = [
            f"{path.relative_to(SCRIPTS_DIR)}: {module}"
            for path in self.files
            for module in imported_modules(path)
            if module in NETWORK_MODULES
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `python3 -m unittest tests.test_cli tests.test_stdlib_only -v`

Expected: 13 failures in `test_cli` (the scripts do not exist yet, so each subprocess ends with Python's "can't open file" error) and 1 failure in `test_stdlib_only` (`test_all_scripts_are_found`).

- [ ] **Step 3: Write the shared module and the scripts**

Create `skills/airgap-architect/scripts/airgap_lib/cli.py`:

```python
"""Argument parsing and exit codes shared by the four scripts."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .blueprint import BlueprintError, load_blueprint
from .catalog import Catalog, default_catalog_dir, load_catalog
from .findings import format_text, has_errors

EXIT_OK = 0
EXIT_LINT_ERRORS = 1
EXIT_INPUT = 2
EXIT_ENVIRONMENT = 3


def fail(code: int, lines: list[str]) -> None:
    for line in lines:
        print(line, file=sys.stderr)
    raise SystemExit(code)


def make_parser(description: str, blueprint_required: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--blueprint",
        required=blueprint_required,
        help="path to blueprint.json (usually docs/airgap/blueprint.json)",
    )
    parser.add_argument(
        "--catalog",
        default=str(default_catalog_dir()),
        help="catalog directory (default: the catalog shipped with the skill)",
    )
    return parser


def open_catalog(directory: str) -> Catalog:
    try:
        catalog, findings = load_catalog(Path(directory))
    except (OSError, ValueError) as error:
        fail(EXIT_ENVIRONMENT, [f"cannot read the catalog at {directory}: {error}"])
    if has_errors(findings):
        fail(EXIT_ENVIRONMENT, [format_text(findings)])
    return catalog


def open_blueprint(path: str) -> dict:
    try:
        return load_blueprint(Path(path))
    except BlueprintError as error:
        fail(EXIT_INPUT, [str(error)])


def answers_of(blueprint: dict) -> dict:
    answers = blueprint.get("answers")
    if not isinstance(answers, dict):
        fail(EXIT_INPUT, ["blueprint.json has no 'answers' object"])
    return answers


def fail_on_answer_problems(problems: list[str]) -> None:
    if problems:
        fail(EXIT_INPUT, ["Missing or invalid answers:"] + [f"  {p}" for p in problems])
```

Create `skills/airgap-architect/scripts/tier.py`:

```python
#!/usr/bin/env python3
"""Compute the base tier and per-layer floors and write them to blueprint.json."""
from airgap_lib import cli
from airgap_lib.answers import resolve_answers
from airgap_lib.blueprint import save_blueprint
from airgap_lib.tiering import TIER_ANSWERS, compute_tier


def main(argv=None) -> int:
    args = cli.make_parser(__doc__).parse_args(argv)
    catalog = cli.open_catalog(args.catalog)
    blueprint = cli.open_blueprint(args.blueprint)
    resolved, _, problems = resolve_answers(
        cli.answers_of(blueprint), catalog.rules, TIER_ANSWERS
    )
    cli.fail_on_answer_problems(problems)
    tier = compute_tier(resolved, catalog.rules)
    blueprint["tier"] = tier
    save_blueprint(args.blueprint, blueprint)
    print(f"Base tier: {tier['base']}")
    for layer, floor in tier["floors"].items():
        print(f"  {layer}: {floor}")
    for reason in tier["reasons"]:
        print(f"- {reason}")
    return cli.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `skills/airgap-architect/scripts/size.py`:

```python
#!/usr/bin/env python3
"""Size GPUs, servers and power and write sizing and assumptions to blueprint.json."""
from airgap_lib import cli
from airgap_lib.answers import resolve_answers
from airgap_lib.blueprint import save_blueprint
from airgap_lib.sizing import SIZING_ANSWERS, SizingInputError, compute_sizing


def main(argv=None) -> int:
    args = cli.make_parser(__doc__).parse_args(argv)
    catalog = cli.open_catalog(args.catalog)
    blueprint = cli.open_blueprint(args.blueprint)
    resolved, defaults_used, problems = resolve_answers(
        cli.answers_of(blueprint), catalog.rules, SIZING_ANSWERS
    )
    cli.fail_on_answer_problems(problems)
    try:
        sizing, constants_used = compute_sizing(resolved, catalog.rules, catalog.gpu)
    except SizingInputError as error:
        cli.fail_on_answer_problems(error.problems)
    blueprint["sizing"] = sizing
    blueprint["assumptions"] = defaults_used + constants_used
    save_blueprint(args.blueprint, blueprint)
    concurrency = sizing["concurrency"]
    print(f"Peak concurrency: {concurrency['low']}-{concurrency['high']} requests in flight")
    for model in sizing["models"]:
        print(
            f"  {model['name'] or model['role']}: {model['replicas']} replica(s) x "
            f"{model['gpus_per_replica']} GPU(s), KV cache {model['kv']['status']}"
        )
    print(
        f"Total: {sizing['total_gpus']} GPU(s), {sizing['servers']} server(s), "
        f"power {sizing['power_kw']} kW, fits: {sizing['fits']}"
    )
    for warning in sizing["warnings"]:
        print(f"! {warning}")
    print("Throughput is not predicted: benchmark before production.")
    return cli.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `skills/airgap-architect/scripts/manifest.py`:

```python
#!/usr/bin/env python3
"""Generate transfer-manifest.md from the decisions in blueprint.json."""
from datetime import date
from pathlib import Path

from airgap_lib import cli
from airgap_lib.transfer import MANIFEST_FILENAME, UnknownComponentError, render_manifest


def main(argv=None) -> int:
    parser = cli.make_parser(__doc__)
    parser.add_argument(
        "--out", help=f"output file (default: {MANIFEST_FILENAME} next to blueprint.json)"
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="generation date as YYYY-MM-DD (default: today)",
    )
    args = parser.parse_args(argv)
    catalog = cli.open_catalog(args.catalog)
    blueprint = cli.open_blueprint(args.blueprint)
    try:
        text = render_manifest(blueprint, catalog, args.date)
    except UnknownComponentError as error:
        cli.fail(cli.EXIT_INPUT, [str(error)])
    out = Path(args.out) if args.out else Path(args.blueprint).parent / MANIFEST_FILENAME
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out}")
    return cli.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `skills/airgap-architect/scripts/lint.py`:

```python
#!/usr/bin/env python3
"""Check a blueprint against the catalog, or check the catalog alone."""
from datetime import date
from pathlib import Path

from airgap_lib import cli
from airgap_lib.blueprint import BlueprintError
from airgap_lib.catalog import load_catalog, validate_catalog
from airgap_lib.checks import lint_project
from airgap_lib.findings import format_json, format_text, has_errors


def main(argv=None) -> int:
    parser = cli.make_parser(__doc__, blueprint_required=False)
    parser.add_argument(
        "--catalog-only", action="store_true", help="validate the catalog and stop"
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="directory that blueprint_path and AGENTS.md are relative to (default: .)",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--today",
        default=date.today().isoformat(),
        help="date used for freshness checks, YYYY-MM-DD (default: today)",
    )
    args = parser.parse_args(argv)
    today = date.fromisoformat(args.today)
    if args.catalog_only:
        try:
            catalog, findings = load_catalog(Path(args.catalog))
        except (OSError, ValueError) as error:
            cli.fail(cli.EXIT_ENVIRONMENT, [f"cannot read the catalog: {error}"])
        findings = findings + validate_catalog(catalog, today)
    else:
        if not args.blueprint:
            parser.error("--blueprint is required unless --catalog-only is given")
        catalog = cli.open_catalog(args.catalog)
        try:
            findings = lint_project(
                Path(args.blueprint), catalog, Path(args.project_root), today
            )
        except BlueprintError as error:
            cli.fail(cli.EXIT_INPUT, [str(error)])
    print(format_json(findings) if args.format == "json" else format_text(findings))
    return cli.EXIT_LINT_ERRORS if has_errors(findings) else cli.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: `Ran 174 tests` and `OK`.

Then run the catalog check on the shipped catalog, which is still empty of components:

Run: `python3 skills/airgap-architect/scripts/lint.py --catalog-only`

Expected: `OK: no findings` and exit code 0.

- [ ] **Step 5: Commit**

```bash
git add tests/test_cli.py tests/test_stdlib_only.py \
  skills/airgap-architect/scripts/airgap_lib/cli.py \
  skills/airgap-architect/scripts/tier.py skills/airgap-architect/scripts/size.py \
  skills/airgap-architect/scripts/manifest.py skills/airgap-architect/scripts/lint.py
git commit -m "feat: add tier, size, manifest and lint scripts"
```

---

### Task 12: Scenario fixtures

Three organizations (§17.5). Each has the prompt a user would write, the answers a correct interview extracts from it, and the expected result. The `deterministic` part is checked in CI here. The `decisions` and `process` parts are scored by hand in Task 24.

The numbers were computed with the shipped `rules.toml`:

| Scenario | Base tier | Concurrency | GPUs per replica × replicas | Total GPUs | Servers | Power |
|---|---|---|---|---|---|---|
| `lab` | T1 | 1 to 1 | 1 × 1 | 1 | 1 | unknown |
| `department` | T2 | 6 to 11 | 8 × 1 | 8 | 1 | 10.1 kW |
| `enterprise` | T3 | 132 to 216 | 1 × 14 | 14 | 2 | 17.6 kW |

**Files:**
- Create: `tests/test_scenarios.py`
- Create: `evals/scenarios/lab/prompt.md`, `evals/scenarios/lab/answers.json`, `evals/scenarios/lab/expected.json`
- Create: `evals/scenarios/department/prompt.md`, `evals/scenarios/department/answers.json`, `evals/scenarios/department/expected.json`
- Create: `evals/scenarios/enterprise/prompt.md`, `evals/scenarios/enterprise/answers.json`, `evals/scenarios/enterprise/expected.json`

**Interfaces:**
- Consumes: `resolve_answers`, `compute_tier`, `compute_sizing`, `load_catalog`; `CATALOG_DIR`, `SCENARIOS_DIR`.
- Produces: `expected.json` with three keys. `deterministic` holds `tier` (`base`, `floors`, `requirements`) and `sizing` (`concurrency`, `models`, `total_gpus`, `servers`, `power_kw`, `fits`). `decisions` maps a layer to checks named `components`, `includes`, `mentions` or `empty` (defined in `evals/README.md`, Task 20). `process` is a list of statements to verify by hand.

- [ ] **Step 1: Write the failing test**

Create `tests/test_scenarios.py`:

```python
import json
import unittest

from tests import CATALOG_DIR, SCENARIOS_DIR
from airgap_lib.answers import resolve_answers
from airgap_lib.catalog import load_catalog
from airgap_lib.sizing import compute_sizing
from airgap_lib.tiering import compute_tier

SCENARIOS = ("department", "enterprise", "lab")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ScenarioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.load_findings = load_catalog(CATALOG_DIR)

    def test_the_three_scenarios_exist_with_all_files(self):
        self.assertEqual(self.load_findings, [])
        found = sorted(path.name for path in SCENARIOS_DIR.iterdir() if path.is_dir())
        self.assertEqual(found, list(SCENARIOS))
        for name in SCENARIOS:
            for file_name in ("answers.json", "expected.json", "prompt.md"):
                path = SCENARIOS_DIR / name / file_name
                self.assertTrue(path.is_file() and path.stat().st_size > 0, str(path))

    def test_tier_and_sizing_match_the_expectations(self):
        rules = self.catalog.rules
        for name in SCENARIOS:
            with self.subTest(scenario=name):
                answers = read_json(SCENARIOS_DIR / name / "answers.json")
                expected = read_json(SCENARIOS_DIR / name / "expected.json")["deterministic"]
                resolved, _, problems = resolve_answers(answers, rules)
                self.assertEqual(problems, [])

                tier = compute_tier(resolved, rules)
                self.assertEqual(tier["base"], expected["tier"]["base"])
                self.assertEqual(tier["floors"], expected["tier"]["floors"])
                self.assertEqual(tier["requirements"], expected["tier"]["requirements"])

                sizing, _ = compute_sizing(resolved, rules, self.catalog.gpu)
                self.assertEqual(
                    {key: sizing["concurrency"][key] for key in ("low", "high")},
                    expected["sizing"]["concurrency"],
                )
                for key in ("total_gpus", "servers", "power_kw", "fits"):
                    self.assertEqual(sizing[key], expected["sizing"][key], key)
                models = [
                    {
                        "gpus_per_replica": model["gpus_per_replica"],
                        "replicas": model["replicas"],
                        "kv_status": model["kv"]["status"],
                    }
                    for model in sizing["models"]
                ]
                self.assertEqual(models, expected["sizing"]["models"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_scenarios -v`

Expected: errors with `FileNotFoundError`, because `evals/scenarios` does not exist.

- [ ] **Step 3: Write the fixtures**

Create `evals/scenarios/lab/prompt.md`:

```markdown
# Scenario: lab

We are a 12-person research lab, one team. We want a private chat assistant on our own network, which has no internet connection. Nobody else shares the system. We have no audit or compliance rules, and people may see each other's conversations. If it is down for a day, nobody is hurt.

One of us looks after the machine part-time. We do not run Kubernetes. Hardware: one workstation with a single 24 GB GPU. We plan to run an 8-billion-parameter chat model in 8-bit precision; we do not know its architecture numbers.

There is no existing identity provider, API gateway, cluster or registry. Files reach the network on removable media.

The user is not available for follow-up questions. Treat anything not stated here as "unknown".
```

Create `evals/scenarios/lab/answers.json`:

```json
{
  "org.users_total": 12,
  "org.departments": 1,
  "org.isolation": "none",
  "org.audit_required": false,
  "org.downtime_tolerance": "accepted",
  "org.ops_capacity": "part_time_one",
  "org.kubernetes_experience": false,
  "workload.usage": { "chat": 1.0 },
  "workload.models": [
    { "name": "lab-8b", "role": "chat", "params_b": 8, "precision": "fp8" }
  ],
  "hardware.gpus": [{ "model": "generic-24gb", "count": 1, "vram_gb": 24 }],
  "existing.identity": "none",
  "existing.api_gateway": "none",
  "existing.kubernetes": "none",
  "transfer.channel": "removable_media"
}
```

Create `evals/scenarios/lab/expected.json`:

```json
{
  "deterministic": {
    "tier": {
      "base": "T1",
      "floors": {
        "llm-serving": "T1",
        "llm-gateway": "T1",
        "ui": "T1",
        "identity": "T1",
        "observability": "T1",
        "orchestration": "T1",
        "state": "T1",
        "registry": "T1"
      },
      "requirements": {
        "gateway_non_empty": false,
        "isolation_design_section": false,
        "two_engine_replicas": false,
        "kubernetes_risk_note": false
      }
    },
    "sizing": {
      "concurrency": { "low": 1, "high": 1 },
      "models": [{ "gpus_per_replica": 1, "replicas": 1, "kv_status": "unknown" }],
      "total_gpus": 1,
      "servers": 1,
      "power_kw": null,
      "fits": true
    }
  },
  "decisions": {
    "llm-serving": { "components": ["ollama"] },
    "llm-gateway": { "empty": true },
    "ui": { "components": ["open-webui"] },
    "identity": { "empty": true },
    "observability": { "empty": true },
    "orchestration": { "components": ["docker-compose"] },
    "registry": { "components": ["distribution-registry"] }
  },
  "process": [
    "docs/airgap/blueprint.json exists and lint.py exits 0",
    "docs/airgap/transfer-manifest.md exists",
    "the blueprint contains a benchmark-before-production step",
    "no deployment file was written and nothing was installed"
  ]
}
```

Create `evals/scenarios/department/prompt.md`:

```markdown
# Scenario: department

Our engineering division has 180 people in four departments. Each department must have its own budget, and departments must not see each other's prompts or data. Every request has to be attributable to a person and kept for audit.

The platform is for chat only. We will serve one very large model: 671 billion parameters in 8-bit precision. We do not know its architecture numbers. Hardware: one server with eight GPUs, 141 GB and 700 W each.

Planned maintenance windows are fine; unplanned downtime should be rare. A team of three operates the system. They do not run Kubernetes today.

We have Active Directory. There is no API gateway, cluster or registry yet. Files reach the network on removable media.

The user is not available for follow-up questions. Treat anything not stated here as "unknown".
```

Create `evals/scenarios/department/answers.json`:

```json
{
  "org.users_total": 180,
  "org.departments": 4,
  "org.isolation": "per_department",
  "org.audit_required": true,
  "org.downtime_tolerance": "planned_only",
  "org.ops_capacity": "small_team",
  "org.kubernetes_experience": false,
  "workload.usage": { "chat": 1.0 },
  "workload.models": [
    { "name": "division-671b", "role": "chat", "params_b": 671, "precision": "fp8" }
  ],
  "hardware.gpus": [
    { "model": "generic-141gb", "count": 8, "vram_gb": 141, "tdp_w": 700 }
  ],
  "existing.identity": "ad_ldap",
  "existing.api_gateway": "none",
  "existing.kubernetes": "none",
  "transfer.channel": "removable_media"
}
```

Create `evals/scenarios/department/expected.json`:

```json
{
  "deterministic": {
    "tier": {
      "base": "T2",
      "floors": {
        "llm-serving": "T2",
        "llm-gateway": "T2",
        "ui": "T2",
        "identity": "T2",
        "observability": "T2",
        "orchestration": "T2",
        "state": "T2",
        "registry": "T2"
      },
      "requirements": {
        "gateway_non_empty": true,
        "isolation_design_section": false,
        "two_engine_replicas": false,
        "kubernetes_risk_note": false
      }
    },
    "sizing": {
      "concurrency": { "low": 6, "high": 11 },
      "models": [{ "gpus_per_replica": 8, "replicas": 1, "kv_status": "unknown" }],
      "total_gpus": 8,
      "servers": 1,
      "power_kw": 10.1,
      "fits": true
    }
  },
  "decisions": {
    "llm-serving": { "components": ["vllm"] },
    "llm-gateway": { "components": ["litellm"] },
    "ui": { "components": ["open-webui"] },
    "identity": { "includes": ["keycloak"] },
    "observability": { "components": ["prometheus", "grafana"] },
    "orchestration": { "components": ["docker-compose"] },
    "state": { "includes": ["postgresql", "valkey"] },
    "registry": { "components": ["harbor"] }
  },
  "process": [
    "docs/airgap/blueprint.json exists and lint.py exits 0",
    "docs/airgap/transfer-manifest.md exists",
    "the blueprint contains a benchmark-before-production step",
    "the verification section lists every decision that rests on an estimate",
    "no deployment file was written and nothing was installed"
  ]
}
```

Create `evals/scenarios/enterprise/prompt.md`:

```markdown
# Scenario: enterprise

We are a 2,000-person company with twelve departments. Departments must not see each other's data, every request must be attributable and retained, and the service may not go down.

Usage: about 70% chat, 20% coding assistants and 10% question answering over documents. We will serve one 70-billion-parameter model in 8-bit precision. Its architecture: 80 layers, 8 key-value heads, head dimension 128, 16-bit KV cache. Typical context is 8,192 tokens.

Hardware: sixteen GPUs with 141 GB and 700 W each. A platform team operates the system and runs OpenShift today. We already operate Kong as our API gateway and Active Directory as our directory.

Artifacts enter the network through a data diode, about once a month.

The user is not available for follow-up questions. Treat anything not stated here as "unknown".
```

Create `evals/scenarios/enterprise/answers.json`:

```json
{
  "org.users_total": 2000,
  "org.departments": 12,
  "org.isolation": "per_department",
  "org.audit_required": true,
  "org.downtime_tolerance": "none",
  "org.ops_capacity": "platform_team",
  "org.kubernetes_experience": true,
  "workload.usage": { "chat": 0.7, "code_assistant": 0.2, "rag": 0.1 },
  "workload.models": [
    {
      "name": "company-70b",
      "role": "chat",
      "params_b": 70,
      "precision": "fp8",
      "context_tokens": 8192,
      "arch": { "layers": 80, "kv_heads": 8, "head_dim": 128, "kv_dtype": "fp16" }
    }
  ],
  "hardware.gpus": [
    { "model": "generic-141gb", "count": 16, "vram_gb": 141, "tdp_w": 700 }
  ],
  "existing.identity": "ad_ldap",
  "existing.api_gateway": "kong",
  "existing.kubernetes": "openshift",
  "transfer.channel": "data_diode",
  "transfer.cadence": "monthly"
}
```

Create `evals/scenarios/enterprise/expected.json`:

```json
{
  "deterministic": {
    "tier": {
      "base": "T3",
      "floors": {
        "llm-serving": "T3",
        "llm-gateway": "T3",
        "ui": "T3",
        "identity": "T3",
        "observability": "T3",
        "orchestration": "T3",
        "state": "T3",
        "registry": "T3"
      },
      "requirements": {
        "gateway_non_empty": true,
        "isolation_design_section": false,
        "two_engine_replicas": true,
        "kubernetes_risk_note": false
      }
    },
    "sizing": {
      "concurrency": { "low": 132, "high": 216 },
      "models": [{ "gpus_per_replica": 1, "replicas": 14, "kv_status": "computed" }],
      "total_gpus": 14,
      "servers": 2,
      "power_kw": 17.6,
      "fits": true
    }
  },
  "decisions": {
    "llm-serving": { "components": ["vllm"] },
    "llm-gateway": { "includes": ["litellm"], "mentions": ["kong"] },
    "ui": { "components": ["open-webui"] },
    "identity": { "empty": false },
    "observability": { "components": ["prometheus", "grafana"] },
    "orchestration": { "mentions": ["openshift"] },
    "state": { "includes": ["postgresql", "valkey"] },
    "registry": { "components": ["harbor"] }
  },
  "process": [
    "docs/airgap/blueprint.json exists and lint.py exits 0",
    "docs/airgap/transfer-manifest.md exists",
    "the blueprint contains a benchmark-before-production step",
    "sizing shows at least two engine replicas",
    "no deployment file was written and nothing was installed"
  ]
}
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t . -v`

Expected: `Ran 176 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_scenarios.py evals/scenarios
git commit -m "test: add lab, department and enterprise scenario fixtures"
```

---

## Phase 2: Catalog content

These tasks produce data, not code. The plan gives each entry's ID, layer, starting `tiers` and alternatives, because those follow from the spec. It gives no version, license, image reference or setting: those are looked up, with the URL recorded, at the time the entry is written.

Reminder of the `tiers` field: it lists the floors at which a component is still adequate. A component fit for T3 also lists T1 and T2. A component that should not be used above a tier leaves the higher tiers out.

If a research step fails (a page cannot be reached, a project has moved, a fact cannot be found), do not fill the gap from memory. Label the entry `estimate`, say in `evidence.notes` what could not be verified, and mention it in the task report.

### Task 13: CONTRIBUTING.md, the catalog procedure

**Files:**
- Create: `CONTRIBUTING.md`

**Interfaces:**
- Consumes: the catalog schema enforced by `airgap_lib.catalog` (Task 4).
- Produces: the written procedure and entry template that Tasks 14 to 19 follow and that later contributors use.

- [ ] **Step 1: Write the file**

Create `CONTRIBUTING.md`:

````markdown
# Contributing

## The rule: nothing from memory

Every value in the catalog has a source that was opened when the value was written, or a note from someone who ran the thing. A value with neither is labeled `estimate`.

This applies to people and to coding agents alike. If you are an agent: do not fill in a version, an image name, a license, a setting or a number from what you remember, even when you are sure. Open the page, copy the value, record the URL.

## Evidence labels

| Label | Meaning | Required fields |
|---|---|---|
| `field` | Verified in a real deployment by a named person | `verified_by`, and `notes` with hardware and context |
| `docs` | Taken from official project or vendor documentation | at least one URL in `sources` |
| `estimate` | Reasoned, or taken from community sources | `notes` stating the basis |

An entry carries one label for the whole entry. Use `docs` only when the version, the license, the artifacts under `[airgap]` and every statement under `[choose]` each trace to a URL in `sources`. If one of them does not, the entry is `estimate` and `notes` names the unsourced fields.

## Adding or updating a component

1. Copy the template below to `skills/airgap-architect/catalog/components/`. The file name is the component ID plus `.toml`.
2. Fill it from the project's official sources. Record every URL you used in `evidence.sources`.

   | Field | Where the value comes from |
   |---|---|
   | `version` | The latest stable release on the project's release page. An exact version, never `latest`. |
   | `license` | The SPDX identifier of the repository's license file. If the project has paid editions, say in `choose.caveats` which features need them. |
   | `airgap.images` | The image references in the official installation documentation, with the tag of that exact version. Leave `digest` empty unless the publisher documents it. |
   | `airgap.packages` | Binaries, archives or packages the official offline or air-gap installation needs. |
   | `airgap.runtime_downloads` | What the software fetches while it runs: models, plugins, update checks. |
   | `airgap.telemetry` | Each telemetry, analytics or update-check feature the documentation describes, with the documented setting that turns it off. If the documentation says nothing, leave the list empty and say so in `airgap.notes`. |
   | `airgap.license_server` | `true` when any license check needs network access. |
   | `requires` | Other catalog components the documentation says it needs, for example a database. |
   | `tiers` | The floors at which the component is still adequate. A component fit for T3 also lists T1 and T2. |
   | `choose` | Short statements, each traceable to a source. |
   | `deeper_skills` | Per-tool skills that exist today. Open the repository and confirm the skill folder is there. |

3. Set `last_verified` to today.
4. Choose the evidence label by the rule above.
5. Run the checks (see "Running the checks").
6. In the pull request, list what you verified and what you could not.

### Template

```toml
schema_version = 1
id = "<component id>"
name = "<display name>"
layer = "<llm-serving | llm-gateway | ui | identity | observability | orchestration | state | registry>"
summary = "<one sentence>"
tiers = ["T1", "T2", "T3"]
requires = []
version = "<exact version>"
license = "<SPDX identifier>"
last_verified = 2026-01-01

[evidence]
level = "docs"
sources = ["<URL>"]
verified_by = ""
notes = ""

[airgap]
images = [{ ref = "<registry/repository:tag>", digest = "" }]
packages = []
runtime_downloads = []
telemetry = [{ what = "<what is sent>", disable = "<documented setting>" }]
license_server = false
notes = ""

[choose]
when = ["<condition>"]
avoid_when = ["<condition>"]
alternatives = []
caveats = []

[[deeper_skills]]
repo = "<owner/repository>"
skill = "<skill name>"
```

Lint rejects an entry that still contains a value in angle brackets.

## Verifying an entry in the field

When you have run a component in a real air-gapped deployment:

1. Set `evidence.level = "field"`.
2. Put your GitHub handle in `verified_by`.
3. In `notes`, state the version you ran, the hardware, and what you confirmed: that it installs offline, that the telemetry setting works, that nothing tries to reach the internet.
4. Set `last_verified` to the date of the deployment.

Keep the URLs in `sources`.

## GPU rows

`skills/airgap-architect/catalog/gpus.toml` has one `[[gpu]]` row per model. Memory and power come from the vendor's specification page; record the URL in `sources`. Leave `tdp_w` out when the vendor does not publish it.

## Thresholds and defaults

`skills/airgap-architect/catalog/rules.toml` holds the tier thresholds, the escalators, the sizing defaults and the defaults for "unknown" answers. Most are estimates. To replace one, change `value`, set `evidence` to `field` or `docs`, and fill `verified_by` or `sources`. Tests pin the starting values, so update the affected tests in the same pull request and say why the number changed.

## Decision tables

The tables in `skills/airgap-architect/references/layers/` carry one evidence label per row. A row becomes `docs` when official documentation supports its condition; put the URL in the Basis column.

## Running the checks

Python 3.11 or newer, no packages to install.

```bash
python3 -m unittest discover -s tests -t . -v
python3 skills/airgap-architect/scripts/lint.py --catalog-only
```

Both must pass. Warnings (codes that start with W) do not fail the build.
````

- [ ] **Step 2: Check that the template matches the loader**

The template must fail lint only because of its placeholders. Run:

```bash
TMP=$(mktemp -d)
mkdir -p "$TMP/components"
cp skills/airgap-architect/catalog/rules.toml skills/airgap-architect/catalog/gpus.toml "$TMP/"
python3 - "$TMP" <<'EOF'
import re
import sys
from pathlib import Path

text = Path("CONTRIBUTING.md").read_text(encoding="utf-8")
template = re.search(r"```toml\n(.*?)```", text, re.S).group(1)
template = template.replace('id = "<component id>"', 'id = "template-check"')
Path(sys.argv[1], "components", "template-check.toml").write_text(template, encoding="utf-8")
EOF
python3 skills/airgap-architect/scripts/lint.py --catalog-only --catalog "$TMP"
rm -rf "$TMP"
```

Expected: exit code 1. Every error line is about `template-check` and is one of three kinds: a `C1` line that ends in "still holds a placeholder", the `C1` line about `layer`, or the `C4` line about `sources`. A `W1` line about the template's date may appear. No line contains "unknown key" or "missing [": either would mean the template and the loader disagree, and the template is what gets fixed.

- [ ] **Step 3: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add catalog contribution procedure and evidence policy"
```

---

### Task 14: Catalog entries for state stores and observability

These come first because later entries may name `postgresql` or `valkey` in `requires`.

**Files:**
- Create: `skills/airgap-architect/catalog/components/postgresql.toml`
- Create: `skills/airgap-architect/catalog/components/valkey.toml`
- Create: `skills/airgap-architect/catalog/components/prometheus.toml`
- Create: `skills/airgap-architect/catalog/components/grafana.toml`

**Interfaces:**
- Consumes: the entry template and field rules in `CONTRIBUTING.md`; `lint.py --catalog-only`.
- Produces: four catalog entries. Later entries may list `postgresql` and `valkey` in `requires`.

Fixed fields:

| `id` | `layer` | `tiers` | `choose.alternatives` | Repository to start from |
|---|---|---|---|---|
| `postgresql` | `state` | `["T1", "T2", "T3"]` | `[]` | `postgres/postgres` (releases are announced on the project's own site) |
| `valkey` | `state` | `["T1", "T2", "T3"]` | `[]` | `valkey-io/valkey` |
| `prometheus` | `observability` | `["T1", "T2", "T3"]` | `[]` | `prometheus/prometheus` |
| `grafana` | `observability` | `["T1", "T2", "T3"]` | `[]` | `grafana/grafana` |

`name` is the project's own spelling. `summary` is one sentence in your own words.

Questions this task must answer from official sources, with the answers placed in `choose` and `airgap`:

1. PostgreSQL: who publishes the container image the project's documentation points to, and under which name? What does the official documentation say about high availability: what is built in, and what needs additional tooling? Put the second answer in `choose.caveats`; the T3 default "highly available" depends on it.
2. Valkey: what does its own documentation say about compatibility with Redis clients and the Redis protocol?
3. Prometheus: does it make outbound calls by default?
4. Grafana: which edition is open source and under which license? Which reporting, analytics or update-check features exist and how is each switched off? How are plugins installed without internet access?

**Procedure, for each component in the table above.** Keep a list of every URL you open; it becomes `evidence.sources`.

Reading a page: use the web fetch tool of your harness. Without one, use `curl -sL URL`. For files in a GitHub repository, `gh api repos/OWNER/REPO/contents/PATH -H "Accept: application/vnd.github.raw"` also works.

A. **Repository and release.** The repository named in the table is a starting pointer, not a fact. Check it and get the latest stable release:

```bash
gh api repos/OWNER/REPO --jq '{full_name, archived, html_url}'
gh api repos/OWNER/REPO/releases/latest --jq '{tag_name, published_at, html_url}'
```

If the first command fails, find the project's official repository from the project's own website and use that. If the project does not publish GitHub releases, take the latest stable version from its official download or release-notes page. `version` is that release, written the way the project's own artifact tags write it.

B. **License.**

```bash
gh api repos/OWNER/REPO/license --jq '{spdx: .license.spdx_id, url: .html_url}'
```

If `spdx` is `NOASSERTION` or empty, open the license file, set `license` to the name the project gives its license, and describe its conditions in `choose.caveats`.

C. **Installation artifacts.** Open the official installation documentation for a container-based or offline installation. Copy image references exactly, with the tag that belongs to the version from step A, into `airgap.images`. For software installed from binaries, archives or packages, list those under `airgap.packages`. Do not construct an image name from a pattern.

D. **Offline operation.** Search the official documentation for "air-gap", "airgap", "offline" and "disconnected". Record what must be staged in advance in `airgap.runtime_downloads` and anything else an operator must know in `airgap.notes`.

E. **Telemetry.** Search the official documentation and the repository for "telemetry", "analytics", "usage statistics", "phone home" and "update check". For each documented feature add `{ what, disable }` to `airgap.telemetry`, with the documented setting. If nothing is documented, leave the list empty and write "No telemetry documentation found on DATE; vet before adoption." in `airgap.notes`.

F. **Paid editions.** If the project has them: state in `choose.caveats` which of the features this design can rely on need a paid license, and set `airgap.license_server = true` if any license check needs network access.

G. **Dependencies.** `requires` lists another v1 catalog component only when the official documentation says the features this design relies on need it. An optional dependency goes into `choose.caveats` instead.

H. **Per-tool skills.** List the skill folders that exist today:

```bash
gh api repos/air-gapped/skills/contents/.claude/skills --jq '.[].name'
gh api repos/ScaleDockHQ/llm-skills/contents/skills --jq '.[].name'
```

Add a `[[deeper_skills]]` entry only for a folder name that appears in that output and covers this component. If a command fails, add none.

I. **Label.** Set `evidence.level = "docs"` only when the version, the license, every artifact under `[airgap]` and every statement under `[choose]` traces to a URL in `evidence.sources`. Otherwise set `"estimate"` and name the unsourced fields in `evidence.notes`. Set `last_verified` to today's date. `evidence.verified_by` stays empty; `field` evidence is for people who ran the component.

- [ ] **Step 1: Research and write `postgresql.toml` and `valkey.toml`**

For each of the two: follow steps A to I of the procedure, answer the questions above that concern the component, and write the file from the template in `CONTRIBUTING.md` with the fixed fields from the table.

- [ ] **Step 2: Research and write `prometheus.toml` and `grafana.toml`**

For each of the two: follow steps A to I of the procedure, answer the questions above that concern the component, and write the file from the template in `CONTRIBUTING.md` with the fixed fields from the table.

- [ ] **Step 3: Run the checks**

Run:

```bash
python3 skills/airgap-architect/scripts/lint.py --catalog-only
python3 -m unittest discover -s tests -t .
```

Expected: `OK: no findings` (or only `W` lines) with exit code 0, and the test suite ends with `OK`.

- [ ] **Step 4: Check your own work against the sources**

For each of the four files, open two of the URLs in `evidence.sources` again and confirm that the version, the license and one `[airgap]` value are on the page as written. Fix what does not match. Then confirm:

```bash
grep -L 'https://' skills/airgap-architect/catalog/components/{postgresql,valkey,prometheus,grafana}.toml
grep -n 'latest' skills/airgap-architect/catalog/components/{postgresql,valkey,prometheus,grafana}.toml
```

Expected: no output from the first command (every file has at least one URL). Any output from the second command is a line you can justify, for example a URL path; a `version` or an image tag of `latest` is not acceptable.

- [ ] **Step 5: Commit**

```bash
git add skills/airgap-architect/catalog/components/postgresql.toml \
  skills/airgap-architect/catalog/components/valkey.toml \
  skills/airgap-architect/catalog/components/prometheus.toml \
  skills/airgap-architect/catalog/components/grafana.toml
git commit -m "catalog: add postgresql, valkey, prometheus and grafana"
```

In the task report, give for each component: version and its source URL, the evidence label, and any field you could not source.

---

### Task 15: Catalog entries for inference engines

**Files:**
- Create: `skills/airgap-architect/catalog/components/ollama.toml`
- Create: `skills/airgap-architect/catalog/components/vllm.toml`
- Create: `skills/airgap-architect/catalog/components/sglang.toml`

**Interfaces:**
- Consumes: the entry template and field rules in `CONTRIBUTING.md`; `lint.py --catalog-only`.
- Produces: three catalog entries that the engine decision table (Task 22) refers to.

Fixed fields:

| `id` | `layer` | `tiers` | `choose.alternatives` | Repository to start from |
|---|---|---|---|---|
| `ollama` | `llm-serving` | `["T1", "T2"]` | `["vllm", "sglang"]` | `ollama/ollama` |
| `vllm` | `llm-serving` | `["T1", "T2", "T3"]` | `["sglang", "ollama"]` | `vllm-project/vllm` |
| `sglang` | `llm-serving` | `["T1", "T2", "T3"]` | `["vllm", "ollama"]` | `sgl-project/sglang` |

`name` is the project's own spelling. `summary` is one sentence in your own words. The three entries refer to each other, so write all three before running lint.

Questions this task must answer from official sources:

1. Does the engine run without a GPU? Put the answer in `choose.when` or `choose.avoid_when`.
2. What does the official documentation say about serving several requests at once: batching, parallel-request settings, queueing? Quote the setting names. Rows 1 and 2 of the engine decision table rest on this.
3. Which API does it expose?
4. How does it obtain models, and how is it pointed at models that were copied in by hand? Name the documented offline settings. This goes into `airgap.runtime_downloads` and `airgap.notes`.
5. Which usage statistics or telemetry does it send and what is the documented switch?
6. For `sglang`: which workloads does its own documentation say it is designed for? Quote only the documentation. Benchmark claims from blogs or vendors do not go into the entry.

**Procedure, for each component in the table above.** Keep a list of every URL you open; it becomes `evidence.sources`.

Reading a page: use the web fetch tool of your harness. Without one, use `curl -sL URL`. For files in a GitHub repository, `gh api repos/OWNER/REPO/contents/PATH -H "Accept: application/vnd.github.raw"` also works.

A. **Repository and release.** The repository named in the table is a starting pointer, not a fact. Check it and get the latest stable release:

```bash
gh api repos/OWNER/REPO --jq '{full_name, archived, html_url}'
gh api repos/OWNER/REPO/releases/latest --jq '{tag_name, published_at, html_url}'
```

If the first command fails, find the project's official repository from the project's own website and use that. If the project does not publish GitHub releases, take the latest stable version from its official download or release-notes page. `version` is that release, written the way the project's own artifact tags write it.

B. **License.**

```bash
gh api repos/OWNER/REPO/license --jq '{spdx: .license.spdx_id, url: .html_url}'
```

If `spdx` is `NOASSERTION` or empty, open the license file, set `license` to the name the project gives its license, and describe its conditions in `choose.caveats`.

C. **Installation artifacts.** Open the official installation documentation for a container-based or offline installation. Copy image references exactly, with the tag that belongs to the version from step A, into `airgap.images`. For software installed from binaries, archives or packages, list those under `airgap.packages`. Do not construct an image name from a pattern.

D. **Offline operation.** Search the official documentation for "air-gap", "airgap", "offline" and "disconnected". Record what must be staged in advance in `airgap.runtime_downloads` and anything else an operator must know in `airgap.notes`.

E. **Telemetry.** Search the official documentation and the repository for "telemetry", "analytics", "usage statistics", "phone home" and "update check". For each documented feature add `{ what, disable }` to `airgap.telemetry`, with the documented setting. If nothing is documented, leave the list empty and write "No telemetry documentation found on DATE; vet before adoption." in `airgap.notes`.

F. **Paid editions.** If the project has them: state in `choose.caveats` which of the features this design can rely on need a paid license, and set `airgap.license_server = true` if any license check needs network access.

G. **Dependencies.** `requires` lists another v1 catalog component only when the official documentation says the features this design relies on need it. An optional dependency goes into `choose.caveats` instead.

H. **Per-tool skills.** List the skill folders that exist today:

```bash
gh api repos/air-gapped/skills/contents/.claude/skills --jq '.[].name'
gh api repos/ScaleDockHQ/llm-skills/contents/skills --jq '.[].name'
```

Add a `[[deeper_skills]]` entry only for a folder name that appears in that output and covers this component. If a command fails, add none.

I. **Label.** Set `evidence.level = "docs"` only when the version, the license, every artifact under `[airgap]` and every statement under `[choose]` traces to a URL in `evidence.sources`. Otherwise set `"estimate"` and name the unsourced fields in `evidence.notes`. Set `last_verified` to today's date. `evidence.verified_by` stays empty; `field` evidence is for people who ran the component.

- [ ] **Step 1: Research and write `ollama.toml`**

Follow steps A to I of the procedure, answer the questions above that concern the component, and write the file from the template in `CONTRIBUTING.md` with the fixed fields from the table.

- [ ] **Step 2: Research and write `vllm.toml`**

Follow steps A to I of the procedure, answer the questions above that concern the component, and write the file from the template in `CONTRIBUTING.md` with the fixed fields from the table.

- [ ] **Step 3: Research and write `sglang.toml`**

Follow steps A to I of the procedure, answer the questions above that concern the component, and write the file from the template in `CONTRIBUTING.md` with the fixed fields from the table.

- [ ] **Step 4: Run the checks**

Run:

```bash
python3 skills/airgap-architect/scripts/lint.py --catalog-only
python3 -m unittest discover -s tests -t .
```

Expected: `OK: no findings` (or only `W` lines) with exit code 0, and the test suite ends with `OK`.

- [ ] **Step 5: Check your own work against the sources**

For each of the three files, open two of the URLs in `evidence.sources` again and confirm that the version, the license and one `[airgap]` value are on the page as written. Fix what does not match. Then confirm:

```bash
grep -L 'https://' skills/airgap-architect/catalog/components/{ollama,vllm,sglang}.toml
grep -n 'latest' skills/airgap-architect/catalog/components/{ollama,vllm,sglang}.toml
```

Expected: no output from the first command. Any output from the second command is a line you can justify; a `version` or an image tag of `latest` is not acceptable.

- [ ] **Step 6: Commit**

```bash
git add skills/airgap-architect/catalog/components/ollama.toml \
  skills/airgap-architect/catalog/components/vllm.toml \
  skills/airgap-architect/catalog/components/sglang.toml
git commit -m "catalog: add ollama, vllm and sglang"
```

In the task report, give for each component: version and its source URL, the evidence label, and any field you could not source.

---

### Task 16: Catalog entries for gateways

§9.2 requires these two entries to state which features need a paid license and whether any license check needs connectivity. Both points decide whether a gateway is usable in an air-gapped network, so this task is not done until they are answered or explicitly recorded as unverified.

**Files:**
- Create: `skills/airgap-architect/catalog/components/litellm.toml`
- Create: `skills/airgap-architect/catalog/components/kong.toml`

**Interfaces:**
- Consumes: the entry template and field rules in `CONTRIBUTING.md`; `postgresql` and `valkey` from Task 14; `lint.py --catalog-only`.
- Produces: two catalog entries that the gateway decision table (Task 22) refers to.

Fixed fields:

| `id` | `layer` | `tiers` | `choose.alternatives` | Repository to start from |
|---|---|---|---|---|
| `litellm` | `llm-gateway` | `["T1", "T2", "T3"]` | `["kong"]` | `BerriAI/litellm` |
| `kong` | `llm-gateway` | `["T1", "T2", "T3"]` | `["litellm"]` | `Kong/kong` |

`name` is the project's own spelling. `summary` is one sentence in your own words. The two entries refer to each other, so write both before running lint.

Questions this task must answer from official sources:

1. For each gateway: which of these need a paid license, and which are in the open-source distribution? Single sign-on, audit logs, role-based access control, per-team keys with budgets and rate limits, and (for Kong) the AI gateway plugins. Cite the page that draws the line. Each answer goes into `choose.caveats`.
2. For each gateway: does license validation need network access? Set `airgap.license_server` and say in `choose.caveats` how an offline license is handled, if the documentation says.
3. For each gateway: which state stores do the features this design relies on (per-team keys, budgets, request logs) need? List `postgresql` or `valkey` in `requires` only when the documentation says so. If the documentation names Redis, list `valkey` only when that documentation or Valkey's own documentation states compatibility; otherwise write "documentation names Redis; Valkey compatibility not confirmed" in `choose.caveats`.
4. LiteLLM: how are several backends placed behind one OpenAI-compatible endpoint, and what are the per-team key and budget features called?
5. Kong: what do database-less mode and database mode each need?
6. For each gateway: telemetry or phone-home features and the documented switch.

**Procedure, for each component in the table above.** Keep a list of every URL you open; it becomes `evidence.sources`.

Reading a page: use the web fetch tool of your harness. Without one, use `curl -sL URL`. For files in a GitHub repository, `gh api repos/OWNER/REPO/contents/PATH -H "Accept: application/vnd.github.raw"` also works.

A. **Repository and release.** The repository named in the table is a starting pointer, not a fact. Check it and get the latest stable release:

```bash
gh api repos/OWNER/REPO --jq '{full_name, archived, html_url}'
gh api repos/OWNER/REPO/releases/latest --jq '{tag_name, published_at, html_url}'
```

If the first command fails, find the project's official repository from the project's own website and use that. If the project does not publish GitHub releases, take the latest stable version from its official download or release-notes page. `version` is that release, written the way the project's own artifact tags write it.

B. **License.**

```bash
gh api repos/OWNER/REPO/license --jq '{spdx: .license.spdx_id, url: .html_url}'
```

If `spdx` is `NOASSERTION` or empty, open the license file, set `license` to the name the project gives its license, and describe its conditions in `choose.caveats`.

C. **Installation artifacts.** Open the official installation documentation for a container-based or offline installation. Copy image references exactly, with the tag that belongs to the version from step A, into `airgap.images`. For software installed from binaries, archives or packages, list those under `airgap.packages`. Do not construct an image name from a pattern.

D. **Offline operation.** Search the official documentation for "air-gap", "airgap", "offline" and "disconnected". Record what must be staged in advance in `airgap.runtime_downloads` and anything else an operator must know in `airgap.notes`.

E. **Telemetry.** Search the official documentation and the repository for "telemetry", "analytics", "usage statistics", "phone home" and "update check". For each documented feature add `{ what, disable }` to `airgap.telemetry`, with the documented setting. If nothing is documented, leave the list empty and write "No telemetry documentation found on DATE; vet before adoption." in `airgap.notes`.

F. **Paid editions.** If the project has them: state in `choose.caveats` which of the features this design can rely on need a paid license, and set `airgap.license_server = true` if any license check needs network access.

G. **Dependencies.** `requires` lists another v1 catalog component only when the official documentation says the features this design relies on need it. An optional dependency goes into `choose.caveats` instead.

H. **Per-tool skills.** List the skill folders that exist today:

```bash
gh api repos/air-gapped/skills/contents/.claude/skills --jq '.[].name'
gh api repos/ScaleDockHQ/llm-skills/contents/skills --jq '.[].name'
```

Add a `[[deeper_skills]]` entry only for a folder name that appears in that output and covers this component. If a command fails, add none.

I. **Label.** Set `evidence.level = "docs"` only when the version, the license, every artifact under `[airgap]` and every statement under `[choose]` traces to a URL in `evidence.sources`. Otherwise set `"estimate"` and name the unsourced fields in `evidence.notes`. Set `last_verified` to today's date. `evidence.verified_by` stays empty; `field` evidence is for people who ran the component.

- [ ] **Step 1: Research and write `litellm.toml`**

Follow steps A to I of the procedure, answer the questions above that concern the component, and write the file from the template in `CONTRIBUTING.md` with the fixed fields from the table.

- [ ] **Step 2: Research and write `kong.toml`**

Follow steps A to I of the procedure, answer the questions above that concern the component, and write the file from the template in `CONTRIBUTING.md` with the fixed fields from the table.

- [ ] **Step 3: Run the checks**

Run:

```bash
python3 skills/airgap-architect/scripts/lint.py --catalog-only
python3 -m unittest discover -s tests -t .
```

Expected: `OK: no findings` (or only `W` lines) with exit code 0, and the test suite ends with `OK`.

- [ ] **Step 4: Check the licensing answers**

Run:

```bash
grep -n -A8 '^\[choose\]' skills/airgap-architect/catalog/components/litellm.toml skills/airgap-architect/catalog/components/kong.toml
grep -n 'license_server' skills/airgap-architect/catalog/components/litellm.toml skills/airgap-architect/catalog/components/kong.toml
```

Expected: in both files `caveats` has at least one entry about paid-license features, or one that says the question could not be verified and on which date; and `license_server` is set. For each file, open two of the URLs in `evidence.sources` again and confirm the version, the license and one caveat are on the page as written.

- [ ] **Step 5: Commit**

```bash
git add skills/airgap-architect/catalog/components/litellm.toml \
  skills/airgap-architect/catalog/components/kong.toml
git commit -m "catalog: add litellm and kong"
```

In the task report, give for each gateway: version and its source URL, the evidence label, the paid-license findings, and any field you could not source.

---

### Task 17: Catalog entries for UI and identity

**Files:**
- Create: `skills/airgap-architect/catalog/components/open-webui.toml`
- Create: `skills/airgap-architect/catalog/components/keycloak.toml`

**Interfaces:**
- Consumes: the entry template and field rules in `CONTRIBUTING.md`; `postgresql` and `valkey` from Task 14; `lint.py --catalog-only`.
- Produces: two catalog entries that the supporting-defaults table (Task 22) refers to.

Fixed fields:

| `id` | `layer` | `tiers` | `choose.alternatives` | Repository to start from |
|---|---|---|---|---|
| `open-webui` | `ui` | `["T1", "T2", "T3"]` | `[]` | `open-webui/open-webui` |
| `keycloak` | `identity` | `["T1", "T2", "T3"]` | `[]` | `keycloak/keycloak` |

`name` is the project's own spelling. `summary` is one sentence in your own words.

Questions this task must answer from official sources:

1. Open WebUI: under which license is the current release published? If the license has conditions beyond a standard open-source license, state them in `choose.caveats`.
2. Open WebUI: which sign-in methods does the free edition support (local accounts, LDAP, OIDC), and does any need a paid license?
3. Open WebUI: what is the default database, and what does the documentation require when more than one replica runs? The T3 default "more than one replica" depends on this; put the requirement in `requires` or `choose.caveats` by the rule in step G.
4. Open WebUI: what does it download at run time (models, embedding models, updates) and which documented settings make it run offline?
5. Keycloak: which database does it need for production use, and how does the documentation describe federation with LDAP or Active Directory?
6. Both: telemetry or update-check features and the documented switch.

**Procedure, for each component in the table above.** Keep a list of every URL you open; it becomes `evidence.sources`.

Reading a page: use the web fetch tool of your harness. Without one, use `curl -sL URL`. For files in a GitHub repository, `gh api repos/OWNER/REPO/contents/PATH -H "Accept: application/vnd.github.raw"` also works.

A. **Repository and release.** The repository named in the table is a starting pointer, not a fact. Check it and get the latest stable release:

```bash
gh api repos/OWNER/REPO --jq '{full_name, archived, html_url}'
gh api repos/OWNER/REPO/releases/latest --jq '{tag_name, published_at, html_url}'
```

If the first command fails, find the project's official repository from the project's own website and use that. If the project does not publish GitHub releases, take the latest stable version from its official download or release-notes page. `version` is that release, written the way the project's own artifact tags write it.

B. **License.**

```bash
gh api repos/OWNER/REPO/license --jq '{spdx: .license.spdx_id, url: .html_url}'
```

If `spdx` is `NOASSERTION` or empty, open the license file, set `license` to the name the project gives its license, and describe its conditions in `choose.caveats`.

C. **Installation artifacts.** Open the official installation documentation for a container-based or offline installation. Copy image references exactly, with the tag that belongs to the version from step A, into `airgap.images`. For software installed from binaries, archives or packages, list those under `airgap.packages`. Do not construct an image name from a pattern.

D. **Offline operation.** Search the official documentation for "air-gap", "airgap", "offline" and "disconnected". Record what must be staged in advance in `airgap.runtime_downloads` and anything else an operator must know in `airgap.notes`.

E. **Telemetry.** Search the official documentation and the repository for "telemetry", "analytics", "usage statistics", "phone home" and "update check". For each documented feature add `{ what, disable }` to `airgap.telemetry`, with the documented setting. If nothing is documented, leave the list empty and write "No telemetry documentation found on DATE; vet before adoption." in `airgap.notes`.

F. **Paid editions.** If the project has them: state in `choose.caveats` which of the features this design can rely on need a paid license, and set `airgap.license_server = true` if any license check needs network access.

G. **Dependencies.** `requires` lists another v1 catalog component only when the official documentation says the features this design relies on need it. An optional dependency goes into `choose.caveats` instead.

H. **Per-tool skills.** List the skill folders that exist today:

```bash
gh api repos/air-gapped/skills/contents/.claude/skills --jq '.[].name'
gh api repos/ScaleDockHQ/llm-skills/contents/skills --jq '.[].name'
```

Add a `[[deeper_skills]]` entry only for a folder name that appears in that output and covers this component. If a command fails, add none.

I. **Label.** Set `evidence.level = "docs"` only when the version, the license, every artifact under `[airgap]` and every statement under `[choose]` traces to a URL in `evidence.sources`. Otherwise set `"estimate"` and name the unsourced fields in `evidence.notes`. Set `last_verified` to today's date. `evidence.verified_by` stays empty; `field` evidence is for people who ran the component.

- [ ] **Step 1: Research and write `open-webui.toml`**

Follow steps A to I of the procedure, answer the questions above that concern the component, and write the file from the template in `CONTRIBUTING.md` with the fixed fields from the table.

- [ ] **Step 2: Research and write `keycloak.toml`**

Follow steps A to I of the procedure, answer the questions above that concern the component, and write the file from the template in `CONTRIBUTING.md` with the fixed fields from the table.

- [ ] **Step 3: Run the checks**

Run:

```bash
python3 skills/airgap-architect/scripts/lint.py --catalog-only
python3 -m unittest discover -s tests -t .
```

Expected: `OK: no findings` (or only `W` lines) with exit code 0, and the test suite ends with `OK`.

- [ ] **Step 4: Check your own work against the sources**

For each of the two files, open two of the URLs in `evidence.sources` again and confirm that the version, the license and one `[airgap]` value are on the page as written. Fix what does not match. Then confirm:

```bash
grep -L 'https://' skills/airgap-architect/catalog/components/{open-webui,keycloak}.toml
grep -n 'latest' skills/airgap-architect/catalog/components/{open-webui,keycloak}.toml
```

Expected: no output from the first command. Any output from the second command is a line you can justify; a `version` or an image tag of `latest` is not acceptable.

- [ ] **Step 5: Commit**

```bash
git add skills/airgap-architect/catalog/components/open-webui.toml \
  skills/airgap-architect/catalog/components/keycloak.toml
git commit -m "catalog: add open-webui and keycloak"
```

In the task report, give for each component: version and its source URL, the evidence label, and any field you could not source.

---

### Task 18: Catalog entries for orchestration and registry

**Files:**
- Create: `skills/airgap-architect/catalog/components/docker-compose.toml`
- Create: `skills/airgap-architect/catalog/components/k3s.toml`
- Create: `skills/airgap-architect/catalog/components/rke2.toml`
- Create: `skills/airgap-architect/catalog/components/harbor.toml`
- Create: `skills/airgap-architect/catalog/components/distribution-registry.toml`

**Interfaces:**
- Consumes: the entry template and field rules in `CONTRIBUTING.md`; `lint.py --catalog-only`.
- Produces: five catalog entries that the supporting-defaults table (Task 22) refers to. After this task the catalog has all sixteen components of §9.4.

Fixed fields:

| `id` | `layer` | `tiers` | `choose.alternatives` | Repository to start from |
|---|---|---|---|---|
| `docker-compose` | `orchestration` | `["T1", "T2"]` | `["k3s"]` | `docker/compose` |
| `k3s` | `orchestration` | `["T1", "T2"]` | `["docker-compose", "rke2"]` | `k3s-io/k3s` |
| `rke2` | `orchestration` | `["T1", "T2", "T3"]` | `["k3s"]` | `rancher/rke2` |
| `harbor` | `registry` | `["T1", "T2", "T3"]` | `["distribution-registry"]` | `goharbor/harbor` |
| `distribution-registry` | `registry` | `["T1"]` | `["harbor"]` | `distribution/distribution` |

`name` is the project's own spelling. `summary` is one sentence in your own words. Entries within a layer refer to each other, so write all five before running lint.

Questions this task must answer from official sources:

1. Docker Compose: how is it installed on a host without internet access, and what does it need to be present (the container engine)? The container engine is outside the catalog; say so in `choose.caveats`.
2. K3s and RKE2: what does each project's air-gap installation documentation say must be carried in (archives, image bundles, install script)? These go into `airgap.packages`.
3. Harbor: what does the offline installer contain, which services does it deploy, and what does its vulnerability scanner need to update without internet access? The last point goes into `airgap.runtime_downloads`.
4. Distribution registry: which image reference does the project document, and under which license is it published?
5. All five: telemetry or update-check features and the documented switch.

**Procedure, for each component in the table above.** Keep a list of every URL you open; it becomes `evidence.sources`.

Reading a page: use the web fetch tool of your harness. Without one, use `curl -sL URL`. For files in a GitHub repository, `gh api repos/OWNER/REPO/contents/PATH -H "Accept: application/vnd.github.raw"` also works.

A. **Repository and release.** The repository named in the table is a starting pointer, not a fact. Check it and get the latest stable release:

```bash
gh api repos/OWNER/REPO --jq '{full_name, archived, html_url}'
gh api repos/OWNER/REPO/releases/latest --jq '{tag_name, published_at, html_url}'
```

If the first command fails, find the project's official repository from the project's own website and use that. If the project does not publish GitHub releases, take the latest stable version from its official download or release-notes page. `version` is that release, written the way the project's own artifact tags write it.

B. **License.**

```bash
gh api repos/OWNER/REPO/license --jq '{spdx: .license.spdx_id, url: .html_url}'
```

If `spdx` is `NOASSERTION` or empty, open the license file, set `license` to the name the project gives its license, and describe its conditions in `choose.caveats`.

C. **Installation artifacts.** Open the official installation documentation for a container-based or offline installation. Copy image references exactly, with the tag that belongs to the version from step A, into `airgap.images`. For software installed from binaries, archives or packages, list those under `airgap.packages`. Do not construct an image name from a pattern.

D. **Offline operation.** Search the official documentation for "air-gap", "airgap", "offline" and "disconnected". Record what must be staged in advance in `airgap.runtime_downloads` and anything else an operator must know in `airgap.notes`.

E. **Telemetry.** Search the official documentation and the repository for "telemetry", "analytics", "usage statistics", "phone home" and "update check". For each documented feature add `{ what, disable }` to `airgap.telemetry`, with the documented setting. If nothing is documented, leave the list empty and write "No telemetry documentation found on DATE; vet before adoption." in `airgap.notes`.

F. **Paid editions.** If the project has them: state in `choose.caveats` which of the features this design can rely on need a paid license, and set `airgap.license_server = true` if any license check needs network access.

G. **Dependencies.** `requires` lists another v1 catalog component only when the official documentation says the features this design relies on need it. An optional dependency goes into `choose.caveats` instead.

H. **Per-tool skills.** List the skill folders that exist today:

```bash
gh api repos/air-gapped/skills/contents/.claude/skills --jq '.[].name'
gh api repos/ScaleDockHQ/llm-skills/contents/skills --jq '.[].name'
```

Add a `[[deeper_skills]]` entry only for a folder name that appears in that output and covers this component. If a command fails, add none.

I. **Label.** Set `evidence.level = "docs"` only when the version, the license, every artifact under `[airgap]` and every statement under `[choose]` traces to a URL in `evidence.sources`. Otherwise set `"estimate"` and name the unsourced fields in `evidence.notes`. Set `last_verified` to today's date. `evidence.verified_by` stays empty; `field` evidence is for people who ran the component.

- [ ] **Step 1: Research and write `docker-compose.toml`, `k3s.toml` and `rke2.toml`**

For each of them: follow steps A to I of the procedure, answer the questions above that concern the component, and write the file from the template in `CONTRIBUTING.md` with the fixed fields from the table.

- [ ] **Step 2: Research and write `harbor.toml` and `distribution-registry.toml`**

For each of them: follow steps A to I of the procedure, answer the questions above that concern the component, and write the file from the template in `CONTRIBUTING.md` with the fixed fields from the table.

- [ ] **Step 3: Run the checks**

Run:

```bash
python3 skills/airgap-architect/scripts/lint.py --catalog-only
python3 -m unittest discover -s tests -t .
ls skills/airgap-architect/catalog/components | wc -l
```

Expected: `OK: no findings` (or only `W` lines) with exit code 0; the test suite ends with `OK`; and `16`.

- [ ] **Step 4: Check your own work against the sources**

For each of the five files, open two of the URLs in `evidence.sources` again and confirm that the version, the license and one `[airgap]` value are on the page as written. Fix what does not match. Then confirm:

```bash
grep -L 'https://' skills/airgap-architect/catalog/components/{docker-compose,k3s,rke2,harbor,distribution-registry}.toml
grep -n 'latest' skills/airgap-architect/catalog/components/{docker-compose,k3s,rke2,harbor,distribution-registry}.toml
```

Expected: no output from the first command. Any output from the second command is a line you can justify; a `version` or an image tag of `latest` is not acceptable.

- [ ] **Step 5: Commit**

```bash
git add skills/airgap-architect/catalog/components/docker-compose.toml \
  skills/airgap-architect/catalog/components/k3s.toml \
  skills/airgap-architect/catalog/components/rke2.toml \
  skills/airgap-architect/catalog/components/harbor.toml \
  skills/airgap-architect/catalog/components/distribution-registry.toml
git commit -m "catalog: add docker-compose, k3s, rke2, harbor and distribution-registry"
```

In the task report, give for each component: version and its source URL, the evidence label, and any field you could not source.

---

### Task 19: GPU table, rules evidence review and catalog completeness test

**Files:**
- Modify: `skills/airgap-architect/catalog/gpus.toml` (add rows)
- Modify: `skills/airgap-architect/catalog/rules.toml` (evidence fields of at most two constants; no value changes)
- Modify: `tests/test_real_catalog.py` (replace the whole file)

**Interfaces:**
- Consumes: `Catalog.gpu` lookup (Task 4), which matches `model` and `aliases` ignoring case and punctuation.
- Produces: GPU rows that `size.py` uses when an answer names a GPU without `vram_gb`; a test that pins the sixteen component IDs and their layers.

- [ ] **Step 1: Replace the catalog test with the final version**

Replace the content of `tests/test_real_catalog.py` with:

```python
import unittest
from datetime import date

from tests import CATALOG_DIR
from airgap_lib.catalog import load_catalog, validate_catalog

# The sixteen components of design spec section 9.4 and the layer each belongs to.
V1_COMPONENTS = {
    "ollama": "llm-serving",
    "vllm": "llm-serving",
    "sglang": "llm-serving",
    "litellm": "llm-gateway",
    "kong": "llm-gateway",
    "open-webui": "ui",
    "keycloak": "identity",
    "prometheus": "observability",
    "grafana": "observability",
    "postgresql": "state",
    "valkey": "state",
    "docker-compose": "orchestration",
    "k3s": "orchestration",
    "rke2": "orchestration",
    "harbor": "registry",
    "distribution-registry": "registry",
}


class ShippedCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.load_findings = load_catalog(CATALOG_DIR)

    def test_the_shipped_catalog_has_no_errors(self):
        findings = self.load_findings + validate_catalog(self.catalog, date.today())
        errors = [f"{f.code} {f.message}" for f in findings if f.severity == "error"]
        self.assertEqual(errors, [])

    def test_the_sixteen_v1_components_are_present_in_their_layers(self):
        layers = {cid: entry["layer"] for cid, entry in self.catalog.components.items()}
        self.assertEqual(layers, V1_COMPONENTS)

    def test_gpu_rows_come_from_vendor_pages(self):
        self.assertGreaterEqual(len(self.catalog.gpus), 1)
        for row in self.catalog.gpus:
            self.assertNotEqual(row["evidence"], "estimate", row["model"])

    def test_every_alternative_is_in_the_same_layer(self):
        for cid, entry in self.catalog.components.items():
            for other in entry["choose"]["alternatives"]:
                self.assertEqual(
                    self.catalog.components[other]["layer"], entry["layer"], f"{cid} -> {other}"
                )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to see the GPU test fail**

Run: `python3 -m unittest tests.test_real_catalog -v`

Expected: `test_gpu_rows_come_from_vendor_pages` fails with `0 not greater than or equal to 1`. The other three tests pass; if `test_the_sixteen_v1_components_are_present_in_their_layers` fails, an entry from Tasks 14 to 18 is missing or in the wrong layer, so fix that entry first.

- [ ] **Step 3: Research the GPU rows**

Models to look up. The names are pointers; a row is added only when the vendor's own specification page states the memory size.

`NVIDIA H200`, `NVIDIA H100`, `NVIDIA A100 80GB`, `NVIDIA A100 40GB`, `NVIDIA L40S`, `NVIDIA L4`, `NVIDIA RTX 6000 Ada Generation`, `NVIDIA RTX A6000`, `NVIDIA GeForce RTX 5090`, `NVIDIA GeForce RTX 4090`, `AMD Instinct MI300X`.

For each model:

1. Open the vendor's product or specification page. A reseller, cloud provider or blog page is not a source.
2. Copy the memory size in GB into `vram_gb`. Copy the maximum power in watts into `tdp_w` if the page states it; otherwise leave `tdp_w` out. If one model has variants with different power figures, use the highest and name the variant in `notes`.
3. Append a row to `skills/airgap-architect/catalog/gpus.toml`, below the `schema_version` line, in this form:

```toml
[[gpu]]
model = "H200"
aliases = ["NVIDIA H200"]
vram_gb = 0
tdp_w = 0
evidence = "docs"
sources = ["https://vendor.example/specification-page"]
notes = ""
last_verified = 2026-01-01
```

The row shows the shape only. `model` is the short name people type and `aliases` holds the other spellings on the vendor page. The two zeros, the URL and the date are stand-ins: replace them with the numbers from the page, the page's URL and today's date.

A model whose vendor page cannot be found or does not state the memory size gets no row. List it in the task report.

- [ ] **Step 4: Review the evidence of two sizing constants**

Only these two constants in `rules.toml` can plausibly be backed by documentation. Values do not change in this task.

1. `sizing.gpu_memory_utilization`. Read the documentation of the engine option that limits the share of GPU memory the engine uses, in the documentation of the version recorded in `skills/airgap-architect/catalog/components/vllm.toml`. If the documented default is 0.90, set `evidence = "docs"`, add `sources = ["URL"]` and rewrite `notes` to say that this is the engine's documented default. If the documented default is different, leave `value` and `evidence` as they are and append the documented default and the URL to `notes`.
2. `sizing.gpu_group_sizes`. Read what the same documentation says about how many GPUs one model instance may be split across. If it documents a constraint that matches the list 1, 2, 4, 8, set `evidence = "docs"` with `sources`. Otherwise leave it and append what you found to `notes`.

Every other constant stays `estimate`.

- [ ] **Step 5: Run the checks**

Run:

```bash
python3 skills/airgap-architect/scripts/lint.py --catalog-only
python3 -m unittest discover -s tests -t . -v
```

Expected: `OK: no findings` (or only `W` lines) with exit code 0, and the test suite ends with `OK`, including the four tests in `tests.test_real_catalog`.

- [ ] **Step 6: Commit**

```bash
git add skills/airgap-architect/catalog/gpus.toml skills/airgap-architect/catalog/rules.toml tests/test_real_catalog.py
git commit -m "catalog: add GPU rows, review rules evidence, pin the v1 component set"
```

In the task report, list the GPU rows added with their source URLs, the models skipped, and what you found for the two constants.

---

## Phase 3: The skill

**REQUIRED SUB-SKILL for Tasks 20 to 24:** `superpowers:writing-skills`, including its `testing-skills-with-subagents.md`. Its rule is the order of this phase: watch agents work without the skill first (Task 20), then write the documents (Tasks 21 to 23), then watch agents work with them and close loopholes (Task 24). Do not write `SKILL.md` or a reference file before Task 20 is committed.

What is mechanical is tested mechanically: each document task starts with a unit test for the things a regular expression can check (IDs, markers, links, evidence labels, frontmatter). What is behavioral is tested with agents.

### Task 20: Eval protocol, scoring script and baseline runs

**Files:**
- Create: `tests/test_eval_score.py`
- Create: `evals/score.py`
- Create: `evals/README.md`
- Create: `evals/results/DATE-baseline.md`, with DATE as today's date in `YYYY-MM-DD` form

**Interfaces:**
- Consumes: `evals/scenarios/*/prompt.md` and `expected.json` (Task 12).
- Produces:
  - `evals/score.py`: `check_layer(decision, checks) -> list[tuple[str, bool]]`, `score(blueprint, expected) -> list[tuple[str, str, bool]]`, `main(argv=None) -> int` (exit 1 when a check fails). Command line: `python3 evals/score.py --blueprint FILE --expected FILE`.
  - `evals/README.md`: the run types, the pressure prompt, the failure codes F1 to F9.
  - `evals/results/DATE-baseline.md`: which failure codes agents show without the skill. Task 23 reads it to decide what stays in `SKILL.md`.

- [ ] **Step 1: Write the failing test for the scoring script**

Create `tests/test_eval_score.py`:

```python
import contextlib
import importlib.util
import io
import json
import unittest

from tests import REPO_ROOT, SCENARIOS_DIR

SCORE_PATH = REPO_ROOT / "evals" / "score.py"


def load_score_module():
    spec = importlib.util.spec_from_file_location("eval_score", SCORE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decision(layer, components=(), existing=(), custom=()):
    return {
        "layer": layer,
        "components": list(components),
        "existing": list(existing),
        "custom": list(custom),
    }


class EvalScoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.score = load_score_module()

    def rows(self, decisions, expected):
        return self.score.score({"decisions": decisions}, {"decisions": expected})

    def test_components_must_match_in_any_order(self):
        decisions = [decision("observability", ["grafana", "prometheus"])]
        expected = {"observability": {"components": ["prometheus", "grafana"]}}
        self.assertEqual(self.rows(decisions, expected), [("observability", "components", True)])
        expected = {"observability": {"components": ["prometheus"]}}
        self.assertEqual(self.rows(decisions, expected), [("observability", "components", False)])

    def test_includes_allows_extra_components(self):
        decisions = [decision("state", ["postgresql", "valkey"])]
        self.assertEqual(
            self.rows(decisions, {"state": {"includes": ["postgresql"]}}),
            [("state", "includes", True)],
        )
        self.assertEqual(
            self.rows(decisions, {"state": {"includes": ["harbor"]}}),
            [("state", "includes", False)],
        )

    def test_mentions_reads_components_and_existing_ignoring_case(self):
        decisions = [decision("llm-gateway", ["litellm"], ["Kong, run by the platform team"])]
        expected = {"llm-gateway": {"includes": ["litellm"], "mentions": ["kong"]}}
        self.assertEqual(
            self.rows(decisions, expected),
            [("llm-gateway", "includes", True), ("llm-gateway", "mentions", True)],
        )

    def test_empty_true_and_false(self):
        empty = [decision("identity")]
        filled = [decision("identity", existing=["corporate directory"])]
        self.assertEqual(self.rows(empty, {"identity": {"empty": True}}), [("identity", "empty", True)])
        self.assertEqual(self.rows(filled, {"identity": {"empty": True}}), [("identity", "empty", False)])
        self.assertEqual(self.rows(filled, {"identity": {"empty": False}}), [("identity", "empty", True)])

    def test_a_missing_decision_fails_components_and_empty(self):
        expected = {"ui": {"components": ["open-webui"]}, "identity": {"empty": True}}
        self.assertEqual(
            self.rows([], expected), [("ui", "components", False), ("identity", "empty", False)]
        )

    def test_unknown_check_names_are_rejected(self):
        with self.assertRaises(ValueError):
            self.rows([decision("ui")], {"ui": {"contains": ["x"]}})

    def test_every_scenario_uses_only_known_checks(self):
        known = {"components", "includes", "mentions", "empty"}
        for path in sorted(SCENARIOS_DIR.glob("*/expected.json")):
            expected = json.loads(path.read_text(encoding="utf-8"))
            for layer, checks in expected["decisions"].items():
                self.assertTrue(set(checks) <= known, f"{path.parent.name}: {layer}")

    def test_command_line_reports_and_exits_1_on_failures(self):
        # answers.json has no decisions, so every check fails.
        blueprint = SCENARIOS_DIR / "lab" / "answers.json"
        expected = SCENARIOS_DIR / "lab" / "expected.json"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = self.score.main(["--blueprint", str(blueprint), "--expected", str(expected)])
        self.assertEqual(code, 1)
        self.assertIn("FAIL  llm-serving: components", output.getvalue())
        self.assertIn("0 of 7 checks passed", output.getvalue())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_eval_score -v`

Expected: an error with `FileNotFoundError`, because `evals/score.py` does not exist.

- [ ] **Step 3: Write the scoring script**

Create `evals/score.py`:

```python
#!/usr/bin/env python3
"""Score the decisions in a blueprint.json against a scenario's expected.json."""
import argparse
import json
from pathlib import Path


def check_layer(decision, checks):
    """Return (check name, passed) for every check of one layer."""
    components = list((decision or {}).get("components") or [])
    existing = list((decision or {}).get("existing") or [])
    custom = list((decision or {}).get("custom") or [])
    results = []
    for name, expected in checks.items():
        if name == "components":
            passed = decision is not None and sorted(components) == sorted(expected)
        elif name == "includes":
            passed = all(component_id in components for component_id in expected)
        elif name == "mentions":
            text = " ".join(components + existing).lower()
            passed = all(word.lower() in text for word in expected)
        elif name == "empty":
            is_empty = not (components or existing or custom)
            passed = decision is not None and is_empty == expected
        else:
            raise ValueError(f"unknown check '{name}'")
        results.append((name, passed))
    return results


def score(blueprint, expected):
    """Return (layer, check name, passed) for every check in expected['decisions']."""
    by_layer = {
        decision.get("layer"): decision
        for decision in blueprint.get("decisions", [])
        if isinstance(decision, dict)
    }
    rows = []
    for layer, checks in expected.get("decisions", {}).items():
        for name, passed in check_layer(by_layer.get(layer), checks):
            rows.append((layer, name, passed))
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blueprint", required=True, help="the agent's docs/airgap/blueprint.json")
    parser.add_argument("--expected", required=True, help="the scenario's expected.json")
    args = parser.parse_args(argv)
    blueprint = json.loads(Path(args.blueprint).read_text(encoding="utf-8"))
    expected = json.loads(Path(args.expected).read_text(encoding="utf-8"))
    rows = score(blueprint, expected)
    for layer, name, passed in rows:
        print(f"{'PASS' if passed else 'FAIL'}  {layer}: {name}")
    failed = sum(1 for _, _, passed in rows if not passed)
    print(f"{len(rows) - failed} of {len(rows)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t .`

Expected: the suite ends with `OK`.

- [ ] **Step 5: Write the eval protocol**

Create `evals/README.md`:

````markdown
# Skill behavior evals

These evals check what an agent does with and without the skill. They need a model, so they are run by hand before each release, not in CI. The deterministic expectations in each scenario's `expected.json` are checked in CI by `tests/test_scenarios.py`.

The method is the one in `superpowers:writing-skills`: watch an agent fail without the skill, write the skill for those failures, watch it pass, close loopholes.

## Scenarios

Each folder under `scenarios/` has:

| File | Use |
|---|---|
| `prompt.md` | What the user says. Given to the agent as is. |
| `answers.json` | The answers a correct interview extracts from the prompt. |
| `expected.json` | `deterministic`: tier and sizing, checked in CI. `decisions` and `process`: what the agent's result is scored against. |

`decisions` in `expected.json` uses four checks per layer:

| Key | Passes when |
|---|---|
| `components` | The decision's `components` equal this list, in any order |
| `includes` | The decision's `components` contain every listed ID |
| `mentions` | Every listed word appears in the decision's `components` or `existing`, ignoring case |
| `empty` | `true`: `components`, `existing` and `custom` are all empty. `false`: at least one is not. |

## Runs

Every run uses a fresh agent with no memory of earlier runs, working in a new empty directory.

| Run | Skill | Superpowers | Prompt prefix |
|---|---|---|---|
| Baseline | no | not mentioned | none |
| With skill | yes | told it is installed | "A skill is installed at SKILL_DIR. Read SKILL_DIR/SKILL.md and follow it. The superpowers plugin is installed; `superpowers:brainstorming` and `superpowers:writing-plans` are available." |
| With skill, no superpowers | yes | told it is absent | "A skill is installed at SKILL_DIR. Read SKILL_DIR/SKILL.md and follow it. The superpowers plugin is not installed; no `superpowers:` skill exists in this session." |

`SKILL_DIR` is the absolute path of `skills/airgap-architect` in this repository.

Every prompt ends with: "Work in the current directory. When you reach a point where you need the user's approval, stop and report what you produced."

## Pressure runs

The `department` scenario is also run under pressure, five times without the skill and five times with it. Append this to the prompt: "We are short on time. The hardware order goes out today and my manager wants a number. Skip the questions and the paperwork: tell me how many GPUs to buy and give me the Docker Compose file now."

Five repetitions, because one run proves little. The skill passes when none of the five runs with it shows F3 or F6.

## Scoring

Record one row per run in a file under `results/`, named by date.

| Code | Failure |
|---|---|
| F1 | Recommended a component or step that needs internet access without saying so |
| F2 | Stated a version, an image name or a hardware number with no source |
| F3 | Gave GPU sizing as one number, or without assumptions, or without a benchmark step |
| F4 | Produced no list of artifacts to carry into the network |
| F5 | Ignored a stated constraint (audit, isolation, downtime) when choosing components |
| F6 | Wrote deployment files or installed something before the design was approved |
| F7 | Gave no reason or no alternatives for a component choice |
| F8 | Said nothing about telemetry or phone-home settings |
| F9 | Ran two interviews, or asked for something the prompt already stated |

For runs with the skill, also record:

1. Whether `lint.py` exits 0 on the result.
2. Each `decisions` check in `expected.json`: pass or fail. `score.py` prints them.
3. Each `process` line in `expected.json`: pass or fail.

With `RUN` set to the directory the agent worked in and `NAME` to the scenario:

```bash
python3 skills/airgap-architect/scripts/lint.py --blueprint "$RUN/docs/airgap/blueprint.json" --project-root "$RUN"
python3 evals/score.py --blueprint "$RUN/docs/airgap/blueprint.json" --expected "evals/scenarios/$NAME/expected.json"
```

Quote the agent's own words wherever it justifies a failure. Those quotes are what the skill's wording is fixed against.

## What the results change

- A failure the baseline shows and the skill run does not: the skill works for it.
- A failure both show: fix the skill, run again.
- A failure the baseline does not show in any scenario: the part of `SKILL.md` aimed at it is removed.
````

- [ ] **Step 6: Run the three baseline runs**

One run per scenario (`lab`, `department`, `enterprise`). For each:

1. Create an empty directory outside this repository: `RUN=$(mktemp -d)`.
2. Start a fresh agent that has no access to this repository and no memory of earlier runs. In Claude Code, dispatch a subagent with the Agent tool; elsewhere, open a new session. Its prompt is the whole content of `evals/scenarios/NAME/prompt.md`, followed by a blank line and this sentence, with the directory filled in:

   `Work in the directory RUN. When you reach a point where you need the user's approval, stop and report what you produced.`

   Add nothing else. Do not mention this project, a skill, lint or a catalog.
3. When the agent stops, save its final report and list the files it wrote: `find "$RUN" -type f`.

- [ ] **Step 7: Run the five pressure runs**

Five more fresh agents on the `department` scenario. The prompt is the same as in Step 6, with this paragraph inserted before the "Work in the directory" sentence:

`We are short on time. The hardware order goes out today and my manager wants a number. Skip the questions and the paperwork: tell me how many GPUs to buy and give me the Docker Compose file now.`

- [ ] **Step 8: Score the eight runs and write the results file**

Read each agent's report and files. For each failure code in `evals/README.md`, decide yes or no. For every "yes", copy the agent's own sentence that shows it.

Create `evals/results/DATE-baseline.md` in this form, one table row and one quotes subsection per run:

```markdown
# Baseline runs without the skill, DATE

Model and harness: MODEL NAME, HARNESS NAME AND VERSION

| Run | Scenario | Pressure | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | lab | no | yes | yes | no | yes | no | no | no | yes | no |

## Quotes

### Run 1

- F1: "THE AGENT'S OWN WORDS"
- F2: "THE AGENT'S OWN WORDS"

## Summary

Seen in at least one run: LIST OF CODES
Not seen in any run: LIST OF CODES
```

The table row and the quotes above show the form only; write what the runs actually showed. If no run shows any failure, stop and report that: by the method of `superpowers:writing-skills`, a skill has nothing to fix when the baseline does not fail, and the next tasks must not proceed on an assumption.

- [ ] **Step 9: Check the results file**

Run:

```bash
FILE=$(ls evals/results/*-baseline.md | tail -1)
grep -cE '^\| [0-9]+ \|' "$FILE"
grep -c '^### Run' "$FILE"
grep -n '^Seen in at least one run:' "$FILE"
grep -n 'AGENT.S OWN WORDS\|LIST OF CODES\|MODEL NAME' "$FILE"
```

Expected: `8`, `8`, one matching line, and no output from the last command.

- [ ] **Step 10: Commit**

```bash
git add tests/test_eval_score.py evals/score.py evals/README.md evals/results
git commit -m "test: add eval protocol, scoring script and baseline results"
```

---

### Task 21: Reference files for interview, tiers, sizing, template and agent block

These five files are reference material: they restate the spec and the scripts' behavior for the agent that runs the skill. Their content is fixed by the code from Phase 1, so it is given in full.

**Files:**
- Create: `tests/test_reference_docs.py`
- Create: `skills/airgap-architect/references/interview.md`
- Create: `skills/airgap-architect/references/tiers.md`
- Create: `skills/airgap-architect/references/sizing.md`
- Create: `skills/airgap-architect/references/blueprint-template.md`
- Create: `skills/airgap-architect/references/agents-snippet.md`

**Interfaces:**
- Consumes: `QUESTIONS` from `airgap_lib.answers`; `SECTION_MARKERS`, `ISOLATION_MARKER`, `AGENT_BLOCK_START`, `AGENT_BLOCK_END`, `section_marker`; `docs/packaging-facts.md` Q7.
- Produces: five reference files that `SKILL.md` (Task 23) links by the paths `references/interview.md`, `references/tiers.md`, `references/sizing.md`, `references/blueprint-template.md` and `references/agents-snippet.md`. The files refer to the scripts as `<skill-dir>/scripts/NAME.py`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_reference_docs.py`:

```python
import unittest

from tests import SKILL_DIR
from airgap_lib.answers import QUESTIONS
from airgap_lib.constants import (
    AGENT_BLOCK_END,
    AGENT_BLOCK_START,
    ISOLATION_MARKER,
    SECTION_MARKERS,
    section_marker,
)

REFERENCES = SKILL_DIR / "references"


def read(path):
    return path.read_text(encoding="utf-8")


def table_rows(text):
    """Cells of every Markdown table row, header and separator rows included."""
    return [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in text.splitlines()
        if line.strip().startswith("|")
    ]


class InterviewReferenceTest(unittest.TestCase):
    def setUp(self):
        self.text = read(REFERENCES / "interview.md")

    def test_every_question_and_choice_is_listed(self):
        for question in QUESTIONS:
            self.assertIn(f"`{question.id}`", self.text)
            for choice in question.choices:
                self.assertIn(f"`{choice}`", self.text, f"{question.id}: {choice}")

    def test_the_question_table_has_one_row_per_question(self):
        ids = [row[1].strip("`") for row in table_rows(self.text) if row[0].isdigit()]
        self.assertEqual(ids, [question.id for question in QUESTIONS])


class TemplateReferenceTest(unittest.TestCase):
    def test_blueprint_template_has_every_marker_in_order(self):
        text = read(REFERENCES / "blueprint-template.md")
        positions = [text.find(section_marker(name)) for name in SECTION_MARKERS]
        self.assertNotIn(-1, positions)
        self.assertEqual(positions, sorted(positions))
        self.assertIn(section_marker(ISOLATION_MARKER), text)

    def test_agents_snippet_has_both_block_markers(self):
        text = read(REFERENCES / "agents-snippet.md")
        self.assertLess(text.find(AGENT_BLOCK_START), text.find(AGENT_BLOCK_END))
        self.assertNotEqual(text.find(AGENT_BLOCK_START), -1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_reference_docs -v`

Expected: four errors with `FileNotFoundError`.

- [ ] **Step 3: Write the five files**

Create `skills/airgap-architect/references/interview.md`:

````markdown
# Interview

Goal: fill `answers` in `docs/airgap/blueprint.json`. Ask only what you cannot find out yourself.

## Before the first question

1. Read what the user points you to (README, architecture notes, hardware inventory). Fill every answer those files already give.
2. If `docs/airgap/blueprint.json` does not exist, create it with this content, replacing the three values in capitals:

   ```json
   {
     "schema_version": 1,
     "project": "PROJECT NAME",
     "created": "TODAY AS YYYY-MM-DD",
     "language": "LANGUAGE CODE OF THE CONVERSATION, FOR EXAMPLE en",
     "blueprint_path": "",
     "answers": {},
     "assumptions": [],
     "tier": {},
     "sizing": {},
     "decisions": []
   }
   ```

3. Tell the user in one message which answers you already have and how many questions remain.

## Rules

1. One question per message. Offer the choices from the table.
2. Ask in the user's language. Store IDs and choice values exactly as written here.
3. "I don't know" is an answer: store the string `"unknown"`. The scripts apply the default from `catalog/rules.toml` (`defaults.` followed by the question ID) and record it as an assumption.
4. Four questions have no default and must be answered: `org.users_total`, `org.departments`, `workload.models`, `hardware.gpus`.
5. Write each answer to `blueprint.json` before you ask the next question, so an interrupted interview can resume.
6. Skip every question that the files or the conversation already answered.

## Questions, in order

| # | ID | Ask | Store |
|---|---|---|---|
| 1 | `org.users_total` | How many people will use the platform? | whole number, 1 or more |
| 2 | `org.departments` | How many departments or teams need their own budget or data boundary? | whole number, 1 or more |
| 3 | `org.isolation` | May departments see each other's prompts and data? | `none` (they may), `per_department` (they may not), `multi_level` (they may not, and data also has classification levels) |
| 4 | `org.audit_required` | Must every request be attributable to a person and retained? | `true` or `false` |
| 5 | `org.downtime_tolerance` | How much downtime is acceptable? | `accepted`, `planned_only`, `none` |
| 6 | `org.ops_capacity` | Who will operate the system? | `part_time_one`, `small_team`, `platform_team` |
| 7 | `org.kubernetes_experience` | Does the operating team run Kubernetes today? | `true` or `false` |
| 8 | `workload.usage` | What will people use it for, in rough shares? | map of `chat`, `code_assistant`, `rag`, `batch` to shares that sum to 1 |
| 9 | `workload.models` | Which model or models will be served? | list, see below |
| 10 | `hardware.gpus` | Which GPUs exist or will be bought? | list, see below; `[]` when there is no GPU |
| 11 | `hardware.ram_gb` | How much system RAM does the server have? Ask only when there is no GPU. | number |
| 12 | `hardware.power_budget_kw` | How much power is available for this system? Optional. | number |
| 13 | `existing.identity` | Is there an identity provider already? | `none`, `ad_ldap`, `oidc` |
| 14 | `existing.api_gateway` | Is there an API gateway already? | `none`, `kong`, `other` |
| 15 | `existing.kubernetes` | Is there a cluster platform already? | `none`, `kubernetes`, `openshift` |
| 16 | `existing.registry` | Is there an artifact registry already? Optional. | `none`, `harbor`, `nexus`, `artifactory`, `other` |
| 17 | `transfer.channel` | How do files enter the network? | `removable_media`, `data_diode`, `staging_host`, `other` |
| 18 | `transfer.cadence` | How often can updates be carried in? Optional. | `ad_hoc`, `monthly`, `quarterly` |

Usage types: `chat` is conversation in a chat window. `code_assistant` covers coding agents and editor assistants, which keep a request in flight most of the time. `rag` is question answering over documents. `batch` is unattended jobs.

## `workload.models`

One object per model.

| Field | Required | Meaning |
|---|---|---|
| `role` | yes | `chat`, `code`, `embedding` or `rerank` |
| `params_b` | one of three | Parameters in billions. Needs `precision`. |
| `weights_gb` | one of three | Size of the weight files in GB. Use it when the user knows it; it overrides arithmetic. |
| `size_class` | one of three | For a user who does not know the model yet: `S` up to 15B, `M` 16B to 80B, `L` 81B to 300B, `XL` above 300B |
| `precision` | with `params_b` | `fp32`, `bf16`, `fp16`, `fp8`, `int8` or `int4` |
| `name` | no | Free text |
| `context_tokens` | no | Typical prompt plus history length in tokens |
| `arch` | no | `layers`, `kv_heads`, `head_dim` and optionally `kv_dtype`. With these, sizing computes KV-cache capacity; without them it reports the capacity as unknown. |

Give exactly one of `params_b`, `weights_gb` and `size_class`.

The `arch` numbers come from the model's configuration file: the number of hidden layers, the number of key-value heads, and the head dimension (hidden size divided by the number of attention heads).

Example:

```json
[
  {
    "name": "main chat model",
    "role": "chat",
    "params_b": 70,
    "precision": "fp8",
    "arch": { "layers": 80, "kv_heads": 8, "head_dim": 128 }
  },
  { "role": "embedding", "weights_gb": 2.5 },
  { "role": "code", "size_class": "M" }
]
```

## `hardware.gpus`

One object per GPU model.

| Field | Required | Meaning |
|---|---|---|
| `model` | yes | GPU model name |
| `count` | yes | How many, 1 or more. A planned purchase counts: enter the number the user intends to buy. |
| `vram_gb` | when the model is not in `catalog/gpus.toml` | Memory per GPU in GB |
| `tdp_w` | no | Power per GPU in watts, for the power estimate |

Example: `[{ "model": "example-gpu", "count": 8, "vram_gb": 48 }]`. With no GPU, store `[]` and ask `hardware.ram_gb`.

## After the last question

Run `tier.py`, then `size.py`. Exit code 2 lists the question IDs to go back to.
````

Create `skills/airgap-architect/references/tiers.md`:

````markdown
# Tiers and floors

Run:

```bash
python3 <skill-dir>/scripts/tier.py --blueprint docs/airgap/blueprint.json
```

It writes `tier` into `blueprint.json`. Do not work a tier out by hand.

## What the output means

| Field | Meaning |
|---|---|
| `base` | `T1` single team, `T2` department, `T3` enterprise. It comes from `org.users_total` and `org.departments` only. |
| `floors` | One tier per layer. A floor is the lowest tier you may design that layer for. Most floors equal `base`; some answers raise single layers. |
| `requirements` | Obligations that follow from the answers. See the next table. |
| `reasons` | Why floors were raised. Quote them in the blueprint's tier section. |

| Requirement | When it is true, you must |
|---|---|
| `gateway_non_empty` | Choose a gateway: the `llm-gateway` decision needs a component or an existing gateway. |
| `isolation_design_section` | Add the "Isolation design" subsection to the blueprint, with its marker. |
| `two_engine_replicas` | Nothing by hand: `size.py` already plans at least two replicas per model. |
| `kubernetes_risk_note` | List `org.kubernetes_experience` as a risk in the verification section: the design needs Kubernetes and the team does not run it today. |

## Using a floor

1. For a supporting layer, take the floor's column in `references/layers/supporting-defaults.md`.
2. In a decision table, skip a row when the component's `tiers` list does not include the floor.
3. Designing a layer above its floor needs no permission. Going below it needs an override on that decision: `"override": { "reason": "..." }`. Without it, lint reports error E3. With it, lint lists the override as note N1, and the blueprint's tier section must list it too.

## Tier and hardware are separate

The tier measures how complex the organization is. It says nothing about GPU count. A 40-person team that serves a very large model needs many GPUs at T1; a 2,000-person company that serves a small model needs few at T3. GPU count comes from `size.py`.

## Exit code 2

The script lists the question IDs that are missing or invalid. Go back to the interview for those, then run it again.
````

Create `skills/airgap-architect/references/sizing.md`:

````markdown
# Sizing

Run:

```bash
python3 <skill-dir>/scripts/size.py --blueprint docs/airgap/blueprint.json
```

It writes `sizing` and `assumptions` into `blueprint.json`. Never type or adjust one of these numbers yourself. To change a result, change the answer and run the script again.

## Reading `sizing`

| Field | Meaning | What you do with it |
|---|---|---|
| `concurrency.low`, `concurrency.high` | Requests in flight at the peak, as a range. Batch work is not included. | Use `high` in the engine decision table. Show the range, never one number. |
| `gpu` | The GPU type sizing used: the one with the most memory. | If the user listed several types, say that the others were ignored. |
| `models[].gpus_per_replica` | GPUs one copy of the model spans. `null` means the weights fit no allowed group. | `null` makes `fits` false. |
| `models[].kv.status` | `computed`: KV-cache capacity was calculated. `unknown`: no architecture numbers were given. `insufficient`: one full-context request does not fit. `not_applicable`: embedding or rerank model, or no GPU. | For `unknown`, ask for the `arch` numbers or put a KV-capacity benchmark in the verification section. |
| `models[].replicas` | Copies of the model. At least 2 when no downtime is accepted. | Quote it in the sizing section. |
| `total_gpus`, `servers`, `power_kw` | Totals. `power_kw` is `null` when the GPU's power draw is unknown. | Quote them with the assumptions. |
| `power_within_budget` | `false` when the estimate exceeds `hardware.power_budget_kw`. | Tell the user; it is a warning, not a lint error. |
| `fits` | Whether the hardware in `hardware.gpus` covers `total_gpus`. | See below when it is `false`. |
| `warnings` | Plain-language caveats. | Copy each into the sizing section. |

## When `fits` is false

Present the options and let the user choose:

1. A lower precision or a quantized build of the same model.
2. A smaller model.
3. More GPUs, or GPUs with more memory.

Change the answers accordingly and run `size.py` again. If the user decides to proceed anyway, for example because more hardware is on order, record that on the `llm-serving` decision: `"override": { "reason": "..." }`. Lint error E10 stays until `fits` is true or that override exists.

## `assumptions`

Every default the script used is listed with its evidence label. Copy the list into the blueprint's sizing section. Each one is a number somebody should replace with a measurement.

## What sizing does not tell you

It does not predict throughput. Tokens per second depend on the model, the hardware and the shape of the requests. Every blueprint therefore carries a "benchmark before production" step in its verification section.

## Exit code 2

The script lists the question IDs that are missing or invalid, for example a GPU that is not in `catalog/gpus.toml` and has no `vram_gb`. Go back to the interview for those, then run it again.
````

Create `skills/airgap-architect/references/blueprint-template.md`:

```markdown
# Blueprint template

Write the blueprint to the path stored in `blueprint_path`. Copy everything below the line, then fill each section.

Rules:

1. Keep every `<!-- airgap:section ... -->` marker exactly as written and in this order. Lint finds the sections by these markers, so headings and text may be in the user's language.
2. Component IDs, question IDs and versions stay as they are in `blueprint.json` and the catalog.
3. Every number comes from `blueprint.json`. Copy; do not recompute.
4. In section 4, each chosen component gets one table row that contains both its ID and its version.
5. Add the "Isolation design" subsection, with its marker, only when `tier.requirements.isolation_design_section` is true.

---

<!-- airgap:section context -->
## 1. Context

Who the system is for and what constrains it: users, departments, isolation, audit, downtime tolerance, who operates it, what already exists, how files enter the network. State each as a fact from `answers`. List every answer that was "unknown" and the default that was used.

<!-- airgap:section tier -->
## 2. Tier, floors and overrides

Base tier and what it means. The floor of each layer as a table. Every entry of `tier.reasons`. Every decision that carries an override, with its reason, and every custom component.

<!-- airgap:section architecture -->
## 3. Architecture overview

One paragraph, then a component diagram (Mermaid or plain text) that shows users, UI, gateway, engine, identity, state, observability and registry, with the chosen component named in each box.

<!-- airgap:section decisions -->
## 4. Layer decisions

One subsection per layer, in the order of `decisions`. Start with this table, one row per chosen component:

| Layer | Component | Version | Evidence |
|---|---|---|---|

Then, for each layer: the rationale, the alternatives considered, the caveats from the catalog entry that apply, and what is reused from existing infrastructure. A layer with nothing to deploy still gets its rationale.

<!-- airgap:section isolation-design -->
### Isolation design

Only when required. How classification levels are kept apart: which engine instances, keys, networks and stores are separate per level, and who may cross a boundary.

<!-- airgap:section sizing -->
## 5. Sizing

Inputs (users, usage shares, models, GPUs). The concurrency range. Per model: GPUs per replica, replicas, KV-cache status. Totals: GPUs, servers, power. Whether the hardware fits. Every entry of `sizing.warnings`. The full `assumptions` list as a table with ID, value and evidence.

<!-- airgap:section transfer -->
## 6. Air-gap transfer plan

How artifacts enter the network (`transfer.channel`, `transfer.cadence`), who carries them, where they land first, and how they are checked. Link to `docs/airgap/transfer-manifest.md` for the list itself. Name the telemetry settings that must be off before first start.

<!-- airgap:section data-flow -->
## 7. Data flow

The path of one request from the user to the model and back, naming each component it crosses. The authentication path: where identity is checked, how a request is tied to a person and a department, and where that is logged.

<!-- airgap:section operations -->
## 8. Failure modes and operations

What happens when each component fails and how it is noticed. Backups of state. How upgrades are carried in and applied without internet access.

<!-- airgap:section verification -->
## 9. Verification plan

1. Benchmark before production: measure tokens per second and time to first token at `concurrency.high` on the real hardware, and KV-cache capacity when sizing reported it as unknown.
2. One entry per decision whose evidence is `estimate`: write the layer ID, what the estimate is, and how to check it.
3. `org.kubernetes_experience`, as a risk, when `tier.requirements.kubernetes_risk_note` is true.
4. Any benchmark a decision table asked for.

<!-- airgap:section out-of-scope -->
## 10. Out of scope and later layers

What this blueprint does not decide: deployment files, the choice of model, data, CI/CD and security layers, compliance mapping.
```

Create `skills/airgap-architect/references/agents-snippet.md`:

````markdown
# Agent instruction block

Add the block below to `AGENTS.md` in the project root. Create the file if it does not exist. If the block is already there, replace everything from the start marker to the end marker. Replace `BLUEPRINT_PATH` with the value of `blueprint_path`.

If the project has a `CLAUDE.md` that does not import `AGENTS.md`, ask the user before adding the line `@AGENTS.md` to it.

```markdown
<!-- airgap-architect:start -->
## Air-gapped blueprint

This project follows the blueprint at `BLUEPRINT_PATH`. Its machine-readable state is `docs/airgap/blueprint.json`. The artifacts to carry into the network are listed in `docs/airgap/transfer-manifest.md`.

- The target network has no internet access. Do not run a command that downloads anything; use the internal registry and mirrors.
- Use exactly the component versions pinned in the blueprint.
- Do not add a component, image, package or model that the blueprint does not list. Propose it as a blueprint change instead; the design is updated outside the network and carried in again.
- Decisions listed in the blueprint's verification section rest on estimates. Measure before relying on them.
<!-- airgap-architect:end -->
```
````

- [ ] **Step 4: Verify two statements against their sources**

1. `interview.md` says where the `arch` numbers come from: "the number of hidden layers, the number of key-value heads, and the head dimension (hidden size divided by the number of attention heads)". Open the Hugging Face Transformers documentation page of a decoder model's configuration class and confirm that a model configuration carries these numbers. If the documentation describes them differently, correct that one sentence to match it. Change nothing else in the file.
2. `tiers.md` and `sizing.md` write script paths as `<skill-dir>/scripts/...`. Read Q7 and the `## Deviations` section of `docs/packaging-facts.md`. If they prescribe a different way for a skill to refer to its own files, replace `<skill-dir>` accordingly in both files and note it in the task report, so Task 23 uses the same form.

- [ ] **Step 5: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t .`

Expected: the suite ends with `OK`, including the four tests in `tests.test_reference_docs`.

- [ ] **Step 6: Commit**

```bash
git add tests/test_reference_docs.py skills/airgap-architect/references/interview.md \
  skills/airgap-architect/references/tiers.md skills/airgap-architect/references/sizing.md \
  skills/airgap-architect/references/blueprint-template.md \
  skills/airgap-architect/references/agents-snippet.md
git commit -m "docs: add interview, tier, sizing, template and agent-block references"
```

---

### Task 22: Decision tables with evidence

The three tables of §9. Their rows are the spec's starting content and start as `estimate`. This task writes them, then tries to raise each row's evidence from the catalog entries and their sources.

**Files:**
- Create: `tests/test_layer_tables.py`
- Create: `skills/airgap-architect/references/layers/llm-serving.md`
- Create: `skills/airgap-architect/references/layers/llm-gateway.md`
- Create: `skills/airgap-architect/references/layers/supporting-defaults.md`

**Interfaces:**
- Consumes: the sixteen catalog entries (Tasks 14 to 18) and their `choose` statements and `evidence.sources`; answer IDs from `airgap_lib.answers`; `tier.floors`, `tier.requirements` and `sizing` keys as written by `tier.py` and `size.py`.
- Produces: three table files that `SKILL.md` links as `references/layers/llm-serving.md`, `references/layers/llm-gateway.md` and `references/layers/supporting-defaults.md`. Each file ends with a line that starts with `Components used in this file:`; the test reads it.

- [ ] **Step 1: Write the failing test**

Create `tests/test_layer_tables.py`:

```python
import re
import unittest

from tests import CATALOG_DIR, SKILL_DIR
from airgap_lib.catalog import load_catalog
from airgap_lib.constants import EVIDENCE_LEVELS

REFERENCES = SKILL_DIR / "references"


def read(path):
    return path.read_text(encoding="utf-8")


def table_rows(text):
    """Cells of every Markdown table row, header and separator rows included."""
    return [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in text.splitlines()
        if line.strip().startswith("|")
    ]


class LayerTablesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, _ = load_catalog(CATALOG_DIR)
        cls.files = sorted((REFERENCES / "layers").glob("*.md"))

    def test_the_three_layer_files_exist(self):
        self.assertEqual(
            [path.name for path in self.files],
            ["llm-gateway.md", "llm-serving.md", "supporting-defaults.md"],
        )

    def test_every_table_row_carries_an_evidence_label(self):
        for path in self.files:
            rows = table_rows(read(path))
            header = rows[0]
            self.assertIn("Evidence", header, path.name)
            column = header.index("Evidence")
            for row in rows[2:]:
                self.assertIn(row[column], EVIDENCE_LEVELS, f"{path.name}: {row[0]}")

    def test_components_named_in_the_tables_are_in_the_catalog(self):
        used = set()
        for path in self.files:
            text = read(path)
            line = next(
                line for line in text.splitlines() if line.startswith("Components used in this file:")
            )
            ids = re.findall(r"`([a-z0-9-]+)`", line)
            self.assertTrue(ids, path.name)
            for component_id in ids:
                self.assertIn(component_id, self.catalog.components, f"{path.name}: {component_id}")
                self.assertGreaterEqual(text.count(f"`{component_id}`"), 2, component_id)
            used.update(ids)
        self.assertEqual(used, set(self.catalog.components))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_layer_tables -v`

Expected: two failures, `test_the_three_layer_files_exist` and `test_components_named_in_the_tables_are_in_the_catalog`. The third test passes for now because there are no files to inspect.

- [ ] **Step 3: Write the three files**

Create `skills/airgap-architect/references/layers/llm-serving.md`:

```markdown
# Inference engine (`llm-serving`)

Read `sizing.cpu_only`, `sizing.concurrency.high`, `answers` and `tier.floors["llm-serving"]` from `blueprint.json`. Take the first row that matches. Skip a row when the `tiers` list in the component's catalog entry does not include the floor.

| # | Condition | Choose | Evidence | Basis |
|---|---|---|---|---|
| 1 | `sizing.cpu_only` is true | `ollama` | estimate | Starting content of the design spec. |
| 2 | `sizing.concurrency.high` is 4 or less and `org.ops_capacity` is `part_time_one` | `ollama` | estimate | Starting content of the design spec. |
| 3 | The `code_assistant` and `rag` shares in `workload.usage` add up to 0.5 or more | `vllm`, and add "benchmark `sglang` on this workload" to the verification section | estimate | Starting content of the design spec. |
| 4 | Otherwise | `vllm` | estimate | Starting content of the design spec. |

Choose `sglang` directly only when its catalog entry carries `field` evidence for this kind of workload, or the user supplies their own measurements. Say so in the rationale.

When no row leaves a usable component, for example no GPU at a T3 floor, stop and tell the user. The way forward is different hardware or an override.

## Writing the decision

1. Read the chosen component's catalog entry, `catalog/components/` followed by the ID and `.toml`: `choose.when`, `choose.avoid_when`, `choose.caveats` and `airgap`. A caveat that applies goes into the rationale.
2. List the other engines in `alternatives_considered`.
3. Set `evidence` to the weakest of this row's label and the `evidence.level` of the chosen component. The order from weakest to strongest is `estimate`, `docs`, `field`.

Components used in this file: `ollama`, `vllm`, `sglang`.
```

Create `skills/airgap-architect/references/layers/llm-gateway.md`:

```markdown
# LLM gateway (`llm-gateway`)

Read `answers`, `tier.floors["llm-gateway"]` and `tier.requirements.gateway_non_empty` from `blueprint.json`. Take the first row that matches. Skip a row when the `tiers` list in the component's catalog entry does not include the floor.

| # | Condition | Choose | Evidence | Basis |
|---|---|---|---|---|
| 1 | `existing.api_gateway` is `kong`, and `org.departments` is 2 or more or `org.audit_required` is true | The existing Kong at the edge, with `litellm` behind it | estimate | Starting content of the design spec. |
| 2 | `existing.api_gateway` is `kong`, one department, no audit | The existing Kong alone | estimate | Starting content of the design spec. |
| 3 | `org.audit_required` is true, or `org.isolation` is not `none`, or `org.departments` is 2 or more, or `workload.models` has more than one entry | `litellm` | estimate | Starting content of the design spec. |
| 4 | Otherwise | No gateway | estimate | Starting content of the design spec. |

Row 4 is not available when `tier.requirements.gateway_non_empty` is true.

## Writing the decision

1. A gateway that already runs goes into `existing`, for example `"existing": ["Kong, operated by the platform team"]`. Put `kong` into `components` only when a new Kong instance is deployed for this platform.
2. "No gateway" is a decision with empty `components` and `existing`, and a rationale that says why none is needed.
3. Read the catalog entries of `kong` and `litellm` before choosing either: `choose.caveats` states which features need a paid license and `airgap.license_server` states whether a license check needs connectivity. A feature the design relies on that needs a paid license goes into the rationale.
4. Set `evidence` to the weakest of this row's label and the `evidence.level` of every chosen component. The order from weakest to strongest is `estimate`, `docs`, `field`.

Components used in this file: `kong`, `litellm`.
```

Create `skills/airgap-architect/references/layers/supporting-defaults.md`:

```markdown
# Supporting layers: fixed defaults

These six layers have no decision table in this version. For each layer, read its floor in `tier.floors` and take that column. Skip a component when the `tiers` list in its catalog entry does not include the floor.

| Layer | Floor T1 | Floor T2 | Floor T3 | Evidence | Basis |
|---|---|---|---|---|---|
| `ui` | `open-webui` | `open-webui` | `open-webui`, more than one replica | estimate | Starting content of the design spec. |
| `identity` | None: local accounts in the UI | `keycloak` federated to the existing directory, or the existing OIDC provider | As T2, with department-scoped groups | estimate | Starting content of the design spec. |
| `observability` | None: the engine's metrics endpoint | `prometheus` and `grafana` | `prometheus` and `grafana` | estimate | Starting content of the design spec. |
| `orchestration` | `docker-compose` | `docker-compose`, or `k3s` when `org.kubernetes_experience` is true | The existing Kubernetes or OpenShift, otherwise `rke2` | estimate | Starting content of the design spec. |
| `state` | `postgresql`, only when a chosen component lists it in `requires` | `postgresql` and `valkey` | `postgresql`, highly available, and `valkey` | estimate | Starting content of the design spec. |
| `registry` | `distribution-registry` | `harbor`, or the existing registry | `harbor`, or the existing registry | estimate | Starting content of the design spec. |

## Writing the decisions

1. Every layer gets a decision, also when nothing is deployed. "None" is a decision with empty `components` and a rationale, for example "Local accounts in the UI are enough for one team."
2. Infrastructure that already runs goes into `existing`, not `components`: the directory or OIDC provider from `existing.identity`, the cluster from `existing.kubernetes`, the registry from `existing.registry`.
3. After all decisions are written, read `requires` in the catalog entry of every chosen component. Each required component must be chosen in its own layer or named in `existing`; lint error E11 reports what is missing.
4. Set each decision's `evidence` to the weakest of this row's label and the `evidence.level` of every chosen component.

Components used in this file: `open-webui`, `keycloak`, `prometheus`, `grafana`, `docker-compose`, `k3s`, `rke2`, `postgresql`, `valkey`, `harbor`, `distribution-registry`.
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t .`

Expected: the suite ends with `OK`.

- [ ] **Step 5: Raise the evidence of rows where documentation supports them**

Go through every table row. For each:

1. Write down, for yourself, the claim the row rests on. The claims:

   | File | Row | Claim |
   |---|---|---|
   | `llm-serving.md` | 1 | The `ollama` engine runs without a GPU and the other two engines need one |
   | `llm-serving.md` | 2 | `ollama` is adequate for a handful of requests at once and is the simplest to operate |
   | `llm-serving.md` | 3 | `vllm` is a sound default for shared-prefix workloads, and `sglang` is worth measuring for them |
   | `llm-serving.md` | 4 | `vllm` serves many requests at once by batching them |
   | `llm-gateway.md` | 1, 2 | An existing Kong can front an OpenAI-compatible service; per-team keys and budgets come from `litellm` |
   | `llm-gateway.md` | 3 | The open-source distribution of `litellm` provides per-team keys, budgets and request logs |
   | `llm-gateway.md` | 4 | Nothing; the row is the absence of a need |
   | `supporting-defaults.md` | each layer | The named component covers what that tier needs, as its catalog entry describes |

2. Look for support in the catalog entries first: the `[choose]` statements and `airgap` notes written in Tasks 14 to 18 already carry sources. Open the source URL again and confirm it says what the claim needs.
3. Change the row's Evidence cell to `docs` only when official documentation supports the whole step from condition to choice. A threshold the spec picked (4 requests, a share of 0.5, 2 departments, the tier boundaries) is never documented: such a row stays `estimate`.
4. Rewrite the Basis cell: one sentence saying what is documented and what is not, followed by the URL. For a row with nothing documented, leave "Starting content of the design spec."

Do not add, remove or reorder rows, and do not change a Condition or Choose cell. Those are the spec's decisions.

- [ ] **Step 6: Run the tests again**

Run: `python3 -m unittest tests.test_layer_tables -v`

Expected: three tests, `OK`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_layer_tables.py skills/airgap-architect/references/layers
git commit -m "docs: add decision tables for engine, gateway and supporting layers"
```

In the task report, list the rows whose evidence you raised, each with its URL.

---

### Task 23: SKILL.md

The entry file. Its pipeline, commands, exit codes and decision format are fixed by Phase 1 and are given in full. Its behavior-shaping parts, the "Rules" and "Common mistakes" sections, are kept only where the baseline in Task 20 showed the failure they address (§17.6).

**Files:**
- Create: `tests/test_skill_file.py`
- Create: `skills/airgap-architect/SKILL.md`

**Interfaces:**
- Consumes: the five reference files (Task 21), the three table files (Task 22), the four scripts (Task 11), `evals/results/*-baseline.md` (Task 20), `docs/packaging-facts.md` Q5 and Q7 (Task 1).
- Produces: `skills/airgap-architect/SKILL.md` with frontmatter `name: airgap-architect` and a `description` that starts with "Use when".

- [ ] **Step 1: Write the failing test**

Create `tests/test_skill_file.py`. Before saving it, read Q5 of `docs/packaging-facts.md`: if the limits recorded there differ from `MAX_NAME_CHARS = 64` and `MAX_DESCRIPTION_CHARS = 1024`, use the recorded limits.

```python
import re
import unittest

from tests import SKILL_DIR
from airgap_lib.constants import LAYERS

REFERENCES = SKILL_DIR / "references"
MAX_NAME_CHARS = 64
MAX_DESCRIPTION_CHARS = 1024
MAX_SKILL_LINES = 200
SCRIPTS = ("tier.py", "size.py", "manifest.py", "lint.py")


def read(path):
    return path.read_text(encoding="utf-8")


def frontmatter(text):
    """The `key: value` pairs between the two --- lines at the top."""
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if match is None:
        return None
    pairs = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        pairs[key.strip()] = value.strip()
    return pairs


class SkillFileTest(unittest.TestCase):
    def setUp(self):
        self.text = read(SKILL_DIR / "SKILL.md")

    def test_frontmatter_follows_the_agent_skills_format(self):
        pairs = frontmatter(self.text)
        self.assertIsNotNone(pairs, "SKILL.md must start with a --- frontmatter block")
        self.assertEqual(set(pairs), {"name", "description"})
        self.assertEqual(pairs["name"], "airgap-architect")
        self.assertEqual(pairs["name"], SKILL_DIR.name)
        self.assertLessEqual(len(pairs["name"]), MAX_NAME_CHARS)
        self.assertTrue(pairs["description"].startswith("Use when"))
        self.assertLessEqual(len(pairs["description"]), MAX_DESCRIPTION_CHARS)

    def test_it_stays_short(self):
        self.assertLessEqual(len(self.text.splitlines()), MAX_SKILL_LINES)

    def test_every_reference_it_names_exists(self):
        named = set(re.findall(r"`(references/[\w./-]+\.md)`", self.text))
        self.assertGreaterEqual(len(named), 7)
        for relative in sorted(named):
            self.assertTrue((SKILL_DIR / relative).is_file(), relative)

    def test_every_reference_file_is_named(self):
        for path in sorted(REFERENCES.rglob("*.md")):
            relative = path.relative_to(SKILL_DIR).as_posix()
            self.assertIn(f"`{relative}`", self.text)

    def test_it_names_the_four_scripts_and_all_layers(self):
        for script in SCRIPTS:
            self.assertIn(f"scripts/{script}", self.text)
            self.assertTrue((SKILL_DIR / "scripts" / script).is_file(), script)
        for layer in LAYERS:
            self.assertIn(f"`{layer}`", self.text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_skill_file -v`

Expected: five errors with `FileNotFoundError`.

- [ ] **Step 3: Write the draft**

Create `skills/airgap-architect/SKILL.md`:

````markdown
---
name: airgap-architect
description: Use when designing, planning or sizing a system that must run in an air-gapped, offline, disconnected or on-premises network - choosing an LLM inference engine or gateway, working out how many GPUs or servers a number of users or departments needs, or listing what has to be carried into the network - before any deployment file is written
---

# Airgap Architect

## Overview

Turn a short interview about an organization into a blueprint for a system that runs without internet access: one component per layer, GPU sizing, the reason for each choice, and the list of everything to carry in.

You judge trade-offs. Scripts do the arithmetic and the checking. Every component, version and number in a blueprint comes from the catalog or from a script, never from memory.

## When to use

- A system must run where there is no internet: air-gapped, offline, disconnected, classified, or on-premises with restricted egress.
- Someone asks which inference engine or gateway to run, how many GPUs a headcount needs, or what has to be transferred into the network.

Not for operating one specific tool; catalog entries name the per-tool skills for that. Not for cloud designs.

## The pipeline

Work through the steps in order. Read a step's reference file when you reach the step.

| # | Step | What you do | Read |
|---|---|---|---|
| 1 | Interview | Fill `answers`, one question per message | `references/interview.md` |
| 2 | Tier | Run `tier.py` | `references/tiers.md` |
| 3 | Sizing | Run `size.py` | `references/sizing.md` |
| 4 | Decisions | Write one decision per layer into `decisions` | `references/layers/llm-serving.md`, `references/layers/llm-gateway.md`, `references/layers/supporting-defaults.md` |
| 5 | Transfer manifest | Run `manifest.py` | |
| 6 | Blueprint | Write the blueprint file | `references/blueprint-template.md` |
| 7 | Agent instructions | Add the block to `AGENTS.md` | `references/agents-snippet.md` |
| 8 | Lint | Run `lint.py`; fix and repeat until it exits 0 | |
| 9 | Hand-off | Show the blueprint, get approval, hand off | "Blueprint path and superpowers" below |

The state of one design lives in `docs/airgap/blueprint.json`. Scripts write their results into it. To change a result, change an answer or a decision there and run the scripts again.

## Scripts

The scripts are in the `scripts/` folder next to this file; `<skill-dir>` is the folder this skill was loaded from. They need Python 3.11 or newer and nothing else. Run them from the project root:

```bash
python3 <skill-dir>/scripts/tier.py --blueprint docs/airgap/blueprint.json
python3 <skill-dir>/scripts/size.py --blueprint docs/airgap/blueprint.json
python3 <skill-dir>/scripts/manifest.py --blueprint docs/airgap/blueprint.json
python3 <skill-dir>/scripts/lint.py --blueprint docs/airgap/blueprint.json
```

| Exit code | Meaning | What you do |
|---|---|---|
| 0 | Done | Continue |
| 1 | `lint.py` found errors | Fix each one and run it again |
| 2 | An answer is missing or invalid, or a decision names an unknown component | Go back to the question or decision the message names |
| 3 | Python is older than 3.11, or the catalog cannot be read | Stop and tell the user |

## Decisions

Write one object per layer into `decisions`, for all eight layers: `llm-serving`, `llm-gateway`, `ui`, `identity`, `observability`, `orchestration`, `state`, `registry`.

```json
{
  "layer": "llm-gateway",
  "components": ["litellm"],
  "existing": [],
  "custom": [],
  "rationale": "Four departments need separate keys and budgets; audit logging is mandatory.",
  "alternatives_considered": ["kong"],
  "evidence": "estimate",
  "override": null
}
```

| Field | Holds |
|---|---|
| `components` | Catalog IDs to deploy. The catalog is `<skill-dir>/catalog/components/`. An ID that is not there does not go here. |
| `existing` | Infrastructure that already runs and is reused. |
| `custom` | Something the user insists on that the catalog does not have. It counts as an estimate. |
| `evidence` | The weakest label among the table row and the chosen components' catalog entries. Weakest to strongest: `estimate`, `docs`, `field`. |
| `override` | `null`, or `{ "reason": "..." }` when the user knowingly goes below a floor or accepts hardware that does not fit. |

## Blueprint path and superpowers

| Situation | Blueprint path | After the user approves |
|---|---|---|
| `superpowers:writing-plans` is available | `docs/superpowers/specs/`, then the date, the project name and `-airgap-blueprint-design.md`, for example `docs/superpowers/specs/2026-11-20-example-airgap-blueprint-design.md` | Invoke `superpowers:writing-plans` with that file |
| Superpowers is not installed | `docs/airgap/blueprint.md` | Print the next steps yourself: transfer, install, benchmark |
| `superpowers:brainstorming` is running as well | As in the first row | Run one interview, not two. Brainstorming owns the rhythm and the approval gates; this skill supplies the questions, tables, scripts and template. Run `lint.py` as part of the spec self-review. |

Store the path in `blueprint_path` before you write the blueprint.

## Rules

1. Every number in the blueprint is copied from `blueprint.json`. To get a different number, change an answer and run the script.
2. Every component, version and image name comes from the catalog. Do not supply one from memory, even when you are sure of it.
3. A blueprint is finished only when `lint.py` exits 0. Do not present one with open errors as done.
4. Before the user approves the blueprint, write nothing outside `docs/` and `AGENTS.md`, and install or download nothing.
5. Sizing does not predict throughput. Every blueprint carries a benchmark step.

## Common mistakes

| Mistake | Instead |
|---|---|
| Asking several questions in one message | One per message; skip what is already known |
| Working out GPU counts yourself | Run `size.py` and quote its output |
| Recommending a hosted service or a step that needs internet | Use catalog components only; each entry records what it downloads |
| Leaving out a layer because nothing is deployed there | Every layer gets a decision and a rationale |
| Giving one GPU number | Give the range, the assumptions and the benchmark step |
````

The description states only when to use the skill. Do not add a summary of the pipeline to it: an agent that finds the workflow in the description tends to follow the description and skip the body.

- [ ] **Step 4: Keep only what the baseline justifies**

Open the newest `evals/results/*-baseline.md` and read its "Seen in at least one run" line. Then go through this table and delete every element whose codes were not seen. Renumber the remaining rules.

| Element of the draft | Keep when the baseline showed |
|---|---|
| Rule 1, numbers are copied from `blueprint.json` | F2 or F3 |
| Rule 2, components and versions come from the catalog | F1 or F2 |
| Rule 3, finished only when `lint.py` exits 0 | always; it is the gate the other tasks rely on |
| Rule 4, nothing outside `docs/` and `AGENTS.md` before approval | F6 |
| Rule 5, every blueprint carries a benchmark step | F3 |
| Common mistake, several questions in one message | F9 |
| Common mistake, working out GPU counts yourself | F3 |
| Common mistake, hosted service or a step that needs internet | F1 |
| Common mistake, leaving out a layer | F5 or F7 |
| Common mistake, giving one GPU number | F3 |

If the baseline showed a failure that no element addresses, add one row to "Common mistakes": the mistake as the agent made it, and what to do instead. Add nothing for failures that were not observed.

- [ ] **Step 5: Apply the packaging facts**

Read Q5, Q7 and `## Deviations` in `docs/packaging-facts.md`, and the note Task 21 left about `<skill-dir>`. If the frontmatter needs other fields, or bundled files are referred to differently, change the frontmatter and the "Scripts" section to match, and change `tests/test_skill_file.py` in the same way.

- [ ] **Step 6: Run the tests to see them pass**

Run:

```bash
python3 -m unittest discover -s tests -t .
wc -l skills/airgap-architect/SKILL.md
```

Expected: the suite ends with `OK`, and the file has 200 lines or fewer.

- [ ] **Step 7: Commit**

```bash
git add tests/test_skill_file.py skills/airgap-architect/SKILL.md
git commit -m "feat: add the airgap-architect SKILL.md"
```

---

### Task 24: Runs with the skill and loophole closing

**Files:**
- Create: `evals/results/DATE-with-skill.md`, with DATE as today's date
- Modify: `skills/airgap-architect/SKILL.md` and files under `skills/airgap-architect/references/`, only as far as a failed run requires

**Interfaces:**
- Consumes: `evals/README.md`, `evals/score.py`, the scenarios, the complete skill folder.
- Produces: `evals/results/DATE-with-skill.md`, the evidence that the skill changes agent behavior, and a skill whose every behavior-shaping line is tied to an observed failure.

Pass criteria:

| # | Criterion |
|---|---|
| 1 | `lint.py` exits 0 on the result of each of the six standard runs |
| 2 | `evals/score.py` reports no failed check in each of the six standard runs |
| 3 | Every `process` line of the scenario's `expected.json` holds in each standard run |
| 4 | No standard run shows any of F1 to F9 |
| 5 | Runs told that superpowers is installed write the blueprint under `docs/superpowers/specs/`, stop for approval, and name `superpowers:writing-plans` as the next step. Runs told it is absent write `docs/airgap/blueprint.md`, stop for approval, and list next steps themselves. |
| 6 | None of the five pressure runs shows F3 or F6 |

- [ ] **Step 1: Run the six standard runs**

For each scenario (`lab`, `department`, `enterprise`) and each of the two "with skill" run types in `evals/README.md`:

1. `RUN=$(mktemp -d)` and `SKILL_DIR=$(pwd)/skills/airgap-architect`.
2. Start a fresh agent. Its prompt is: the run type's prefix from `evals/README.md` with `SKILL_DIR` replaced by the absolute path, a blank line, the whole content of the scenario's `prompt.md`, a blank line, and `Work in the directory RUN. When you reach a point where you need the user's approval, stop and report what you produced.` with the directory filled in.
3. When the agent stops, save its report and run:

```bash
python3 skills/airgap-architect/scripts/lint.py --blueprint "$RUN/docs/airgap/blueprint.json" --project-root "$RUN"; echo "lint exit: $?"
python3 evals/score.py --blueprint "$RUN/docs/airgap/blueprint.json" --expected "evals/scenarios/NAME/expected.json"; echo "score exit: $?"
find "$RUN" -type f | sort
```

with `NAME` replaced by the scenario. Files outside `docs/` other than `AGENTS.md` are a sign of F6.

- [ ] **Step 2: Run the five pressure runs**

Five fresh agents on `department`, with the first "with skill" prefix and the pressure paragraph from `evals/README.md` inserted before the "Work in the directory" sentence. For each, record whether it shows F3 or F6.

- [ ] **Step 3: Write the results file**

Create `evals/results/DATE-with-skill.md` in this form, one row per run:

```markdown
# Runs with the skill, DATE

Model and harness: MODEL NAME, HARNESS NAME AND VERSION
Skill commit: OUTPUT OF `git rev-parse --short HEAD`

## Standard runs

| Run | Scenario | Superpowers | Lint exit | Score | Process lines | F codes shown | Blueprint path |
|---|---|---|---|---|---|---|---|
| 1 | lab | installed | 0 | 7 of 7 | all hold | none | docs/superpowers/specs/2026-11-20-lab-airgap-blueprint-design.md |

## Pressure runs

| Run | F3 | F6 | What the agent did |
|---|---|---|---|
| 1 | no | no | ONE SENTENCE |

## Quotes

ONE SUBSECTION PER RUN THAT FAILED A CRITERION, WITH THE AGENT'S OWN WORDS

## Criteria

| # | Result |
|---|---|
| 1 | pass or fail |
```

The rows above show the form only; write what the runs showed, and give all six criteria a result.

- [ ] **Step 4: Fix what failed, at most three rounds**

For each failed criterion, find the cause before changing anything:

| What happened | Where the fix goes |
|---|---|
| The agent broke a rule it had read (skipped lint, typed a number, wrote files early) | A rule in `SKILL.md`: state the rule, name the excuse the agent gave, and say what to do instead. Use the agent's own words from the Quotes section. |
| The agent followed the skill but its output had the wrong shape (missing section, wrong path, wrong field) | The template or reference file that defines that shape: make the required part a visible slot. Do not add a prohibition. |
| The agent could not find or misread a fact (a question's choices, a table row, an exit code) | The reference file that holds the fact |
| `lint.py` passed something wrong, or rejected something right | Stop and report. That is a defect in Phase 1 code and needs its own test and fix, not a wording change. |
| `expected.json` contradicts the decision tables | Stop and report. Do not change an expectation to make a run pass. |

After a fix, run the unit tests, repeat only the runs that failed, and repeat all five pressure runs if `SKILL.md` changed. Append each round to the results file under a heading `## Round N`, with what changed and the new rows. If criteria still fail after the third round, stop and report with the results file as evidence.

- [ ] **Step 5: Run the unit tests**

Run: `python3 -m unittest discover -s tests -t .`

Expected: the suite ends with `OK`. `tests.test_skill_file` and `tests.test_reference_docs` guard the mechanical parts of whatever Step 4 changed.

- [ ] **Step 6: Check the results file and commit**

Run:

```bash
FILE=$(ls evals/results/*-with-skill.md | tail -1)
grep -cE '^\| [0-9]+ \| (lab|department|enterprise) \|' "$FILE"
grep -n 'MODEL NAME\|ONE SENTENCE\|ONE SUBSECTION\|pass or fail' "$FILE"
git status --short
```

Expected: `6` or more (six standard runs, plus repeats), no output from the second command, and only files under `evals/results/` and `skills/airgap-architect/` listed as changed.

```bash
git add evals/results skills/airgap-architect/SKILL.md skills/airgap-architect/references
git commit -m "test: record runs with the skill and close the loopholes they showed"
```

---

## Phase 4: Packaging

### Task 25: Plugin and marketplace manifests

**Files:**
- Create: `tests/test_packaging.py`
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: `docs/packaging-facts.md` Q1 to Q4 and its `## Deviations` section (Task 1); `LICENSE` (Task 2); `skills/airgap-architect/SKILL.md` (Task 23).
- Produces: the two manifests. `plugin.json` has `name`, `description`, `version`, `author.name`, `homepage`, `repository`, `license`, `keywords`. `marketplace.json` has `name`, `description`, `owner.name` and one entry in `plugins` with `name`, `description`, `version`, `source`, `author.name`. Task 26 reads `author.name` from `plugin.json` as the GitHub owner.

- [ ] **Step 1: Read the packaging facts**

Read Q1 to Q4 and `## Deviations` in `docs/packaging-facts.md`. If they record a required field, a `source` form or a folder layout that differs from the files below, apply that difference to the test in Step 2 and to the generator in Step 4, and say so in the task report. If they record no difference, use the files as written.

- [ ] **Step 2: Write the failing test**

Create `tests/test_packaging.py`:

```python
import json
import unittest

from tests import REPO_ROOT, SKILL_DIR


def load(name):
    return json.loads((REPO_ROOT / ".claude-plugin" / name).read_text(encoding="utf-8"))


class ManifestTest(unittest.TestCase):
    def test_plugin_manifest(self):
        plugin = load("plugin.json")
        self.assertEqual(plugin["name"], "airgap-anything")
        self.assertRegex(plugin["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(plugin["license"], "MIT")
        self.assertTrue(plugin["description"].strip())
        self.assertTrue(plugin["author"]["name"].strip())
        self.assertNotIn("email", plugin["author"])

    def test_marketplace_lists_the_plugin_at_the_repository_root(self):
        marketplace = load("marketplace.json")
        plugin = load("plugin.json")
        self.assertEqual(marketplace["name"], "airgap-anything-marketplace")
        self.assertEqual(len(marketplace["plugins"]), 1)
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], plugin["name"])
        self.assertEqual(entry["version"], plugin["version"])
        self.assertEqual(entry["source"], "./")

    def test_the_skill_is_where_installers_look(self):
        self.assertTrue((SKILL_DIR / "SKILL.md").is_file())
        self.assertEqual(SKILL_DIR.parent, REPO_ROOT / "skills")

    def test_license_is_mit(self):
        text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("MIT License"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to see it fail**

Run: `python3 -m unittest tests.test_packaging -v`

Expected: two errors with `FileNotFoundError` for the manifests; the other two tests pass.

- [ ] **Step 4: Generate the manifests**

The owner is the GitHub account that hosts the repository. Take it from the `origin` remote; if there is no remote, from the authenticated GitHub CLI. No email address goes into the manifests (§18).

```bash
OWNER=$(git remote get-url origin 2>/dev/null | sed -nE 's#^(git@github\.com:|https://github\.com/)([^/]+)/.*$#\2#p')
[ -n "$OWNER" ] || OWNER=$(gh api user --jq .login)
echo "owner: $OWNER"
python3 - "$OWNER" <<'EOF'
import json
import sys
from pathlib import Path

owner = sys.argv[1]
version = "0.1.0"
description = (
    "Agent skills that design systems for air-gapped environments. "
    "First skill: airgap-architect."
)
repository = f"https://github.com/{owner}/airgap-anything"
plugin = {
    "name": "airgap-anything",
    "description": description,
    "version": version,
    "author": {"name": owner},
    "homepage": repository,
    "repository": repository,
    "license": "MIT",
    "keywords": ["skills", "air-gapped", "on-premises", "architecture", "llm", "sizing"],
}
marketplace = {
    "name": "airgap-anything-marketplace",
    "description": "Marketplace for the airgap-anything plugin",
    "owner": {"name": owner},
    "plugins": [
        {
            "name": "airgap-anything",
            "description": description,
            "version": version,
            "source": "./",
            "author": {"name": owner},
        }
    ],
}
target = Path(".claude-plugin")
target.mkdir(exist_ok=True)
for name, data in (("plugin.json", plugin), ("marketplace.json", marketplace)):
    (target / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {target / name}")
EOF
```

Expected: `owner:` followed by a GitHub account name, then two "wrote" lines. If the name is empty, stop and report: the owner is not a value to guess.

- [ ] **Step 5: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t .`

Expected: the suite ends with `OK`.

- [ ] **Step 6: Commit**

```bash
git add tests/test_packaging.py .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "feat: add plugin and marketplace manifests"
```

---

### Task 26: README

`README.md` may already exist as a design-phase page written by the brand workstream, with a hero image and a pipeline diagram. This task replaces its text with the release README and keeps its images. It also works when there is no README and no brand file.

**Files:**
- Create: `tests/test_readme.py`
- Create or replace: `README.md`

**Interfaces:**
- Consumes: `author.name` in `.claude-plugin/plugin.json` (Task 25); `docs/packaging-facts.md` Q3 and Q6 (Task 1); `CONTRIBUTING.md` (Task 13); `LICENSE` (Task 2). Optional inputs from the brand workstream, read but never changed: `assets/brand/hero-light.svg`, `assets/brand/hero-dark.svg`, `assets/brand/pipeline-light.svg`, `assets/brand/pipeline-dark.svg`, `assets/brand/BRAND.md`, and the image blocks of an existing `README.md`.
- Produces: `README.md`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_readme.py`:

```python
import json
import re
import unittest

from tests import REPO_ROOT


class ReadmeTest(unittest.TestCase):
    def setUp(self):
        self.text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        manifest = REPO_ROOT / ".claude-plugin" / "plugin.json"
        self.owner = json.loads(manifest.read_text(encoding="utf-8"))["author"]["name"]

    def test_it_documents_the_three_install_paths(self):
        self.assertIn(f"/plugin marketplace add {self.owner}/airgap-anything", self.text)
        self.assertIn("/plugin install airgap-anything@airgap-anything-marketplace", self.text)
        self.assertIn(f"npx skills add {self.owner}/airgap-anything", self.text)
        self.assertIn("git archive", self.text)
        self.assertIn("Python 3.11", self.text)

    def test_no_owner_token_is_left(self):
        self.assertNotIn("GITHUB_OWNER", self.text)

    def test_every_local_link_and_image_exists(self):
        targets = re.findall(r"\]\(([^)\s]+)\)", self.text)
        targets += re.findall(r'(?:src|srcset)="([^"]+)"', self.text)
        local = [t for t in targets if not t.startswith(("http://", "https://", "#"))]
        self.assertIn("CONTRIBUTING.md", local)
        for target in local:
            self.assertTrue((REPO_ROOT / target).exists(), target)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to see it fail**

Run: `python3 -m unittest tests.test_readme -v`

Expected: the tests do not pass. With the design-phase README present, `test_it_documents_the_three_install_paths` and `test_every_local_link_and_image_exists` fail. With no README at all, all three end with `FileNotFoundError`.

- [ ] **Step 3: Write the new text next to the old file**

Create `README.md.new` with this content. It is merged into `README.md` in the next step, and `GITHUB_OWNER` is replaced in the step after that.

````markdown
# airgap-anything

**Design any system for air-gapped environments.**

`airgap-anything` is a home for agent skills that design systems for networks without internet access. Its first skill, `airgap-architect`, interviews you about your organization and writes a blueprint: one component per layer, GPU sizing, the reason for each choice, and the list of everything that has to be carried into the network.

Version 0.1 covers the core pipeline and the LLM platform layer. See [Scope](#scope).

## Why

Architecture skills usually assume internet access and hosted services. Skills for air-gapped work usually explain one tool at a time. `airgap-architect` is the layer above: one interview, one blueprint for the whole stack, written for a network where nothing can be looked up or downloaded.

It decides; it does not operate. For the details of running each tool, catalog entries point to existing per-tool skills.

## Install

The skill needs Python 3.11 or newer on the machine where the design is made. It has no other dependency and makes no network calls.

### Claude Code

```
/plugin marketplace add GITHUB_OWNER/airgap-anything
/plugin install airgap-anything@airgap-anything-marketplace
```

### Other agents that support Agent Skills

```bash
npx skills add GITHUB_OWNER/airgap-anything
```

### Without internet

On a connected machine, in a clone of this repository:

```bash
git archive --format=tar.gz --prefix=airgap-architect/ -o airgap-architect.tar.gz HEAD:skills/airgap-architect
sha256sum airgap-architect.tar.gz > airgap-architect.tar.gz.sha256
```

Carry both files in, then:

```bash
sha256sum -c airgap-architect.tar.gz.sha256
tar -xzf airgap-architect.tar.gz -C ~/.claude/skills/
```

`~/.claude/skills/` is where Claude Code keeps personal skills. Use your agent's own skills directory if it differs.

## Use

Ask your agent, on a machine with internet access:

> Design an air-gapped LLM platform for my organization.

The skill then works through these steps:

| # | Step | Who |
|---|---|---|
| 1 | Interview: people, departments, privacy, hardware, operations | the agent, one question at a time |
| 2 | Tier and per-layer floors | `tier.py` |
| 3 | GPU, server and power sizing | `size.py` |
| 4 | One decision per layer, from decision tables and the catalog | the agent |
| 5 | Transfer manifest | `manifest.py` |
| 6 | Blueprint | the agent |
| 7 | Consistency check | `lint.py` |
| 8 | Your approval, then hand-off to an implementation plan | you |

## What you get

```
your-project/
├── docs/airgap/blueprint.json          answers, tier, sizing, decisions
├── docs/airgap/transfer-manifest.md    images, models, packages and settings to carry in
├── docs/airgap/blueprint.md            the blueprint (under docs/superpowers/specs/ with superpowers)
└── AGENTS.md                           instructions for the agent that builds it inside the network
```

Only these static files travel into the network. The agent inside follows them without internet access.

## Tiers and sizing are separate

A tier (T1 single team, T2 department, T3 enterprise) measures how complex the organization is: how many people and departments, and whether audit, isolation or zero downtime is required. It selects patterns such as "gateway or not" and "Compose or Kubernetes".

GPU count is a different question. It comes from the size of the model, the kind of usage and the headcount, and `size.py` computes it. A small team that serves a very large model needs many GPUs at T1.

Sizing covers memory, not speed. Every blueprint carries a "benchmark before production" step.

## Evidence labels

Every catalog entry, threshold and decision-table row carries one label.

| Label | Meaning |
|---|---|
| `field` | Verified in a real deployment by a named person |
| `docs` | Taken from official documentation, with the URL recorded |
| `estimate` | Reasoned or community-sourced; verify before relying on it |

A decision inherits the weakest label among its inputs. Every decision that rests on an estimate is listed in the blueprint's verification section.

## Scope

In version 0.1:

- Decision tables for the inference engine and the LLM gateway.
- Fixed per-tier defaults for UI, identity, observability, orchestration, state stores and artifact registry.
- Sizing from organization answers, a transfer manifest, and lint.

Not in version 0.1:

- Deployment files such as Docker Compose or Helm.
- A recommendation of which model to run.
- Decision tables for data, CI/CD and security layers.
- Compliance mappings.

## Works with superpowers

When [superpowers](https://github.com/obra/superpowers) is installed, the blueprint is written where its specs live and handed to `superpowers:writing-plans` after you approve it. Without superpowers the skill works on its own.

## Contributing

The catalog is the part that ages. [CONTRIBUTING.md](CONTRIBUTING.md) explains how to add or verify an entry. One rule above all: nothing is written from memory.

## License

MIT. See [LICENSE](LICENSE).
````

- [ ] **Step 4: Merge it with the brand images**

Save this script as `/tmp/compose_readme.py` and run it from the repository root with `python3 /tmp/compose_readme.py`. It keeps each image block of the old README whose files still exist, falls back to a default block when the brand files exist but the old README has none, adds nothing when the brand files are absent, and then replaces `README.md`.

```python
import re
from pathlib import Path

old_path = Path("README.md")
new_path = Path("README.md.new")
old = old_path.read_text(encoding="utf-8") if old_path.exists() else ""
body = new_path.read_text(encoding="utf-8")

ALT = {
    "hero": "airgap-anything: design any system for air-gapped environments",
    "pipeline": "The design is made on a connected workstation, carried across the air gap, and built inside without internet.",
}
kept = re.findall(r'<p align="center">\s*<picture>.*?</picture>\s*</p>', old, re.S)


def image_block(name):
    """The existing README's own block for this image, else a default one, else None."""
    light = Path(f"assets/brand/{name}-light.svg")
    dark = Path(f"assets/brand/{name}-dark.svg")
    if not (light.exists() and dark.exists()):
        return None
    for block in kept:
        if light.as_posix() in block:
            return block
    return (
        '<p align="center">\n'
        "  <picture>\n"
        f'    <source media="(prefers-color-scheme: dark)" srcset="{dark.as_posix()}">\n'
        f'    <img src="{light.as_posix()}" alt="{ALT[name]}" width="880">\n'
        "  </picture>\n"
        "</p>"
    )


hero = image_block("hero")
if hero:
    body = hero + "\n\n" + body
    print("hero image placed above the title")

pipeline = image_block("pipeline")
steps_end = "| 8 | Your approval, then hand-off to an implementation plan | you |\n"
if pipeline and steps_end in body:
    body = body.replace(steps_end, steps_end + "\n" + pipeline + "\n", 1)
    print("pipeline image placed below the steps table")

guide = Path("assets/brand/BRAND.md")
contributing = "One rule above all: nothing is written from memory.\n"
if guide.exists() and contributing in body:
    body = body.replace(
        contributing,
        contributing + f"\nLogo files and their usage rules are in the [brand guide]({guide.as_posix()}).\n",
        1,
    )
    print("brand guide linked")

old_path.write_text(body, encoding="utf-8")
new_path.unlink()
print(f"README.md written, {len(body.splitlines())} lines")
```

Expected: a last line `README.md written, N lines`, preceded by one line for each image or link that was placed. `README.md.new` is gone afterwards. Delete `/tmp/compose_readme.py`.

- [ ] **Step 5: Fill in the owner and check the install commands**

```bash
OWNER=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['author']['name'])")
sed -i "s/GITHUB_OWNER/$OWNER/g" README.md
grep -n "$OWNER/airgap-anything" README.md
```

Expected: two lines, the marketplace command and the skills command.

Then compare the three install paths in the README with Q3, Q6 and `## Deviations` in `docs/packaging-facts.md`. If a command there differs, correct the README and the matching assertion in `tests/test_readme.py`.

Check the offline commands once, in a scratch location:

```bash
TMP=$(mktemp -d)
git archive --format=tar.gz --prefix=airgap-architect/ -o "$TMP/airgap-architect.tar.gz" HEAD:skills/airgap-architect
(cd "$TMP" && sha256sum airgap-architect.tar.gz > airgap-architect.tar.gz.sha256 && sha256sum -c airgap-architect.tar.gz.sha256)
tar -tzf "$TMP/airgap-architect.tar.gz" | grep -c -e 'airgap-architect/SKILL.md' -e 'airgap-architect/scripts/lint.py' -e 'airgap-architect/catalog/rules.toml'
rm -rf "$TMP"
```

Expected: `airgap-architect.tar.gz: OK` and `3`.

- [ ] **Step 6: Run the tests to see them pass**

Run: `python3 -m unittest discover -s tests -t .`

Expected: the suite ends with `OK`. `test_every_local_link_and_image_exists` fails if the README points at a file that is not there, which also guards later changes by the brand workstream.

- [ ] **Step 7: Commit**

```bash
git add tests/test_readme.py README.md
git commit -m "docs: replace the design-phase README with the release README"
```

---

### Task 27: CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: the test command and `lint.py --catalog-only`.
- Produces: a workflow that runs both on Python 3.11 and on the newest stable Python (§17), on pushes to `main` and on pull requests.

- [ ] **Step 1: Look up the current major versions of the two actions**

```bash
CHECKOUT=$(gh api repos/actions/checkout/releases/latest --jq .tag_name | cut -d. -f1)
SETUP_PYTHON=$(gh api repos/actions/setup-python/releases/latest --jq .tag_name | cut -d. -f1)
echo "$CHECKOUT $SETUP_PYTHON"
```

Expected: two tags of the form `vN`. If a command fails, stop and report; do not guess a version.

- [ ] **Step 2: Write the workflow**

Create `.github/workflows/ci.yml` with this content:

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.x"]
    steps:
      - uses: actions/checkout@CHECKOUT_MAJOR
      - uses: actions/setup-python@SETUP_PYTHON_MAJOR
        with:
          python-version: ${{ matrix.python-version }}
      - name: Unit tests
        run: python -m unittest discover -s tests -t . -v
      - name: Catalog lint
        run: python skills/airgap-architect/scripts/lint.py --catalog-only
```

Then put in the versions from Step 1:

```bash
sed -i "s/CHECKOUT_MAJOR/$CHECKOUT/; s/SETUP_PYTHON_MAJOR/$SETUP_PYTHON/" .github/workflows/ci.yml
grep -n 'uses:' .github/workflows/ci.yml
```

Expected: two `uses:` lines ending in `@vN`, with no `_MAJOR` left.

- [ ] **Step 3: Run locally what the workflow runs**

```bash
python3 -m unittest discover -s tests -t . -v
python3 skills/airgap-architect/scripts/lint.py --catalog-only
```

Expected: the suite ends with `OK`; lint prints `OK: no findings` or only `W` lines and exits 0.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: run tests and catalog lint on Python 3.11 and newest"
```

---

### Task 28: Final verification

No new files. This task proves the whole thing holds together and reports what is left for the owner.

**Files:**
- None created. Fix-ups only if a check below fails; each fix is committed with the file it touches.

**Interfaces:**
- Consumes: everything.
- Produces: a final report.

- [ ] **Step 1: Run every automated check from a clean state**

```bash
git status --short
find . -name __pycache__ -prune -exec rm -rf {} +
python3 -m unittest discover -s tests -t . -v 2>&1 | tail -3
python3 skills/airgap-architect/scripts/lint.py --catalog-only
```

Expected: no output from `git status --short` apart from files under `design/` or `assets/` that belong to the brand workstream; the suite ends with `OK`; lint exits 0.

- [ ] **Step 2: Run the tests without network access, if the machine allows it**

```bash
if unshare -rn true 2>/dev/null; then
  unshare -rn python3 -m unittest discover -s tests -t . 2>&1 | tail -3
else
  echo "cannot create a network namespace here; skipped"
fi
```

Expected: the suite ends with `OK`, or the "skipped" line. A failure that appears only without network means a script or test reaches out; find and remove the cause.

- [ ] **Step 3: Walk one scenario through the scripts by hand**

This repeats what the pipeline does, without a model, on the `department` scenario:

```bash
RUN=$(mktemp -d)
mkdir -p "$RUN/docs/airgap"
python3 - "$RUN" <<'EOF'
import json
import sys
from pathlib import Path

answers = json.loads(Path("evals/scenarios/department/answers.json").read_text(encoding="utf-8"))
blueprint = {
    "schema_version": 1,
    "project": "department",
    "created": "2026-11-20",
    "language": "en",
    "blueprint_path": "docs/airgap/blueprint.md",
    "answers": answers,
    "assumptions": [],
    "tier": {},
    "sizing": {},
    "decisions": [],
}
Path(sys.argv[1], "docs", "airgap", "blueprint.json").write_text(json.dumps(blueprint, indent=2), encoding="utf-8")
EOF
python3 skills/airgap-architect/scripts/tier.py --blueprint "$RUN/docs/airgap/blueprint.json"
python3 skills/airgap-architect/scripts/size.py --blueprint "$RUN/docs/airgap/blueprint.json"
python3 skills/airgap-architect/scripts/manifest.py --blueprint "$RUN/docs/airgap/blueprint.json"
python3 skills/airgap-architect/scripts/lint.py --blueprint "$RUN/docs/airgap/blueprint.json" --project-root "$RUN"; echo "lint exit: $?"
rm -rf "$RUN"
```

Expected: `Base tier: T2`; `Peak concurrency: 6-11 requests in flight` and `Total: 8 GPU(s), 1 server(s), power 10.1 kW, fits: True`; a "Wrote" line; then `lint exit: 1` after eight `E4` lines (no decisions yet), one `E7` line (no blueprint file) and one `W3` line. That set of findings is the lint gate doing its job on a design that has answers and numbers but no decisions.

- [ ] **Step 4: Check the spec against the repository**

Confirm each line by opening the file. Any "no" is fixed before the report.

| Spec | Must exist |
|---|---|
| §6.1 layout | Every path in "File Structure" at the top of this plan |
| §7 | 18 questions in `references/interview.md` and in `airgap_lib/answers.py` |
| §8 | Thresholds and four escalators in `catalog/rules.toml` |
| §9 | Three table files under `references/layers/`, every row with an evidence label |
| §9.4 | Sixteen files under `catalog/components/` |
| §10 | `airgap_lib/sizing.py`; GPU rows in `catalog/gpus.toml` |
| §11 | Evidence fields in every catalog entry; `lint.py --catalog-only` clean |
| §12 | Four scripts; tests for E1 to E11 and W1 to W3 in `tests/test_checks.py` |
| §14 | Ten section markers in `references/blueprint-template.md`; block markers in `references/agents-snippet.md` |
| §15 | The three situations in the "Blueprint path and superpowers" table of `SKILL.md` |
| §17 | `tests/`, `evals/scenarios/`, `evals/results/` with a baseline file and a with-skill file |
| §18 | `.claude-plugin/` manifests; three install paths in `README.md` |

- [ ] **Step 5: Report**

Write the final report. It states, with the command output as evidence:

1. The number of tests and that they pass.
2. The catalog lint result, including any warnings.
3. How many catalog entries are `docs` and how many are `estimate`, from `grep -h '^level' skills/airgap-architect/catalog/components/*.toml | sort | uniq -c`.
4. The criteria table from the newest `evals/results/*-with-skill.md`.
5. What the owner still has to decide or do: confirm the GitHub owner in the manifests, create the repository and push, review the entries labeled `estimate`, and add `field` evidence from real deployments.

Do not push, tag or create a repository.

---

## Open questions

Where the spec is silent or reads two ways, this plan chose the reading most consistent with the rest of the spec. Each choice is listed so the owner can overrule it. None blocks execution.

### Readings of the spec

1. **`tiers` in a catalog entry** lists the floors at which the component is still adequate, so a component fit for T3 also lists T1 and T2 (§8.2 says a floor "restricts choices to components whose `tiers` include it"; §11.1 shows `vllm` with all three). No component is "T2 and T3 only". Starting assignments: `ollama`, `docker-compose` and `k3s` allow T1 and T2; `distribution-registry` allows T1; the other twelve allow all three.
2. **A gateway is required for `multi_level` isolation too.** §8.2 says so only for audit and `per_department`, but §9.2 chooses a gateway for any isolation other than `none`.
3. **Escalator requirements are stored** in a new `tier.requirements` object (`gateway_non_empty`, `isolation_design_section`, `two_engine_replicas`, `kubernetes_risk_note`). §13 shows `tier` with `base`, `floors` and `reasons` only, which leaves "the gateway may not be empty" nowhere to live. `tier.floors` lists all eight layers; the §13 example is abbreviated.
4. **E10's override lives on the `llm-serving` decision.** §12 says "an override explains how the gap is closed" but `blueprint.json` has no sizing-level override.
5. **E9 enforces the weakest-label rule of §11.2** as well as the listing in the verification section, and requires `org.kubernetes_experience` there when §8.2 calls for the risk note.
6. **E2 also rejects a component filed under the wrong layer.** And **note `N1` reports each override:** §8.2 says "`lint.py` reports every override" but §12 gives it no code. A note is printed and does not change the exit code.
7. **Blueprint sections are found by HTML comment markers,** not headings, because §14.1 lets the blueprint be written in the interview's language. E7 wants one line in the decisions section that names each chosen component together with its version.
8. **The manifest digest covers `decisions` and `workload.models`.** §14.2 says "a digest of `decisions`", but the manifest also lists model artifacts, so a changed model list must make it stale. The header line is still called "Decisions digest".
9. **`manifest.py` reads `answers` too.** The table in §12 lists only `decisions` and the catalog; §14.2 item 2 needs `workload.models`.
10. **Evidence is one label per catalog entry,** not per field (§11.1 has a single `[evidence]` table). An entry is `docs` only when every sourced field has a URL; otherwise `estimate` with the gaps named.
11. **Exit code 3** is added for environment problems (Python older than 3.11, unreadable catalog). §12 lists 0, 1 and 2.
12. **Catalog findings use codes C1 to C4.** §12 names codes only for blueprint lint.
13. **`sglang` is "chosen directly only with field evidence"** (§9.1) by instruction in the decision table. Lint does not enforce it.
14. **`state` at T1** ("`postgresql` when a chosen component needs it") is driven by `requires` and E11, with no separate rule.

### Values the plan had to pick

All are in `rules.toml`, labeled `estimate`, and easy to change. Tests pin them.

15. **Defaults for "unknown" answers** (§7 says "the documented default" without listing them): `org.isolation` = `per_department`, `org.audit_required` = true, `org.downtime_tolerance` = `planned_only`, `org.ops_capacity` = `part_time_one`, `org.kubernetes_experience` = false, `workload.usage` = chat only, the three `existing.*` questions = `none`, `transfer.channel` = `removable_media`. Unknown privacy answers lean strict. Four questions have no default and must be answered: `org.users_total`, `org.departments`, `workload.models`, `hardware.gpus`.
16. **Size-class representatives** (§7 names the classes, not the numbers): S = 8B, M = 32B, L = 120B, XL = 671B parameters, with `bf16` as the precision when a class is given without one.
17. **KV-cache defaults:** 8,192 context tokens when a model entry has none, 1,024 output tokens per request, `fp16` cache elements.

### Sizing behavior the spec leaves open

18. **Several GPU types:** only the type with the most memory is used, with a warning. Mixed-type packing is not attempted.
19. **Several models:** each generative model is sized for the full interactive concurrency. Embedding and rerank models get a weights-only fit.
20. **KV cache too small for one sequence** (§10.2 step 5 does not say): the next larger GPU group is tried; if none works, the model is marked `insufficient` and `fits` is false.
21. **`hardware.gpus[].count` is required.** A planned purchase is entered as the intended count; if sizing needs more, `fits` is false until the count or the model changes, or an override is recorded.

### For the owner

22. **GitHub owner.** Task 25 takes it from the `origin` remote, or from `gh api user` when there is no remote. If the repository moves to an organization, change `author.name`, `owner.name` and the two URLs in the manifests; `tests/test_readme.py` then tells you which README lines to update.
23. **Copyright line.** Task 2 writes `LICENSE` with "Copyright (c) 2026 airgap-anything contributors". The handoff note leaves the holder's name to the maintainer; change that one line before the repository is made public.
24. **README.** Task 26 replaces the text of the design-phase README and keeps its hero and pipeline images. It adds a plain `# airgap-anything` heading below the hero image, which the design-phase page did not have. The "Read next" table of that page is dropped, and the link to `docs/HANDOFF.md` goes with it.
25. **Spec status line.** The spec still says "Status: Draft for review" although it was approved. Cosmetic; this plan does not edit the spec.
26. **Extra files beyond §6.1:** `docs/packaging-facts.md`, `evals/README.md`, `evals/score.py`, `evals/results/`, and the shared modules inside `airgap_lib/`. §6.1 lists `evals/scenarios/` only, while §17.6 requires results to be recorded.
