"""The agent catalog of airgap-agent: one entry per coding-agent tool, with the fields and
sections the skill reads, a pinned version, the API it speaks, and a source for every switch."""
import re
import unittest
from datetime import date

from tests import AGENT_CATALOG_DIR, AGENT_TOOLS, APIS, EVIDENCE_LEVELS

FIELDS = ["Kind", "Version", "License", "Speaks", "Install", "Evidence", "Last verified"]
AGENT_SECTIONS = ["## Choose when", "## Avoid when", "## Serving needs", "## Configuration",
                  "## Egress switches", "## Permissions and central policy", "## Skills, context and MCP",
                  "## Caveats", "## Carry in", "## Evidence"]
CARRY_IN = ["### Packages", "### Runtime downloads to stage in advance",
            "### Telemetry and egress to switch off before the first start"]


def entries():
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(AGENT_CATALOG_DIR.glob("*.md"))}


def fields(text):
    table = {}
    for line in text.splitlines():
        match = re.match(r"\| (" + "|".join(FIELDS) + r") \| (.*) \|$", line)
        if match:
            table[match.group(1)] = match.group(2)
    return table


class AgentCatalogTest(unittest.TestCase):
    def setUp(self):
        self.entries = entries()

    def test_entries_are_there(self):
        # Task 1 adds qwen-code; Task 2 makes this the full set.
        self.assertTrue(set(self.entries) <= set(AGENT_TOOLS))
        self.assertIn("qwen-code", self.entries)

    def test_the_title_names_the_file(self):
        for tool, text in self.entries.items():
            with self.subTest(tool=tool):
                self.assertRegex(text.splitlines()[0], rf"^# .+ \(`{re.escape(tool)}`\)$")

    def test_fields(self):
        for tool, text in self.entries.items():
            table = fields(text)
            with self.subTest(tool=tool):
                self.assertEqual(list(table), FIELDS)
                self.assertEqual(table["Kind"], "`coding-agent`")
                self.assertRegex(table["Version"], r"^`[^`\s]+`$")
                self.assertNotIn("latest", table["Version"])
                self.assertTrue(set(re.findall(r"`([a-z-]+)`", table["Speaks"])) <= set(APIS))
                self.assertIn(table["Evidence"], EVIDENCE_LEVELS)
                self.assertLessEqual(date.fromisoformat(table["Last verified"]), date.today())

    def test_sections_in_order(self):
        for tool, text in self.entries.items():
            with self.subTest(tool=tool):
                positions = [text.find("\n" + h + "\n") for h in AGENT_SECTIONS + CARRY_IN]
                self.assertNotIn(-1, positions)
                self.assertEqual(positions[: len(AGENT_SECTIONS)], sorted(positions[: len(AGENT_SECTIONS)]))

    def test_every_egress_switch_row_has_a_source(self):
        for tool, text in self.entries.items():
            section = text.split("\n## Egress switches\n", 1)[1].split("\n## ", 1)[0]
            rows = [l for l in section.splitlines() if l.startswith("| ") and not l.startswith("| Connection") and "---" not in l]
            with self.subTest(tool=tool):
                self.assertGreater(len(rows), 0)
                for row in rows:
                    self.assertIn("https://", row)

    def test_evidence_has_sources(self):
        for tool, text in self.entries.items():
            with self.subTest(tool=tool):
                self.assertRegex(text.split("\n## Evidence\n", 1)[1], r"\n- https://")

    def test_no_curl_next_to_a_pipe_or_url(self):
        # The directory scanner flags curl with | or a URL on one prose line.
        for tool, text in self.entries.items():
            for line in text.splitlines():
                if "curl" in line:
                    with self.subTest(tool=tool, line=line):
                        self.assertNotRegex(line, r"\||https?://")


if __name__ == "__main__":
    unittest.main()
