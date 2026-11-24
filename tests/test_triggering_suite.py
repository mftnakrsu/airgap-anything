"""Shape of plugins/airgap-anything/evals/triggering, the `claude plugin eval` suite that checks Claude Code picks the skill.

Running the suite needs a model and costs money; these checks only keep its cases well formed.
"""

import re
import unittest

from tests import PLUGIN_DIR, REPO_ROOT

SUITE = PLUGIN_DIR / "evals" / "triggering"


def skill_match(skill):
    return rf"""'"skill"\s*:\s*"(?:[\w-]+:)?{skill}"'"""


# Grader files that check a Skill call, and the skill each one names. The architect names
# are the ones of the first suite; the transfer and agent ones carry the skill's name.
POSITIVE = {"fires.md": "airgap-architect", "fires-transfer.md": "airgap-transfer", "fires-agent.md": "airgap-agent"}
NEGATIVE = {"does-not-fire.md": "airgap-architect", "does-not-fire-transfer.md": "airgap-transfer",
            "does-not-fire-agent.md": "airgap-agent"}
# The reply each skill's auto case is graded on.
STARTS = {"airgap-architect": "starts-the-interview.md", "airgap-transfer": "starts-the-transfer.md",
          "airgap-agent": "starts-the-agent-interview.md"}
TRANSFER_CASES = {"auto-en-build-bundle", "auto-tr-usb-hazirla", "auto-en-verify-inside", "skip-en-docker-save"}
AGENT_CASES = {"auto-en-coding-agent", "auto-tr-kodlama-ajani", "skip-en-cloud-copilot"}


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

    def graders(self, case):
        return {path.name: frontmatter(path) for path in (case / "graders").glob("*.md")}

    def test_every_kind_of_case_is_there(self):
        names = [case.name for case in self.cases]
        for prefix in ("auto-en-", "auto-tr-", "manual-", "skip-en-", "skip-tr-"):
            self.assertTrue(any(name.startswith(prefix) for name in names), prefix)
        self.assertTrue(TRANSFER_CASES <= set(names))
        self.assertTrue(AGENT_CASES <= set(names))

    def test_every_session_can_call_the_skill(self):
        for case in self.cases:
            with self.subTest(case=case.name):
                tools = frontmatter(case / "prompt.md")["allowed_tools"]
                self.assertIn("Skill", re.findall(r"\w+", tools))

    def test_every_skill_check_names_its_skill(self):
        for case in self.cases:
            for name, grader in self.graders(case).items():
                if grader.get("type") == "tool_used" and grader.get("tool") == "Skill":
                    with self.subTest(case=case.name, grader=name):
                        skill = {**POSITIVE, **NEGATIVE}[name]
                        self.assertEqual(grader["input_match"], skill_match(skill))
                        if name in NEGATIVE:
                            self.assertEqual((grader["min"], grader["max"]), ("0", "0"))
                        else:
                            self.assertNotIn("max", grader)

    def test_each_case_checks_the_right_thing(self):
        for case in self.cases:
            graders = self.graders(case)
            positive = [POSITIVE[name] for name in graders if name in POSITIVE]
            negative = [NEGATIVE[name] for name in graders if name in NEGATIVE]
            with self.subTest(case=case.name):
                if case.name.startswith("skip-"):
                    self.assertEqual(positive, [])
                    self.assertIn("airgap-architect", negative)
                elif case.name.startswith("auto-"):
                    self.assertEqual(len(positive), 1)
                    self.assertIn(STARTS[positive[0]], graders)
                    self.assertNotIn(positive[0], negative)
                else:
                    # A slash command is expanded before the session, so no Skill call is made.
                    self.assertEqual(positive, [])
                    self.assertEqual(graders["loads-the-skill.md"]["target"], "trace")
                    self.assertIn("starts-the-interview.md", graders)
                    prompt = (case / "prompt.md").read_text(encoding="utf-8")
                    self.assertIn("/airgap-anything:airgap-architect ", prompt)

    def test_the_two_skills_are_kept_apart(self):
        # The architect case about what to carry must not start airgap-transfer, and a plain
        # Docker question starts neither skill.
        self.assertIn("does-not-fire-transfer.md", self.graders(SUITE / "auto-tr-tasima-listesi"))
        self.assertEqual(
            sorted(NEGATIVE[name] for name in self.graders(SUITE / "skip-en-docker-save") if name in NEGATIVE),
            ["airgap-architect", "airgap-transfer"],
        )

    def test_agent_and_architect_are_kept_apart(self):
        self.assertIn("does-not-fire-agent.md", self.graders(SUITE / "auto-en-offline-platform"))
        self.assertIn("does-not-fire.md", self.graders(SUITE / "auto-en-coding-agent"))


class TriggeringWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.text = (REPO_ROOT / ".github" / "workflows" / "triggering.yml").read_text(encoding="utf-8")

    def test_it_never_hands_the_key_to_untrusted_code(self):
        # pull_request_target would run a fork's code with this repository's secrets.
        self.assertNotIn("pull_request_target", self.text)
        self.assertIn("permissions:\n  contents: read", self.text)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", self.text)

    def test_it_runs_only_when_triggering_can_change(self):
        for path in (
            "plugins/airgap-anything/skills/airgap-architect/SKILL.md",
            "plugins/airgap-anything/skills/airgap-transfer/SKILL.md",
            "plugins/airgap-anything/skills/airgap-agent/SKILL.md",
            "plugins/airgap-anything/evals/triggering/**",
            ".github/workflows/triggering.yml",
        ):
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
