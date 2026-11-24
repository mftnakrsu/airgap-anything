import json
import re
import subprocess
import unittest

from tests import PLUGIN_DIR, REPO_ROOT, SKILL_DIRS


def marketplace():
    return json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))


def plugin():
    return json.loads((PLUGIN_DIR / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))


class ManifestTest(unittest.TestCase):
    def test_plugin_manifest(self):
        manifest = plugin()
        self.assertEqual(manifest["name"], "airgap-anything")
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(manifest["license"], "MIT")
        self.assertTrue(manifest["description"].strip())
        self.assertTrue(manifest["author"]["name"].strip())
        self.assertNotIn("email", manifest["author"])

    def test_marketplace_lists_the_plugin_folder(self):
        listing = marketplace()
        self.assertEqual(listing["name"], "airgap-anything-marketplace")
        self.assertEqual(len(listing["plugins"]), 1)
        entry = listing["plugins"][0]
        self.assertEqual(entry["name"], plugin()["name"])
        self.assertEqual(entry["version"], plugin()["version"])
        self.assertEqual(REPO_ROOT / entry["source"], PLUGIN_DIR)

    def test_the_only_plugin_manifest_is_in_the_plugin_folder(self):
        manifests = sorted(p.relative_to(REPO_ROOT).as_posix() for p in REPO_ROOT.glob("**/.claude-plugin/plugin.json")
                           if "node_modules" not in p.parts)
        self.assertEqual(manifests, ["plugins/airgap-anything/.claude-plugin/plugin.json"])

    def test_the_skills_are_where_installers_look(self):
        for skill_dir in SKILL_DIRS:
            with self.subTest(skill=skill_dir.name):
                self.assertTrue((skill_dir / "SKILL.md").is_file())
                self.assertEqual(skill_dir.parent, PLUGIN_DIR / "skills")
        found = sorted(p.name for p in (PLUGIN_DIR / "skills").iterdir() if p.is_dir())
        self.assertEqual(found, sorted(skill_dir.name for skill_dir in SKILL_DIRS))

    def test_the_icon_is_a_square_png_the_listing_accepts(self):
        # claude plugin validate: a square PNG or JPEG of 512 to 2048 px a side, under 2 MB.
        icon = PLUGIN_DIR / plugin()["icon"]
        data = icon.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        self.assertEqual(width, height)
        self.assertTrue(512 <= width <= 2048, width)
        self.assertLess(len(data), 2 * 1024 * 1024)

    def test_the_icon_is_the_brand_icon(self):
        # The plugin folder holds a copy, because an install gets nothing outside it.
        icon = PLUGIN_DIR / plugin()["icon"]
        self.assertEqual(icon.read_bytes(), (REPO_ROOT / "assets" / "brand" / "icons" / "icon-512.png").read_bytes())

    def test_every_agent_manifest_names_the_same_plugin_and_version(self):
        # Codex reads .agents/plugins/marketplace.json and the portable plugin.json
        # (https://developers.openai.com/plugins/build/plugins); Cursor reads
        # .cursor-plugin/marketplace.json and the same plugin.json (https://cursor.com/docs/plugins/building).
        portable = json.loads((PLUGIN_DIR / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(portable["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual((portable["name"], portable["version"]), (plugin()["name"], plugin()["version"]))
        codex = json.loads((REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        cursor = json.loads((REPO_ROOT / ".cursor-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual([e["name"] for e in codex["plugins"]], [plugin()["name"]])
        entry = codex["plugins"][0]
        self.assertEqual(entry["source"], {"source": "local", "path": "./plugins/airgap-anything"})
        self.assertTrue({"installation", "authentication"} <= set(entry["policy"]) and entry["category"])
        self.assertEqual(cursor["owner"]["name"], marketplace()["owner"]["name"])
        self.assertEqual([(e["name"], e["source"]) for e in cursor["plugins"]], [(plugin()["name"], "./plugins/airgap-anything")])

    def test_license_is_mit(self):
        text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("MIT License"))


# The rules below are the ones Anthropic's directory applies to a plugin folder submitted by an
# organization that is not Verified (developer portal validation, 2026-11-22, and
# https://claude.com/docs/plugins/pre-submission-checklist): only Markdown, text, JSON, YAML and
# images; no scripts with #!; no SVG other than the icon; no package-manager files; no commands
# that download and run code, even in documentation. Since 0.3 the skills ship markdown only, so
# the plugin meets them without Verified status. See docs/packaging-facts.md, Q8.
ALLOWED_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
PACKAGE_FILES = {"package.json", "package-lock.json", "npm-shrinkwrap.json", "pnpm-workspace.yaml", "requirements.txt",
                 "pyproject.toml", "uv.lock", "bun.lock", "bun.lockb", ".npmrc", "bunfig.toml", "uv.toml"}
DOWNLOAD_AND_RUN = re.compile(r"(curl|wget)[^\n|]*\|\s*(ba|z)?sh\b|\b(npx|bunx|uvx|pnpm dlx|yarn dlx|pipx run)\s", re.I)


def plugin_files():
    # The directory reads what is committed, so files that git ignores (run results, caches) do not count.
    listed = subprocess.run(["git", "ls-files", "-z", "--", "."], cwd=PLUGIN_DIR, capture_output=True)
    if listed.returncode == 0:
        return sorted(PLUGIN_DIR / name for name in listed.stdout.decode().split("\0") if name)
    return sorted(p for p in PLUGIN_DIR.rglob("*") if p.is_file() and "__pycache__" not in p.parts)


class DirectoryRulesTest(unittest.TestCase):
    def test_every_file_has_a_type_the_directory_accepts(self):
        for path in plugin_files():
            with self.subTest(path=path.relative_to(PLUGIN_DIR).as_posix()):
                self.assertIn(path.suffix.lower(), ALLOWED_SUFFIXES)
                self.assertNotIn(path.name, PACKAGE_FILES)
                self.assertFalse(path.name.startswith("."), "no dotfiles such as .DS_Store")

    def test_no_file_starts_with_a_shebang(self):
        for path in plugin_files():
            if path.suffix not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                with self.subTest(path=path.relative_to(PLUGIN_DIR).as_posix()):
                    self.assertFalse(path.read_bytes().startswith(b"#!"))

    def test_files_stay_under_the_size_and_count_limits(self):
        files = plugin_files()
        self.assertLessEqual(len(files), 512)
        for path in files:
            limit = 5 * 1024 * 1024 if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"} else 256 * 1024
            self.assertLess(path.stat().st_size, limit, path)

    def test_no_text_downloads_and_runs_code(self):
        for path in plugin_files():
            if path.suffix in {".md", ".txt", ".json", ".yaml", ".yml"}:
                with self.subTest(path=path.relative_to(PLUGIN_DIR).as_posix()):
                    self.assertIsNone(DOWNLOAD_AND_RUN.search(path.read_text(encoding="utf-8")))

    def test_the_only_manifest_folder_is_the_plugins_own(self):
        folders = [p for p in PLUGIN_DIR.rglob(".claude-plugin") if p.is_dir()]
        self.assertEqual(folders, [PLUGIN_DIR / ".claude-plugin"])
        self.assertEqual(sorted(p.name for p in folders[0].iterdir()), ["icon.png", "plugin.json"])


if __name__ == "__main__":
    unittest.main()
