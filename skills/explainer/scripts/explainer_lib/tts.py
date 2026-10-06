"""Speech synthesis. Every line becomes one clip; clips are cached by (engine, voice, rate, text).

Engines are pluggable — add a function to ``ENGINES``. ``edge`` uses the Microsoft Edge online voices
(needs internet; check their terms before commercial use). ``none`` synthesizes nothing and estimates timing,
which is enough to draft and preview a video offline.
"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Callable
from pathlib import Path

from . import media
from .lang import Lang
from .paths import cache_dir
from .script import Script
from .timeline import estimate


def _edge(text: str, voice: str, rate: str, out: Path) -> None:
    import edge_tts

    async def run() -> None:
        await edge_tts.Communicate(text, voice, rate=rate).save(str(out))

    for attempt in range(3):
        try:
            asyncio.run(run())
            return
        except Exception:  # noqa: BLE001 — the online service drops connections now and then
            if attempt == 2:
                raise


ENGINES: dict[str, Callable[[str, str, str, Path], None]] = {"edge": _edge}


def synthesize(
    script: Script, lang: Lang, engine: str = "edge", voice: str | None = None, log: Callable[[str], None] = print
) -> tuple[list[list[float]], list[list[Path | None]]]:
    """Return per-line durations and clip paths (paths are None for engine ``none``)."""
    durations: list[list[float]] = []
    clips: list[list[Path | None]] = []
    v = lang.voice(voice or script.meta.get("voice"))
    if engine != "none" and engine not in ENGINES:
        raise ValueError(f"unknown TTS engine '{engine}' — choose {', '.join([*ENGINES, 'none'])}")
    store = cache_dir() / "tts"
    store.mkdir(exist_ok=True)
    for sec in script.sections:
        ds: list[float] = []
        cs: list[Path | None] = []
        for line in sec.lines:
            spoken = lang.spoken(line.say or line.text)
            if engine == "none":
                ds.append(estimate(spoken, lang))
                cs.append(None)
                continue
            key = hashlib.sha1(f"{engine}|{v}|{lang.rate}|{spoken}".encode()).hexdigest()[:20]
            clip = store / f"{key}.mp3"
            if not clip.exists() or clip.stat().st_size == 0:
                log(f"  tts {sec.id}: {spoken[:50]}")
                ENGINES[engine](spoken, v, lang.rate, clip)
            ds.append(media.duration(clip))
            cs.append(clip)
        durations.append(ds)
        clips.append(cs)
    return durations, clips
