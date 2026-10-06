"""explainer-studio command line.

python cli.py doctor [--online]
python cli.py ingest <folder|file|git-url> --workspace explainer
python cli.py new <workspace>/<episode-id> --lang en [--title "..."]
python cli.py build <episode-dir> [--lang en,ko | all] [--tts edge|none] [--voice female|male|<id>]
python cli.py render <episode-dir> [--lang ...] [--fps 30] [--crf 26]
python cli.py stills <episode-dir> --lang en cover:2 art1:4 63.5
python cli.py all <episode-dir> [--lang ...]          # build + render
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from explainer_lib import build, doctor, ingest, render  # noqa: E402
from explainer_lib.lang import SUPPORTED  # noqa: E402
from explainer_lib.paths import TEMPLATE_DIR, Episode  # noqa: E402


def _langs(ep: Episode, arg: str | None) -> list[str]:
    have = ep.languages()
    if not have:
        raise SystemExit(f"no script.<lang>.md in {ep.root}")
    if not arg or arg == "all":
        return have
    want = [x.strip() for x in arg.split(",") if x.strip()]
    missing = [x for x in want if x not in have]
    if missing:
        raise SystemExit(f"no script for {', '.join(missing)} in {ep.root} (have: {', '.join(have)})")
    return want


def _new(target: Path, lang: str, title: str | None) -> None:
    if lang not in SUPPORTED:
        raise SystemExit(f"--lang must be one of {', '.join(SUPPORTED)}")
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"script.{lang}.md"
    if path.exists():
        raise SystemExit(f"{path} already exists")
    body = (TEMPLATE_DIR / "script.md").read_text(encoding="utf-8")
    body = body.replace("{{id}}", target.name).replace("{{lang}}", lang).replace("{{title}}", title or target.name)
    path.write_text(body, encoding="utf-8")
    print(f"created {path}")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    ap = argparse.ArgumentParser(prog="explainer", description="Narrated explainer videos from your material.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("doctor", help="check dependencies")
    d.add_argument("--online", action="store_true", help="also synthesize a test phrase")
    g = sub.add_parser("ingest", help="inventory a folder, file or git repository")
    g.add_argument("source")
    g.add_argument("--workspace", default="explainer")
    n = sub.add_parser("new", help="start an episode script from the template")
    n.add_argument("episode")
    n.add_argument("--lang", required=True)
    n.add_argument("--title")
    for name in ("build", "render", "stills", "all"):
        s = sub.add_parser(name)
        s.add_argument("episode")
        s.add_argument("--lang", help="comma list or 'all' (default: every script present)")
        if name in ("build", "all"):
            s.add_argument("--tts", default="edge", help="edge (default) or none (estimate timing, silent)")
            s.add_argument("--voice", help="female | male | full voice id")
        if name in ("render", "all"):
            s.add_argument("--fps", type=int, default=30)
            s.add_argument("--crf", type=int, default=26, help="x264 quality (lower = bigger, sharper)")
        if name == "stills":
            s.add_argument("marks", nargs="+", help="seconds or section:seconds")
    a = ap.parse_args(argv)

    if a.cmd == "doctor":
        return 0 if doctor.run(online=a.online) else 1
    if a.cmd == "ingest":
        ingest.run(a.source, Path(a.workspace))
        return 0
    if a.cmd == "new":
        _new(Path(a.episode), a.lang, a.title)
        return 0
    ep = Episode(Path(a.episode).resolve())
    langs = _langs(ep, a.lang)
    if a.cmd == "stills":
        if len(langs) != 1:
            raise SystemExit("stills: pass exactly one --lang")
        render.stills(ep, langs[0], a.marks)
        return 0
    for code in langs:
        if a.cmd in ("build", "all"):
            build.build(ep, code, engine=a.tts, voice=a.voice)
        if a.cmd in ("render", "all"):
            render.render(ep, code, fps=a.fps, crf=a.crf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
