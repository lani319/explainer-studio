from explainer_lib import lang, script, timeline

SRC = """---
id: t
lang: en
title: T
sources: [Somewhere]
---

## Cover {#cover}

```screen
type: cover
title: Hi
```

- One.
- Two <b> & **three**.

## Body {#body}

```screen
type: list
items: [a]
```

- Body line that is quite a bit longer than the others, to test wrapping into subtitle lines.
"""


def _build() -> tuple[script.Script, lang.Lang, dict]:
    s = script.parse(SRC)
    L = lang.load("en")
    return s, L, timeline.build(s, L, [[1.0, 2.0], [3.0]])


def test_lines_follow_speech_with_gaps_and_sections_chain() -> None:
    s, L, tl = _build()
    cover, body = tl["sections"]
    assert cover["t0"] == 0
    assert cover["lines"][0]["t0"] == timeline.COVER_LEAD
    assert cover["lines"][1]["t0"] == round(timeline.COVER_LEAD + 1.0 + L.gap, 3)
    end_cover = timeline.COVER_LEAD + 1.0 + L.gap + 2.0 + timeline.HOLD
    assert body["t0"] == round(end_cover, 3)
    assert body["lines"][0]["t0"] == round(end_cover + timeline.LEAD_IN, 3)
    assert tl["duration"] == round(end_cover + timeline.LEAD_IN + 3.0 + timeline.HOLD, 3)


def test_subtitle_html_is_escaped_but_keeps_emphasis() -> None:
    _, _, tl = _build()
    assert tl["sections"][0]["lines"][1]["html"] == "Two &lt;b&gt; &amp; <b>three</b>."


def test_meta_carries_language_and_sources() -> None:
    _, _, tl = _build()
    assert tl["meta"]["lang"] == "en" and tl["meta"]["sources"] == ["Somewhere"]
    assert tl["meta"]["font"]


def test_srt_numbering_times_and_wrapping() -> None:
    s, L, tl = _build()
    out = timeline.srt(tl, L, s)
    blocks = out.strip().split("\n\n")
    assert len(blocks) == 3
    assert blocks[0].startswith("1\n00:00:01,400 --> 00:00:02,400\nOne.")
    assert "**" not in out
    assert len(blocks[2].splitlines()) >= 4  # number, times, and at least two wrapped lines


def test_estimate_is_positive_and_grows_with_text() -> None:
    L = lang.load("ko")
    assert timeline.estimate("가", L) >= 1.2
    assert timeline.estimate("가" * 70, L) > timeline.estimate("가" * 20, L)


def test_pacing_warnings() -> None:
    s, L, _ = _build()
    warns = timeline.pacing_warnings(s, L, [[1.0, 12.0], [3.0]])
    assert any("12.0s" in w for w in warns)
