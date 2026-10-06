# Script format

One file per language: `<episode-dir>/script.<lang>.md` — YAML front matter, then sections. Each section has a heading, one `screen` block and narration lines.

````markdown
---
id: my-episode            # folder name; used in output file names
lang: en                  # ko | en | ja | zh | es — must match the file name
title: Episode title      # shown top-right on every scene
voice: female             # female | male | a full edge-tts voice id
theme: {accent: "#38bdf8", accent2: "#a78bfa"}   # optional: accent, accent2, bg, bg2, fg, muted
sources:                  # shown on the closing scene
  - Document or repository the facts come from
---

## Section title {#section-id}

```screen
type: quote               # scene type — see scene-types.md
kicker: Article 1
items:
  - {label: "1", text: "Quoted text with **emphasis**.", at: 0}
```

- Narration line one. **Bold** is highlighted in the subtitle.
- Narration line two. {say: what the narrator reads instead of the subtitle}
````

## Rules

- A section starts with `## Title {#id}`. Ids use letters, digits, `-` and `_`, unique in the file. The title is shown top-left (except on the cover).
- Each section needs exactly one `screen` block (YAML) and at least one `- ` narration line.
- **Everything visible comes from the screen block.** Translating a script never touches code.
- YAML gotcha: in `{key: value}` flow style, a value containing a comma or colon must be quoted — `text: "Yes, quoted."`.
- `at: N` (0-based narration line index) makes an item appear when line N starts and highlights it until the next item's line. Without `at`, items appear one after another during the first line (quote items and flow steps default to their own index).
- Keep each line to at most two on-screen subtitle lines and under ~9 seconds of speech; `build` warns otherwise.
- Translations keep the same section ids and the same number of lines per section.

## Timing

Speech is synthesized first, one clip per line, and the timeline is built from the measured lengths: a short lead-in before the first line of each section (longer for the cover), a pause between lines (`gap` in the language file), and a hold after the last line. Sections cross-fade.
