"""Parse an episode script (``script.<lang>.md``).

Format::

    ---
    id: my-episode
    lang: en
    title: Episode title
    voice: female            # or male, or a full voice id
    theme: {accent: "#38bdf8"}
    sources: ["Where the facts come from"]
    ---

    ## Section title {#section-id}

    ```screen
    type: quote               # which scene layout draws this section (see references/scene-types.md)
    kicker: Article 1
    items: [...]
    ```

    - First narration line — shown as a subtitle and read aloud.
    - A line with **emphasis**. {say: what the narrator reads instead}

The screen block is free-form YAML handed to the scene; everything visible on screen comes from it,
so translating a script never touches code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_HEADING = re.compile(r"^##\s+(?P<title>.+?)\s*\{#(?P<id>[A-Za-z0-9_-]+)\}\s*$")
_SAY = re.compile(r"\s*\{say:\s*(?P<say>.+?)\}\s*$")


class ScriptError(ValueError):
    """A script that cannot be turned into a video — the message says which line and why."""


@dataclass
class Line:
    text: str  # subtitle (may contain **emphasis**)
    say: str | None = None  # narration override; None = read the subtitle


@dataclass
class Section:
    id: str
    title: str
    screen: dict[str, Any]
    lines: list[Line] = field(default_factory=list)


@dataclass
class Script:
    meta: dict[str, Any]
    sections: list[Section]

    @property
    def id(self) -> str:
        return str(self.meta["id"])

    @property
    def lang(self) -> str:
        return str(self.meta["lang"])

    @property
    def title(self) -> str:
        return str(self.meta.get("title", self.id))


def parse(text: str, source: str = "<script>") -> Script:
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ScriptError(f"{source}: must start with a '---' front-matter block")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ScriptError(f"{source}: front matter is not closed with '---'")
    meta = yaml.safe_load(text[4:end]) or {}
    for key in ("id", "lang"):
        if key not in meta:
            raise ScriptError(f"{source}: front matter needs '{key}'")

    sections: list[Section] = []
    cur: Section | None = None
    in_screen = False
    screen_buf: list[str] = []
    body = text[end + 5 :].split("\n")
    first_line_no = text[: end + 5].count("\n") + 1
    for offset, raw in enumerate(body):
        no = first_line_no + offset
        line = raw.rstrip()
        if in_screen:
            if line.strip() == "```":
                in_screen = False
                try:
                    data = yaml.safe_load("\n".join(screen_buf)) or {}
                except yaml.YAMLError as exc:
                    raise ScriptError(f"{source}:{no}: screen block is not valid YAML — {exc}") from exc
                if not isinstance(data, dict) or "type" not in data:
                    raise ScriptError(f"{source}:{no}: screen block needs a 'type'")
                split = _split_value(data)
                if split:
                    raise ScriptError(
                        f"{source}:{no}: '{split}' looks like the tail of a value cut at a comma — "
                        'quote values that contain commas: text: "a, b"'
                    )
                assert cur is not None
                cur.screen = data
                screen_buf = []
            else:
                screen_buf.append(raw)
            continue
        m = _HEADING.match(line)
        if m:
            cur = Section(id=m["id"], title=m["title"].strip(), screen={})
            sections.append(cur)
            continue
        if line.strip() == "```screen":
            if cur is None:
                raise ScriptError(f"{source}:{no}: screen block before any '## Title {{#id}}' heading")
            in_screen = True
            continue
        if line.startswith("- "):
            if cur is None:
                raise ScriptError(f"{source}:{no}: narration line before any section heading")
            content = line[2:].strip()
            say = None
            sm = _SAY.search(content)
            if sm:
                say = sm["say"].strip()
                content = content[: sm.start()].rstrip()
            cur.lines.append(Line(text=content, say=say))
    if in_screen:
        raise ScriptError(f"{source}: a screen block is not closed")
    if not sections:
        raise ScriptError(f"{source}: no sections — add '## Title {{#id}}' headings")
    seen: set[str] = set()
    for s in sections:
        if s.id in seen:
            raise ScriptError(f"{source}: section id '{s.id}' is used twice")
        seen.add(s.id)
        if not s.screen:
            raise ScriptError(f"{source}: section '{s.id}' has no screen block")
        if not s.lines:
            raise ScriptError(f"{source}: section '{s.id}' has no narration lines")
    return Script(meta=meta, sections=sections)


def _split_value(node: Any) -> str | None:
    """In YAML flow style ``{text: a, b}`` silently becomes ``{text: "a", "b": None}`` — the text loses its tail.
    Catch it: a key with spaces and no value is almost always such a tail."""
    if isinstance(node, dict):
        for k, v in node.items():
            if v is None and isinstance(k, str) and " " in k.strip():
                return k
            found = _split_value(v)
            if found:
                return found
    elif isinstance(node, list):
        for v in node:
            found = _split_value(v)
            if found:
                return found
    return None


def load(path: Path) -> Script:
    return parse(path.read_text(encoding="utf-8"), source=str(path))


def check_same_shape(base: Script, other: Script) -> list[str]:
    """Translations must keep the same sections and line counts so scenes reveal things on the same cues."""
    problems: list[str] = []
    a = [(s.id, len(s.lines)) for s in base.sections]
    b = [(s.id, len(s.lines)) for s in other.sections]
    if [x[0] for x in a] != [x[0] for x in b]:
        problems.append(f"{other.lang}: section ids differ from {base.lang}")
    else:
        for (sid, n1), (_, n2) in zip(a, b, strict=True):
            if n1 != n2:
                problems.append(f"{other.lang}: section '{sid}' has {n2} lines, {base.lang} has {n1}")
    return problems
