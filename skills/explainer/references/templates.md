# Design templates

A template changes how scenes look — colors, background texture, fonts, corner radius, borders, emphasis — never where things are. Every script therefore works with every template, and a gallery of one episode in all templates is a fair comparison.

| template | look |
|---|---|
| `midnight` (default) | deep navy, sky-blue and violet accents, soft dot texture |
| `paper` | warm off-white page, serif headings, ink and terracotta |
| `blueprint` | blue grid sheet, amber highlights, monospace labels |
| `chalk` | green chalkboard, chalk-yellow and pink, dashed outlines, wavy underlines |

## Choosing

1. Script front matter: `template: paper`.
2. Override at build time: `cli.py build <episode> --template chalk` (the script is not changed).
3. Brand colors on top of any template: `theme: {accent: "#e4572e", accent2: "#1b998b"}` in the front matter. Allowed keys: `accent`, `accent2`, `bg`, `bg2`, `fg`, `muted`.

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

Rules:
- Fonts: name a Latin font first and end with a generic family (`serif`, `monospace`, `cursive`, `sans-serif`) so Korean, Japanese and Chinese fall back to a suitable system font for the page language. Don't depend on downloaded web fonts — rendering may run offline.
- No `transition` or `animation` — frames are rendered by jumping in time.
- Keep subtitle contrast high (`--sub-fg` on `--sub-bg`) and check a light template's stills in all five languages.
