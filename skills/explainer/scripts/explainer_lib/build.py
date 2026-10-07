"""Script → playable page. Writes ``build/<lang>/`` (page, engine copy, timeline, narration) and the .srt."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import brand as brandmod
from . import lang as langmod
from . import media, timeline, tts
from .paths import ENGINE_DIR, Episode
from .script import Script, check_same_shape, load

DEFAULT_TEMPLATE = "midnight"

PAGE = """<!doctype html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<link rel="stylesheet" href="engine/explainer.css" />
<link rel="stylesheet" href="{template_href}" />
{font_link}</head>
<body class="template-{template}">
<div id="app"></div>
<script src="timeline.js"></script>
<script src="engine/player.js"></script>
<script src="engine/scenes.js"></script>
{extra}<script>Explainer.start(document.getElementById("app"), window.TIMELINE);</script>
</body>
</html>
"""


def templates() -> list[str]:
    """Design templates shipped with the engine (``engine/themes/<name>.css``)."""
    return sorted(p.stem for p in (ENGINE_DIR / "themes").glob("*.css"))


def resolve_template(script: Script, override: str | None, base: Path | None = None) -> str:
    """A built-in template name, or the path of the user's own template CSS (relative to the episode)."""
    name = override or str(script.meta.get("template") or DEFAULT_TEMPLATE)
    if brandmod.is_path(name):
        path = Path(name) if Path(name).is_absolute() else (base or Path.cwd()) / name
        if not path.is_file():
            raise ValueError(f"template file not found — {path}")
        return str(path.resolve())
    have = templates()
    if name not in have:
        raise ValueError(f"unknown template '{name}' — choose one of {', '.join(have)}, or give a .css path")
    return name


def build(
    ep: Episode,
    code: str,
    engine: str = "edge",
    voice: str | None = None,
    template: str | None = None,
    out: Path | None = None,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Build one language. ``template`` overrides the script's; ``out`` overrides the build folder
    (used by the template gallery so a preview never replaces the real build)."""
    lang = langmod.load(code)
    script = load(ep.script(code))
    if script.lang != code:
        raise ValueError(f"{ep.script(code)} says lang '{script.lang}' but the file name says '{code}'")
    tpl = resolve_template(script, template, ep.root)
    theme = brandmod.parse_theme(script.meta.get("theme"), ep.root)
    _check_translations(ep, script, log)
    durations, clips = tts.synthesize(script, lang, engine=engine, voice=voice, log=log)
    tl = timeline.build(script, lang, durations)
    for w in timeline.pacing_warnings(script, lang, durations):
        log(f"  warn {w}")
    tpl_css = Path(tpl) if brandmod.is_path(tpl) else ENGINE_DIR / "themes" / f"{tpl}.css"
    for w in brandmod.contrast_warnings([brandmod.tokens(), brandmod.css_tokens(tpl_css), theme.vars]):
        log(f"  warn {w}")

    out = out or ep.build_dir(code)
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

    template_href = brandmod.copy_template(tpl_css, out) if brandmod.is_path(tpl) else f"engine/themes/{tpl}.css"
    logo_href, fonts_href = brandmod.ship_assets(theme, out)
    tl["meta"]["template"] = tpl_css.stem
    tl["meta"]["theme"] = theme.vars
    tl["meta"]["logo"] = logo_href
    if theme.font:
        tl["meta"]["font"] = f"{_quote(theme.font)}, {lang.font}"

    has_audio = engine != "none"
    tl["audio"] = "narration.m4a" if has_audio else None
    (out / "timeline.js").write_text(
        "window.TIMELINE = " + json.dumps(tl, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8"
    )
    (out / "index.html").write_text(
        PAGE.format(
            html_lang=lang.html_lang,
            title=_esc(script.title),
            template=_esc(tpl_css.stem),
            template_href=template_href,
            font_link=f'<link rel="stylesheet" href="{fonts_href}" />\n' if fonts_href else "",
            extra=extra,
        ),
        encoding="utf-8",
    )
    if has_audio:
        placed = [
            (line_t["t0"], clip)
            for sec_t, sec_clips in zip(tl["sections"], clips, strict=True)
            for line_t, clip in zip(sec_t["lines"], sec_clips, strict=True)
            if clip is not None
        ]
        media.narration_track(placed, tl["duration"], out / "narration.m4a")
    if out == ep.build_dir(code):
        ep.out_dir().mkdir(parents=True, exist_ok=True)
        ep.srt(code).write_text(timeline.srt(tl, lang, script), encoding="utf-8")
    log(f"built {ep.id} [{code}] {tpl_css.stem} — {len(script.sections)} sections, {tl['duration']:.1f}s")
    log(f"  → {out / 'index.html'}")
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


def _quote(family: str) -> str:
    """Quote a single family name; leave a stack ("A", B, serif) as written."""
    return family if "," in family or family.startswith(('"', "'")) else f'"{family}"'


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def page_url(bdir: Path) -> str:
    return (bdir / "index.html").resolve().as_uri()


def ensure_built(bdir: Path) -> Path:
    page = bdir / "index.html"
    if not page.exists():
        raise FileNotFoundError(f"{page} not found — run 'build' first")
    return page
