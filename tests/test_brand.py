from pathlib import Path

import pytest
from explainer_lib import brand, build
from explainer_lib.paths import ENGINE_DIR, Episode


def test_token_list_comes_from_the_engine_stylesheet() -> None:
    t = brand.tokens()
    for name in ("bg", "fg", "accent", "sub-bg", "sub-fg", "heading-font", "logo-height"):
        assert name in t


def test_theme_accepts_any_token_with_dash_or_underscore(tmp_path: Path) -> None:
    b = brand.parse_theme({"accent": "#e4572e", "sub_bg": "#000", "--radius": "4px"}, tmp_path)
    assert b.vars == {"--accent": "#e4572e", "--sub-bg": "#000", "--radius": "4px"}


def test_unknown_theme_key_stops_with_a_hint(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown token 'accnt'"):
        brand.parse_theme({"accnt": "#fff"}, tmp_path)
    with pytest.raises(ValueError, match="did you mean"):
        brand.parse_theme({"sub-color": "#fff"}, tmp_path)


def test_missing_logo_or_font_file_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="theme.logo: file not found"):
        brand.parse_theme({"logo": "nope.svg"}, tmp_path)
    with pytest.raises(ValueError, match="needs 'family' and 'file'"):
        brand.parse_theme({"fonts": [{"file": "x.woff2"}]}, tmp_path)


@pytest.mark.parametrize("name", build.templates())
def test_built_in_templates_pass_the_contrast_check(name: str) -> None:
    layers = [brand.tokens(), brand.css_tokens(ENGINE_DIR / "themes" / f"{name}.css")]
    assert brand.contrast_warnings(layers) == []


def test_contrast_check_flags_unreadable_subtitles_and_composites_alpha() -> None:
    base = brand.tokens()
    bad = brand.contrast_warnings([base, {"sub-fg": "#94a3b8", "sub-bg": "rgba(255, 255, 255, 0.95)"}])
    assert len(bad) == 1 and "subtitles" in bad[0] and "needs 4.5:1" in bad[0]
    # a translucent dark box over a light page is light — light text on it must be flagged
    light_page = brand.contrast_warnings([base, {"bg": "#ffffff", "sub-bg": "rgba(0,0,0,0.1)", "sub-fg": "#ffffff"}])
    assert any("subtitles" in w for w in light_page)


def test_contrast_check_skips_what_it_cannot_parse() -> None:
    assert brand.contrast_warnings([brand.tokens(), {"card": "linear-gradient(red, blue)"}]) == []


def test_copy_template_brings_its_assets_and_refuses_outside_paths(tmp_path: Path) -> None:
    src_dir = tmp_path / "brand"
    (src_dir / "img").mkdir(parents=True)
    (src_dir / "img" / "bg.png").write_bytes(b"png")
    css = src_dir / "brand.css"
    css.write_text(':root { --texture: url("img/bg.png"); }', encoding="utf-8")
    out = tmp_path / "out"
    assert brand.copy_template(css, out) == "brand/brand.css"
    assert (out / "brand" / "img" / "bg.png").read_bytes() == b"png"
    (tmp_path / "secret.png").write_bytes(b"x")
    css.write_text(':root { --texture: url("../secret.png"); }', encoding="utf-8")
    with pytest.raises(ValueError, match="outside the template folder"):
        brand.copy_template(css, tmp_path / "out2")


def test_logo_and_fonts_are_shipped(tmp_path: Path) -> None:
    (tmp_path / "logo.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path / "Brand.woff2").write_bytes(b"font")
    b = brand.parse_theme(
        {"logo": "logo.svg", "font": "Brand", "fonts": [{"family": "Brand", "file": "Brand.woff2", "weight": 700}]},
        tmp_path,
    )
    logo, fonts = brand.ship_assets(b, tmp_path / "out")
    assert logo == "assets/logo.svg" and (tmp_path / "out" / logo).exists()
    face = (tmp_path / "out" / "assets" / "fonts.css").read_text(encoding="utf-8")
    assert 'font-family: "Brand"' in face and 'url("fonts/Brand.woff2")' in face and "font-weight: 700" in face
    assert fonts == "assets/fonts.css"


SCRIPT = """---
id: demo
lang: en
title: Demo
template: ../brand/brand.css
theme:
  logo: ../brand/logo.svg
  font: Brand Sans
---

## Cover {#cover}

```screen
type: cover
title: Hello
```

- Hello there.
"""


def test_build_with_own_template_logo_and_font(tmp_path: Path) -> None:
    brand_dir = tmp_path / "eps" / "brand"  # the script points at ../brand from eps/demo
    brand_dir.mkdir(parents=True)
    (brand_dir / "brand.css").write_text("/* acme */\n:root { --accent: #0f766e; }\n", encoding="utf-8")
    (brand_dir / "logo.svg").write_text("<svg/>", encoding="utf-8")
    root = tmp_path / "eps" / "demo"
    root.mkdir(parents=True)
    (root / "script.en.md").write_text(SCRIPT, encoding="utf-8")
    ep = Episode(root)
    tl = build.build(ep, "en", engine="none", log=lambda _m: None)
    page = (ep.build_dir("en") / "index.html").read_text(encoding="utf-8")
    assert 'href="brand/brand.css"' in page
    assert (ep.build_dir("en") / "brand" / "brand.css").exists()
    assert tl["meta"]["logo"] == "assets/logo.svg"
    assert tl["meta"]["font"].startswith('"Brand Sans", ')
    assert tl["meta"]["template"] == "brand"


def test_missing_template_file_is_an_error(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    root.mkdir()
    (root / "script.en.md").write_text(SCRIPT, encoding="utf-8")
    with pytest.raises(ValueError, match="template file not found"):
        build.build(Episode(root), "en", engine="none", log=lambda _m: None)
