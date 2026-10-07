# Design templates

A template changes how scenes look — colors, background texture, fonts, corner radius, borders, emphasis — never where things are. Every script therefore works with every template, and a gallery of one episode in all templates is a fair comparison.

| template | look |
|---|---|
| `midnight` (default) | deep navy, sky-blue and violet accents, soft dot texture |
| `paper` | warm off-white page, serif headings, ink and terracotta |
| `blueprint` | blue grid sheet, amber highlights, monospace labels |
| `chalk` | green chalkboard, chalk-yellow and pink, dashed outlines, wavy underlines |

## Choosing

1. Script front matter: `template: paper` — or a path to your own CSS: `template: ../brand/brand.css` (relative to the episode folder).
2. Override at build time: `cli.py build <episode> --template chalk` (the script is not changed).
3. Single tokens on top of any template: `theme: {accent: "#e4572e", sub-bg: "rgba(0,0,0,.85)"}`. Any token from the table below works (`-` or `_`). An unknown key stops the build with a hint instead of being ignored.

Show the user a gallery before they choose:

```bash
python <skill>/scripts/cli.py templates <episode> --lang <code> --marks cover:3 <section>:5
```

It builds the episode once per template (cached speech, separate folders) and writes `out/templates.<lang>.png`.

## Making a template

Copy `engine/themes/midnight.css` (or the closest one) to `engine/themes/<name>.css` and redefine tokens in `:root`. The first comment line is the description `cli.py templates` prints. Tokens (defaults in `engine/explainer.css`):

| token | used for |
|---|---|
| `--bg`, `--bg2`, `--stage-bg` | stage background (`--stage-bg` is the full CSS background) |
| `--texture`, `--texture-size`, `--texture-opacity` | the slowly drifting background pattern |
| `--fg`, `--muted` | main and secondary text |
| `--accent`, `--accent2`, `--on-accent` | highlights, badges, arrows; text on filled badges |
| `--card`, `--line`, `--active`, `--chip-bg` | card fill, outlines, the item being talked about, summary chips |
| `--radius`, `--border-w`, `--border-style`, `--shadow`, `--glow` | shapes |
| `--sub-bg`, `--sub-fg`, `--sub-shadow` | the subtitle box |
| `--heading-font`, `--label-font`, `--label-spacing` | titles; kickers, tags and numbers |
| `--em-decoration` | extra styling of **emphasis** (e.g. `underline wavy var(--accent2) 3px`) |
| `--logo-height` | logo size top-right (the cover shows it 1.5× larger) |

Rules:
- Assets a template references with `url(...)` (font files, background images) must sit beside it or below it; `build` copies them.
- Fonts: name a Latin font first and end with a generic family (`serif`, `monospace`, `cursive`, `sans-serif`) so Korean, Japanese and Chinese fall back to a suitable system font for the page language. Don't depend on downloaded web fonts — rendering may run offline.
- No `transition` or `animation` — frames are rendered by jumping in time.
- Keep subtitle contrast high (`--sub-fg` on `--sub-bg`) and check a light template's stills in all five languages.

## Your own design {#your-own-design}

Everything a user might bring maps onto three mechanisms:

| they have | use |
|---|---|
| a brand guide, sample slides, screenshots | read them, then write `brand/brand.css` (copy `paper` or `midnight`, change tokens) |
| color codes | tokens in `brand/brand.css`, or `theme:` keys for a few |
| a logo (SVG or PNG) | `theme: {logo: ../brand/logo.svg}` — top-right on every scene and on the cover; size with the `logo-height` token |
| font files (.woff2, .ttf, .otf) | `theme: {fonts: [{family: Brand Sans, file: ../brand/BrandSans.woff2, weight: 700}], font: Brand Sans}` — `font` goes in front of the language's stack; or use the family in `heading-font` |

```yaml
template: ../brand/brand.css
theme:
  logo: ../brand/logo.svg
  font: Brand Sans
  fonts:
    - {family: Brand Sans, file: ../brand/BrandSans-Regular.woff2, weight: 400}
    - {family: Brand Sans, file: ../brand/BrandSans-Bold.woff2, weight: 800}
```

**Contrast.** `build` resolves the final colors (base → template → `theme:`) and warns when text would be hard to read (WCAG ratios: 4.5:1 for body text and subtitles, 3:1 for large accent text and badges). Brand colors are often too light for text — keep them as `accent` and pick a darker or lighter variant for `fg`, `sub-fg` or `on-accent`. Values the check cannot parse (gradients) are skipped, so look at stills too.

**Logos.** Use a version that reads on the template's background — a dark logo disappears on `midnight`, `blueprint` or `chalk`. Ask for the light (reversed) variant when the template is dark, and check the gallery.

**Fonts and licenses.** Only ship font files the user is licensed to embed. Most brand fonts cover Latin only; Korean, Japanese and Chinese text then falls back to the language's font stack automatically.

