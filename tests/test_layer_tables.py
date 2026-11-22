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
