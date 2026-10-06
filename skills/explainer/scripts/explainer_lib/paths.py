"""Where things live: the skill's own assets and a user's episode workspace."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
ENGINE_DIR = SKILL_DIR / "engine"
LANG_DIR = SKILL_DIR / "lang"
TEMPLATE_DIR = SKILL_DIR / "templates"


@dataclass(frozen=True)
class Episode:
    """One episode folder: ``<root>/<id>/script.<lang>.md`` plus generated ``build/`` and ``out/``."""

    root: Path

    @property
    def id(self) -> str:
        return self.root.name

    def script(self, lang: str) -> Path:
        return self.root / f"script.{lang}.md"

    def build_dir(self, lang: str) -> Path:
        return self.root / "build" / lang

    def out_dir(self) -> Path:
        return self.root / "out"

    def video(self, lang: str) -> Path:
        return self.out_dir() / f"{self.id}.{lang}.mp4"

    def srt(self, lang: str) -> Path:
        return self.out_dir() / f"{self.id}.{lang}.srt"

    def languages(self) -> list[str]:
        """Languages that have a script file, in a stable order."""
        return sorted(p.name.split(".")[1] for p in self.root.glob("script.*.md"))


def cache_dir() -> Path:
    """Shared cache for synthesized speech, so re-renders don't call the TTS service again."""
    d = Path.home() / ".cache" / "explainer-studio"
    d.mkdir(parents=True, exist_ok=True)
    return d
