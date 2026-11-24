"""The markdown catalog of airgap-architect: every entry has the fields and sections the skill
reads, names only components and layers that exist, and carries an evidence label and sources."""
import re
import unittest
from datetime import date

from tests import CATALOG_DIR, EVIDENCE_LEVELS, LAYERS, SKILL_DIR

SECTIONS = ["## Choose when", "## Avoid when", "## Alternatives", "## Caveats", "## Carry in", "## Per-tool skills", "## Evidence"]
CARRY_IN = ["### Images", "### Packages", "### Runtime downloads to stage in advance",
            "### Telemetry and egress to switch off before the first start", "### License server"]
FIELDS = ["Layer", "Version", "License", "Tiers", "Requires", "Evidence", "Last verified"]


def entries():
    return {path.stem: path.read_text(encoding="utf-8") for path in sorted(CATALOG_DIR.glob("*.md"))}


def fields(text):
    table = {}
    for line in text.splitlines():
        match = re.match(r"\| (Layer|Version|License|Tiers|Requires|Evidence|Last verified) \| (.*) \|$", line)
        if match:
            table[match.group(1)] = match.group(2)
    return table


def ids(cell):
    return re.findall(r"`([a-z0-9-]+)`", cell)


class CatalogEntryTest(unittest.TestCase):
    def setUp(self):
        self.entries = entries()

    def test_there_are_entries_for_every_layer(self):
        layers = {ids(fields(text)["Layer"])[0] for text in self.entries.values()}
        self.assertEqual(layers, set(LAYERS))

    def test_the_title_names_the_file(self):
        for component_id, text in self.entries.items():
            with self.subTest(entry=component_id):
                self.assertRegex(text.splitlines()[0], rf"^# .+ \(`{re.escape(component_id)}`\)$")

    def test_every_field_is_there_and_valid(self):
        for component_id, text in self.entries.items():
            table = fields(text)
            with self.subTest(entry=component_id):
                self.assertEqual(list(table), FIELDS)
                self.assertIn(ids(table["Layer"])[0], LAYERS)
                self.assertRegex(table["Version"], r"^`[^`\s]+`$")
                self.assertTrue(set(table["Tiers"].split(", ")) <= {"T1", "T2", "T3"})
                self.assertIn(table["Evidence"], EVIDENCE_LEVELS)
                verified = date.fromisoformat(table["Last verified"])
                self.assertLessEqual(verified, date.today())
                for required in ids(table["Requires"]):
                    self.assertIn(required, self.entries)

    def test_sections_come_in_the_order_the_skill_reads_them(self):
        for component_id, text in self.entries.items():
            with self.subTest(entry=component_id):
                positions = [text.find("\n" + heading + "\n") for heading in SECTIONS + CARRY_IN]
                self.assertNotIn(-1, positions)
                self.assertEqual(positions[: len(SECTIONS)], sorted(positions[: len(SECTIONS)]))

    def test_alternatives_are_catalog_entries(self):
        for component_id, text in self.entries.items():
            section = text.split("\n## Alternatives\n", 1)[1].split("\n## ", 1)[0]
            for alternative in ids(section):
                with self.subTest(entry=component_id, alternative=alternative):
                    self.assertIn(alternative, self.entries)

    def test_images_are_pinned_references(self):
        for component_id, text in self.entries.items():
            section = text.split("\n### Images\n", 1)[1].split("\n### ", 1)[0]
            for ref in re.findall(r"^\| `([^`]+)` \|", section, re.M):
                with self.subTest(entry=component_id, image=ref):
                    self.assertRegex(ref, r":[^/]+$|@sha256:[0-9a-f]{64}$")
                    self.assertNotRegex(ref, r":latest$")

    def test_evidence_has_sources(self):
        for component_id, text in self.entries.items():
            section = text.split("\n## Evidence\n", 1)[1]
            with self.subTest(entry=component_id):
                self.assertRegex(section, r"\n- https://")

    def test_skill_md_lists_every_entry_under_its_layer(self):
        listing = {}
        for line in (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").splitlines():
            match = re.match(r"\| `([a-z-]+)` \| (`catalog/.*)\|$", line)
            if match:
                listing.update({stem: match.group(1) for stem in re.findall(r"catalog/([a-z0-9-]+)\.md", match.group(2))})
        self.assertEqual(set(listing), set(self.entries))
        for component_id, layer in listing.items():
            with self.subTest(entry=component_id):
                self.assertEqual(ids(fields(self.entries[component_id])["Layer"])[0], layer)


class GuidesTest(unittest.TestCase):
    def test_components_a_guide_names_are_in_the_catalog(self):
        catalog = set(entries())
        used = set()
        for path in sorted((SKILL_DIR / "references" / "layers").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            line = next(l for l in text.splitlines() if l.startswith("Components used in this file:"))
            for component_id in ids(line):
                with self.subTest(guide=path.name, component=component_id):
                    self.assertIn(component_id, catalog)
                    self.assertGreaterEqual(text.count(f"`{component_id}`"), 2)
                used.add(component_id)
        self.assertEqual(used, catalog)

    def test_every_guide_row_has_an_evidence_label(self):
        for path in sorted((SKILL_DIR / "references" / "layers").glob("*.md")):
            rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("|")]
            column = rows[0].index("Evidence")
            for row in rows[2:]:
                with self.subTest(guide=path.name, row=row[0]):
                    self.assertIn(row[column], EVIDENCE_LEVELS)


class GpuTableTest(unittest.TestCase):
    def test_every_row_has_memory_vendor_and_a_source(self):
        text = (SKILL_DIR / "references" / "gpus.md").read_text(encoding="utf-8")
        rows = re.findall(r"^\| ([^|]+) \| [^|]* \| (nvidia|amd|intel) \| (\d+(?:\.\d+)?) \| (\d+|unknown) \| (\w+) \| (\d{4}-\d{2}-\d{2}) \|$", text, re.M)
        self.assertGreaterEqual(len(rows), 10)
        for model, _, _, _, evidence, _ in rows:
            with self.subTest(gpu=model):
                self.assertIn(evidence, EVIDENCE_LEVELS)
                self.assertRegex(text.split(f"\n### {model}\n", 1)[1].split("\n### ", 1)[0], r"\n- https://")



class TransferFixtureTest(unittest.TestCase):
    """The finished designs the airgap-transfer evals start from name what the catalog says today."""

    def test_every_manifest_row_matches_its_catalog_entry(self):
        catalog = entries()
        for manifest in sorted((CATALOG_DIR.parents[3] / "evals" / "transfer-scenarios").glob("*/project/docs/airgap/transfer-manifest.md")):
            text = manifest.read_text(encoding="utf-8")
            section = text.split("\n## 1. Container images\n", 1)[1].split("\n## ", 1)[0]
            for component, version, image in re.findall(r"^\| `([a-z0-9-]+)`(?: \(benchmark only\))? \| `([^`]+)` \| `([^`]+)` \|", section, re.M):
                with self.subTest(scenario=manifest.parents[3].name, image=image):
                    self.assertEqual(fields(catalog[component])["Version"], f"`{version}`")
                    self.assertIn(f"| `{image}` |", catalog[component])


if __name__ == "__main__":
    unittest.main()
