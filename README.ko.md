# explainer-studio

**문서나 git 저장소를 넣으면 낭독과 자막이 붙은 설명 영상이 나옵니다. 한국어·영어·일본어·중국어·스페인어를 지원합니다.**

Claude Code 스킬이자 일반 명령줄 도구입니다. 자료를 읽고, 사용자와 편 구성을 정하고, 대본을 쓰고, 음성을 합성하고, 장면을 움직여 MP4 와 SRT 로 만듭니다.

[English README](README.md)

## 예시

**대한민국 헌법 제1장 총강** — 대본 하나, 5개 언어:

| | 영상 | 자막 |
|---|---|---|
| 한국어 | [kr-constitution-ch1.ko.mp4](examples/kr-constitution-ch1/out/kr-constitution-ch1.ko.mp4) | [.srt](examples/kr-constitution-ch1/out/kr-constitution-ch1.ko.srt) |
| English | [kr-constitution-ch1.en.mp4](examples/kr-constitution-ch1/out/kr-constitution-ch1.en.mp4) | [.srt](examples/kr-constitution-ch1/out/kr-constitution-ch1.en.srt) |
| 日本語 | [kr-constitution-ch1.ja.mp4](examples/kr-constitution-ch1/out/kr-constitution-ch1.ja.mp4) | [.srt](examples/kr-constitution-ch1/out/kr-constitution-ch1.ja.srt) |
| 中文 | [kr-constitution-ch1.zh.mp4](examples/kr-constitution-ch1/out/kr-constitution-ch1.zh.mp4) | [.srt](examples/kr-constitution-ch1/out/kr-constitution-ch1.zh.srt) |
| Español | [kr-constitution-ch1.es.mp4](examples/kr-constitution-ch1/out/kr-constitution-ch1.es.mp4) | [.srt](examples/kr-constitution-ch1/out/kr-constitution-ch1.es.srt) |

대본 원본은 [examples/kr-constitution-ch1](examples/kr-constitution-ch1) 에 있습니다. 형식을 익히기에 좋습니다.

## 동작 방식

- **대본은 마크다운입니다.** 장마다 `screen` 블록(화면에 보일 것, YAML)과 낭독 줄(말할 것)이 있습니다. 번역할 때 코드는 건드리지 않습니다.
- **음성이 화면 시각을 정합니다.** 줄마다 음성을 먼저 만들어 길이를 재고, 화면 요소는 그 내용을 말하는 줄에 맞춰 나타납니다. 어느 언어에서도 마찬가지입니다.
- **렌더 결과가 늘 같습니다.** 장면은 시각 t 의 순수 함수라, 헤드리스 브라우저에서 한 프레임씩 넘기며 찍어 ffmpeg 로 묶습니다. 느린 PC 에서도 프레임이 빠지지 않고 시간만 더 걸립니다.

## 설치

Python 3.10 이상, 렌더용 Chromium 계열 브라우저, 기본 음성용 인터넷 연결이 필요합니다.

```bash
git clone https://github.com/lani319/explainer-studio.git
cd explainer-studio
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium                         # Chrome 이 설치돼 있으면 생략 가능
python skills/explainer/scripts/cli.py doctor --online
```

중국어·일본어는 CJK 글꼴이 필요합니다(Windows·macOS 는 기본 포함, Linux 는 `fonts-noto-cjk` 설치).

### Claude Code 에서 쓰기

플러그인으로 설치:

```
/plugin marketplace add lani319/explainer-studio
/plugin install explainer-studio@explainer-studio
```

또는 `skills/explainer` 폴더를 `~/.claude/skills/` 에 복사합니다. 그다음 이렇게 요청하면 됩니다.

> ./docs 의 문서로 신입 팀원용 3분짜리 설명 영상을 한국어와 영어로 만들어 줘.

Claude 가 환경을 점검하고, 자료 목록을 만들고, 편 구성을 제안해 승인을 받은 뒤, 대본 작성 → 빌드 → 정지 화면 검수 → 렌더까지 진행합니다.

### 직접 쓰기

```bash
S=skills/explainer/scripts/cli.py
python $S ingest https://github.com/you/your-repo.git --workspace explainer
python $S new explainer/intro --lang ko --title "이 프로젝트가 하는 일"
# explainer/intro/script.ko.md 편집
python $S build explainer/intro              # 음성·시각표·재생 페이지·.srt (build/ko/index.html 로 미리보기)
python $S stills explainer/intro --lang ko cover:3 overview:5
python $S render explainer/intro             # → explainer/intro/out/intro.ko.mp4
```

`--tts none` 은 인터넷 없이 시간을 추정한 무음 초안을 만듭니다. `--voice male` 은 남성 음성으로 바꿉니다.

## 참고

- **음성**: 기본 엔진은 [edge-tts](https://github.com/rany2/edge-tts) 로 Microsoft Edge 온라인 음성을 씁니다. 인터넷이 필요하고, 상업적으로 쓰기 전에는 서비스 약관을 확인하세요. 음성 엔진은 교체할 수 있습니다(`scripts/explainer_lib/tts.py`).
- **자료**: 사용·공유가 허락된 자료로만 영상을 만드세요. 영상의 마지막 장면에 출처가 표시됩니다.
- **현황**: 0.1 — 글 기반 설명 장면. 예정: 실행 중인 웹 앱의 화면 캡처 투어.

## 라이선스

아직 정하지 않았습니다. 라이선스 파일이 추가되기 전까지는 모든 권리를 보유합니다.
