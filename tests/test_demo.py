import json
import unittest
import xml.etree.ElementTree as ET

from tests import REPO_ROOT
from airgap_lib.constants import LAYERS

DEMO_INPUT = REPO_ROOT / "design" / "demo" / "department-blueprint.json"
SVG_FILES = [
    REPO_ROOT / "assets" / "demo" / "terminal-light.svg",
    REPO_ROOT / "assets" / "demo" / "terminal-dark.svg",
]
SCRIPT_NAMES = ("tier.py", "size.py", "manifest.py", "lint.py")
PRIVATE_PATHS = ("/Users/", "/home/", "/private/", "/tmp/", "/var/folders/")


SVG = "{http://www.w3.org/2000/svg}"


def row_elements(root):
    """The terminal rows: groups whose class list holds "row"."""
    return [g for g in root.iter(f"{SVG}g") if "row" in g.attrib.get("class", "").split()]


def row_texts(path):
    root = ET.parse(path).getroot()
    return ["".join(row.itertext()) for row in row_elements(root)]


class TerminalDemoTest(unittest.TestCase):
    def test_both_svgs_exist_and_parse_as_xml(self):
        for path in SVG_FILES:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), "run design/demo/build_demo.py")
                self.assertEqual(ET.parse(path).getroot().tag, "{http://www.w3.org/2000/svg}svg")

    def test_the_rows_show_the_four_scripts_and_a_clean_lint(self):
        # Read the rows of the terminal, not the static description of the image.
        for path in SVG_FILES:
            with self.subTest(path=path.name):
                rows = row_texts(path)
                commands = [row for row in rows if row.startswith("$ ")]
                for name in SCRIPT_NAMES:
                    self.assertIn(
                        f"$ python3 $skill/scripts/{name} --blueprint docs/airgap/blueprint.json",
                        commands,
                    )
                self.assertEqual(rows[-1], "OK: no findings")

    def test_every_row_is_visible_without_the_animation(self):
        for path in SVG_FILES:
            with self.subTest(path=path.name):
                root = ET.parse(path).getroot()
                css = "".join(root.find(f"{SVG}style").itertext())
                base_css = css[: css.index("@media")]
                self.assertIn("prefers-reduced-motion: no-preference", css)
                self.assertNotRegex(base_css, r"\.(row|fade)[^{}]*\{[^}]*opacity")
                self.assertTrue(row_elements(root), "the SVG has no rows")
                for row in row_elements(root):
                    self.assertNotIn("opacity", row.attrib.get("style", ""))
                    self.assertNotIn("display", row.attrib.get("style", ""))
                    self.assertNotIn("visibility", row.attrib.get("style", ""))

    def test_the_image_height_matches_its_view_box(self):
        for path in SVG_FILES:
            with self.subTest(path=path.name):
                root = ET.parse(path).getroot()
                view_box = [float(part) for part in root.attrib["viewBox"].split()]
                self.assertEqual(view_box[2], float(root.attrib["width"]))
                self.assertEqual(view_box[3], float(root.attrib["height"]))

    def test_no_path_of_this_machine_and_no_script(self):
        for path in SVG_FILES:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                for fragment in PRIVATE_PATHS:
                    self.assertNotIn(fragment, text)
                self.assertNotIn("<script", text)


class DemoInputTest(unittest.TestCase):
    def setUp(self):
        self.blueprint = json.loads(DEMO_INPUT.read_text(encoding="utf-8"))

    def test_keys_are_exactly_the_input_of_the_scripts(self):
        self.assertEqual(
            set(self.blueprint),
            {
                "schema_version",
                "project",
                "created",
                "language",
                "blueprint_path",
                "answers",
                "decisions",
            },
        )

    def test_one_decision_per_layer(self):
        layers = [decision["layer"] for decision in self.blueprint["decisions"]]
        self.assertCountEqual(layers, LAYERS)


if __name__ == "__main__":
    unittest.main()
