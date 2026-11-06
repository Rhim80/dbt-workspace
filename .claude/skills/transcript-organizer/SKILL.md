---
name: transcript-organizer
description: |
  긴 녹음 텍스트 파일(강의, 미팅, 인터뷰)을 끝까지 읽고 구조화된 문서로 정리.
  "녹음 정리", "강의 정리", "미팅록", "인터뷰 정리", "txt 파일 분석", "트랜스크립트" 등 언급 시 자동 실행.
  인코딩 확인(UTF-16·CP949→UTF-8), 음성인식 오인식 교정, 저장까지. 임의로 줄이지 않고 원문 인용을 근거로 남긴다.
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
---

# Transcript Organizer

이미 글로 받아쓴 긴 녹음 파일을 정리된 문서로 만든다. 음성을 글로 바꾸는 일은 이 스킬이 아니다.

## 1. 파일 열기 — 인코딩부터

글자가 깨져 보이거나 Read가 이상하게 읽으면 파이썬으로 인코딩을 확인하고 UTF-8 사본을 만든다. 사본은 원본 옆에 `<이름>-utf8.txt`로 둔다(`/tmp`는 윈도우에서 도구마다 다른 곳을 가리키므로 쓰지 않는다).

```bash
python3 - "<파일 경로>" <<'EOF'   # 윈도우는 python
import sys, pathlib
p = pathlib.Path(sys.argv[1]); raw = p.read_bytes()
# UTF-16은 파일 맨 앞 표시(BOM)가 있을 때만 — 없이 시도하면 CP949 파일도 엉뚱하게 읽힌다
encs = ("utf-16",) if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else ("utf-8-sig", "cp949")
for enc in encs:
    try:
        text = raw.decode(enc); break
    except UnicodeDecodeError:
        continue
else:
    sys.exit("인코딩을 못 알아냄 — 사용자에게 파일 출처를 묻는다")
out = p.with_name(p.stem + "-utf8.txt"); out.write_text(text, encoding="utf-8")
print(enc, "→", out, len(text.splitlines()), "줄")
EOF
```

UTF-8로 잘 열리면 사본을 만들지 않는다.

## 2. 맥락 확인

유형(강의·미팅·인터뷰), 날짜, 주제, 저장 위치가 파일 이름·내용에서 보이면 그대로 쓰고, 안 보이는 것만 묻는다. 저장 위치는 관련 프로젝트 폴더(`10-projects/` 등)를 찾아 제안하고, 모르면 `00-inbox/`.

## 3. 끝까지 읽기

**전체를 끝까지 읽는다.** 앞부분만 보고 정리하지 않는다. 길면 여러 번에 나눠 읽는다. 화자 표시·타임스탬프가 있으면 살린다.

## 4. 음성인식 오인식 교정

받아쓴 파일이면 주제와 앞뒤 맥락으로 잘못 알아들은 말을 고친다 — 문맥에 안 맞는 단어, 같은 대상의 표기 흔들림, 영어가 한글로 잘못 바뀐 것, 사람·브랜드 이름. 확실한 것과 추정을 나누고, 고친 것은 문서 끝 「음성인식 교정 노트」 표(오인식 | 교정 | 근거)에 전부 남긴다. 추정은 "(추정)"으로 표시한다.

## 5. 정리

`templates/`의 강의·미팅·인터뷰 양식을 출발점으로 쓰되 내용에 맞게 바꾼다. 저장 폴더에 `_schema*.md`가 있으면 그 구조가 먼저다.

- **임의로 줄이지 않는다.** 논의된 내용·사례·Q&A는 빠짐없이 담는다. 분량은 원문이 정한다.
- **설명이 앞, 인용은 근거로.** 핵심 발언은 `> "원문"`으로 남긴다.
- 미팅이면 결정 사항과 할 일(누가·언제)을 따로 모은다.

## 6. 저장과 보고

파일 이름 `YYYY-MM-DD_주제.md`. 저장 경로·줄 수·유형을 알린다. 다시 꺼내 쓸 앎이 보이면 위키에 넣을지 **묻는다** — 넣기로 하면 `wiki-ingest`가 한다.

---

Made by Do Better Things
