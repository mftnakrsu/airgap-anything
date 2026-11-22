#!/usr/bin/env python3
"""Render GIF and PNG fallbacks of the animated SVGs, for places that do not animate SVG
(for example a wiki that only accepts raster images).

Usage:
    python3 design/brand/tools/render_fallbacks.py --assets assets/brand

Needs Pillow and a Chrome or Chromium binary, found on PATH or, on macOS, at the default
Google Chrome location. Frames are captured by pausing the CSS animations at exact times,
so the result does not depend on machine speed.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

CHROME_NAMES = ("google-chrome", "chromium", "chromium-browser", "chrome")
# Used when no name above is on PATH: where the macOS installer puts Google Chrome.
MAC_CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
# Passed to every Chrome this script starts. MacAppCodeSignClone is a feature of Chrome
# on macOS; the flag is harmless on other systems.
CHROME_FLAGS = ("--disable-features=MacAppCodeSignClone",)
CHUNK = 24  # frames per screenshot

# name, width, height, loop in ms, frames per second, background, time of the still frame in ms
JOBS = (
    ("hero-light", 960, 270, 9000, 12, "#FFFFFF", 7200),
    ("hero-dark", 960, 270, 9000, 12, "#0D1117", 7200),
    ("pipeline-light", 1024, 432, 16000, 10, "#FFFFFF", 100),
    ("pipeline-dark", 1024, 432, 16000, 10, "#0D1117", 100),
    ("symbol-animated", 256, 256, 10000, 12, "#FFFFFF", 4800),
)


def chrome() -> str:
    for name in CHROME_NAMES:
        path = shutil.which(name)
        if path:
            return path
    if MAC_CHROME.is_file():
        return str(MAC_CHROME)
    raise SystemExit(f"Chrome or Chromium was not found on PATH or at {MAC_CHROME}.")


def filmstrip(svg: str, times: list[int], width: int, height: int, background: str, work: Path, tag: str) -> list[Image.Image]:
    """Screenshot one page holding a copy of the SVG per time, then cut it into frames."""
    cells = "".join(f'<div class="f" data-t="{t}">{svg}</div>' for t in times)
    page = work / f"{tag}.html"
    page.write_text(
        f"<!doctype html><meta charset=utf-8><style>html,body{{margin:0;background:{background}}}"
        f".f{{width:{width}px;height:{height}px;overflow:hidden}}"
        f".f svg{{display:block;width:{width}px;height:{height}px}}</style>{cells}"
        "<script>const go=()=>document.querySelectorAll('.f').forEach(f=>f.querySelector('svg')"
        ".getAnimations({subtree:true}).forEach(a=>{a.pause();a.currentTime=+f.dataset.t}));"
        "go();requestAnimationFrame(go);</script>")
    shot = work / f"{tag}.png"
    subprocess.run(
        [chrome(), *CHROME_FLAGS, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
         "--force-prefers-color-scheme=light", f"--window-size={width},{height * len(times)}",
         "--virtual-time-budget=800", f"--screenshot={shot}", f"file://{page}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120, check=True)
    strip = Image.open(shot).convert("RGB")
    return [strip.crop((0, i * height, width, (i + 1) * height)) for i in range(len(times))]


def render(assets: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name, width, height, loop, fps, background, still_at in JOBS:
            svg = (assets / f"{name}.svg").read_text()
            step = 1000 // fps
            times = list(range(0, loop, step))
            frames: list[Image.Image] = []
            for start in range(0, len(times), CHUNK):
                frames += filmstrip(svg, times[start:start + CHUNK], width, height, background, work, f"{name}-{start}")
            palette = frames[len(frames) // 3].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
            indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
            indexed[0].save(out / f"{name}.gif", save_all=True, append_images=indexed[1:], duration=step, loop=0, optimize=True)
            still = filmstrip(svg, [still_at], width * 2, height * 2, background, work, f"{name}-still")[0]
            still.save(out / f"{name}.png", optimize=True)
            print(f"{name}: {len(frames)} frames, gif {(out / f'{name}.gif').stat().st_size // 1024} KB")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--assets", required=True, type=Path, help="folder with the animated SVGs, e.g. assets/brand")
    parser.add_argument("--out", type=Path, help="output folder (default: <assets>/fallback)")
    args = parser.parse_args()
    render(args.assets, args.out or args.assets / "fallback")


if __name__ == "__main__":
    main()
