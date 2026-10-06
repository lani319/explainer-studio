import pytest
from explainer_lib import lang


@pytest.mark.parametrize("code", lang.SUPPORTED)
def test_every_language_loads_with_two_voices(code: str) -> None:
    L = lang.load(code)
    assert L.code == code
    assert set(L.voices) >= {"female", "male"}
    assert L.voice(None) == L.voices["female"]
    assert L.voice("male") == L.voices["male"]
    assert L.voice("xx-XX-CustomNeural") == "xx-XX-CustomNeural"


def test_unknown_language_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported language"):
        lang.load("fr")


def test_spoken_strips_emphasis_and_applies_rules() -> None:
    ko = lang.load("ko")
    assert ko.spoken("제1조 ① **민주공화국**") == "제1조 1항 민주공화국"
    en = lang.load("en")
    assert en.spoken("plan → build") == "plan, then build"


def test_word_wrap_keeps_words_and_balances_two_lines() -> None:
    en = lang.load("en")
    lines = en.wrap_lines("one two three four five six seven eight nine ten", width=30)
    assert len(lines) == 2
    assert all(len(x) <= 30 for x in lines)
    assert " ".join(lines) == "one two three four five six seven eight nine ten"
    assert abs(len(lines[0]) - len(lines[1])) <= 10


def test_char_wrap_never_starts_a_line_with_closing_punctuation() -> None:
    ja = lang.load("ja")
    text = "あ" * 10 + "。" + "い" * 5
    lines = ja.wrap_lines(text, width=10)
    assert all(not ln.startswith("。") for ln in lines)
    assert "".join(lines) == text


def test_short_text_is_one_line() -> None:
    assert lang.load("zh").wrap_lines("你好") == ["你好"]
