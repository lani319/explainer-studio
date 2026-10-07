"""Bring the user's design: a template CSS file of their own, token overrides, a logo, font files —
and check that the resulting colors are still readable.

Tokens are the custom properties declared in ``engine/explainer.css`` (``:root``). A template file redefines
some of them; ``theme:`` in a script overrides single ones on top::

    template: ./brand/brand.css              # a built-in name, or a path relative to the episode folder
    theme:
      accent: "#e4572e"                      # any token, without the leading --  (- or _ both fine)
      sub-bg: "rgba(0, 0, 0, 0.8)"
      logo: ./brand/logo.svg                 # shown top-right and on the cover
      font: "Brand Sans"                     # put in front of the language's font stack
      fonts:                                 # font files to ship with the page
        - {family: Brand Sans, file: ./brand/BrandSans-Regular.woff2, weight: 400}
        - {family: Brand Sans, file: ./brand/BrandSans-Bold.woff2, weight: 800}
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .paths import ENGINE_DIR

SPECIAL = {"logo", "font", "fonts"}
_DECL = re.compile(r"--([a-z0-9-]+)\s*:\s*([^;]+);", re.S)
_URL = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)")


def tokens() -> dict[str, str]:
    """Token name → default value, from the engine's base stylesheet."""
    css = (ENGINE_DIR / "explainer.css").read_text(encoding="utf-8")
    root = css[css.index(":root") : css.index("}", css.index(":root"))]
    return {m[1]: " ".join(m[2].split()) for m in _DECL.finditer(root)}


def css_tokens(path: Path) -> dict[str, str]:
    """Tokens a template file sets in its ``:root`` blocks."""
    css = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
    out: dict[str, str] = {}
    for block in re.findall(r":root\s*\{(.*?)\}", css, flags=re.S):
        out.update({m[1]: " ".join(m[2].split()) for m in _DECL.finditer(block)})
    return out


@dataclass
class Brand:
    vars: dict[str, str] = field(default_factory=dict)  # "--accent" → value, applied inline by the player
    font: str | None = None
    logo: Path | None = None
    fonts: list[dict[str, Any]] = field(default_factory=list)


def parse_theme(theme: Any, base: Path) -> Brand:
    """Validate ``theme:`` from a script. Unknown keys and missing files are errors, never silently ignored."""
    if not theme:
        return Brand()
    if not isinstance(theme, dict):
        raise ValueError('theme: must be a mapping, e.g. {accent: "#e4572e"}')
    known = tokens()
    b = Brand()
    for raw_key, value in theme.items():
        key = str(raw_key).strip().lstrip("-").replace("_", "-")
        if key == "logo":
            b.logo = _file(base, value, "theme.logo")
        elif key == "font":
            b.font = str(value)
        elif key == "fonts":
            for f in value or []:
                if not isinstance(f, dict) or "family" not in f or "file" not in f:
                    raise ValueError("theme.fonts: each entry needs 'family' and 'file'")
                b.fonts.append({**f, "file": _file(base, f["file"], "theme.fonts")})
        elif key in known:
            b.vars[f"--{key}"] = str(value)
        else:
            close = [k for k in known if key.split("-")[0] in k][:6]
            hint = f" — did you mean {', '.join(close)}?" if close else ""
            raise ValueError(f"theme: unknown token '{raw_key}'{hint} (all tokens: references/templates.md)")
    return b


def _file(base: Path, value: Any, what: str) -> Path:
    p = Path(str(value))
    p = p if p.is_absolute() else (base / p)
    if not p.is_file():
        raise ValueError(f"{what}: file not found — {p}")
    return p.resolve()


def is_path(template: str) -> bool:
    return template.endswith(".css") or "/" in template or "\\" in template


def copy_template(src: Path, out: Path) -> str:
    """Copy a user's template and every file its ``url(...)`` points to; return the href for the page."""
    dest = out / "brand"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest / src.name)
    for ref in _URL.findall(src.read_text(encoding="utf-8")):
        if re.match(r"^(data:|https?:|/)", ref):
            continue
        asset = (src.parent / ref).resolve()
        if not asset.is_file():
            raise ValueError(f"{src.name}: url({ref}) not found — {asset}")
        target = (dest / ref).resolve()
        if dest.resolve() not in target.parents:
            raise ValueError(f"{src.name}: url({ref}) points outside the template folder — keep assets beside it")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset, target)
    return f"brand/{src.name}"


def ship_assets(b: Brand, out: Path) -> tuple[str | None, str | None]:
    """Copy logo and font files into the build; return (logo href, fonts.css href)."""
    assets = out / "assets"
    logo_href = None
    if b.logo:
        assets.mkdir(parents=True, exist_ok=True)
        shutil.copy2(b.logo, assets / f"logo{b.logo.suffix.lower()}")
        logo_href = f"assets/logo{b.logo.suffix.lower()}"
    fonts_href = None
    if b.fonts:
        (assets / "fonts").mkdir(parents=True, exist_ok=True)
        faces = []
        for f in b.fonts:
            src: Path = f["file"]
            shutil.copy2(src, assets / "fonts" / src.name)
            faces.append(
                "@font-face {"
                f' font-family: "{f["family"]}"; src: url("fonts/{src.name}");'
                f" font-weight: {f.get('weight', 400)}; font-style: {f.get('style', 'normal')}; font-display: block; }}"
            )
        (assets / "fonts.css").write_text("\n".join(faces) + "\n", encoding="utf-8")
        fonts_href = "assets/fonts.css"
    return logo_href, fonts_href


# ---------- contrast ----------

# (foreground token, background token, minimum ratio, what it is)
PAIRS = [
    ("fg", "bg", 4.5, "main text on the background"),
    ("fg", "card", 4.5, "main text on cards"),
    ("muted", "bg", 3.0, "secondary text on the background"),
    ("sub-fg", "sub-bg", 4.5, "subtitles"),
    ("on-accent", "accent", 3.0, "numbers and labels on accent badges"),
    ("accent", "bg", 3.0, "accent text (kickers, emphasis) on the background"),
]


def contrast_warnings(layers: list[dict[str, str]]) -> list[str]:
    """Resolve the token layers (base → template → theme) and check readability. Unparsable values
    (gradients, unknown functions) are skipped, not guessed."""
    merged: dict[str, str] = {}
    for layer in layers:
        merged.update({k.lstrip("-"): v for k, v in layer.items()})
    page = _color(_resolve("bg", merged)) or (0.0, 0.0, 0.0, 1.0)
    out = []
    for fg_name, bg_name, need, what in PAIRS:
        bg = _color(_resolve(bg_name, merged))
        fg = _color(_resolve(fg_name, merged))
        if not bg or not fg:
            continue
        bg_s = _over(bg, page)
        ratio = _ratio(_over(fg, bg_s), bg_s)
        if ratio < need:
            out.append(f"low contrast {ratio:.1f}:1 (needs {need}:1) — {what}: --{fg_name} on --{bg_name}")
    return out


def _resolve(name: str, merged: dict[str, str], depth: int = 0) -> str:
    v = merged.get(name, "")
    m = re.fullmatch(r"var\(--([a-z0-9-]+)\)", v.strip())
    if m and depth < 10:
        return _resolve(m[1], merged, depth + 1)
    return v


def _color(v: str) -> tuple[float, float, float, float] | None:
    v = v.strip().lower()
    if v in ("white", "black"):
        return (255.0, 255.0, 255.0, 1.0) if v == "white" else (0.0, 0.0, 0.0, 1.0)
    m = re.fullmatch(r"#([0-9a-f]{3,8})", v)
    if m:
        h = m[1]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (float(int(h[0:2], 16)), float(int(h[2:4], 16)), float(int(h[4:6], 16)), a)
    m = re.fullmatch(r"rgba?\(([^)]+)\)", v)
    if m:
        parts = [p.strip() for p in re.split(r"[,/\s]+", m[1]) if p.strip()]
        try:
            r, g, b = (float(x) for x in parts[:3])
            a = float(parts[3].rstrip("%")) / (100 if parts[3].endswith("%") else 1) if len(parts) > 3 else 1.0
        except ValueError:
            return None
        return (r, g, b, a)
    return None


def _over(c: tuple[float, float, float, float], under: tuple[float, float, float, float]) -> tuple[float, ...]:
    a = c[3]
    return (c[0] * a + under[0] * (1 - a), c[1] * a + under[1] * (1 - a), c[2] * a + under[2] * (1 - a), 1.0)


def _lum(c: tuple[float, ...]) -> float:
    def ch(x: float) -> float:
        x /= 255
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4

    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def _ratio(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)
