"""Built page → MP4. The page is driven frame by frame (``window.__seek(t)``) and screenshots are piped
into ffmpeg, so a slow machine never drops frames — it only takes longer."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import media
from .build import ensure_built, page_url
from .paths import Episode

W, H = 1920, 1080


def _open(p: Any, url: str) -> tuple[Any, Any]:
    try:
        browser = p.chromium.launch()
    except Exception:  # noqa: BLE001 — no bundled Chromium: fall back to an installed Chrome
        browser = p.chromium.launch(channel="chrome")
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    page.goto(url + "?render=1")
    page.wait_for_function("window.__ready === true", timeout=30000)
    page.evaluate("document.fonts.ready")
    return browser, page


def render(
    ep: Episode,
    code: str,
    fps: int = 30,
    crf: int = 26,
    log: Callable[[str], None] = print,
) -> Path:
    from playwright.sync_api import sync_playwright

    ensure_built(ep, code)
    bdir = ep.build_dir(code)
    tl = _timeline(bdir)
    total = float(tl["duration"])
    frames = int(total * fps)
    out = ep.video(code)
    out.parent.mkdir(parents=True, exist_ok=True)
    audio = bdir / "narration.m4a" if tl.get("audio") else None
    args = [media.ffmpeg(), "-hide_banner", "-loglevel", "error", "-y"]
    args += ["-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(fps), "-i", "-"]
    if audio and audio.exists():
        args += ["-i", str(audio), "-c:a", "aac", "-b:a", "128k", "-shortest"]
    # JPEG frames are full-range; convert to the TV range every player expects, or colors look washed out.
    args += ["-vf", "scale=in_range=full:out_range=tv,format=yuv420p", "-color_range", "tv"]
    args += ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf)]
    args += ["-movflags", "+faststart", str(out)]
    log(f"render {ep.id} [{code}] {total:.1f}s × {fps}fps = {frames} frames")
    with sync_playwright() as p:
        browser, page = _open(p, page_url(ep, code))
        proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        assert proc.stdin is not None
        try:
            for i in range(frames):
                page.evaluate("t => window.__seek(t)", i / fps)
                proc.stdin.write(page.screenshot(type="jpeg", quality=92))
                if i and i % (fps * 20) == 0:
                    log(f"  {i / fps:.0f}s / {total:.0f}s")
        finally:
            proc.stdin.close()
            proc.wait()
            browser.close()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({proc.returncode}) for {out}")
    log(f"wrote {out}")
    return out


def stills(ep: Episode, code: str, marks: list[str], log: Callable[[str], None] = print) -> list[Path]:
    """Still frames for review. A mark is seconds (``42.5``) or ``section:seconds`` (``art1:3``)."""
    from playwright.sync_api import sync_playwright

    ensure_built(ep, code)
    bdir = ep.build_dir(code)
    tl = _timeline(bdir)
    starts = {s["id"]: float(s["t0"]) for s in tl["sections"]}
    out_dir = ep.out_dir() / "stills" / code
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with sync_playwright() as p:
        browser, page = _open(p, page_url(ep, code))
        for mark in marks:
            if ":" in mark:
                sid, sec = mark.split(":", 1)
                if sid not in starts:
                    raise KeyError(f"no section '{sid}' — sections: {', '.join(starts)}")
                t = starts[sid] + float(sec)
            else:
                t = float(mark)
            page.evaluate("t => window.__seek(t)", t)
            path = out_dir / f"{mark.replace(':', '_')}.png"
            page.screenshot(path=str(path))
            written.append(path)
            log(f"  still {path}")
        browser.close()
    return written


def _timeline(bdir: Path) -> dict[str, Any]:
    body = (bdir / "timeline.js").read_text(encoding="utf-8")
    return json.loads(body[body.index("{") : body.rindex("}") + 1])
