import importlib.util
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tests import PLUGIN_DIR, REPO_ROOT


def _length(value, whole):
    value = value.strip()
    if value.endswith("%"):
        return float(value[:-1]) / 100 * whole
    return float(value.removesuffix("px"))


def paints_own_background(path):
    """True when the image covers its whole canvas itself, so that it reads the same on any page colour."""
    data = path.read_bytes()
    if path.suffix == ".png":
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            return False
        pos, colour_type = 8, None
        while pos + 8 <= len(data):
            length = int.from_bytes(data[pos:pos + 4], "big")
            kind = data[pos + 4:pos + 8]
            if kind == b"IHDR":
                colour_type = data[pos + 17]
            elif kind == b"tRNS":
                return False
            pos += 12 + length
        return colour_type in (0, 2)  # greyscale or RGB: no alpha channel
    if path.suffix == ".svg":
        root = ET.fromstring(data)
        _, _, width, height = (float(v) for v in root.get("viewBox").split())
        for child in root:
            tag = child.tag.rsplit("}", 1)[-1]
            if tag in ("title", "desc", "style", "defs", "metadata"):
                continue
            # The first thing drawn must be an opaque rectangle over the whole canvas.
            return (
                tag == "rect"
                and _length(child.get("x", "0"), width) <= 0.02 * width
                and _length(child.get("y", "0"), height) <= 0.02 * height
                and _length(child.get("width", "0"), width) >= 0.98 * width
                and _length(child.get("height", "0"), height) >= 0.98 * height
                and child.get("fill", "black") not in ("none", "transparent")
                and float(child.get("fill-opacity", "1")) == 1
                and float(child.get("opacity", "1")) == 1
            )
    return False


# GitHub's page colours in the light and the dark theme.
PAGE_COLOURS = ("#ffffff", "#0d1117")
NAMED_COLOURS = {"white": "#ffffff", "black": "#000000"}
DRAWN = ("rect", "line", "path", "polyline", "polygon", "circle", "ellipse")


def _hex(value):
    value = NAMED_COLOURS.get((value or "").strip().lower(), (value or "").strip().lower())
    if re.fullmatch(r"#[0-9a-f]{3}", value):
        value = "#" + "".join(c * 2 for c in value[1:])
    return value if re.fullmatch(r"#[0-9a-f]{6}", value) else None


def _luminance(colour):
    channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def fits_both_page_colours(path):
    """True for a transparent SVG that reads on GitHub's light and dark page alike.

    Every text sits on an opaque rectangle drawn before it and clears 4.5:1 against it.
    Every stroke, and every fill that is not such a rectangle, clears 3:1 against both page
    colours. Styles, classes, transforms, translucency and embedded images are refused,
    because they would hide from this check what is drawn.
    """
    if path.suffix != ".svg":
        return False
    surfaces = []

    def visible_on_both_pages(colour):
        return colour is not None and all(contrast(colour, page) >= 3 for page in PAGE_COLOURS)

    def walk(element, inherited, in_marker):
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in ("title", "desc", "metadata"):
            return True
        if tag in ("style", "image", "foreignObject", "use", "tspan") or {"style", "class", "transform"} & set(element.attrib):
            return False
        if any(float(element.get(a, "1")) != 1 for a in ("opacity", "fill-opacity", "stroke-opacity")):
            return False
        paint = {**inherited, **{a: element.get(a) for a in ("fill", "stroke") if element.get(a) is not None}}
        if tag == "defs":
            return all(child.tag.rsplit("}", 1)[-1] == "marker" and walk(child, paint, True) for child in element)
        if tag == "text":
            x, y = float(element.get("x", "0")), float(element.get("y", "0"))
            y -= float(element.get("font-size", "16")) * 0.35  # middle of a lower-case letter
            under = [fill for (sx, sy, sw, sh, fill) in surfaces if sx <= x <= sx + sw and sy <= y <= sy + sh]
            colour = _hex(paint.get("fill", "black"))
            return bool(under) and colour is not None and contrast(colour, under[-1]) >= 4.5 and len(element) == 0
        if tag in DRAWN:
            stroke = paint.get("stroke", "none")
            fill = "none" if tag == "line" else paint.get("fill", "black")  # a line has no inside to fill
            if stroke != "none" and not visible_on_both_pages(_hex(stroke)):
                return False
            if fill != "none":
                if tag == "rect" and not in_marker:
                    if _hex(fill) is None:
                        return False
                    surfaces.append((float(element.get("x", "0")), float(element.get("y", "0")),
                                     float(element.get("width", "0")), float(element.get("height", "0")), _hex(fill)))
                elif not visible_on_both_pages(_hex(fill)):
                    return False
            return True
        if tag in ("svg", "g", "marker"):
            return all(walk(child, paint, in_marker) for child in element)
        return False

    return walk(ET.fromstring(path.read_bytes()), {}, False)


def _load_builder(name):
    path = REPO_ROOT / "design" / "brand" / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReadmeTest(unittest.TestCase):
    def setUp(self):
        self.text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        manifest = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
        self.owner = json.loads(manifest.read_text(encoding="utf-8"))["author"]["name"]

    def test_it_documents_the_three_install_paths(self):
        self.assertIn(f"/plugin install airgap-anything --marketplace {self.owner}/airgap-anything", self.text)
        self.assertIn(f"/plugin marketplace add {self.owner}/airgap-anything", self.text)
        self.assertIn("/plugin install airgap-anything@airgap-anything-marketplace", self.text)
        self.assertIn(f"npx skills add {self.owner}/airgap-anything", self.text)
        self.assertIn(f"codex plugin marketplace add {self.owner}/airgap-anything", self.text)
        self.assertIn("git archive", self.text)
        self.assertNotIn("Python 3.11", self.text, "the skills need no Python since 0.3")

    def test_the_skills_table_lists_the_agent_skill(self):
        self.assertIn("[`airgap-agent`](plugins/airgap-anything/skills/airgap-agent/SKILL.md)", self.text)

    def test_no_owner_token_is_left(self):
        self.assertNotIn("GITHUB_OWNER", self.text)

    def test_every_local_link_and_image_exists(self):
        targets = re.findall(r"\]\(([^)\s]+)\)", self.text)
        targets += re.findall(r'(?:src|srcset)="([^"]+)"', self.text)
        local = [t for t in targets if not t.startswith(("http://", "https://", "#"))]
        self.assertIn("CONTRIBUTING.md", local)
        for target in local:
            self.assertTrue((REPO_ROOT / target).exists(), target)

    def test_it_has_the_house_style_parts(self):
        self.assertIn('<img src="assets/brand/icon-tile-animated.svg"', self.text)
        self.assertIn('<h1 align="center">airgap-anything</h1>', self.text)
        self.assertIn("assets/brand/how-it-works.svg", self.text)
        self.assertIn(f"{self.owner}/airgap-anything/actions/workflows/ci.yml/badge.svg", self.text)
        self.assertIn("\n## Türkçe\n", self.text)
        self.assertIn("[Without internet](#without-internet)", self.text)

    def test_no_image_depends_on_the_viewers_colour_scheme(self):
        # The browser picks a <picture> source by the computer's colour scheme, while GitHub
        # draws the page in the GitHub theme, so a switched image can land on the wrong
        # background. Every image in the README therefore either brings its own background or
        # is transparent and reads on both GitHub page colours.
        for marker in ("<picture", "prefers-color-scheme", "#gh-dark-mode-only", "#gh-light-mode-only"):
            self.assertFalse(marker in self.text, marker)
        images = re.findall(r'<img[^>]*\ssrc="([^"]+)"', self.text)
        images += re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", self.text)
        local = [i for i in images if not i.startswith(("http://", "https://"))]
        self.assertIn("assets/brand/how-it-works.svg", local)
        for image in local:
            with self.subTest(image=image):
                path = REPO_ROOT / image
                self.assertTrue(paints_own_background(path) or fits_both_page_colours(path), image)

    def test_the_background_check_rejects_a_transparent_image(self):
        self.assertFalse(paints_own_background(REPO_ROOT / "assets/brand/hero-light.svg"))
        self.assertFalse(paints_own_background(REPO_ROOT / "assets/brand/pipeline-dark.svg"))
        self.assertTrue(paints_own_background(REPO_ROOT / "assets/brand/fallback/pipeline-dark.png"))

    def test_the_two_page_check_reads_what_is_drawn(self):
        self.assertTrue(fits_both_page_colours(REPO_ROOT / "assets/brand/how-it-works.svg"))
        self.assertFalse(fits_both_page_colours(REPO_ROOT / "assets/brand/hero-light.svg"))
        self.assertFalse(fits_both_page_colours(REPO_ROOT / "assets/brand/fallback/pipeline-dark.png"))
        head = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">'
        card = '<rect x="10" y="10" width="120" height="40" fill="#ffffff" stroke="#8c959f"/>'
        cases = {
            "text on its own card": (card + '<text x="20" y="34" font-size="12" fill="#121417">Lint</text>', True),
            "ink text on the bare canvas": ('<text x="20" y="34" font-size="12" fill="#121417">Lint</text>', False),
            "text that the card cannot carry": (card + '<text x="20" y="34" font-size="12" fill="#d0d7de">Lint</text>', False),
            "an ink line, lost on the dark page": ('<line x1="0" y1="80" x2="200" y2="80" stroke="#121417"/>', False),
            "a light border, lost on the light page": ('<rect x="10" y="10" width="120" height="40" fill="#ffffff" stroke="#eef1f4"/>', False),
            "a grey line": ('<line x1="0" y1="80" x2="200" y2="80" stroke="#7d8590"/>', True),
            "a translucent card": (card.replace("/>", ' opacity="0.5"/>'), False),
            "a transformed group": ('<g transform="translate(4 4)">' + card + "</g>", False),
        }
        with tempfile.TemporaryDirectory() as folder:
            for name, (body, expected) in cases.items():
                with self.subTest(name):
                    path = Path(folder) / "case.svg"
                    path.write_text(head + body + "</svg>", encoding="utf-8")
                    self.assertEqual(fits_both_page_colours(path), expected)

    def test_the_animated_icon_is_its_builders_output(self):
        builder = _load_builder("build_brand")  # importable without fontTools
        on_disk = (REPO_ROOT / "assets/brand/icon-tile-animated.svg").read_text(encoding="utf-8")
        self.assertEqual(on_disk, builder.render_icon_tile_animated(),
                         "rebuild: python3 design/brand/tools/build_brand.py --without-fonts --out assets/brand")

    def test_the_diagram_is_its_builders_output(self):
        builder = _load_builder("build_how_it_works")
        on_disk = (REPO_ROOT / "assets/brand/how-it-works.svg").read_text(encoding="utf-8")
        self.assertEqual(on_disk, builder.render(), "rebuild: python3 design/brand/tools/build_how_it_works.py")

    def test_every_anchor_matches_a_heading(self):
        targets = re.findall(r"\]\(#([^)\s]+)\)", self.text)
        targets += re.findall(r'href="#([^"]+)"', self.text)
        self.assertIn("türkçe", targets)
        self.assertIn("without-internet", targets)
        slugs = set()
        in_fence = False
        for line in self.text.splitlines():
            if line.startswith("```"):
                in_fence = not in_fence
            elif not in_fence and re.match(r"#{1,6} ", line):
                title = line.lstrip("#").strip().lower()
                slugs.add(re.sub(r"[^\w\- ]", "", title).replace(" ", "-"))
        for target in targets:
            self.assertIn(target, slugs, target)

    def test_every_local_href_exists(self):
        for target in re.findall(r'href="([^"]+)"', self.text):
            if target.startswith(("http://", "https://", "#")):
                continue
            self.assertTrue((REPO_ROOT / target).exists(), target)


if __name__ == "__main__":
    unittest.main()
