---
name: explainer
description: Turn documents, a folder or a git repository into narrated motion-graphic explainer videos (MP4 + SRT) in Korean, English, Japanese, Chinese or Spanish. Use when the user asks to make an explainer, tutorial, training or onboarding video, a narrated walkthrough of docs or code, or "a video from this repo/document", in any of those languages.
---

# explainer — narrated explainer videos from your material

You turn the user's material into short videos: animated scenes on a 1920×1080 stage, a synthesized narrator, burned-in subtitles and a separate `.srt`. The user brings the knowledge; you read it, plan episodes, write scripts, build and review.

Everything you need is in this skill folder (`<skill>` below):
`scripts/cli.py` (commands) · `engine/` (player and scene types) · `lang/` (per-language settings) · `templates/script.md` · `references/` (read on demand).

## Ground rules

- **Faithful to the source.** Every claim on screen or in narration must come from the material. Quote exact wording when wording matters (laws, APIs, error messages) and paraphrase only to explain. Never invent numbers, names or behavior. If the material is unclear, say so in the outline and ask.
- **Cite.** Put the sources in each script's front matter (`sources:`); the closing scene shows them.
- **Check the right to use it.** Before building, confirm the user may turn the material into a video they will share (their own work, public domain, or licensed). Mark translations you made as unofficial (`note:` on the scene).
- **The user approves the plan** before you write full scripts. Building and rendering are cheap to redo; a wrong outline is not.
- **Speech times the picture.** Don't hand-tune timings. Each narration line is synthesized and measured; scene elements appear on the line they belong to (`at:`).

## Workflow

### 1. Check the machine

```bash
python <skill>/scripts/cli.py doctor --online
```

Needs Python 3.10+, `pip install edge-tts playwright imageio-ffmpeg pyyaml`, and a browser (`playwright install chromium`, or an installed Chrome is used). `--online` also tests the voice service. If there is no internet, use `--tts none` later (silent drafts with estimated timing).

### 2. Connect the material

```bash
python <skill>/scripts/cli.py ingest <folder | file | git URL> --workspace explainer
```

This clones git URLs (shallow) and writes `explainer/_sources/inventory.md` — every readable file with its first heading. Read the files that matter (README, docs, key modules) yourself. For a large repo, start from the inventory and the user's goal; don't read everything.

### 3. Agree the plan (stop and ask)

Ask, in one message, with a recommendation for each:
- **Audience and goal** — who watches, what they should be able to do afterwards.
- **Language(s)** — any of ko, en, ja, zh, es. One base language is written first; the others are translations with the same shape.
- **Episodes** — a list: title, 3–6 sections each, what each section shows. Aim for 2–4 minutes per episode (about 8–12 sections, 2–4 narration lines each).
- **Voice** — female (default) or male.
- **Design template** — `midnight` (default), `paper`, `blueprint` or `chalk`. Show `docs/templates.<lang>.png` from this repository if present, or render a gallery once a draft exists (`cli.py templates <episode> --lang <code>`). Brand colors can go on top. See `references/templates.md`.

Write the plan to `explainer/plan.md` and wait for approval.

### 3b. If the user brings their own design

A brand guide, a sample slide or screenshot, a logo, color codes, font files — turn them into a template instead of hand-tuning scenes (details: `references/templates.md#your-own-design`):

1. **Look** at the images and documents yourself. Note: background (light or dark), text color, one or two accent colors, a muted color, corner style, heading font. Use exact codes when the material gives them; otherwise pick from the image and say they are approximations.
2. **Write** `explainer/brand/brand.css`: copy the closest built-in template (`paper` for light, `midnight` for dark) and change only the tokens. Put logo and font files in `explainer/brand/`.
3. **Point** each script at it: `template: ../brand/brand.css`, plus `theme: {logo: ../brand/logo.svg, fonts: [...]}` if there is a logo or font files.
4. **Check**: `build` prints `low contrast` warnings — fix every one (brand colors often fail as text or subtitle colors; keep the brand color as `accent` and use a darker or lighter variant for text). Then run `templates <episode> --lang <code>` so the user sees their template next to the built-in ones, and ask for approval.

### 4. Write the scripts

```bash
python <skill>/scripts/cli.py new explainer/<episode-id> --lang <base>
```

Edit `explainer/<episode-id>/script.<lang>.md`. Format: `references/script-format.md`. Put the chosen `template:` in the front matter. Scene types and their fields: `references/scene-types.md` (`cover`, `cards`, `quote`, `flow`, `list`, `closing`). Rules of thumb:
- One idea per narration line; a line is one subtitle (at most two on-screen lines — `build` warns).
- Put on-screen text in the `screen` block, never in code; narration lives in `- ` lines.
- Use `at: <line index>` to make an item appear (and highlight) while its line is spoken.
- `{say: ...}` at the end of a line overrides what the narrator reads (numbers, abbreviations, symbols).

For each extra language, copy the base script to `script.<lang>.md` and translate it **keeping the same section ids and the same number of lines per section** — `build` warns when they drift. Language specifics: `references/languages.md`.

### 5. Build and review

```bash
python <skill>/scripts/cli.py build explainer/<episode-id> --lang all
python <skill>/scripts/cli.py stills explainer/<episode-id> --lang <code> cover:3 <section>:<seconds> ...
```

`build` synthesizes speech (cached), times everything, writes `build/<lang>/index.html` (open it in a browser to play with sound) and `out/<id>.<lang>.srt`. Fix every `warn` line. Then look at stills — at least one per section, in every language — with `references/review.md`: text overflowing its box, subtitles covering content, wrong fonts (tofu boxes) for ja/zh, an element appearing on the wrong line.

### 6. Render

```bash
python <skill>/scripts/cli.py render explainer/<episode-id> --lang all
```

Writes `out/<id>.<lang>.mp4` (H.264 + AAC). It renders frame by frame, so it takes a few minutes per language; run it in the background. Report each video's path and duration to the user.

## When something goes wrong

- `unsupported language` → only ko, en, ja, zh, es have settings in `lang/`. A new language is a new YAML file there (copy the closest one).
- The narrator mispronounces something → add `{say: ...}` to that line, or a `say:` rule in `lang/<code>.yaml` if it repeats.
- A scene needs a layout the six types can't express → write a custom type in `explainer/<episode-id>/scenes.js` (`Explainer.scene("name", (root, ctx) => (t) => {...})`, see `references/scene-types.md#custom`); `build` loads it automatically.
- Speech service unreachable → `--tts none` produces a silent, correctly paced draft; build with speech later.
