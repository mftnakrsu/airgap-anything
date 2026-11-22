"""Shape of plugins/airgap-anything/evals/triggering, the `claude plugin eval` suite that checks Claude Code picks the skill.

Running the suite needs a model and costs money; these checks only keep its cases well formed.
"""

import re
import unittest

from tests import PLUGIN_DIR, REPO_ROOT

SUITE = PLUGIN_DIR / "evals" / "triggering"
SKILL_MATCH = r"""'"skill"\s*:\s*"(?:[\w-]+:)?airgap-architect"'"""


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert match, path
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


class TriggeringSuiteTest(unittest.TestCase):
    def setUp(self):
        self.cases = sorted(p for p in SUITE.iterdir() if p.is_dir() and p.name != "results")

    def test_every_kind_of_case_is_there(self):
        names = [case.name for case in self.cases]
        for prefix in ("auto-en-", "auto-tr-", "manual-", "skip-en-", "skip-tr-"):
            self.assertTrue(any(name.startswith(prefix) for name in names), prefix)

    def test_every_session_can_call_the_skill(self):
        for case in self.cases:
            with self.subTest(case=case.name):
                tools = frontmatter(case / "prompt.md")["allowed_tools"]
                self.assertIn("Skill", re.findall(r"\w+", tools))

    def test_each_case_checks_the_right_thing(self):
        for case in self.cases:
            graders = {path.name: frontmatter(path) for path in (case / "graders").glob("*.md")}
            with self.subTest(case=case.name):
                skill_checks = [g for g in graders.values() if g.get("type") == "tool_used" and g.get("tool") == "Skill"]
                if case.name.startswith("skip-"):
                    self.assertEqual(len(skill_checks), 1)
                    self.assertEqual(skill_checks[0]["input_match"], SKILL_MATCH)
                    self.assertEqual((skill_checks[0]["min"], skill_checks[0]["max"]), ("0", "0"))
                elif case.name.startswith("auto-"):
                    self.assertEqual(len(skill_checks), 1)
                    self.assertEqual(skill_checks[0]["input_match"], SKILL_MATCH)
                    self.assertNotIn("max", skill_checks[0])
                    self.assertIn("starts-the-interview.md", graders)
                else:
                    # A slash command is expanded before the session, so no Skill call is made.
                    self.assertEqual(skill_checks, [])
                    self.assertEqual(graders["loads-the-skill.md"]["target"], "trace")
                    self.assertIn("starts-the-interview.md", graders)
                    prompt = (case / "prompt.md").read_text(encoding="utf-8")
                    self.assertIn("/airgap-anything:airgap-architect ", prompt)


class TriggeringWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.text = (REPO_ROOT / ".github" / "workflows" / "triggering.yml").read_text(encoding="utf-8")

    def test_it_never_hands_the_key_to_untrusted_code(self):
        # pull_request_target would run a fork's code with this repository's secrets.
        self.assertNotIn("pull_request_target", self.text)
        self.assertIn("permissions:\n  contents: read", self.text)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", self.text)

    def test_it_runs_only_when_triggering_can_change(self):
        for path in ("plugins/airgap-anything/skills/airgap-architect/SKILL.md", "plugins/airgap-anything/evals/triggering/**", ".github/workflows/triggering.yml"):
            self.assertIn(f'- "{path}"', self.text)
        self.assertIn("workflow_dispatch", self.text)

    def test_it_skips_rather_than_fails_without_a_credential(self):
        self.assertIn("::notice::", self.text)
        self.assertNotIn("::error::", self.text)
        steps_after_the_check = self.text.split("id: credential", 1)[1].split("- uses: ")[1:]
        steps_after_the_check += self.text.split("- name: Triggering suite", 1)[1:]
        for step in steps_after_the_check:
            self.assertIn("steps.credential.outputs.found == 'true'", step)

    def test_every_run_has_a_ceiling_and_stays_local(self):
        for flag in ("claude plugin eval plugins/airgap-anything --eval-dir evals/triggering", "--max-cost-usd", "--no-publish", "--threshold", "--json"):
            self.assertIn(flag, self.text)

if __name__ == "__main__":
    unittest.main()
