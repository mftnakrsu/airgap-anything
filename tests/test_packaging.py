import json
import unittest

from tests import REPO_ROOT, SKILL_DIR


def load(name):
    return json.loads((REPO_ROOT / ".claude-plugin" / name).read_text(encoding="utf-8"))


class ManifestTest(unittest.TestCase):
    def test_plugin_manifest(self):
        plugin = load("plugin.json")
        self.assertEqual(plugin["name"], "airgap-anything")
        self.assertRegex(plugin["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(plugin["license"], "MIT")
        self.assertTrue(plugin["description"].strip())
        self.assertTrue(plugin["author"]["name"].strip())
        self.assertNotIn("email", plugin["author"])

    def test_marketplace_lists_the_plugin_at_the_repository_root(self):
        marketplace = load("marketplace.json")
        plugin = load("plugin.json")
        self.assertEqual(marketplace["name"], "airgap-anything-marketplace")
        self.assertEqual(len(marketplace["plugins"]), 1)
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], plugin["name"])
        self.assertEqual(entry["version"], plugin["version"])
        self.assertEqual(entry["source"], "./")

    def test_the_skill_is_where_installers_look(self):
        self.assertTrue((SKILL_DIR / "SKILL.md").is_file())
        self.assertEqual(SKILL_DIR.parent, REPO_ROOT / "skills")

    def test_the_icon_is_a_square_png_the_listing_accepts(self):
        # claude plugin validate: a square PNG or JPEG of 512 to 2048 px a side, under 2 MB.
        icon = REPO_ROOT / load("plugin.json")["icon"]
        data = icon.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        self.assertEqual(width, height)
        self.assertTrue(512 <= width <= 2048, width)
        self.assertLess(len(data), 2 * 1024 * 1024)

    def test_license_is_mit(self):
        text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("MIT License"))


if __name__ == "__main__":
    unittest.main()
