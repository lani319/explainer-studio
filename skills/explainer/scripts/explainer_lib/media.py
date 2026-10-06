"""ffmpeg helpers — measure audio and assemble the narration track."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def duration(path: Path) -> float:
    """Length of a media file in seconds (decodes the stream, so it is exact for mp3)."""
    proc = subprocess.run(
        [ffmpeg(), "-hide_banner", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    times = re.findall(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
    if not times:
        m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
        if not m:
            raise RuntimeError(f"cannot read duration of {path}")
        times = [m.groups()]
    h, m_, s = times[-1]
    return int(h) * 3600 + int(m_) * 60 + float(s)


def narration_track(clips: list[tuple[float, Path]], total: float, out: Path) -> None:
    """Place each clip at its start time on a silent track of ``total`` seconds (AAC in .m4a)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    args = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y"]
    for _, clip in clips:
        args += ["-i", str(clip)]
    parts = []
    for i, (t0, _) in enumerate(clips):
        ms = int(round(t0 * 1000))
        parts.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=mono,adelay={ms}:all=1[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(clips)))
    graph = ";".join(parts) + f";{mix}amix=inputs={len(clips)}:normalize=0:dropout_transition=0,apad[out]"
    args += [
        "-filter_complex",
        graph,
        "-map",
        "[out]",
        "-t",
        f"{total:.3f}",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(out),
    ]
    subprocess.run(args, check=True)
