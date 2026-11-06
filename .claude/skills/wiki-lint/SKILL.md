---
name: wiki-lint
description: |
  00-wiki 토픽 페이지 헬스체크. 검사기로 형식·링크·오래된 페이지를 잡고, 페이지 간 모순·빠진 연결은 읽어서 본다.
  "wiki-lint", "위키 점검", "위키 헬스체크", "wiki health", "토픽 점검" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Edit
  - AskUserQuestion
---

# Wiki Lint

`./30-knowledge/00-wiki/` 토픽 페이지의 헬스체크.

## 기계 검사 실행

먼저 대상 워크스페이스의 `CLAUDE.md`와 `30-knowledge/00-wiki/SCHEMA.md`를 읽는다. 대상 루트에서 다음을 실행한다(Mac·Linux·Windows Git Bash). 추가 패키지나 venv는 필요 없다.

```bash
WIKI_PY=""
for c in python3 python py; do
  if "$c" -c 'import sys; assert sys.version_info >= (3, 9)' 2>/dev/null; then WIKI_PY="$c"; break; fi
done
if [ -z "$WIKI_PY" ]; then
  echo "Python 3.9 이상이 필요합니다. setup-workspace의 Python 설치 안내를 따르세요."
else
  "$WIKI_PY" .claude/skills/wiki-lint/scripts/wiki_check.py --root "$PWD" --json
fi
```

변경분은 같은 명령에 `--files 토픽A.md 토픽B.md`를 추가한다. 다른 폴더/글로벌에 설치한 스킬에서 실행할 때는 검사기의 실제 경로와 `--root "대상 워크스페이스 절대경로"`를 함께 지정한다. 루트를 생략하면 스크립트가 설치된 워크스페이스를 검사하며 홈이나 다른 PKM을 찾지 않는다.

종료 코드 0은 구조 오류 없음(경고는 남을 수 있음), 1은 구조 오류, 2는 실행 실패다. Python이 없거나 실행이 실패했으면 통과로 보고하지 않는다. `--index`는 index 수정 후보 출력만 하며 원본 파일로 직접 리다이렉트하지 않는다.

## 동작 방식

### Step 1: 기계 검사

위 명령으로 전체 검사를 돌리고 출력의 root·scope·files_read와 오류/경고를 그대로 옮긴다. index 등록·끊긴 링크·오래된 페이지(유형별 기한)·열린 모순(30일 초과)·근거 크기·관련 줄·설명/Facets 길이·출처 형식은 검사기가 잡는다 — 손으로 다시 세지 않는다. 오래됐다는 경고는 "내용이 틀렸다"가 아니라 "다시 볼 때가 됐다"는 뜻이다.

### Step 2: 읽어야 아는 것

검사기가 못 보는 것만 페이지를 열어 본다. 토픽이 적으면 짧게 끝난다.

- **페이지끼리 부딪히는 주장** — 같은 주제를 다른 페이지가 다르게 말하면 양쪽 위치를 짚는다. 플래그를 달지는 사용자가 정한다(SCHEMA 「모순의 수명주기」). **lint가 모순을 닫지 않는다**
- **연결 빠짐** — 본문에 다른 토픽 이름이 나오는데 관련 줄·Related에 링크가 없는 것, 다른 어느 페이지에서도 가리키지 않는 페이지
- **있어야 할 페이지** — 여러 페이지가 언급하는데 전용 페이지가 없는 개념
- **근거 없는 주장** — 핵심 절의 주장에 받쳐 주는 근거 불릿이 없는 것
- **index 허브 블록** — 상단 허브 5개가 실제로 많이 가리켜지는 페이지와 어긋나면 알린다

### Step 3: 리포트

검사기 결과와 Step 2 발견을 페이지별로 묶어 보여준다. 확실한 것만 낸다 — 개수를 채우려고 약한 지적을 넣지 않는다.

### Step 4: 승인 후 수정

- 고칠 항목을 사용자가 고른다. 승인한 것만 Edit (index.md, 관련 줄, Related 등)
- 수정 뒤 같은 범위로 기계 검사를 다시 돌린다. 지식 보강이 없는 정리는 Last enriched를 올리지 않는다
- 수정 내용과 검사 결과를 log.md에 `## [YYYY-MM-DD] lint | Wiki Health Check`로 남긴다

## 핵심 원칙

- **리포트 먼저, 수정은 승인 후**: 자동으로 고치지 않음
- **모순은 플래그만**: 판단은 사용자
- **과잉 제안 금지**: 확실한 문제만 리포트

---

Made by Do Better Things
