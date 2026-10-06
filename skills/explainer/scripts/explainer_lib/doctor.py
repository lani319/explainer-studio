"""Check the machine can build and render: Python packages, ffmpeg, a headless browser, the TTS service."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable


def run(online: bool = False, log: Callable[[str], None] = print) -> bool:
    ok = True

    def check(name: str, fn: Callable[[], str]) -> None:
        nonlocal ok
        try:
            log(f"  ok   {name}: {fn()}")
        except Exception as exc:  # noqa: BLE001 — report every failure, don't stop at the first
            ok = False
            log(f"  FAIL {name}: {exc}")

    check("python", lambda: sys.version.split()[0] if sys.version_info >= (3, 10) else _fail("needs 3.10+"))
    for mod in ("yaml", "edge_tts", "playwright", "imageio_ffmpeg"):
        check(mod, lambda m=mod: getattr(importlib.import_module(m), "__version__", "installed"))
    check("ffmpeg", _ffmpeg)
    check("browser", _browser)
    if online:
        check("tts (edge, online)", _tts)
    log("ready" if ok else "fix the FAIL lines — see README 'Install'")
    return ok


def _fail(msg: str) -> str:
    raise RuntimeError(msg)


def _ffmpeg() -> str:
    from . import media

    return media.ffmpeg()


def _browser() -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
            kind = "bundled chromium"
        except Exception:  # noqa: BLE001
            b = p.chromium.launch(channel="chrome")
            kind = "installed chrome"
        version = b.version
        b.close()
    return f"{kind} {version}"


def _tts() -> str:
    import tempfile
    from pathlib import Path

    from . import media
    from .tts import ENGINES

    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "t.mp3"
        ENGINES["edge"]("Hello.", "en-US-JennyNeural", "+0%", out)
        return f"{media.duration(out):.2f}s sample"
