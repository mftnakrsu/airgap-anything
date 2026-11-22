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
            self.assertIn(f'"${{CLAUDE_SKILL_DIR}}/scripts/{script}"', self.text)
            self.assertTrue((SKILL_DIR / "scripts" / script).is_file(), script)
        for layer in LAYERS:
            self.assertIn(f"`{layer}`", self.text)


if __name__ == "__main__":
    unittest.main()
