from pathlib import Path

import pytest
from explainer_lib import script

GOOD = """---
id: demo
lang: en
title: Demo
---

## Cover {#cover}

```screen
type: cover
title: Hello
```

- First line with **bold**.
- Second line. {say: Second line, read differently}

## Steps {#steps}

```screen
type: flow
steps:
  - {title: One, at: 0}
  - {title: "Two, with a comma", at: 1}
```

- Step one.
- Step two.
"""


def test_parses_sections_screens_and_lines() -> None:
    s = script.parse(GOOD)
    assert s.id == "demo" and s.lang == "en" and s.title == "Demo"
    assert [x.id for x in s.sections] == ["cover", "steps"]
    assert s.sections[0].screen == {"type": "cover", "title": "Hello"}
    assert s.sections[0].lines[0].text == "First line with **bold**."
    assert s.sections[0].lines[1].text == "Second line."
    assert s.sections[0].lines[1].say == "Second line, read differently"
    assert s.sections[1].screen["steps"][1]["title"] == "Two, with a comma"


def test_crlf_input_is_accepted() -> None:
    assert len(script.parse(GOOD.replace("\n", "\r\n")).sections) == 2


@pytest.mark.parametrize(
    ("broken", "message"),
    [
        (GOOD.replace("---\nid: demo", "id: demo", 1), "front-matter"),
        (GOOD.replace("id: demo\n", ""), "needs 'id'"),
        (GOOD.replace("type: cover\n", ""), "needs a 'type'"),
        (GOOD.replace("{#steps}", "{#cover}"), "used twice"),
        (GOOD.replace("- Step one.\n- Step two.\n", ""), "no narration"),
        (GOOD.replace("```\n\n- Step one.", "\n- Step one.", 1), "not closed"),
    ],
)
def test_errors_name_the_problem(broken: str, message: str) -> None:
    with pytest.raises(script.ScriptError, match=message):
        script.parse(broken)


def test_unquoted_comma_that_would_silently_cut_a_value_is_reported() -> None:
    # {title: Two, with a comma} parses without error as {"title": "Two", "with a comma": None}
    bad = GOOD.replace('title: "Two, with a comma"', "title: Two, with a comma")
    with pytest.raises(script.ScriptError, match="cut at a comma"):
        script.parse(bad)


def test_translation_shape_check() -> None:
    base = script.parse(GOOD)
    other = script.parse(GOOD.replace("lang: en", "lang: ko").replace("- Step two.\n", ""))
    problems = script.check_same_shape(base, other)
    assert problems == ["ko: section 'steps' has 1 lines, en has 2"]


def test_example_episode_languages_have_the_same_shape() -> None:
    ep = Path(__file__).resolve().parents[1] / "examples" / "kr-constitution-ch1"
    scripts = {p.name.split(".")[1]: script.load(p) for p in ep.glob("script.*.md")}
    assert set(scripts) == {"ko", "en", "ja", "zh", "es"}
    base = scripts["ko"]
    for code, s in scripts.items():
        assert s.lang == code
        assert script.check_same_shape(base, s) == []
