"""Connect source material: a local folder/file or a git URL → an inventory the author (or Claude) reads from.

Writes ``<workspace>/_sources/inventory.md`` (one row per readable file, with its first heading) and
``inventory.json``. Nothing is summarized here — reading and judging the material is the author's job.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

TEXT_EXT = {
    ".md", ".mdx", ".txt", ".rst", ".adoc", ".html", ".htm", ".csv", ".json", ".yaml", ".yml", ".toml",
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt", ".cs", ".c", ".h", ".cpp", ".rb",
    ".php", ".swift", ".sql", ".sh", ".ps1", ".ipynb",
}  # fmt: skip
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".next", "target", "vendor"}
MAX_BYTES = 400_000


def is_git_url(src: str) -> bool:
    return src.startswith(("http://", "https://", "git@")) and (src.endswith(".git") or "github.com" in src)


def fetch(src: str, workspace: Path, log: Callable[[str], None] = print) -> Path:
    """Return a local path for ``src`` — cloning git URLs (shallow) into ``<workspace>/_sources/repos``."""
    if not is_git_url(src):
        p = Path(src).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(src)
        return p
    name = re.sub(r"\.git$", "", src.rstrip("/").split("/")[-1])
    dest = workspace / "_sources" / "repos" / name
    if dest.exists():
        log(f"using existing clone {dest} (delete it to re-clone)")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    log(f"cloning {src} …")
    subprocess.run(["git", "clone", "--depth", "1", src, str(dest)], check=True)
    return dest


def inventory(root: Path) -> list[dict[str, Any]]:
    files = [root] if root.is_file() else sorted(_walk(root))
    rows: list[dict[str, Any]] = []
    for f in files:
        if f.suffix.lower() not in TEXT_EXT:
            continue
        size = f.stat().st_size
        if size > MAX_BYTES:
            rows.append({"path": _rel(f, root), "bytes": size, "lines": None, "heading": "(too large — skim only)"})
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rows.append({"path": _rel(f, root), "bytes": size, "lines": text.count("\n") + 1, "heading": _heading(text)})
    return rows


def run(src: str, workspace: Path, log: Callable[[str], None] = print) -> Path:
    root = fetch(src, workspace, log)
    rows = inventory(root)
    out = workspace / "_sources"
    out.mkdir(parents=True, exist_ok=True)
    (out / "inventory.json").write_text(
        json.dumps({"source": src, "root": str(root), "files": rows}, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    md = [f"# Source inventory\n\n- source: `{src}`\n- local root: `{root}`\n- readable files: {len(rows)}\n"]
    md.append("| file | lines | first heading |\n|---|---:|---|")
    md += [f"| `{r['path']}` | {r['lines'] or ''} | {r['heading']} |" for r in rows]
    (out / "inventory.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    log(f"{len(rows)} readable files → {out / 'inventory.md'}")
    return out / "inventory.md"


def _walk(root: Path):  # noqa: ANN202 — generator of Paths
    for p in root.rglob("*"):
        if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            yield p


def _rel(f: Path, root: Path) -> str:
    return f.name if root.is_file() else f.relative_to(root).as_posix()


def _heading(text: str) -> str:
    for line in text.splitlines()[:80]:
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()[:80]
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    return first[:80]
