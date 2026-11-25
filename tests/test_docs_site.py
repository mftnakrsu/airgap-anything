"""The documentation site in docs-site/ stays true to its sources.

Reference pages, the example, the contributing page and the shared images are written by
docs-site/scripts/generate_reference.py; these tests fail when one of them was not
regenerated after its source changed, or was edited by hand.
"""

import importlib.util
import re
import unittest

from tests import REPO_ROOT

SITE = REPO_ROOT / "docs-site"
DOCS = SITE / "src" / "content" / "docs"


def _generator():
    path = SITE / "scripts" / "generate_reference.py"
    spec = importlib.util.spec_from_file_location("generate_reference", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _slug(path):
    slug = path.relative_to(DOCS).with_suffix("").as_posix()
    return "" if slug == "index" else slug.removesuffix("/index")


class CodeStaysVerbatimTest(unittest.TestCase):
    def test_redirects_inside_nested_fences_are_not_escaped(self):
        generator = _generator()
        source = "Prose with <b>.\n\n````markdown\n# Title\n\n```sh\necho x >> .env\n```\n\nText a > b inside the template.\n````\n\nAfter: a > b and `c > d`.\n"
        text = generator._text_outside_code(source)
        self.assertIn("echo x >> .env", text)
        self.assertIn("Text a > b inside the template.", text)
        self.assertIn("Prose with &lt;b&gt;.", text)
        self.assertIn("After: a &gt; b and `c > d`.", text)

    def test_the_generated_install_runbook_keeps_its_redirects(self):
        page = DOCS / "reference" / "install" / "runbook.md"
        text = page.read_text(encoding="utf-8")
        self.assertIn(">> .env", text)
        self.assertNotIn("&gt;&gt;", text)


class GeneratedFilesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = _generator()
        cls.pages = cls.generator.pages()

    def test_every_generated_page_is_current(self):
        for path, text in self.pages.items():
            with self.subTest(page=str(path.relative_to(SITE))):
                self.assertTrue(path.is_file(), "run: python3 docs-site/scripts/generate_reference.py")
                self.assertEqual(path.read_text(encoding="utf-8"), text,
                                 "run: python3 docs-site/scripts/generate_reference.py")

    def test_no_stale_reference_page_is_left(self):
        for path in (DOCS / "reference").rglob("*.md"):
            with self.subTest(page=str(path.relative_to(SITE))):
                self.assertIn(path, self.pages)

    def test_shared_images_match_their_sources(self):
        for target, source in self.generator.SHARED.items():
            with self.subTest(image=str(target.relative_to(SITE))):
                self.assertEqual(target.read_bytes(), source.read_bytes(),
                                 "run: python3 docs-site/scripts/generate_reference.py")


class SiteStructureTest(unittest.TestCase):
    def setUp(self):
        self.files = [p for p in DOCS.rglob("*") if p.suffix in (".md", ".mdx")]
        self.slugs = {_slug(p) for p in self.files}

    def test_every_sidebar_entry_has_a_page(self):
        config = (SITE / "astro.config.mjs").read_text(encoding="utf-8")
        sidebar = config.split("sidebar:", 1)[1]
        for slug in re.findall(r"'([a-z0-9-]+/[a-z0-9-]+)'", sidebar):
            with self.subTest(slug=slug):
                self.assertIn(slug, self.slugs)
        for directory in re.findall(r"directory: '([^']+)'", sidebar):
            self.assertTrue((DOCS / directory).is_dir(), directory)

    def test_every_internal_link_resolves(self):
        public = {p.relative_to(SITE / "public").as_posix() for p in (SITE / "public").rglob("*") if p.is_file()}
        for path in self.files:
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\]\((/[^)\s]*)\)", text) + re.findall(r'(?:src|link)[=:] ?"?(/[^"\s]+)', text):
                with self.subTest(page=_slug(path), link=target):
                    clean = target.split("#", 1)[0].strip("/")
                    self.assertTrue(clean in self.slugs or clean in public, target)

    def test_the_build_output_and_dependencies_stay_out_of_git(self):
        ignored = (SITE / ".gitignore").read_text(encoding="utf-8").split()
        for entry in ("node_modules/", "dist/", ".astro/"):
            self.assertIn(entry, ignored)


if __name__ == "__main__":
    unittest.main()
