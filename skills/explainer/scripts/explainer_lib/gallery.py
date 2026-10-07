"""Template gallery: the same moments of one episode in every design template, side by side in one image.

Each template is built into its own folder (``build/<lang>@<template>``) so the real build is never replaced.
"""

from __future__ import annotations

import html
import shutil
from collections.abc import Callable
from pathlib import Path

from .brand import is_path
from .build import DEFAULT_TEMPLATE, build, resolve_template, templates
from .paths import Episode
from .render import stills
from .script import load

THUMB_W = 640


def make(
    ep: Episode,
    code: str,
    marks: list[str],
    out_png: Path,
    engine: str = "edge",
    names: list[str] | None = None,
    log: Callable[[str], None] = print,
) -> Path:
    from playwright.sync_api import sync_playwright

    names = names or sorted(templates(), key=lambda n: (n != DEFAULT_TEMPLATE, n))  # default first
    own = resolve_template(load(ep.script(code)), None, ep.root)
    if is_path(own) and own not in names:
        names = [own, *names]  # the episode's own template first
    work = ep.root / "build" / "_gallery"
    shots: dict[str, list[Path]] = {}
    for name in names:
        label = Path(name).stem if is_path(name) else name
        bdir = ep.root / "build" / f"{code}@{label}"
        build(ep, code, engine=engine, template=name, out=bdir, log=lambda _m: None)
        shots[label] = stills(ep, code, marks, bdir=bdir, out_dir=work / label, log=lambda _m: None)
        log(f"  {label}: {len(shots[label])} stills")

    page = work / "gallery.html"
    rows = "".join(
        f'<div class="name">{html.escape(name)}</div>'
        + "".join(f'<img src="{p.relative_to(work).as_posix()}">' for p in paths)
        for name, paths in shots.items()
    )
    cols = len(marks)
    width = 200 + cols * (THUMB_W + 16) + 24
    page.write_text(
        f"""<!doctype html><meta charset="utf-8"><style>
body {{ margin: 0; background: #111827; font-family: "Segoe UI", Arial, sans-serif; }}
.grid {{ display: grid; grid-template-columns: 200px repeat({cols}, {THUMB_W}px);
  gap: 16px; padding: 24px 24px 24px 0; }}
.name {{ color: #e5e7eb; font-size: 26px; font-weight: 700;
  display: flex; align-items: center; justify-content: flex-end; }}
img {{ width: {THUMB_W}px; border-radius: 8px; display: block; }}
</style><div class="grid">{rows}</div>""",
        encoding="utf-8",
    )
    out_png.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:  # noqa: BLE001 — fall back to an installed Chrome
            browser = p.chromium.launch(channel="chrome")
        pg = browser.new_page(viewport={"width": width, "height": 400})
        pg.goto(page.resolve().as_uri())
        pg.wait_for_load_state("load")
        pg.screenshot(path=str(out_png), full_page=True)
        browser.close()
    for label in shots:
        shutil.rmtree(ep.root / "build" / f"{code}@{label}", ignore_errors=True)
    log(f"wrote {out_png}")
    return out_png
