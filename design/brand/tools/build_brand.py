#!/usr/bin/env python3
"""Build the airgap-anything brand assets: logo files and animated SVGs.

Usage:
    python3 design/brand/tools/build_brand.py --bold B612-Bold.ttf --regular B612-Regular.ttf --out assets/brand
    python3 design/brand/tools/build_brand.py --without-fonts --out assets/brand

Needs fontTools for the files that carry text. The B612 fonts (SIL Open Font License 1.1)
are not stored in the repository: text is converted to outlines, so the output files do
not need the fonts. --without-fonts rebuilds only the files that set no text in B612
(the animated symbol, the animated icon tile and the pipeline) and needs only Python.
"""
from __future__ import annotations

import argparse
from pathlib import Path

# ---------------------------------------------------------------- palette
INK = "#121417"
PAPER = "#FFFFFF"
SNOW = "#F2F3F5"        # mark and type on dark backgrounds
GAP_YELLOW = "#FFC800"
MUTE_ON_LIGHT = "#5F6368"
MUTE_ON_DARK = "#9AA1A9"
LINE_ON_LIGHT = "#C9CDD2"
LINE_ON_DARK = "#3A414A"
NIGHT = "#0D1117"       # reference dark background (GitHub dark)

# ---------------------------------------------------------------- symbol geometry (256 x 256)
# Letter A: flat apex, legs on a 1:2 slope, 40-unit horizontal leg width.
A_LEGS = "M108 30H148L240 214H200L128 70L56 214H16Z"
# Crossbar stubs stop 32 units short of each other (the air gap).
A_STUB_L = "M82 140H112V172H66Z"
A_STUB_R = "M144 140H174L190 172H144Z"
A_MASTER = A_LEGS + A_STUB_L + A_STUB_R
# Stubs that reach deeper into the legs, for animation (they slide by 17 units).
A_STUB_L_LONG = "M66 140H112V172H50Z"
A_STUB_R_LONG = "M144 140H190L206 172H144Z"
# Small-size cut (favicon, 16-24 px): 44-unit legs, 40-unit gap, 36-unit stubs.
A_SMALL = "M104 30H152L244 214H200L128 70L56 214H12ZM80 138H108V174H62ZM148 138H176L194 174H148Z"

TAGLINE = "Design any system for air-gapped environments."
NAME = "airgap-anything"
TRACKING = -14.0        # font units between letters of the wordmark (2000/em)


def _num(value: float) -> str:
    text = f"{value:.1f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


class Outliner:
    """Turn a string into SVG path data using a TrueType font."""

    def __init__(self, font_path: Path):
        from fontTools.ttLib import TTFont  # imported here, so that the font-free builders need only Python

        self.font = TTFont(str(font_path))
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm
        self.kern = {}
        if "kern" in self.font:
            for table in self.font["kern"].kernTables:
                self.kern.update(getattr(table, "kernTable", {}))

    def path(self, text: str, size: float, x: float, baseline: float, tracking: float = 0.0) -> tuple[str, float]:
        """Return (path data, advance width in px) for text set at the given size."""
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen

        scale = size / self.upm
        parts, pen_x, previous = [], 0.0, None
        for char in text:
            glyph = self.cmap[ord(char)]
            if previous is not None:
                pen_x += (self.kern.get((previous, glyph), 0) + tracking) * scale
            pen = SVGPathPen(self.glyphs, ntos=_num)
            self.glyphs[glyph].draw(TransformPen(pen, (scale, 0, 0, -scale, x + pen_x, baseline)))
            parts.append(pen.getCommands())
            pen_x += self.font["hmtx"][glyph][0] * scale
            previous = glyph
        return "".join(parts), pen_x


def svg(view_w: float, view_h: float, title: str, body: str, desc: str = "", style: str = "") -> str:
    desc_tag = f"\n  <desc id=\"desc\">{desc}</desc>" if desc else ""
    labelled = "title desc" if desc else "title"
    style_tag = f"\n  <style>{style}</style>" if style else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_num(view_w)} {_num(view_h)}" '
            f'width="{_num(view_w)}" height="{_num(view_h)}" role="img" aria-labelledby="{labelled}">\n'
            f'  <title id="title">{title}</title>{desc_tag}{style_tag}\n{body}\n</svg>\n')


# ---------------------------------------------------------------- static logo files
def build_logo(bold: Outliner, out: Path) -> None:
    logo = out / "logo"
    logo.mkdir(parents=True, exist_ok=True)

    for name, fill in (("ink", INK), ("white", PAPER)):
        (logo / f"symbol-{name}.svg").write_text(
            svg(256, 256, "airgap-anything symbol", f'  <path id="symbol" fill="{fill}" d="{A_MASTER}"/>'))
        (logo / f"symbol-small-{name}.svg").write_text(
            svg(256, 256, "airgap-anything symbol, small-size cut", f'  <path id="symbol" fill="{fill}" d="{A_SMALL}"/>'))

        # Wordmark only: x-height 74.8 at size 136; 16 units of padding.
        size = 136
        d, width = bold.path(NAME, size, 16, 128, TRACKING)
        (logo / f"wordmark-{name}.svg").write_text(
            svg(round(width) + 32, 176, "airgap-anything wordmark", f'  <path id="wordmark" fill="{fill}" d="{d}"/>'))

        # Horizontal lockup: symbol, a gap of 56, then the wordmark centred on the symbol.
        d, width = bold.path(NAME, size, 296, 170, TRACKING)
        (logo / f"lockup-horizontal-{name}.svg").write_text(
            svg(296 + round(width) + 24, 256, "airgap-anything logo",
                f'  <path id="symbol" fill="{fill}" d="{A_MASTER}"/>\n'
                f'  <path id="wordmark" fill="{fill}" d="{d}"/>'))

        # Stacked lockup: symbol above, wordmark centred below.
        size_s = 60
        _, width_s = bold.path(NAME, size_s, 0, 0, TRACKING)
        view_w = max(round(width_s) + 48, 304)
        d, _ = bold.path(NAME, size_s, (view_w - width_s) / 2, 300, TRACKING)
        (logo / f"lockup-stacked-{name}.svg").write_text(
            svg(view_w, 340, "airgap-anything logo, stacked",
                f'  <path id="symbol" fill="{fill}" transform="translate({_num((view_w - 256) / 2)} 0)" d="{A_MASTER}"/>\n'
                f'  <path id="wordmark" fill="{fill}" d="{d}"/>'))

    # App icon / avatar: ink A on a Gap Yellow tile, symbol at 64 % and nudged up for optical centring.
    scale, offset_x, offset_y = 0.64, 128 - 128 * 0.64, 128 - 122 * 0.64 - 4
    (logo / "icon-tile.svg").write_text(
        svg(256, 256, "airgap-anything icon",
            f'  <rect width="256" height="256" rx="56" fill="{GAP_YELLOW}"/>\n'
            f'  <path fill="{INK}" transform="translate({_num(offset_x)} {_num(offset_y)}) scale({scale})" d="{A_MASTER}"/>'))


# ---------------------------------------------------------------- animated assets
def _theme(dark: bool) -> dict[str, str]:
    return {
        "ink": SNOW if dark else INK,
        "mute": MUTE_ON_DARK if dark else MUTE_ON_LIGHT,
        "line": LINE_ON_DARK if dark else LINE_ON_LIGHT,
        "on_ink": NIGHT if dark else PAPER,
    }


def build_hero(bold: Outliner, regular: Outliner, out: Path) -> None:
    """Header banner, 1280 x 360, transparent background, for pages that set their own
    background colour (not the README, whose images bring their own). The crossbar opens
    into a gap, then one block passes through it in one direction."""
    for dark in (False, True):
        t = _theme(dark)
        d, _ = bold.path(NAME, 108, 366, 196, TRACKING)
        tag, _ = regular.path(TAGLINE, 30, 368, 268)
        style = """
    .sl, .sr, .blk { animation-duration: 9s; animation-iteration-count: infinite; animation-timing-function: cubic-bezier(.3, 0, .2, 1); }
    .sl { animation-name: bar-l; } .sr { animation-name: bar-r; }
    @keyframes bar-l { 0%, 8% { transform: translateX(17px); } 20%, 90% { transform: translateX(0); } 100% { transform: translateX(17px); } }
    @keyframes bar-r { 0%, 8% { transform: translateX(-17px); } 20%, 90% { transform: translateX(0); } 100% { transform: translateX(-17px); } }
    .blk { opacity: 0; animation-name: pass; animation-timing-function: cubic-bezier(.45, 0, .2, 1); }
    @keyframes pass { 0%, 22% { transform: translateY(238px); opacity: 0; } 27% { opacity: 1; } 58% { transform: translateY(98px); opacity: 1; } 66%, 100% { transform: translateY(92px); opacity: 0; } }
    @media (prefers-reduced-motion: reduce) { .sl, .sr, .blk { animation: none; } }
  """
        body = (
            f'  <g transform="translate(86 64)">\n'
            f'    <path fill="{t["ink"]}" d="{A_LEGS}"/>\n'
            f'    <path class="sl" fill="{t["ink"]}" d="{A_STUB_L_LONG}"/>\n'
            f'    <path class="sr" fill="{t["ink"]}" d="{A_STUB_R_LONG}"/>\n'
            f'    <rect class="blk" x="118" y="0" width="20" height="20" fill="{GAP_YELLOW}"/>\n'
            f'  </g>\n'
            f'  <path fill="{t["ink"]}" d="{d}"/>\n'
            f'  <path fill="{t["mute"]}" d="{tag}"/>')
        name = "hero-dark.svg" if dark else "hero-light.svg"
        (out / name).write_text(svg(
            1280, 360, "airgap-anything", body,
            desc=f"{TAGLINE} The crossbar of the letter A opens into a gap and a block passes through it in one direction.",
            style=style))


def build_symbol_animated(out: Path) -> None:
    """Standalone animated mark, 256 x 256. Follows the viewer's colour scheme.
    The gap opens, a block passes, then the A turns over into the for-all sign and back."""
    style = f"""
    svg {{ --ink: {INK}; }}
    @media (prefers-color-scheme: dark) {{ svg {{ --ink: {SNOW}; }} }}
    .ink {{ fill: var(--ink); }}
    .turn {{ transform-box: fill-box; transform-origin: center; animation: turn 10s cubic-bezier(.6, 0, .3, 1) infinite; }}
    @keyframes turn {{ 0%, 50% {{ transform: scaleY(1); }} 58%, 78% {{ transform: scaleY(-1); }} 86%, 100% {{ transform: scaleY(1); }} }}
    .sl, .sr {{ animation: bar-l 10s cubic-bezier(.3, 0, .2, 1) infinite; }}
    .sr {{ animation-name: bar-r; }}
    @keyframes bar-l {{ 0%, 4% {{ transform: translateX(17px); }} 12%, 92% {{ transform: translateX(0); }} 100% {{ transform: translateX(17px); }} }}
    @keyframes bar-r {{ 0%, 4% {{ transform: translateX(-17px); }} 12%, 92% {{ transform: translateX(0); }} 100% {{ transform: translateX(-17px); }} }}
    .blk {{ opacity: 0; animation: pass 10s cubic-bezier(.45, 0, .2, 1) infinite; }}
    @keyframes pass {{ 0%, 13% {{ transform: translateY(232px); opacity: 0; }} 17% {{ opacity: 1; }} 40% {{ transform: translateY(98px); opacity: 1; }} 46%, 100% {{ transform: translateY(92px); opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .turn, .sl, .sr, .blk {{ animation: none; }} }}
  """
    body = (
        f'  <g class="turn">\n'
        f'    <path class="ink" d="{A_LEGS}"/>\n'
        f'    <path class="ink sl" d="{A_STUB_L_LONG}"/>\n'
        f'    <path class="ink sr" d="{A_STUB_R_LONG}"/>\n'
        f'  </g>\n'
        f'  <rect class="blk" x="118" y="0" width="20" height="20" fill="{GAP_YELLOW}"/>')
    (out / "symbol-animated.svg").write_text(svg(
        256, 256, "airgap-anything symbol, animated", body,
        desc="The crossbar opens, a block passes through the gap, and the A turns over into the for-all sign.",
        style=style))


PIPELINE_STEPS = (
    ("1", "Interview", "the model asks", "model"),
    ("2", "Tier", "a script computes", "script"),
    ("3", "Sizing", "a script computes", "script"),
    ("4", "Decisions", "the model chooses", "model"),
    ("5", "Manifest", "a script lists", "script"),
    ("6", "Blueprint", "the model writes", "model"),
    ("7", "Lint", "a script verifies", "script"),
    ("8", "Hand-off", "after you approve", "model"),
)
FONT_STACK = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def build_pipeline(out: Path) -> None:
    """Pipeline diagram, 1280 x 540: eight steps outside, the air gap, the build inside."""
    loop = 16.0          # seconds
    step = 1.2           # seconds each step stays lit
    xs, ys, chip_w, chip_h = (48, 268, 488, 708), (112, 300), 196, 96

    def pct(seconds: float) -> str:
        return _num(seconds / loop * 100) + "%"

    for dark in (False, True):
        t = _theme(dark)

        def line(d: str) -> str:
            return f'<path d="{d}" stroke="{t["line"]}" stroke-width="2" fill="none"/>'

        def arrow(x1: float, y: float, x2: float) -> str:
            return line(f"M{x1} {y}H{x2 - 2}") + line(f"M{x2 - 9} {y - 5}L{x2} {y}L{x2 - 9} {y + 5}")

        rules = [f"""
    text {{ font-family: {FONT_STACK}; }}
    .name {{ font-size: 23px; font-weight: 650; }}
    .sub {{ font-size: 16px; }}
    .zone {{ font-size: 19px; font-weight: 600; fill: {t["mute"]}; }}
    .lit, .blk, .ok {{ opacity: 0; animation-duration: {_num(loop)}s; animation-iteration-count: infinite; animation-timing-function: linear; }}"""]
        chips = []
        for index, (number, name, sub, kind) in enumerate(PIPELINE_STEPS):
            x, y = xs[index % 4], ys[index // 4]
            filled = kind == "script"
            fg = t["on_ink"] if filled else t["ink"]
            sub_fg = (MUTE_ON_LIGHT if dark else LINE_ON_LIGHT) if filled else t["mute"]
            box = (f'<rect x="{x}" y="{y}" width="{chip_w}" height="{chip_h}" rx="10" fill="{t["ink"]}"/>' if filled else
                   f'<rect x="{x + 1}" y="{y + 1}" width="{chip_w - 2}" height="{chip_h - 2}" rx="9" fill="none" stroke="{t["ink"]}" stroke-width="2"/>')
            start = 0.4 + step * index
            rules.append(
                f"    .l{index} {{ animation-name: l{index}; }} "
                f"@keyframes l{index} {{ 0%, {pct(start)} {{ opacity: 0; }} {pct(start + 0.2)}, {pct(start + step)} {{ opacity: 1; }} "
                f"{pct(start + step + 0.2)}, 100% {{ opacity: 0; }} }}")
            chips.append(
                f'  <g>{box}'
                f'<text class="name" x="{x + 20}" y="{y + 43}" fill="{fg}">{number} {name}</text>'
                f'<text class="sub" x="{x + 20}" y="{y + 71}" fill="{sub_fg}">{sub}</text>'
                f'<rect class="lit l{index}" x="{x}" y="{y + chip_h + 10}" width="{chip_w}" height="6" rx="3" fill="{GAP_YELLOW}"/></g>')

        # Connectors between steps, and the wrap from step 4 down to step 5.
        links = [arrow(xs[i] + chip_w + 3, ys[row] + chip_h / 2, xs[i + 1] - 3) for row in (0, 1) for i in range(3)]
        wrap_x1, wrap_x2 = xs[3] + chip_w / 2, xs[0] + chip_w / 2
        links.append(line(f"M{wrap_x1} {ys[0] + chip_h + 24}V254H{wrap_x2}V{ys[1] - 5}")
                     + line(f"M{wrap_x2 - 5} {ys[1] - 12}L{wrap_x2} {ys[1] - 3}L{wrap_x2 + 5} {ys[1] - 12}"))

        # The air gap: two walls with nothing between them.
        gap_l, gap_r, gap_mid, row_y = 944, 992, 968, ys[1] + chip_h / 2
        px, pw = 1024, 208
        links.append(line(f"M{xs[3] + chip_w + 3} {row_y}H{gap_l - 8}"))
        links.append(arrow(gap_r + 8, row_y, px - 3))
        walls = (f'<rect x="{gap_l - 4}" y="96" width="4" height="316" fill="{t["ink"]}"/>'
                 f'<rect x="{gap_r}" y="96" width="4" height="316" fill="{t["ink"]}"/>'
                 f'<text class="zone" x="{gap_mid}" y="62" text-anchor="middle">air gap</text>'
                 f'<rect x="{gap_mid - 34}" y="72" width="68" height="5" rx="2.5" fill="{GAP_YELLOW}"/>')

        # Inside: one panel.
        panel = (f'<rect x="{px + 1}" y="{ys[0] + 1}" width="{pw - 2}" height="{ys[1] + chip_h - ys[0] - 2}" rx="9" fill="none" stroke="{t["ink"]}" stroke-width="2"/>'
                 f'<path fill="{t["ink"]}" transform="translate({px + 20} {ys[0] + 22}) scale(0.3)" d="{A_MASTER}"/>'
                 f'<text class="name" x="{px + 20}" y="{ys[0] + 136}" fill="{t["ink"]}">Build</text>'
                 f'<text class="sub" x="{px + 20}" y="{ys[0] + 166}" fill="{t["mute"]}">no internet,</text>'
                 f'<text class="sub" x="{px + 20}" y="{ys[0] + 188}" fill="{t["mute"]}">by the blueprint</text>'
                 f'<rect class="lit lin" x="{px}" y="{ys[1] + chip_h + 10}" width="{pw}" height="6" rx="3" fill="{GAP_YELLOW}"/>')

        # The transfer: a block leaves step 8 and waits in the gap while it is checked; a block continues inside.
        t0 = 0.4 + step * 8                      # 10.0 s
        out_x, in_x = xs[3] + chip_w + 8, px + 14
        rules.append(
            f"    .b1 {{ animation-name: b1; }} @keyframes b1 {{ 0%, {pct(t0)} {{ transform: translateX(0); opacity: 0; }} {pct(t0 + 0.2)} {{ opacity: 1; }} "
            f"{pct(t0 + 1.0)}, {pct(t0 + 2.2)} {{ transform: translateX({gap_mid - 9 - out_x}px); opacity: 1; }} {pct(t0 + 2.5)}, 100% {{ transform: translateX({gap_mid - 9 - out_x}px); opacity: 0; }} }}")
        rules.append(
            f"    .ok {{ animation-name: ok; }} @keyframes ok {{ 0%, {pct(t0 + 1.2)} {{ opacity: 0; }} {pct(t0 + 1.5)}, {pct(t0 + 2.3)} {{ opacity: 1; }} {pct(t0 + 2.6)}, 100% {{ opacity: 0; }} }}")
        rules.append(
            f"    .b2 {{ animation-name: b2; }} @keyframes b2 {{ 0%, {pct(t0 + 2.4)} {{ transform: translateX(0); opacity: 0; }} {pct(t0 + 2.7)} {{ opacity: 1; }} "
            f"{pct(t0 + 3.5)} {{ transform: translateX({in_x - (gap_r + 12)}px); opacity: 1; }} {pct(t0 + 3.9)}, 100% {{ transform: translateX({in_x - (gap_r + 12)}px); opacity: 0; }} }}")
        rules.append(
            f"    .lin {{ animation-name: lin; }} @keyframes lin {{ 0%, {pct(t0 + 3.5)} {{ opacity: 0; }} {pct(t0 + 3.8)}, {pct(loop - 0.6)} {{ opacity: 1; }} {pct(loop - 0.3)}, 100% {{ opacity: 0; }} }}")
        rules.append("    @media (prefers-reduced-motion: reduce) { .lit, .blk, .ok { animation: none; } }\n  ")
        transfer = (f'<rect class="blk b1" x="{out_x}" y="{row_y - 9}" width="18" height="18" fill="{GAP_YELLOW}"/>'
                    f'<path class="ok" d="M{gap_mid - 9} {row_y - 34}l6 6l12 -13" stroke="{t["ink"]}" stroke-width="3" fill="none"/>'
                    f'<rect class="blk b2" x="{gap_r + 12}" y="{row_y - 9}" width="18" height="18" fill="{GAP_YELLOW}"/>')

        zones = (f'<text class="zone" x="{xs[0]}" y="62">Outside: a connected workstation</text>'
                 f'<text class="zone" x="{px}" y="62">Inside</text>')
        legend_y = 470
        legend = (f'<rect x="{xs[0] + 1}" y="{legend_y + 1}" width="26" height="18" rx="4" fill="none" stroke="{t["ink"]}" stroke-width="2"/>'
                  f'<text class="sub" x="{xs[0] + 38}" y="{legend_y + 15}" fill="{t["mute"]}">the model decides</text>'
                  f'<rect x="{xs[0] + 210}" y="{legend_y}" width="28" height="20" rx="4" fill="{t["ink"]}"/>'
                  f'<text class="sub" x="{xs[0] + 248}" y="{legend_y + 15}" fill="{t["mute"]}">a script computes or verifies</text>'
                  f'<rect x="{xs[0] + 498}" y="{legend_y + 1}" width="18" height="18" fill="{GAP_YELLOW}"/>'
                  f'<text class="sub" x="{xs[0] + 526}" y="{legend_y + 15}" fill="{t["mute"]}">what is carried across</text>')
        body = "\n".join(["  " + zones, *chips, "  " + "".join(links), "  " + walls, "  " + panel, "  " + transfer, "  " + legend])
        name = "pipeline-dark.svg" if dark else "pipeline-light.svg"
        (out / name).write_text(svg(
            1280, 540, "How airgap-architect works", body,
            desc="Eight steps run on a connected workstation: interview, tier, sizing, decisions, manifest, blueprint, lint, hand-off. "
                 "The result is checked and carried across the air gap, and the system is built inside without internet.",
            style="\n".join(rules)))


def build_social(bold: Outliner, regular: Outliner, out: Path) -> None:
    """Social preview source, 1280 x 640: ink lockup on Gap Yellow."""
    size = 112
    _, width = bold.path(NAME, size, 0, 0, TRACKING)
    x0 = (1280 - (256 * 0.9 + 44 + width)) / 2
    d, _ = bold.path(NAME, size, x0 + 256 * 0.9 + 44, 318, TRACKING)
    _, tag_w = regular.path(TAGLINE, 34, 0, 0)
    tag, _ = regular.path(TAGLINE, 34, (1280 - tag_w) / 2, 452)
    body = (f'  <rect width="1280" height="640" fill="{GAP_YELLOW}"/>\n'
            f'  <path fill="{INK}" transform="translate({_num(x0)} 172) scale(0.9)" d="{A_MASTER}"/>\n'
            f'  <path fill="{INK}" d="{d}"/>\n'
            f'  <path fill="{INK}" d="{tag}"/>')
    (out / "social-preview.svg").write_text(svg(1280, 640, "airgap-anything", body, desc=TAGLINE))


ICON_TILE_TRANSFORM = "translate(46.1 45.9) scale(0.64)"  # the A inside logo/icon-tile.svg


def render_icon_tile_animated() -> str:
    """The icon tile with the symbol's story: the gap opens, a block passes, the A turns over.
    The tile is opaque Gap Yellow, so it reads on any page; the README shows it above the name."""
    style = f"""
    .turn {{ transform-box: fill-box; transform-origin: center; animation: turn 10s cubic-bezier(.6, 0, .3, 1) infinite; }}
    @keyframes turn {{ 0%, 50% {{ transform: scaleY(1); }} 58%, 78% {{ transform: scaleY(-1); }} 86%, 100% {{ transform: scaleY(1); }} }}
    .sl, .sr {{ animation: bar-l 10s cubic-bezier(.3, 0, .2, 1) infinite; }}
    .sr {{ animation-name: bar-r; }}
    @keyframes bar-l {{ 0%, 4% {{ transform: translateX(17px); }} 12%, 92% {{ transform: translateX(0); }} 100% {{ transform: translateX(17px); }} }}
    @keyframes bar-r {{ 0%, 4% {{ transform: translateX(-17px); }} 12%, 92% {{ transform: translateX(0); }} 100% {{ transform: translateX(-17px); }} }}
    .blk {{ opacity: 0; animation: pass 10s cubic-bezier(.45, 0, .2, 1) infinite; }}
    @keyframes pass {{ 0%, 13% {{ transform: translateY(232px); opacity: 0; }} 17% {{ opacity: 1; }} 40% {{ transform: translateY(98px); opacity: 1; }} 46%, 100% {{ transform: translateY(92px); opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .turn, .sl, .sr, .blk {{ animation: none; }} }}
  """
    body = (
        f'  <rect width="256" height="256" rx="56" fill="{GAP_YELLOW}"/>\n'
        f'  <g transform="{ICON_TILE_TRANSFORM}" fill="{INK}">\n'
        f'    <g class="turn">\n'
        f'      <path d="{A_LEGS}"/>\n'
        f'      <path class="sl" d="{A_STUB_L_LONG}"/>\n'
        f'      <path class="sr" d="{A_STUB_R_LONG}"/>\n'
        f'    </g>\n'
        f'    <rect class="blk" x="118" y="0" width="20" height="20"/>\n'
        f'  </g>')
    return svg(256, 256, "airgap-anything icon, animated", body,
               desc="On a yellow tile, the crossbar of the A opens, a block passes through the gap, "
                    "and the A turns over into the for-all sign.",
               style=style)


def build_icon_tile_animated(out: Path) -> None:
    (out / "icon-tile-animated.svg").write_text(render_icon_tile_animated())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--bold", type=Path, help="B612-Bold.ttf")
    parser.add_argument("--regular", type=Path, help="B612-Regular.ttf")
    parser.add_argument("--without-fonts", action="store_true",
                        help="rebuild only the files that set no text in B612; needs no fontTools")
    parser.add_argument("--out", required=True, type=Path, help="output folder, e.g. assets/brand")
    args = parser.parse_args()
    if not args.without_fonts and not (args.bold and args.regular):
        parser.error("--bold and --regular are required unless --without-fonts is given")

    args.out.mkdir(parents=True, exist_ok=True)
    build_symbol_animated(args.out)
    build_icon_tile_animated(args.out)
    build_pipeline(args.out)
    if not args.without_fonts:
        bold, regular = Outliner(args.bold), Outliner(args.regular)
        build_logo(bold, args.out)
        build_hero(bold, regular, args.out)
        build_social(bold, regular, args.out)
    print(f"wrote brand assets to {args.out}")


if __name__ == "__main__":
    main()
