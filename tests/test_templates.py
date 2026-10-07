from pathlib import Path

import pytest
from explainer_lib import build, script
from explainer_lib.paths import ENGINE_DIR, Episode

SRC = """---
id: demo
lang: en
title: Demo
{template}---

## Cover {{#cover}}

```screen
type: cover
title: Hello
```

- Hello there.
"""


def _episode(tmp_path: Path, template_line: str = "") -> Episode:
    root = tmp_path / "demo"
    root.mkdir()
    (root / "script.en.md").write_text(SRC.format(template=template_line), encoding="utf-8")
    return Episode(root)


def test_four_templates_ship_and_each_has_a_description() -> None:
    names = build.templates()
    assert names == ["blueprint", "chalk", "midnight", "paper"]
    for n in names:
        first = (ENGINE_DIR / "themes" / f"{n}.css").read_text(encoding="utf-8").splitlines()[0]
        assert first.startswith(f"/* {n} — ")


def test_templates_never_animate() -> None:
    for css in [ENGINE_DIR / "explainer.css", *(ENGINE_DIR / "themes").glob("*.css")]:
        body = css.read_text(encoding="utf-8")
        assert "transition:" not in body and "animation:" not in body, css.name


def test_resolve_order_override_then_script_then_default() -> None:
    plain = script.parse(SRC.format(template=""))
    chosen = script.parse(SRC.format(template="template: paper\n"))
    assert build.resolve_template(plain, None) == "midnight"
    assert build.resolve_template(chosen, None) == "paper"
    assert build.resolve_template(chosen, "chalk") == "chalk"
    with pytest.raises(ValueError, match="unknown template 'neon'"):
        build.resolve_template(plain, "neon")


def test_built_page_loads_the_chosen_template(tmp_path: Path) -> None:
    ep = _episode(tmp_path, "template: blueprint\n")
    tl = build.build(ep, "en", engine="none", log=lambda _m: None)
    page = (ep.build_dir("en") / "index.html").read_text(encoding="utf-8")
    assert 'href="engine/themes/blueprint.css"' in page
    assert (ep.build_dir("en") / "engine" / "themes" / "blueprint.css").exists()
    assert tl["meta"]["template"] == "blueprint"
    assert ep.srt("en").exists()


def test_preview_build_leaves_the_real_build_alone(tmp_path: Path) -> None:
    ep = _episode(tmp_path)
    other = ep.root / "build" / "en@paper"
    build.build(ep, "en", engine="none", template="paper", out=other, log=lambda _m: None)
    assert (other / "index.html").exists()
    assert not ep.build_dir("en").exists()
    assert not ep.srt("en").exists()
