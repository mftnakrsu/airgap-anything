#!/usr/bin/env python3
"""Build the README terminal demo: assets/demo/terminal-light.svg and terminal-dark.svg.

The demo is not drawn by hand. This script copies design/demo/department-blueprint.json
into a temporary project, runs the four scripts of the skill on it the way an agent
following SKILL.md does (tier.py, size.py, manifest.py, lint.py), and turns their real
output into an animated terminal. Run it from the repository root:

    python3 design/demo/build_demo.py

Python standard library only. The output has no timestamps and no random ids, so running
it twice gives the same bytes. The script stops with an error when a command exits with
anything but 0, when an output names a path on this machine, or when lint reports
anything (for example a stale catalog entry): a demo must not be rebuilt over a finding.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "plugins" / "airgap-anything" / "skills" / "airgap-architect"
SCRIPTS_DIR = SKILL_DIR / "scripts"
INPUT = REPO_ROOT / "design" / "demo" / "department-blueprint.json"
OUT_DIR = REPO_ROOT / "assets" / "demo"

sys.dont_write_bytecode = True  # a build writes only the two SVGs
sys.path.insert(0, str(SCRIPTS_DIR))
from airgap_lib.catalog import default_catalog_dir, load_catalog  # noqa: E402
from airgap_lib.constants import (  # noqa: E402
    AGENT_BLOCK_END,
    AGENT_BLOCK_START,
    SECTION_MARKERS,
    section_marker,
)

BLUEPRINT_ARG = "docs/airgap/blueprint.json"
SKILL_VARIABLE = "skill=~/.claude/skills/airgap-architect"
FORBIDDEN_IN_OUTPUT = ("/Users/", "/home/", "/private/", "/tmp/", "/var/folders/")

# Colors are the tokens of assets/brand/BRAND.md (section 5) and the neutral lines of the
# brand's pipeline diagrams. Ink #121417, Snow #F2F3F5, Gap Yellow #FFC800,
# Mute #5F6368 (light) and #9AA1A9 (dark).
PALETTES = {
    "light": {
        "window": "#FFFFFF",  # pipeline-light.svg panel white
        "titlebar": "#F2F3F5",  # Snow
        "line": "#C9CDD2",  # pipeline-light.svg neutral line
        "text": "#121417",  # Ink
        "mute": "#5F6368",  # Mute on light
        "cursor": "#FFC800",  # Gap Yellow
    },
    "dark": {
        "window": "#0D1117",  # pipeline-dark.svg panel
        "titlebar": "#121417",  # Ink
        "line": "#3A414A",  # pipeline-dark.svg neutral line
        "text": "#F2F3F5",  # Snow
        "mute": "#9AA1A9",  # Mute on dark
        "cursor": "#FFC800",  # Gap Yellow
    },
}

FONT_STACK = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
WIDTH = 880
PAD_X = 20
TITLE_H = 36
PAD_TOP = 14
PAD_BOTTOM = 12
LINE_HEIGHT_EM = 1.44  # 18 px at 12.5 px; the window grows with the content, nothing scrolls
FONT_SIZES = (14, 13.5, 13, 12.5, 12)  # the largest one that needs no wrapping is used
CHAR_EM = 0.6  # advance of one character, in em
TYPE_SECONDS_PER_CHAR = 0.024
CURSOR_HOLD = 0.3
ROW_STAGGER = 0.06
PAUSE_AFTER_OUTPUT = 0.9
START = 0.6
FINAL_HOLD = 5.0
EPS = 0.002  # seconds; the width of an instant jump


class DemoError(Exception):
    pass


# ---------------------------------------------------------------- running the scripts


def run(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8"
    )


def check_clean(label: str, text: str, private: list[str]) -> None:
    for needle in FORBIDDEN_IN_OUTPUT + tuple(private):
        if needle and needle in text:
            raise DemoError(f"{label}: the output contains '{needle}'")
    if not text.isascii():
        raise DemoError(f"{label}: the output is not plain ASCII")


def blueprint_markdown(blueprint: dict, versions: dict[str, str]) -> str:
    """A faithful rendering of the input: one section per marker, one line per chosen
    component with its catalog version and the decision's rationale."""
    headings = {
        "context": "1. Context",
        "tier": "2. Tier, floors and overrides",
        "architecture": "3. Architecture overview",
        "decisions": "4. Layer decisions",
        "sizing": "5. Sizing",
        "transfer": "6. Air-gap transfer plan",
        "data-flow": "7. Data flow",
        "operations": "8. Failure modes and operations",
        "verification": "9. Verification plan",
        "out-of-scope": "10. Out of scope and later layers",
    }
    answers = blueprint["answers"]
    lines: list[str] = []
    for name in SECTION_MARKERS:
        lines += [section_marker(name), f"## {headings[name]}", ""]
        if name == "context":
            lines += [f"- {key}: {json.dumps(value)}" for key, value in answers.items()]
        elif name == "decisions":
            for decision in blueprint["decisions"]:
                for component in decision["components"]:
                    lines.append(
                        f"- {decision['layer']}: {component} {versions[component]}: "
                        f"{decision['rationale']}"
                    )
        elif name == "transfer":
            lines.append(
                "The list of what to carry in is docs/airgap/transfer-manifest.md, "
                "written by manifest.py."
            )
        elif name == "verification":
            lines.append(
                "1. Benchmark before production: sizing does not predict throughput."
            )
            for decision in blueprint["decisions"]:
                if decision["evidence"] == "estimate":
                    lines.append(
                        f"- {decision['layer']}: rests on an estimate; measure before relying on it."
                    )
        lines.append("")
    return "\n".join(lines)


def agents_text(blueprint_path: str) -> str:
    snippet = (SKILL_DIR / "references" / "agents-snippet.md").read_text(encoding="utf-8")
    start, end = snippet.index(AGENT_BLOCK_START), snippet.index(AGENT_BLOCK_END)
    return snippet[start : end + len(AGENT_BLOCK_END)].replace("BLUEPRINT_PATH", blueprint_path) + "\n"


def capture() -> list[dict]:
    """Run the commands in a temporary project; return one dict per terminal step."""
    blueprint = json.loads(INPUT.read_text(encoding="utf-8"))
    catalog, _ = load_catalog(default_catalog_dir())
    versions = {cid: entry["version"] for cid, entry in catalog.components.items()}

    steps: list[dict] = [{"shown": SKILL_VARIABLE, "output": []}]
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "project"
        (project / "docs" / "airgap").mkdir(parents=True)
        shutil.copyfile(INPUT, project / BLUEPRINT_ARG)
        blueprint_file = project / blueprint["blueprint_path"]
        blueprint_file.parent.mkdir(parents=True, exist_ok=True)
        blueprint_file.write_text(blueprint_markdown(blueprint, versions), encoding="utf-8")
        (project / "AGENTS.md").write_text(agents_text(blueprint["blueprint_path"]), encoding="utf-8")

        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", NO_COLOR="1")
        private = [str(Path.home()), tmp, Path(tmp).name]
        commands = [
            ("tier.py", ["python3", str(SCRIPTS_DIR / "tier.py")]),
            ("size.py", ["python3", str(SCRIPTS_DIR / "size.py")]),
            ("manifest.py", ["python3", str(SCRIPTS_DIR / "manifest.py")]),
            ("grep", None),
            ("lint.py", ["python3", str(SCRIPTS_DIR / "lint.py")]),
        ]
        for name, argv in commands:
            if name == "grep":
                shown = "grep '^## ' docs/airgap/transfer-manifest.md"
                argv = ["grep", "^## ", "docs/airgap/transfer-manifest.md"]
            else:
                argv = argv + ["--blueprint", BLUEPRINT_ARG]
                shown = f"python3 $skill/scripts/{name} --blueprint {BLUEPRINT_ARG}"
            result = run(argv, project, env)
            if result.returncode != 0:
                raise DemoError(
                    f"{name} exited with {result.returncode}, expected 0:\n"
                    f"{result.stdout}{result.stderr}"
                )
            output = result.stdout + result.stderr
            check_clean(name, shown + "\n" + output, private)
            if name == "lint.py" and output.strip() != "OK: no findings":
                raise DemoError(
                    f"lint.py reported findings; fix them first:\n{output}\n"
                    "A W1 line means the catalog entries are older than the freshness "
                    "window: refresh the catalog, then rebuild. The committed SVGs stay "
                    "valid until then."
                )
            steps.append({"shown": shown, "output": output.rstrip("\n").split("\n")})
    return steps


# ---------------------------------------------------------------------------- layout


def wrap(line: str, cols: int) -> list[str]:
    """Break a row the way a terminal does, at a space, with a two-space continuation."""
    rows = []
    while len(line) > cols:
        cut = line.rfind(" ", 2, cols + 1)
        if cut <= 0:
            cut = cols
        rows.append(line[:cut].rstrip())
        line = "  " + line[cut:].lstrip()
    rows.append(line)
    return rows


class Row:
    def __init__(self, text: str, kind: str):
        self.text = text
        self.kind = kind  # "command", "output" or "ok"
        self.index = 0
        self.show = 0.0  # seconds; when the row appears
        self.type_start = 0.0
        self.type_end = 0.0
        self.cursor_end = 0.0


def layout(steps: list[dict]) -> tuple[float, int, list[Row]]:
    longest = max(
        len("$ " + step["shown"]) if step["shown"] else 0 for step in steps
    )
    longest = max([longest] + [len(line) for step in steps for line in step["output"]])
    for size in FONT_SIZES + (FONT_SIZES[-1],):
        cols = int((WIDTH - 2 * PAD_X) // (CHAR_EM * size))
        if longest <= cols or size == FONT_SIZES[-1]:
            break
    rows: list[Row] = []
    for step in steps:
        command = "$ " + step["shown"]
        if len(command) > cols:
            raise DemoError(f"command does not fit one row: {command}")
        rows.append(Row(command, "command"))
        for line in step["output"]:
            for part in wrap(line, cols):
                kind = "ok" if part.startswith("OK:") else "output"
                rows.append(Row(part, kind))
    for index, row in enumerate(rows):
        row.index = index
    return size, cols, rows


def schedule(rows: list[Row]) -> float:
    """Give every row its times; return the loop length in seconds."""
    t = START
    previous_command = None
    for row in rows:
        if row.kind == "command":
            if previous_command is not None:
                t += PAUSE_AFTER_OUTPUT
            row.show = t
            row.type_start = t
            row.type_end = t + (len(row.text) - 2) * TYPE_SECONDS_PER_CHAR
            row.cursor_end = row.type_end + CURSOR_HOLD
            t = row.cursor_end
            previous_command = row
        else:
            t += ROW_STAGGER
            row.show = t
    return round(t + FINAL_HOLD + 1.7, 3)


# ------------------------------------------------------------------------------ svg


def pct(seconds: float, loop: float) -> str:
    value = round(seconds / loop * 100, 4)
    return f"{value:.4f}".rstrip("0").rstrip(".")


def num(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def build_svg(theme: str, size: float, rows: list[Row], loop: float) -> str:
    colors = PALETTES[theme]
    cw = CHAR_EM * size
    line_h = round(size * LINE_HEIGHT_EM)
    body_top = TITLE_H + PAD_TOP
    viewport_h = len(rows) * line_h
    height = body_top + viewport_h + PAD_BOTTOM
    baseline = round(size * 1.2) - 1

    for row in rows:
        if PAD_X + len(row.text) * cw > WIDTH - PAD_X + 0.5:
            raise DemoError(f"row is wider than the window: {row.text}")

    reset = loop - 0.7
    p = lambda seconds: pct(seconds, loop)  # noqa: E731

    css: list[str] = []
    css.append(f"text {{ font-family: {FONT_STACK}; font-size: {size}px; white-space: pre; }}")
    css.append(f".t {{ fill: {colors['text']}; }} .m {{ fill: {colors['mute']}; }} .b {{ font-weight: 600; }}")
    css.append(".cur { opacity: 0; }")

    anim: list[str] = []
    anim.append(
        f".fade, .row, .cur {{ animation-duration: {loop}s; "
        "animation-iteration-count: infinite; animation-timing-function: linear; }"
    )
    anim.append(".fade { animation-name: fade; }")
    anim.append(
        f"@keyframes fade {{ 0%, {p(loop - 1.7)}% {{ opacity: 1; }} {p(loop - 1.2)}%, {p(loop - 0.4)}% "
        "{ opacity: 0; } 100% { opacity: 1; } }"
    )
    body: list[str] = []
    for row in rows:
        y = body_top + row.index * line_h
        xs = " ".join(num(PAD_X + i * cw) for i in range(len(row.text)))
        if row.kind == "command":
            spans = (
                f'<tspan class="m">{escape(row.text[:2])}</tspan>'
                f'<tspan class="t b">{escape(row.text[2:])}</tspan>'
            )
        elif row.kind == "ok":
            spans = f'<tspan class="t b">{escape(row.text)}</tspan>'
        else:
            spans = f'<tspan class="t">{escape(row.text)}</tspan>'
        anim.append(f".r{row.index} {{ animation-name: r{row.index}; }}")
        anim.append(
            f"@keyframes r{row.index} {{ 0%, {p(row.show)}% {{ opacity: 0; }} "
            f"{p(row.show + EPS)}%, {p(reset)}% {{ opacity: 1; }} {p(reset + EPS)}%, 100% {{ opacity: 0; }} }}"
        )
        body.append(
            f'<g class="row r{row.index}"><text x="{xs}" y="{y + baseline}" '
            f'xml:space="preserve">{spans}</text></g>'
        )
        if row.kind == "command":
            n = len(row.text) - 2
            travel = num(n * cw)
            x0 = PAD_X + 2 * cw
            anim.append(f".c{row.index} {{ animation-name: c{row.index}; }}")
            anim.append(
                f"@keyframes c{row.index} {{ 0%, {p(row.type_start)}% {{ opacity: 0; transform: translateX(0px); }} "
                f"{p(row.type_start + EPS)}% {{ opacity: 1; transform: translateX(0px); animation-timing-function: steps({n}, end); }} "
                f"{p(row.type_end)}%, {p(row.cursor_end)}% {{ opacity: 1; transform: translateX({travel}px); }} "
                f"{p(row.cursor_end + EPS)}% {{ opacity: 0; transform: translateX({travel}px); }} "
                f"100% {{ opacity: 0; transform: translateX(0px); }} }}"
            )
            body.append(
                f'<g class="cur c{row.index}">'
                f'<rect x="{num(x0)}" y="{y}" width="{num(n * cw + 1)}" height="{line_h}" fill="{colors["window"]}"/>'
                f'<rect x="{num(x0)}" y="{y + 3}" width="{num(cw)}" height="{line_h - 6}" fill="{colors["cursor"]}"/>'
                f"</g>"
            )

    css_text = "\n    ".join(css)
    anim_text = "\n      ".join(anim)

    dots = "".join(
        f'<circle cx="{18 + 16 * i}" cy="{TITLE_H // 2}" r="4.5" fill="none" stroke="{colors["line"]}" stroke-width="1.5"/>'
        for i in range(3)
    )
    title = "department-llm-platform"
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" role="img" aria-labelledby="title desc">',
            "  <title id=\"title\">airgap-architect in a terminal</title>",
            "  <desc id=\"desc\">The four scripts of the airgap-architect skill run on a department blueprint: tier.py, size.py, manifest.py and lint.py. Lint ends with OK: no findings. The output is the scripts' real output, rebuilt by design/demo/build_demo.py.</desc>",
            "  <style>",
            f"    {css_text}",
            "    @media (prefers-reduced-motion: no-preference) {",
            f"      {anim_text}",
            "    }",
            "  </style>",
            "  <defs>",
            f'    <clipPath id="win"><rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="10"/></clipPath>',
            f'    <clipPath id="view"><rect x="{PAD_X - 6}" y="{body_top}" width="{WIDTH - 2 * PAD_X + 12}" height="{viewport_h}"/></clipPath>',
            "  </defs>",
            f'  <rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="10" fill="{colors["window"]}"/>',
            '  <g clip-path="url(#win)">',
            f'    <rect x="0" y="0" width="{WIDTH}" height="{TITLE_H}" fill="{colors["titlebar"]}"/>',
            f'    <rect x="0" y="{TITLE_H - 1}" width="{WIDTH}" height="1" fill="{colors["line"]}"/>',
            "  </g>",
            f"  {dots}",
            f'  <text class="m" x="{WIDTH // 2}" y="{TITLE_H // 2 + 4}" text-anchor="middle" xml:space="preserve" style="font-size: 12px">{title}</text>',
            f'  <rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="10" fill="none" stroke="{colors["line"]}" stroke-width="1"/>',
            '  <g clip-path="url(#view)">',
            '    <g class="fade">',
            *[f"      {line}" for line in body],
            "    </g>",
            "  </g>",
            "</svg>",
            "",
        ]
    )


def main() -> int:
    try:
        steps = capture()
        size, cols, rows = layout(steps)
        loop = schedule(rows)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for theme in PALETTES:
            svg = build_svg(theme, size, rows, loop)
            for needle in FORBIDDEN_IN_OUTPUT:
                if needle in svg:
                    raise DemoError(f"the {theme} SVG contains '{needle}'")
            path = OUT_DIR / f"terminal-{theme}.svg"
            path.write_bytes(svg.encode("utf-8"))
            print(f"{path.relative_to(REPO_ROOT)}: {path.stat().st_size} bytes")
        print(f"font {size} px, {cols} columns, {len(rows)} rows, loop {loop} s")
    except DemoError as error:
        print(f"build_demo: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
