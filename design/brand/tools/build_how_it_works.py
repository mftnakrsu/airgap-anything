"""Build assets/brand/how-it-works.svg, the README's "How it works" diagram.

The canvas is transparent, so the diagram takes the page colour of whichever
GitHub theme the reader uses. To read on both, every text sits on its own
opaque shape, and every line and border uses a grey that clears 3:1 against
GitHub's light (#ffffff) and dark (#0d1117) page colours. tests/test_readme.py
checks both rules.

Standard library only. Run from the repository root:

    python3 design/brand/tools/build_how_it_works.py
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT = REPO_ROOT / "assets" / "brand" / "how-it-works.svg"

INK = "#121417"  # brand ink
SUBTLE = "#57606A"  # secondary text, on white and on the chip fill
LINE = "#7D8590"  # connectors: 3.7:1 on white, 5.1:1 on #0d1117
BORDER = "#8C959F"  # card borders: 3.0:1 on white, 6.2:1 on #0d1117
YELLOW = "#FFC800"  # Gap Yellow, the air gap
MODEL_FILL = "#FFFFFF"
CHIP_FILL = "#EEF1F4"

SANS = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# (who, name, what) for the eight steps on the connected workstation.
STEPS = [
    ("AGENT", "1  Interview", "asks, one by one"),
    ("AGENT", "2  Tier", "org complexity"),
    ("AGENT", "3  Sizing", "every step shown"),
    ("AGENT", "4  Decisions", "one per layer"),
    ("AGENT", "5  Manifest", "what to carry in"),
    ("AGENT", "6  Blueprint", "the plan and why"),
    ("AGENT", "7  Self-review", "until it all holds"),
    ("YOU", "8  Hand-off", "after you approve"),
]
BUILD_LINES = ("No internet.", "People or an agent", "follow the runbook", "and the files", "carried in.")

WIDTH, HEIGHT = 1000, 352
CARD_W, CARD_H, GAP, LEFT = 156, 84, 20, 40
ROWS = (100, 220)
GAP_X = 744  # left edge of the air gap band
BUILD_X, BUILD_Y, BUILD_W, BUILD_H = 780, 100, 180, 204

TITLE = "How airgap-anything works"
DESC = (
    "Eight steps on a connected workstation, done by the agent and you; "
    "the files cross the air gap, and the people or the agent inside build the system without internet."
)


def _card_x(column):
    return LEFT + column * (CARD_W + GAP)


def _chip(x, text):
    width = (len(text) * 7 + 16 + 3) // 4 * 4  # 10px mono with 0.1em tracking
    return [
        f'<rect x="{x}" y="44" width="{width}" height="24" rx="4" fill="{CHIP_FILL}"/>',
        f'<text x="{x + 8}" y="60" font-family="{MONO}" font-size="10" font-weight="600" '
        f'letter-spacing="0.1em" fill="{INK}">{text}</text>',
    ]


def render():
    out = []
    out += _chip(LEFT, "OUTSIDE · A CONNECTED WORKSTATION")
    out += _chip(BUILD_X, "INSIDE · OFFLINE")

    # Connectors before cards, so that lines sit behind them.
    for top in ROWS:
        y = top + CARD_H // 2
        for column in range(3):
            x = _card_x(column) + CARD_W
            out.append(
                f'<line x1="{x}" y1="{y}" x2="{x + GAP - 2}" y2="{y}" stroke="{LINE}" '
                f'stroke-width="1.5" marker-end="url(#arrow)"/>'
            )
    first, last = _card_x(0) + CARD_W // 2, _card_x(3) + CARD_W // 2
    turn = ROWS[0] + CARD_H + 18
    out.append(
        f'<path d="M{last} {ROWS[0] + CARD_H} V{turn - 8} Q{last} {turn} {last - 8} {turn} '
        f'H{first + 8} Q{first} {turn} {first} {turn + 8} V{ROWS[1] - 2}" fill="none" '
        f'stroke="{LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>'
    )

    # The air gap, then the hand-off arrow across it.
    out.append(f'<rect x="{GAP_X}" y="84" width="16" height="232" fill="{YELLOW}"/>')
    y = ROWS[1] + CARD_H // 2
    out.append(
        f'<line x1="{_card_x(3) + CARD_W}" y1="{y}" x2="{BUILD_X - 2}" y2="{y}" stroke="{LINE}" '
        f'stroke-width="2" marker-end="url(#arrow)"/>'
    )
    out.append(f'<rect x="{GAP_X - 24}" y="{HEIGHT - 34}" width="64" height="22" rx="4" fill="{YELLOW}"/>')
    out.append(
        f'<text x="{GAP_X + 8}" y="{HEIGHT - 19}" font-family="{MONO}" font-size="10" font-weight="700" '
        f'letter-spacing="0.1em" text-anchor="middle" fill="{INK}">AIR GAP</text>'
    )

    for index, (who, name, what) in enumerate(STEPS):
        x, y = _card_x(index % 4), ROWS[index // 4]
        fill = MODEL_FILL
        dash = ' stroke-dasharray="5,4"' if who == "YOU" else ""
        out.append(
            f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{CARD_H}" rx="6" fill="{fill}" '
            f'stroke="{BORDER}" stroke-width="1.25"{dash}/>'
        )
        out.append(
            f'<text x="{x + 14}" y="{y + 24}" font-family="{MONO}" font-size="10" font-weight="600" '
            f'letter-spacing="0.12em" fill="{SUBTLE}">{who}</text>'
        )
        out.append(f'<text x="{x + 14}" y="{y + 48}" font-family="{SANS}" font-size="15" font-weight="600" fill="{INK}">{name}</text>')
        out.append(f'<text x="{x + 14}" y="{y + 68}" font-family="{SANS}" font-size="12" fill="{SUBTLE}">{what}</text>')

    out.append(
        f'<rect x="{BUILD_X}" y="{BUILD_Y}" width="{BUILD_W}" height="{BUILD_H}" rx="6" fill="{MODEL_FILL}" '
        f'stroke="{BORDER}" stroke-width="1.5"/>'
    )
    out.append(
        f'<text x="{BUILD_X + 16}" y="{BUILD_Y + 28}" font-family="{MONO}" font-size="10" font-weight="600" '
        f'letter-spacing="0.12em" fill="{SUBTLE}">INSIDE THE NETWORK</text>'
    )
    out.append(f'<text x="{BUILD_X + 16}" y="{BUILD_Y + 56}" font-family="{SANS}" font-size="17" font-weight="600" fill="{INK}">Build</text>')
    for k, line in enumerate(BUILD_LINES):
        out.append(f'<text x="{BUILD_X + 16}" y="{BUILD_Y + 84 + 20 * k}" font-family="{SANS}" font-size="13" fill="{SUBTLE}">{line}</text>')

    body = "\n  ".join(out)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" '
        f'role="img" aria-labelledby="how-it-works-title how-it-works-desc">\n'
        f'  <title id="how-it-works-title">{TITLE}</title>\n'
        f'  <desc id="how-it-works-desc">{DESC}</desc>\n'
        f'  <defs><marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
        f'<polygon points="0 0, 8 3, 0 6" fill="{LINE}"/></marker></defs>\n'
        f"  {body}\n</svg>\n"
    )


def main():
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
