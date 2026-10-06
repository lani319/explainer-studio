"""Script → playable page. Writes ``build/<lang>/`` (page, engine copy, timeline, narration) and the .srt."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import lang as langmod
from . import media, timeline, tts
from .paths import ENGINE_DIR, Episode
from .script import Script, check_same_shape, load

PAGE = """<!doctype html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<link rel="stylesheet" href="engine/explainer.css" />
</head>
<body>
<div id="app"></div>
<script src="timeline.js"></script>
<script src="engine/player.js"></script>
<script src="engine/scenes.js"></script>
{extra}<script>Explainer.start(document.getElementById("app"), window.TIMELINE);</script>
</body>
</html>
"""


def build(
    ep: Episode,
    code: str,
    engine: str = "edge",
    voice: str | None = None,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    lang = langmod.load(code)
    script = load(ep.script(code))
    if script.lang != code:
        raise ValueError(f"{ep.script(code)} says lang '{script.lang}' but the file name says '{code}'")
    _check_translations(ep, script, log)
    durations, clips = tts.synthesize(script, lang, engine=engine, voice=voice, log=log)
    tl = timeline.build(script, lang, durations)
    for w in timeline.pacing_warnings(script, lang, durations):
        log(f"  warn {w}")

    out = ep.build_dir(code)
    out.mkdir(parents=True, exist_ok=True)
    eng = out / "engine"
    if eng.exists():
        shutil.rmtree(eng)
    shutil.copytree(ENGINE_DIR, eng)
    extra = ""
    custom = ep.root / "scenes.js"  # optional episode-specific scene types
    if custom.exists():
        shutil.copy2(custom, out / "scenes.custom.js")
        extra = '<script src="scenes.custom.js"></script>\n'

    has_audio = engine != "none"
    tl["audio"] = "narration.m4a" if has_audio else None
    (out / "timeline.js").write_text(
        "window.TIMELINE = " + json.dumps(tl, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8"
    )
    (out / "index.html").write_text(
        PAGE.format(html_lang=lang.html_lang, title=_esc(script.title), extra=extra), encoding="utf-8"
    )
    if has_audio:
        placed = [
            (line_t["t0"], clip)
            for sec_t, sec_clips in zip(tl["sections"], clips, strict=True)
            for line_t, clip in zip(sec_t["lines"], sec_clips, strict=True)
            if clip is not None
        ]
        media.narration_track(placed, tl["duration"], out / "narration.m4a")
    ep.out_dir().mkdir(parents=True, exist_ok=True)
    ep.srt(code).write_text(timeline.srt(tl, lang, script), encoding="utf-8")
    log(f"built {ep.id} [{code}] — {len(script.sections)} sections, {tl['duration']:.1f}s → {out / 'index.html'}")
    return tl


def _check_translations(ep: Episode, script: Script, log: Callable[[str], None]) -> None:
    """Warn when language versions drift apart (different sections or line counts)."""
    for other in ep.languages():
        if other == script.lang:
            continue
        try:
            for p in check_same_shape(script, load(ep.script(other))):
                log(f"  warn {p}")
        except Exception as exc:  # noqa: BLE001 — a broken sibling script must not block this build
            log(f"  warn cannot compare with {other}: {exc}")


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def page_url(ep: Episode, code: str) -> str:
    return (ep.build_dir(code) / "index.html").resolve().as_uri()


def ensure_built(ep: Episode, code: str) -> Path:
    page = ep.build_dir(code) / "index.html"
    if not page.exists():
        raise FileNotFoundError(f"{page} not found — run 'build' first")
    return page
