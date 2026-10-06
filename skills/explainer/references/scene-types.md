# Scene types

All text fields accept `**emphasis**` and `\n` line breaks. `at` is a narration line index (0-based) within the section.

## cover
Title card with an animated orbit.

| field | |
|---|---|
| `kicker` | small line above the title (series, chapter) |
| `title` | big title — shrinks automatically if it is too wide |
| `sub` | one-sentence subtitle |
| `badge` | optional pill (date, version) |

## cards
A grid of cards — an overview, a list of parts, options.

| field | |
|---|---|
| `title` | optional heading |
| `columns` | default: number of cards up to 4, else 3 |
| `cards` | list of `{tag, title, sub, at}` — a card with `at` is highlighted while its line plays |

Fits about 9 short cards (3×3) or 6 cards with a one-line `sub`.

## quote
A key on the left (article number, term), quoted passages on the right, summary chips below.

| field | |
|---|---|
| `kicker` | big label on the left (`Article 1`, `Rule 3`) |
| `title` | smaller line under it |
| `items` | list of `{label, text, at}`; default `at` = item index |
| `points` | chips shown with the last line (or at their own `at`) |
| `note` | small print under the kicker (e.g. "Unofficial translation") |

Fits three items of up to ~3 lines each.

## flow
Steps connected by arrows — a process, a pipeline, a sequence of conditions.

| field | |
|---|---|
| `title` | heading |
| `steps` | list of `{title, sub, at}`; default `at` = step index |
| `note` | line under the row, shown with the last narration line |

Fits 3–5 steps.

## list
Numbered rows — a checklist, ordered points.

| field | |
|---|---|
| `title` | heading |
| `items` | strings or `{text, at}` |

Fits about 6 rows.

## closing
Recap with check marks, an optional "next" card and the sources from the front matter.

| field | |
|---|---|
| `title` | default: the language's "recap" wording |
| `items` | recap lines |
| `next`, `next_kicker` | the next episode |

## Custom scene types {#custom}

Put `scenes.js` in the episode folder; `build` copies and loads it after the built-in types.

```js
Explainer.scene("timeline", (root, ctx) => {
  const { el, appear, rich } = Explainer.util;
  const events = ctx.screen.events || [];
  const rows = events.map((e, k) => {
    const r = el("div", "card", root, rich(e.text));
    Object.assign(r.style, { position: "absolute", left: "150px", top: `${220 + k * 130}px`, width: "1620px" });
    return r;
  });
  return (t) => rows.forEach((r, k) => appear(r, t, ctx.at(events[k], k)));
});
```

- `root` is the section's layer on the 1920×1080 stage; `t` is seconds since the section started.
- `ctx.screen` (the YAML), `ctx.cue(i)` / `ctx.cueEnd(i)` (line i start/end), `ctx.at(item, k)`, `ctx.dur`, `ctx.lines`, `ctx.ui`, `ctx.meta`.
- Draw only from `t`: no timers, no CSS transitions or animations — the renderer jumps between frames.
- Keep content above y ≈ 840; the subtitle sits below.
