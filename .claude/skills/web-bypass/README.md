# web-bypass

막힌 웹 페이지를 curl → Aside fetch → Aside 탭 순서로 받는 스크립트. 쓰는 법·판정·결과 형식은 `SKILL.md`가 원본이다.

```
web-bypass/
├── SKILL.md            # 진입점 — 단계·판정·옵션
├── README.md           # 이 파일
└── scripts/
    ├── fetch.sh        # 파이썬을 찾아 fetch.py 실행
    └── fetch.py        # 3단계 + 판정 + 24h 캐시 + 저장 (표준 라이브러리만)
```

## 책임 경계

| 시나리오 | 사용 |
|---|---|
| URL 한 개 본문 요약 | `WebFetch` |
| WebFetch·curl 403 / 차단 / 빈 껍데기 | **web-bypass** |
| 텍스트만 워크스페이스에 저장 | **web-bypass** `--save-to-pkm` |
| 클릭·폼·로그인 조작 | Aside 스킬 |
| 네이버 리뷰 | `review-analyzer` |

---

Made by Do Better Things
