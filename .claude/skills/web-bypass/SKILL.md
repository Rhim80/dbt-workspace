---
name: web-bypass
description: WebFetch·curl이 403/차단/빈 껍데기로 실패한 URL을 3단계(curl·사이트가 열어 둔 길 → Aside fetch → Aside 탭)로 받고, 글자 수·막힘 문구·찾는 말로 "받았다"를 판정한다. 24h 캐시, 워크스페이스 저장. "WebFetch 실패", "403 우회", "차단 우회", "막힌 페이지", "web-bypass" 등을 언급하면 자동 실행. 단순 URL 요약은 WebFetch, 클릭·로그인 조작은 Aside 스킬, 네이버 리뷰는 review-analyzer 우선.
context: fork
background: false
allowed-tools:
  - Bash
  - Read
---

# web-bypass

막힌 웹 페이지를 받는 스크립트 하나. 순서와 판정만 우리가 정하고, 막힌 페이지는 Aside(진짜 브라우저)가 연다.

| 단계 | 하는 일 | 걸린 시간 (2026-10-21 측정) | 내 계정 |
|---|---|---|---|
| 1 `curl` | 브라우저 이름을 단 일반 요청 | 0.3~1초 | 안 씀 |
| 1 `curl:route` | 사이트가 열어 둔 길 — Reddit 글 → `.rss`, 네이버 블로그 → `PostView.naver` | 0.3~2초 | 안 씀 |
| 2 `aside_fetch` | Aside 브라우저 안에서 요청 (탭 안 뜸) | 1~2.6초 | **씀** |
| 3 `aside_tab` | Aside 탭으로 열어 화면 글자 읽기 (Cloudflare 확인 화면 통과) | 6~11초 | **씀** |

앞 단계에서 받으면 멈춘다. 2·3단계로 받은 결과는 `used_login: true` — 공개 화면이 아니라 **내게 보이는 화면**이다(내가 볼 권한이 있는 비공개 글도 보인다). 남에게 줄 자료를 공개 화면 기준으로 만들어야 하면 `--no-login`.

## 호출

```bash
bash .claude/skills/web-bypass/scripts/fetch.sh "<URL>" --grep "<글 제목·핵심어>"
```

| 옵션 | 뜻 |
|---|---|
| `--grep REGEX` | 찾을 말. **단계 판정에도 쓰인다** — 없으면 다음 단계로 간다. 앞뒤 200자를 `matches`로 돌려준다(최대 10개) |
| `--no-login` | 1단계에서 멈춘다 (내 계정 안 씀) |
| `--save-to-pkm PATH` | 워크스페이스 안 경로에 화면 글자를 frontmatter(source·fetched_at·step·used_login)와 함께 .md로 저장. 이미 있으면 `--force` |
| `--no-cache` / `--ttl SEC` | 캐시 무시 / 캐시 수명(기본 86400초) |
| `--timeout N` | curl 한 번의 제한(기본 20초) |

필요한 것: `curl`, 파이썬 3.9 이상(표준 라이브러리만, 이름은 `fetch.sh`가 찾는다), 2·3단계는 `aside` CLI + Aside 앱이 떠 있을 것. `aside`가 없는 기계에서는 1단계만 하고 `summary`에 "이 기계에 aside 없음"을 남긴다.

## "받았다" 판정 (`fetch.py`의 `judge`)

단계마다 아래가 모두 맞아야 받은 것:

1. 상태 200 (탭 단계는 상태 없음)
2. 화면 글자 200자 이상 — 단 `--grep`의 말이 있으면 짧아도 됨(Cloudflare 통과 화면은 78자)
3. 8,000자 미만 페이지에 막힘 문구 없음 — `BLOCK_PHRASES`(Just a moment · Access Denied · Please enable JS · blocked by network security · Something went wrong(X) · 비공개 글 등). 긴 정상 글에 낱말이 섞인 오탐을 막으려고 긴 페이지는 안 본다
4. 안내가 화면 글자에 안 나오는 사이트는 원본에 본문 칸이 있어야 함 — `BODY_MARKERS`(네이버 PostView는 `postViewArea`)
5. `--grep`을 줬으면 그 말이 있음

**그래서 부르는 쪽은 `ok`만 보고 끝내지 말고 `--grep`을 건다.** 찾는 말 없이 부르면 2·3번까지만 보고 받았다고 한다.

## 결과 (stdout JSON)

```json
{
  "ok": true,
  "step": "aside_fetch",
  "used_login": true,
  "url": "https://...",
  "fetched_url": "https://...",
  "visible_chars": 48934,
  "attempts": [{"step": "curl", "status": 200, "visible_chars": 6, "reason": "thin (6자)"},
               {"step": "aside_fetch", "status": 200, "visible_chars": 48934, "reason": "ok"}],
  "summary": "",
  "cache_file": "~/.cache/web-bypass/<hash>.json",
  "content_preview": "화면 글자 앞 500자",
  "matches": ["--grep 줬을 때"]
}
```

- 본문이 더 필요하면 `--grep`을 다른 말로 다시 부른다(캐시에서 바로 돈다). `cache_file`의 `content`는 원본이라 크다 — 통째로 Read하지 않는다
- 실패(`ok: false`)면 `attempts`의 `reason`을 그대로 전한다. 세 단계가 다 막힌 곳(2026-10-21 G2)은 "못 받음"으로 끝낸다 — 클릭·로그인이 필요한 일이면 Aside 스킬로 직접 연다

## 판정 못 하는 범위

- 화면 글자 8,000자 이상인 막힘 화면(긴 안내문)은 문구로 못 거른다 → `--grep`이 거른다
- 8,000자 미만 정상 글이 막힘 문구를 인용하면 실패로 떨어진다 → 다음 단계로 넘어가 시간만 더 든다
- 200자 미만 정상 페이지(example.com 171자)는 `--grep` 없으면 3단계까지 간다

## 캐시

`~/.cache/web-bypass/<sha256 앞 16자>.json`, 받은 것만 저장. 계정으로 받은 캐시는 `--no-login` 호출에 내주지 않는다. 만료 캐시는 지우지 않는다(`~/.cache/web-bypass/` 수동 정리).

## 종료 코드

0 받음 · 1 못 받음 · 2 인자 오류 · 3 `--save-to-pkm` 경로 충돌

---

Made by Do Better Things
