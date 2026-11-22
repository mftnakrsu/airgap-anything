# airgap-anything — Logo Guidelines

> Status: first version. The maintainer approved the logo, the colour and the typeface on 2026-11-21.

## 1. The logo

- **Idea:** an A whose crossbar never meets. The air between the two halves forms an arrow that points one way.
- **Versions:** horizontal lockup, stacked lockup, symbol only, wordmark only, icon tile.
- **Rotated by 180 degrees** the symbol becomes ∀, the "for all" sign. The animated symbol uses this.

| File | Use |
|---|---|
| `logo/lockup-horizontal-ink.svg`, `-white.svg` | Headers, documents |
| `logo/lockup-stacked-ink.svg`, `-white.svg` | Square formats |
| `logo/symbol-ink.svg`, `-white.svg` | Symbol alone, 32 px and larger |
| `logo/symbol-small-ink.svg`, `-white.svg` | Symbol below 32 px (heavier legs, wider gap) |
| `logo/wordmark-ink.svg`, `-white.svg` | Name alone |
| `logo/icon-tile.svg` | Avatar and app icon: ink A on Gap Yellow |
| `icons/` | Favicon and web icon set, with `head-snippet.html` |
| `social-preview.png` | Repository social preview, 1280 x 640 |

## 2. Animated assets

| File | Where |
|---|---|
| `hero-light.svg`, `hero-dark.svg` | Header banner on pages that set their own background colour |
| `pipeline-light.svg`, `pipeline-dark.svg` | Animated "how it works" diagram on pages that set their own background colour |
| `symbol-animated.svg` | Standalone animated symbol; follows the viewer's colour scheme |
| `icon-tile-animated.svg` | The icon tile with the same story; opaque Gap Yellow, so it reads on any page. The README's header |
| `fallback/*.gif`, `fallback/*.png` | Places that do not animate SVG. The PNGs have an opaque background |

The README's "How it works" diagram is `how-it-works.svg`, not an animated asset. It is static and transparent, so it takes the page colour of the reader's GitHub theme. Every text sits on its own card or chip, and every line and border is a grey that clears 3:1 against both GitHub page colours, `#ffffff` and `#0d1117`. `design/brand/tools/build_how_it_works.py` builds it with the standard library alone.

README usage: the animated icon tile above the name, as below. Every other image either brings its own background or, like `how-it-works.svg`, is transparent and reads on both GitHub page colours. Do not switch images with `<picture>` in the README. The browser picks a `<picture>` source by the computer's colour scheme, while GitHub draws the page in the GitHub theme. On 2026-11-22, a computer in dark mode with a light GitHub theme got the dark hero on a white page, and the logo nearly disappeared. `tests/test_readme.py` checks the README for this.

```html
<p align="center">
  <img src="assets/brand/icon-tile-animated.svg" width="96" height="96" alt="">
</p>

<h1 align="center">airgap-anything</h1>
```

Motion rules:

1. Only `transform` and `opacity` are animated.
2. Every animation stops under `prefers-reduced-motion: reduce` and leaves the finished logo.
3. The resting state of an animation equals the static logo.
4. Motion tells one story: the bar opens, one block passes through the gap, one way.

## 3. Clear space

Keep a clear zone of one leg width of the A on all sides. One leg is 40 units of the 256-unit symbol. The zone scales with the logo.

## 4. Minimum size

| Version | Screen | Print |
|---|---|---|
| Horizontal lockup | 160 px wide | 30 mm wide |
| Symbol | 16 px, using the small cut or `icons/` | 6 mm |

## 5. Colour

| Name | HEX | RGB | CMYK (naive conversion) | Use |
|---|---|---|---|---|
| Ink | `#121417` | 18 20 23 | 22 13 0 91 | Logo and type on light backgrounds |
| Snow | `#F2F3F5` | 242 243 245 | 1 1 0 4 | Logo and type on dark backgrounds |
| Gap Yellow | `#FFC800` | 255 200 0 | 0 22 100 0 | The one signal colour: the moving block, the icon tile, highlights |
| Mute | `#5F6368` on light, `#9AA1A9` on dark | | | Secondary text |

- The CMYK values are arithmetic conversions. Verify them and choose a spot colour against a physical guide before any print job.
- Approved pairs: Ink on white, Snow or white on dark, Ink on Gap Yellow.
- Never set the logo or text in Gap Yellow on a white background: the contrast is too low.
- Why yellow: it is rare among infrastructure and security marks, and it recalls the platform-edge line of "mind the gap".

## 6. Typography

- **Wordmark and tagline:** B612 Bold and B612 Regular, converted to outlines. Letter spacing of the wordmark is -14/2000 em.
- **Licence:** B612 is under the SIL Open Font License 1.1. The fonts are not stored in this repository.
- **Diagram labels:** the system UI font stack.
- Do not recreate the wordmark by typing it. Use the files.

## 7. Don'ts

Do not stretch or squash the logo. Do not recolour it outside the palette. Do not close the gap in the crossbar. Do not add shadows, outlines or gradients. Do not rearrange the parts of a lockup. Do not place it on a busy background without the icon tile.

## 8. Rebuilding and limits

- All files are generated. See `design/brand/README.md` for the commands.
- No trademark search has been done. Run one before the project is published widely.
