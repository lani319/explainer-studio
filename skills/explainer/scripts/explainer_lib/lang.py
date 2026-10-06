"""Per-language settings (``lang/<code>.yaml``): voices, pacing, wrapping, fonts and reading rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .paths import LANG_DIR

SUPPORTED = ("ko", "en", "ja", "zh", "es")

# Characters a line must not start with (closing punctuation) — basic line-breaking rule for CJK.
_NO_LINE_START = set("、。，．・：；？！）」』】〕〉》”’,.:;?!)]}%")


@dataclass(frozen=True)
class Lang:
    code: str
    name: str
    html_lang: str
    voices: dict[str, str]
    rate: str
    gap: float
    cps: float
    wrap: str  # "word" (split on spaces) or "char" (CJK: break anywhere)
    srt_width: int
    screen_width: int
    font: str
    word_break: str
    ui: dict[str, str]
    say: list[tuple[str, str]] = field(default_factory=list)

    def voice(self, choice: str | None) -> str:
        """``female``/``male`` picks from the table; anything else is taken as a full voice id."""
        if not choice:
            return self.voices["female"]
        return self.voices.get(choice, choice)

    def spoken(self, text: str) -> str:
        """Subtitle text → what the narrator should read (strip emphasis, apply reading rules)."""
        t = strip_marks(text)
        for pattern, repl in self.say:
            t = re.sub(pattern, repl, t)
        return re.sub(r"\s{2,}", " ", t).strip()

    def wrap_lines(self, text: str, width: int | None = None) -> list[str]:
        """Break a subtitle into display lines no longer than ``width`` (by characters)."""
        w = width or self.srt_width
        t = strip_marks(text).strip()
        if len(t) <= w:
            return [t]
        return _wrap_words(t, w) if self.wrap == "word" else _wrap_chars(t, w)


def strip_marks(text: str) -> str:
    return text.replace("**", "")


def _wrap_words(text: str, width: int) -> list[str]:
    lines: list[str] = []
    cur = ""
    for word in text.split():
        cand = f"{cur} {word}" if cur else word
        if len(cand) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return _balance(lines, " ")


def _wrap_chars(text: str, width: int) -> list[str]:
    lines: list[str] = []
    cur = ""
    for ch in text:
        if len(cur) >= width and ch not in _NO_LINE_START:
            lines.append(cur)
            cur = ""
        cur += ch
    if cur:
        lines.append(cur)
    return [ln.strip() for ln in lines if ln.strip()]


def _balance(lines: list[str], sep: str) -> list[str]:
    """Two lines read better when they are about the same length — move words from the first to the second."""
    if len(lines) != 2:
        return lines
    a, b = lines[0].split(sep), lines[1].split(sep)
    while len(a) > 1 and len(sep.join(a[:-1])) >= len(sep.join([a[-1], *b])):
        b.insert(0, a.pop())
    return [sep.join(a), sep.join(b)]


def load(code: str, lang_dir: Path = LANG_DIR) -> Lang:
    if code not in SUPPORTED:
        raise ValueError(f"unsupported language '{code}' — choose one of {', '.join(SUPPORTED)}")
    raw: dict[str, Any] = yaml.safe_load((lang_dir / f"{code}.yaml").read_text(encoding="utf-8"))
    return Lang(
        code=raw["code"],
        name=raw["name"],
        html_lang=raw["html_lang"],
        voices=dict(raw["voices"]),
        rate=str(raw.get("rate", "+0%")),
        gap=float(raw.get("gap", 0.35)),
        cps=float(raw["cps"]),
        wrap=raw["wrap"],
        srt_width=int(raw["srt_width"]),
        screen_width=int(raw.get("screen_width", raw["srt_width"])),
        font=raw["font"],
        word_break=raw.get("word_break", "normal"),
        ui={str(k): str(v) for k, v in (raw.get("ui") or {}).items()},
        say=[(str(p), str(r)) for p, r in (raw.get("say") or [])],
    )
