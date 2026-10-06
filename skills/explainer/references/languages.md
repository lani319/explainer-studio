# Languages

Settings live in `lang/<code>.yaml`: voices, pause between lines (`gap`), a speaking-rate estimate (`cps`, used offline), wrapping (`wrap: word | char`, `screen_width` for on-screen subtitles, `srt_width` for the .srt file), font stack, UI words and `say` rules (regex → replacement, applied to narration only).

| code | voices (female / male) | wrapping | font stack (first available wins) |
|---|---|---|---|
| ko | ko-KR-SunHiNeural / InJoonNeural | words, `keep-all` | Pretendard, Malgun Gothic, Apple SD Gothic Neo, Noto Sans KR |
| en | en-US-JennyNeural / GuyNeural | words | Inter, Segoe UI, Helvetica Neue, Arial |
| ja | ja-JP-NanamiNeural / KeitaNeural | characters (a line never starts with closing punctuation) | Yu Gothic, Meiryo, Hiragino Sans, Noto Sans JP |
| zh | zh-CN-XiaoxiaoNeural / YunxiNeural | characters | Microsoft YaHei, PingFang SC, Noto Sans SC |
| es | es-ES-ElviraNeural / AlvaroNeural | words | Inter, Segoe UI, Helvetica Neue, Arial |

## Writing for each language

- **Length differs.** The same content ran about 25% longer in Japanese than in Chinese in the example episode. Timing follows the speech, so nothing breaks — but keep lines short in the longer languages.
- **Chinese and Japanese share characters but not glyphs.** The page sets `lang` (`zh-CN`, `ja`) so the browser picks the right forms; make sure a CJK font from the stack is installed (Linux: `fonts-noto-cjk`). Missing fonts show as empty boxes — check stills.
- **Numbers and symbols** are read literally. Add `{say: ...}` for anything the narrator should read differently (part numbers, version strings, formulas).
- **Translations are yours.** Mark them unofficial on screen (`note:`) when the source has an official text in another language.

## Adding a language

Copy the closest YAML to `lang/<code>.yaml`, change the voices (list them with `edge-tts --list-voices`), wrapping, font and UI words, and add the code to `SUPPORTED` in `scripts/explainer_lib/lang.py`.
