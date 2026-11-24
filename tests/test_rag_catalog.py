"""The catalog of airgap-rag: one sourced entry per component, with the fields and sections
the skill reads, a pinned version, and a source for every egress switch."""
import re
import unittest
from datetime import date

from tests import EVIDENCE_LEVELS, RAG_CATALOG_DIR, RAG_ENTRIES, RAG_KINDS

FIELDS = ["Kind", "Version", "License", "Install", "Evidence", "Last verified"]
SECTIONS = ["## Choose when", "## Avoid when", "## Configuration", "## Egress switches",
            "## Caveats", "## Carry in", "## Evidence"]
CARRY_IN = ["### Images", "### Models", "### Runtime downloads to stage in advance",
            "### Telemetry and egress to switch off before the first start"]


def entries():
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(RAG_CATALOG_DIR.glob("*.md"))}


def fields(text):
    table = {}
    for line in text.splitlines():
        match = re.match(r"\| (" + "|".join(FIELDS) + r") \| (.*) \|$", line)
        if match:
            table[match.group(1)] = match.group(2)
    return table


class RagCatalogTest(unittest.TestCase):
    def setUp(self):
        self.entries = entries()

    def test_entries_are_known(self):
        self.assertEqual(set(self.entries), set(RAG_ENTRIES))

    def test_ragflow_states_its_permission_model_and_hf_endpoint(self):
        text = self.entries["ragflow"]
        self.assertIn("HF_ENDPOINT", text)
        self.assertRegex(text, r"(?i)only me")

    def test_models_carry_their_serving_command(self):
        for name in ("qwen3-embedding", "bge-m3", "qwen3-reranker", "bge-reranker-v2-m3"):
            with self.subTest(entry=name):
                self.assertIn("--runner pooling", self.entries[name])

    def test_qwen3_reranker_has_the_documented_overrides(self):
        self.assertIn("is_original_qwen3_reranker", self.entries["qwen3-reranker"])

    def test_the_title_names_the_file(self):
        for name, text in self.entries.items():
            with self.subTest(entry=name):
                self.assertRegex(text.splitlines()[0], rf"^# .+ \(`{re.escape(name)}`\)$")

    def test_fields(self):
        for name, text in self.entries.items():
            table = fields(text)
            with self.subTest(entry=name):
                self.assertEqual(list(table), FIELDS)
                self.assertIn(table["Kind"].strip("`"), RAG_KINDS)
                self.assertRegex(table["Version"], r"^`[^`\s]+`")
                self.assertNotIn("latest", table["Version"])
                self.assertIn(table["Evidence"], EVIDENCE_LEVELS)
                self.assertLessEqual(date.fromisoformat(table["Last verified"]), date.today())

    def test_sections_in_order(self):
        for name, text in self.entries.items():
            with self.subTest(entry=name):
                positions = [text.find("\n" + h + "\n") for h in SECTIONS + CARRY_IN]
                self.assertNotIn(-1, positions)
                self.assertEqual(positions[: len(SECTIONS)], sorted(positions[: len(SECTIONS)]))

    def test_every_egress_row_has_a_source(self):
        for name, text in self.entries.items():
            section = text.split("\n## Egress switches\n", 1)[1].split("\n## ", 1)[0]
            rows = [l for l in section.splitlines()
                    if l.startswith("| ") and not l.startswith("| Connection") and "---" not in l]
            for row in rows:
                with self.subTest(entry=name, row=row[:40]):
                    self.assertIn("https://", row)

    def test_evidence_has_sources(self):
        for name, text in self.entries.items():
            with self.subTest(entry=name):
                self.assertRegex(text.split("\n## Evidence\n", 1)[1], r"\n- https://")

    def test_no_curl_next_to_a_pipe_or_url(self):
        for name, text in self.entries.items():
            for line in text.splitlines():
                if "curl" in line:
                    with self.subTest(entry=name, line=line[:60]):
                        self.assertNotRegex(line, r"\||https?://")


if __name__ == "__main__":
    unittest.main()
