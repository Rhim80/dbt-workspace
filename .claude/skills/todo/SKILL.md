---
name: todo
description: 할 일을 담고 꺼내 본다. "할 일 추가", "이거 해야 해", "기억해둬", "todo" 같은 말은 담기, "할 일 보여줘", "오늘 할 일", "오래된 할 일", "할 일 정리" 같은 말은 보기. 할 일 목록 파일 하나를 같은 형식으로 쓰고 읽는다.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# todo — 할 일 담기·보기

할 일은 `40-personal/46-todos/active-todos.md` 한 파일에 둔다. 이 스킬이 정하는 것은 **파일 자리와 한 줄 형식**뿐이다. 어떻게 보여줄지(오늘 것만, 프로젝트별, 오래된 순, 개수)는 요청을 보고 판단한다.

## 파일 모양

```markdown
# Active Todos

## Today
## This Week
## Backlog
```

파일이나 절이 없으면 이 모양으로 만든다. 절 안에 빈 `- [ ]` 줄만 있으면 그 줄을 새 항목으로 바꾼다 — 빈 줄은 할 일로 세지 않는다.

## 한 줄 형식 (항상 이대로)

```markdown
- [ ] 촬영 업체에 견적 회신하기
  - added: 2026-11-07 14:30
  - priority: high | normal | low
  - project: 신제품-상세페이지   # 있을 때만
```

- `added`는 `date +"%Y-%m-%d %H:%M"`로 찍는다. "오래된 할 일"(담은 지 7일 넘은 것)을 가르는 기준이라 빠뜨리지 않는다.
- 급하다는 말이 있으면 `high` → Today, 나중이라는 말이 있으면 `low` → Backlog, 그 밖은 `normal` → This Week. 애매하면 This Week에 넣고 어디 넣었는지 말한다.
- 프로젝트 이름이 나오면 `10-projects/`의 폴더 이름과 맞춘다.

## 끝낸 것

체크된 항목(`- [x]`)은 볼 때 `40-personal/46-todos/completed-todos.md`의 월별 절(`## 2026-11`)로 옮기고 `done:` 날짜를 붙인다. 옮겼으면 몇 건 옮겼는지 한 줄로 알린다.

---

Made by Do Better Things
