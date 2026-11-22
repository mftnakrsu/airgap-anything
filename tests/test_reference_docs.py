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
