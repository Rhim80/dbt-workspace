---
name: weekly-synthesis
description: 한 주간의 작업과 사고를 종합하여 Weekly Synthesis 생성. "주간 정리", "이번 주 회고", "weekly review", "일주일 요약", "주간 리뷰" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
---

# weekly-synthesis

이번 주 작업과 사고를 종합하여 `./40-personal/42-weekly/YYYY-WXX.md`에 저장.

## 분석 프로세스

### 1. 이번 주 범위 파악

```bash
# 이번 주 시작 (월요일) 계산
if [ "$(uname)" = "Darwin" ]; then
  WEEK_START=$(date -v-Mon +%Y-%m-%d 2>/dev/null || date -v-monday +%Y-%m-%d)
else
  WEEK_START=$(date -d "monday this week" +%Y-%m-%d)
fi

WEEK_NUM=$(date +%Y-W%V)
```

### 2. 이번 주 활동 수집

**Daily notes**: `./40-personal/41-daily/` 하위에서 이번 주에 해당하는 파일들

**이번 주에 고친 파일** (git이 아니라 파일 수정 시각으로 본다 — 참가자는 커밋을 하지 않아 git 기록에 자기 일이 안 남는다):
```bash
find 00-inbox 10-projects 20-operations 30-knowledge 40-personal 50-resources \
  -type f -mtime -7 -not -name ".DS_Store" 2>/dev/null | head -60
```
워크스페이스를 받은 지 일주일이 안 됐으면 받은 파일이 섞여 나온다 — 사용자가 만든 것만 골라 본다.

**활성 프로젝트**: `10-projects/` 에서 이번 주에 수정된 폴더

### 3. 정리

양식은 `00-system/01-templates/weekly-review-template.md`를 쓴다(없으면 같은 칸으로 만든다). 칸을 채우는 기준:

- **이번 주 요약** — 몇 건 했는지보다 **무엇이 반복됐는지**를 먼저 쓴다(예: "사진이 와야 끝나는 일이 세 번 나왔다"). 어느 노트·파일에서 봤는지 짚는다
- **성취·배운 것·막힌 것** — 노트의 「완료한 일」과 프로젝트 `progress.md`에서 가져온다. 근거가 없는 칸은 비워 둔다
- **다음 주 방향** — 3개 이하
- **월 목표 대비 진행도** — 사용자가 적어 둔 월 목표가 있을 때만 채우고, 없으면 칸을 지운다

## 저장 경로

`./40-personal/42-weekly/{WEEK_NUM}.md`
예: `./40-personal/42-weekly/2026-W17.md`

## 후속 행동

분석 후 사용자에게 제안:
- 완료된 프로젝트가 있으면 → "90-archive로 이동할까요?"
- Inbox 항목 많으면 → "00-inbox 폴더를 지금 함께 정리할까요?" (해당 폴더를 직접 훑어서 10-projects / 30-knowledge / 43-ideas / 90-archive로 재배치)
- 00-wiki에 승격할 인사이트가 있으면 → "wiki-ingest로 저장할까요?"

## 원칙

- **숫자보다 패턴에 집중** — "몇 개 했다"보다 "무엇이 반복되고 있나"
- **다음 주 방향은 3개 이하** — 너무 많으면 지킬 수 없음

---

Made by Do Better Things
