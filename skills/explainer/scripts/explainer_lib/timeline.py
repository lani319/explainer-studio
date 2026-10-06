"""Turn a script plus measured narration lengths into absolute times (the timeline the player and renderer share).

Speech comes first: every line is synthesized, measured, and the picture is timed to it. A scene element that
appears "with line 2" therefore appears exactly when line 2 is spoken, in every language.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any

from .lang import Lang, strip_marks
from .script import Script

LEAD_IN = 0.6  # seconds a section is on screen before its first line
HOLD = 1.0  # seconds after the last line before the next section
COVER_LEAD = 1.4  # the cover animates in before anyone speaks


@dataclass
class TimedLine:
    t0: float
    t1: float
    text: str


def estimate(text: str, lang: Lang) -> float:
    """Narration length guess when no speech is synthesized (offline drafts)."""
    n = len(re.sub(r"\s", "", strip_marks(text)))
    return max(1.2, n / lang.cps)


def build(script: Script, lang: Lang, durations: list[list[float]]) -> dict[str, Any]:
    """``durations[i][j]`` = seconds of speech for line j of section i."""
    t = 0.0
    sections: list[dict[str, Any]] = []
    for i, sec in enumerate(script.sections):
        start = t
        lead = COVER_LEAD if sec.screen.get("type") == "cover" else LEAD_IN
        cur = start + lead
        lines: list[dict[str, Any]] = []
        for j, line in enumerate(sec.lines):
            d = durations[i][j]
            lines.append({"t0": round(cur, 3), "t1": round(cur + d, 3), "html": to_html(line.text)})
            cur += d + lang.gap
        end = cur - lang.gap + HOLD
        sections.append(
            {
                "id": sec.id,
                "title": sec.title,
                "t0": round(start, 3),
                "dur": round(end - start, 3),
                "screen": sec.screen,
                "lines": lines,
            }
        )
        t = end
    return {
        "meta": {
            "id": script.id,
            "title": script.title,
            "lang": lang.code,
            "html_lang": lang.html_lang,
            "font": lang.font,
            "word_break": lang.word_break,
            "ui": lang.ui,
            "theme": script.meta.get("theme") or {},
            "sources": script.meta.get("sources") or [],
        },
        "duration": round(t, 3),
        "sections": sections,
    }


def to_html(text: str) -> str:
    """Subtitle markup: escape everything, then turn **x** into emphasis."""
    esc = html.escape(text, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc)


def pacing_warnings(script: Script, lang: Lang, durations: list[list[float]]) -> list[str]:
    """Lines whose speech is much longer than a comfortable reading pace — usually a sign to split the line."""
    out: list[str] = []
    for i, sec in enumerate(script.sections):
        for j, line in enumerate(sec.lines):
            if durations[i][j] > 9.0:
                out.append(f"{sec.id} line {j + 1}: {durations[i][j]:.1f}s — consider splitting")
            if len(lang.wrap_lines(line.text, lang.screen_width)) > 2:
                out.append(f"{sec.id} line {j + 1}: needs more than two on-screen subtitle lines")
    return out


def srt(timeline: dict[str, Any], lang: Lang, script: Script) -> str:
    def stamp(sec: float) -> str:
        ms = int(round(sec * 1000))
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    blocks: list[str] = []
    n = 0
    for sec_t, sec in zip(timeline["sections"], script.sections, strict=True):
        for line_t, line in zip(sec_t["lines"], sec.lines, strict=True):
            n += 1
            body = "\n".join(lang.wrap_lines(line.text))
            blocks.append(f"{n}\n{stamp(line_t['t0'])} --> {stamp(line_t['t1'])}\n{body}\n")
    return "\n".join(blocks)
