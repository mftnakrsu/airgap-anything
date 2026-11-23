import re
import unittest

from tests import TRANSFER_DIR, TRANSFER_SCRIPTS_DIR
from tests.test_skill_file import MAX_DESCRIPTION_CHARS, MAX_NAME_CHARS, frontmatter, read
from transfer_lib.constants import CHANNELS, FILESYSTEMS
from transfer_lib.questions import QUESTION_IDS
from transfer_lib.tools import COMMANDS

REFERENCES = TRANSFER_DIR / "references"
MAX_SKILL_LINES = 150
SCRIPTS = ("plan.py", "pack.py", "check.py")


def table_rows(text):
    return [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in text.splitlines() if line.strip().startswith("|")]


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
