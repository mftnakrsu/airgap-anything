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
