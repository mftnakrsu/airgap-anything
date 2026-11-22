# Brand working files

Everything under `assets/brand/` is generated from the tools in this folder.

| Path | What it is |
|---|---|
| `tools/build_brand.py` | Builds the logo files, the animated SVGs (the README's animated icon tile among them) and the social preview source |
| `tools/render_fallbacks.py` | Renders GIF and PNG fallbacks of the animated SVGs |
| `tools/build_how_it_works.py` | Builds `how-it-works.svg`, the README's diagram; standard library only |
| `concepts/` | Round 1 logo concepts (A "open bar" was chosen), the concept sheet and a motion sketch |
| `preview.html` | One page that shows every asset on light and dark backgrounds |

## Rebuild

Requirements: Python 3.11+, `fontTools`, `Pillow`, and Chrome or Chromium on `PATH` (on macOS, Google Chrome in its default place under `/Applications` is found too). These are needed only to rebuild brand assets, not to use the skill.

```bash
# 1. Fetch the two B612 fonts (SIL Open Font License 1.1). They are not stored in the repository.
mkdir -p /tmp/b612
curl -sSL --max-time 30 -o /tmp/b612/B612-Bold.ttf    https://raw.githubusercontent.com/google/fonts/main/ofl/b612/B612-Bold.ttf
curl -sSL --max-time 30 -o /tmp/b612/B612-Regular.ttf https://raw.githubusercontent.com/google/fonts/main/ofl/b612/B612-Regular.ttf

# 2. Build the SVG files.
python3 design/brand/tools/build_brand.py --bold /tmp/b612/B612-Bold.ttf --regular /tmp/b612/B612-Regular.ttf --out assets/brand

# 3. Render the GIF and PNG fallbacks.
python3 design/brand/tools/render_fallbacks.py --assets assets/brand
```

The animated symbol, the animated icon tile and the pipeline set no text in B612, so they rebuild without fonts or fontTools: `python3 design/brand/tools/build_brand.py --without-fonts --out assets/brand`. The README's diagram needs none of these either: `python3 design/brand/tools/build_how_it_works.py`. `tests/test_readme.py` fails when the committed file differs from the builder's output, and when a text or a line would not read on GitHub's light or dark page.

The favicon and web icon set in `assets/brand/icons/` and `assets/brand/social-preview.png` were exported with the `logo-design` skill's `export_variants.py` and `render_png.py`. Those scripts are not part of this repository.

## Change something

- Colours, symbol geometry, tagline and letter spacing are constants at the top of `tools/build_brand.py`.
- Animation timing lives in the `build_hero`, `build_symbol_animated` and `build_pipeline` functions.
- After a change: rebuild, open `preview.html`, then render the fallbacks again.
