# Estée Lauder 디자인 가이드

> 보고서·대시보드·PDF 등 어떤 산출물이든 이 파일을 참조하면 에스티 로더 톤이 적용된다.
> 호출: `@templates/esteelauder/design.md 디자인으로`

---

## 1. Overview

에스티 로더 한국 공식몰(esteelauder.co.kr)의 화면은 흰 바탕 위에 아주 짙은 네이비 한 색으로 거의 모든 것을 말한다. 메뉴 제목, 버튼 테두리, 채움 버튼의 바탕이 모두 같은 네이비다. 버튼은 모서리가 직각이고, 글자는 작은 대문자이며, 본문은 가는 서체로 넉넉한 자간을 둔다. **색을 많이 쓰지 않고 여백과 선의 정돈으로 고급스러움을 만드는 화면**이다.

이 가이드가 쓰이는 곳은 판매 화면이 아니라 사내 문서다. 온라인 PMO가 재무팀에 넘기는 정산 차액 정리, OMS 운영과 같이 보는 클레임 목록, 월간 온라인 매출 점검표 같은 것들이다. 이런 문서는 숫자가 틀림없이 읽혀야 하고, 전표를 칠 사람이 금액을 그대로 옮겨 적을 수 있어야 한다. 그래서 브랜드의 절제를 가져오되, **숫자와 표가 주인공**이 되게 한다.

네이비는 제목·표 머리·결론 블록의 틀에 쓴다. 공식몰 홀리데이 배너 버튼에 쓰인 밝은 보라빛 파랑은 이 가이드에서 **표시용 바탕**(결론 블록, 강조 행)으로만 쓴다. 금색은 공식몰 스타일시트에서 찾지 못했으므로 넣지 않는다.

톤은 **정돈된 확인**이다. 형용사로 꾸미지 않고, 금액에는 원 단위와 천 단위 쉼표를, 날짜에는 기준(정산기준일·주문일)을 붙인다. 확정된 것과 확인이 필요한 것은 눈으로 구분되게 놓는다.

## 2. Key Characteristics

- 흰 바탕 · 네이비 글자 · 네이비 선, 이 셋으로 대부분을 해결한다
- 밝은 보라빛 파랑은 바탕으로만 쓴다. 글자색으로 쓰지 않는다
- 모서리는 직각. 버튼·블록·표 모두 `{rounded.none}`
- 표 머리와 라벨은 작은 대문자(라틴) 또는 작은 굵은 한글, 자간을 넓게
- 금액은 오른쪽 정렬 + tabular-nums + 천 단위 쉼표 + "원"
- 차액의 방향(내부가 많음/적음)은 색보다 **부호와 글자로 먼저** 말한다
- "확인 필요"는 바탕색으로 구분한다 — 확정된 숫자와 같은 모양으로 두지 않는다
- 그림자·그라데이션 없음. 깊이는 선과 바탕 한 단계로만
- 인쇄(A4 세로)를 항상 상정한다

## 3. Colors

> **공식몰에서 잰 값과 작업용으로 정한 값을 구분합니다.** `el-navy`와 `el-periwinkle`은 esteelauder.co.kr의 화면에서 브라우저가 계산한 색 값입니다(2026-11-06). 나머지는 그 둘에서 문서 가독성에 맞게 정한 작업용 값이고 공식 지정색이 아닙니다. 공식 CI 문서는 확인하지 못했습니다(§12).

**Brand & Accent**
- `{colors.el-navy}` `#040A2B` — 공식몰 메뉴 제목 글자, 버튼 테두리·글자, 채움 버튼 바탕. 제목, 표 머리 선, 결론 블록 틀
- `{colors.el-periwinkle}` `#9EAFFF` — 공식몰 홀리데이 배너 버튼의 강조색. **바탕·막대 채움에만**. 흰 바탕 위 글자로 쓰지 않는다

**Surface**
- `{colors.canvas}` `#FFFFFF` — 페이지 바탕 (공식몰과 같음)
- `{colors.surface-sunken}` `#F5F6FA` — 표 머리, 요약 블록
- `{colors.periwinkle-tint}` `#ECEFFF` — 결론 블록 바탕, 강조 행
- `{colors.check-tint}` `#FFF6DC` — "확인 필요" 칸과 "(추정)" 문장 바탕

**Hairlines & Borders**
- `{colors.hairline}` `rgba(4,10,43,0.14)` — 표 구분선
- `{colors.hairline-strong}` `rgba(4,10,43,0.40)` — 섹션 구분
- `{colors.border-navy}` `{colors.el-navy}` — 1px 테두리 버튼, 결론 블록 틀 (공식몰 버튼과 같은 1px)

**Text**
- `{colors.ink}` `{colors.el-navy}` — 본문·제목 기본
- `{colors.text-secondary}` `#4A4F6A` — 단위, 캡션, 기준일 라벨
- `{colors.text-muted}` `#6B7088` — 각주·출처

**Chart**
- `{colors.bar-positive}` `{colors.el-navy}` — 차액 다리에서 내부 금액을 키우는 사유
- `{colors.bar-negative}` `{colors.el-periwinkle}` — 내부 금액을 줄이는 사유
- `{colors.bar-total}` `#2B3152` — 시작·끝 합계 막대

**Semantic**
- `{colors.adjust}` `#B3261E` — "조정 필요" 라벨 점
- `{colors.no-adjust}` `#2F6B4F` — "조정 불필요" 라벨 점
- `{colors.check}` `#8A6100` — "확인 필요" 라벨 점

Semantic 색은 **라벨 앞 작은 점**에만 쓴다. 금액 글자를 빨강·초록으로 칠하지 않는다. 차액이 많다는 것이 나쁜 일인지는 사유에 따라 다르다.

## 4. Typography

**Font Family**
- 라틴 제목·라벨: `{typography.family-latin}` — `'Akzidenz-Grotesk', 'Helvetica Neue', Arial, sans-serif` (공식몰 메뉴 제목이 `AkzidenzGrotesk W1G` 700을 쓴다)
- 라틴 본문·브랜드 문구: `{typography.family-display}` — `'Optima', 'Candara', sans-serif` (공식몰 본문이 `OptimaDisplayLight`를 쓴다)
- 한글: `{typography.family-sans}` — `'Pretendard', 'Apple SD Gothic Neo', system-ui, sans-serif`
- 표 안 숫자: `{typography.family-sans}` + tabular-nums

**Hierarchy**

| 토큰 | 크기/굵기 | 용도 |
|------|-----------|------|
| `{typography.display-lg}` | 26px / 600 | 문서 제목, 한 줄 결론 |
| `{typography.heading-md}` | 16px / 700, 자간 0.04em | 섹션 제목 |
| `{typography.body-md}` | 13px / 400, 줄간격 1.6 | 본문 |
| `{typography.label-uppercase}` | 11px / 700, 자간 0.08em, 대문자 | 표 머리, 기준일 라벨 (공식몰 버튼 12px 대문자에서 한 단계 작게) |
| `{typography.number-lg}` | 24px / 600, tabular-nums | 핵심 금액 |
| `{typography.number-table}` | 12.5px / 500, tabular-nums | 표 안 금액 |

**Principles**
- 금액 뒤 "원"은 한 단계 작게 `{colors.text-secondary}`. 건수는 "건"
- 차액에는 부호를 항상 붙인다 (`+2,277,460원`, `−49,600원`). 부호의 뜻(내부 − 네이버)은 문서 첫 표 아래 한 줄로 밝힌다
- 본문 굵은 글자는 문단마다 한 번 이하
- 공식몰처럼 본문 자간을 약간 넓힌다(0.01~0.02em). 한글은 넓히지 않는다

**Note on Font Substitutes**: Akzidenz-Grotesk와 OptimaDisplayLight는 상용 서체라 대부분의 노트북에 없다. Akzidenz는 Helvetica Neue → Arial로, Optima는 macOS 기본 Optima → Candara로 대체한다. 공식몰의 한글 서체 `NanumBarun Gothic Ultralight`는 문서 본문에 쓰기에 너무 가늘어 Pretendard로 바꿨다(작업용 판단).

## 5. Layout

**Spacing System**
- `{spacing.section}` 32px — 섹션 사이
- `{spacing.lg}` 18px — 블록 안, 표와 해설 사이
- `{spacing.md}` 10px — 표 칸 안쪽
- `{spacing.sm}` 6px — 라벨과 값 사이

**Grid & Container**
- A4 세로 기준 본문 폭 180mm(좌우 여백 15mm). 화면에서는 최대 1040px
- 핵심 금액 블록은 3열(전체 차액 · 조정 필요 · 확인 필요)
- 표는 항상 전체 폭

**Whitespace Philosophy**: 공식몰은 여백이 넓다. 사내 문서는 한 장에 들어가야 하므로 블록 안 여백은 줄이되 **섹션 사이 여백은 지킨다.** 조정 필요와 확인 필요가 붙어 보이면 재무팀이 확인 필요 금액까지 전표로 옮긴다.

## 6. Elevation & Depth

| Level | 용도 | 스타일 |
|-------|------|--------|
| `{elevation.flat}` | 표, 본문, 그래프 | 그림자 없음, 헤어라인만 |
| `{elevation.block}` | 핵심 금액 블록 | `{colors.surface-sunken}` 바탕 |
| `{elevation.conclusion}` | 한 줄 결론 | 1px `{colors.border-navy}` 틀 + `{colors.periwinkle-tint}` 바탕 |
| `{elevation.check}` | 확인 필요 칸 | `{colors.check-tint}` 바탕, 틀 없음 |

**Decorative Depth**: 그림자를 쓰지 않는다. 인쇄했을 때 그대로 나오는 바탕색과 1px 선만 쓴다.

## 7. Shapes

**Border Radius Scale**

| 토큰 | 값 | 용도 |
|------|-----|------|
| `{rounded.none}` | 0px | 버튼, 블록, 표, 막대 — 기본값 (공식몰 버튼이 0px) |
| `{rounded.full}` | 999px | 라벨 앞 점, 범례 점 |

**Photography Geometry**: 정산 문서에는 사진을 넣지 않는다. 제품을 보여줘야 하면 공식몰 상품 사진을 정사각으로, 흰 바탕 그대로 쓰고 글자를 올리지 않는다.

**표기 규칙**
- 브랜드 이름은 `에스티 로더`(공식 스토어 표기, 띄어 씀). 라틴은 `ESTĒE LAUDER`를 워드마크로만, 본문은 `Estée Lauder`
- 제품명은 상품마스터의 `제품명`을 그대로 쓴다. 증정 구성 괄호를 지우지 않는다 — 같은 용량의 다른 구성과 구분하는 정보다
- 날짜는 `2026-10-26`, 문장 안에서는 `10/26`

## 8. Components

**Top Navigation**: 맨 위 가운데에 워드마크 `ESTĒE LAUDER`(`{typography.family-display}`, 자간 0.2em, `{colors.ink}`), 그 아래 한 줄에 문서 제목과 기준 월. 그 아래 1px `{colors.border-navy}` 선 하나로 본문과 나눈다. 공식 로고 파일이 있으면 워드마크 자리에 넣는다.

**Buttons**: 인쇄용 문서에는 없다. 대시보드에서는 공식몰과 같은 두 종류만 쓴다 — 테두리 버튼(흰 바탕 + 1px 네이비 테두리 + 네이비 글자)과 채움 버튼(네이비 바탕 + 흰 글자). 둘 다 `{rounded.none}`, `{typography.label-uppercase}`, 좌우 안쪽 20px.

**Cards & Containers**: 핵심 금액 블록 = `{elevation.block}` + 안쪽 `{spacing.lg}`. 위에서부터 라벨(`{typography.label-uppercase}`) → 금액(`{typography.number-lg}`) + 원 → 건수 → "그래서" 한 줄(`{typography.body-md}`).

**Inputs & Forms**: 대시보드의 **작성자 코멘트 칸**만 정의한다. 흰 바탕, 1px `{colors.hairline-strong}` 테두리, `{rounded.none}`, 높이 3줄. 비어 있으면 인쇄본에도 빈 칸으로 남긴다.

**Signature Components**:
- **차액 다리** — 내부 합계 막대에서 시작해 사유마다 위아래로 떠 있는 막대를 이어, 네이버 합계 막대에서 끝난다. 시작·끝은 `{colors.bar-total}`, 내부를 키우는 사유는 `{colors.bar-positive}`, 줄이는 사유는 `{colors.bar-negative}`. 막대마다 위에 부호 붙은 금액, 아래에 사유 이름. 마지막 막대 옆에 "다리 닫힘 ✓" 또는 "끊김 OO원"을 반드시 적는다
- **조정 판단 세 칸** — 조정 필요 · 조정 불필요 · 확인 필요를 같은 폭의 세 칸으로. 라벨 앞에 Semantic 점. 확인 필요 칸만 `{elevation.check}`
- **기준일 라벨** — 표·그래프 오른쪽 위에 `정산기준일 10/1~10/31` · `주문일 10/1~10/31`처럼 붙이는 작은 라벨. 두 파일의 기준이 다르다는 것을 화면에서 놓치지 않게 한다
- **추정 표시** — "(추정)"이 붙은 문장은 `{colors.check-tint}` 바탕
- **SKU별 조정표** — SAP자재코드 · 제품명 · 사유 · ZCM/ZDM · 금액. 마지막 줄에 합계, 합계 위에 2px `{colors.border-navy}` 선

**Footer**: 맨 아래 한 줄. 만든 날짜 + 쓴 파일 이름 + 각 파일의 기준(주문일/정산기준일)과 기간. `{typography.label-uppercase}`, `{colors.text-muted}`.

## 9. Do's and Don'ts

**Do**
- 금액마다 원 단위와 부호를 붙인다
- 다리의 마지막에 닫혔는지를 적는다
- 확인 필요 금액은 바탕색으로 따로 둔다
- 버튼·블록 모서리는 직각으로 둔다
- 제품명은 마스터 표기 그대로 쓴다
- 기준일이 다른 두 자료를 한 화면에 놓을 때 기준일 라벨을 붙인다

**Don't**
- `{colors.el-periwinkle}` 위에 흰 글자를 올리지 않는다, 흰 바탕 위 글자로도 쓰지 않는다 (대비가 낮다)
- 금액을 빨강·초록으로 칠하지 않는다
- 공식몰에서 확인하지 못한 금색을 쓰지 않는다
- 둥근 카드·그림자·그라데이션을 쓰지 않는다
- 확인 필요 금액을 조정 필요 합계에 더하지 않는다
- 증정 구성 괄호를 지워 제품명을 줄이지 않는다
- 워드마크를 본문 제목 서체로 흉내 내지 않는다

## 10. Responsive Behavior

| Breakpoint | 폭 | 동작 |
|------------|-----|------|
| Print (A4) | 180mm 본문 | 고정. 본문 한 장, 부록은 새 페이지에서 시작 |
| Desktop | ≥1040px | 핵심 금액 3열, 조정 판단 3열 |
| Tablet | 640~1039px | 핵심 금액 3열 유지, 조정 판단 1열 |
| Mobile | <640px | 전부 1열, 표는 가로 스크롤 |

**Touch Targets**: 대시보드 버튼·필터는 최소 44px.

**Collapsing Strategy**: 좁은 화면에서는 한 줄 결론 → 핵심 금액 → 차액 다리 → 조정 판단 → 표 순서. 표의 열을 숨기지 않고 가로 스크롤을 준다. 상품주문번호 열이 빠지면 다시 찾아갈 수 없다.

**Image Behavior**: 차액 다리는 SVG로 그려 폭에 맞춘다. 막대 위 금액 글자는 11px 아래로 내려가지 않게 한다.

## 11. Iteration Guide

1. 공식 CI를 받으면 §3의 `el-` 토큰 둘만 바꾼다. 나머지는 그 둘을 가리킨다
2. 금색이 공식 색으로 확인되면 `{colors.el-gold}`를 새로 만들고 결론 블록 틀에만 쓴다
3. 사유가 늘면 차액 다리 막대를 늘리되, 열 개를 넘으면 작은 사유를 "기타"로 묶고 부록에 풀어 둔다
4. 다른 채널(컬리·SSG닷컴·롯데온) 정산에 쓸 때는 기준일 라벨의 이름만 그 채널 용어로 바꾼다
5. 임계값은 이 파일이 아니라 `네이버-정산-차액-정리.md`의 검출 규칙이 원본이다. 여기에 옮겨 적지 않는다
6. 대시보드로 넓힐 때는 §8의 Buttons·Inputs부터 채운다
7. 크리니크·맥 등 다른 브랜드 문서에 쓸 때는 이 파일을 복사하지 말고 브랜드 토큰만 바꾼 새 파일을 만든다
8. 고칠 때는 §12에서 풀린 항목을 지우고 새로 확인 안 된 것만 남긴다

## 12. Known Gaps

- **공식 CI 문서 미확인** — 두 색은 공식몰 화면에서 브라우저가 계산한 값이다(2026-11-06). 회사가 정한 색 번호·인쇄용 값은 모른다
- **워드마크 철자** — `ESTĒE` 위 장음 부호는 조사에서 로고 파일로 확인한 것이 아니다. 로고 파일을 받으면 맞춘다
- **금색 미확인** — 브랜드 하면 떠오르는 금색은 공식몰 스타일시트에서 찾지 못했다. 로고 파일도 보지 못했다
- **보라빛 파랑의 지위** — `#9EAFFF`는 홀리데이 배너 버튼에서 잰 값이라 계절 캠페인 색일 수 있다. 상시 브랜드 색인지는 확인하지 못했다
- **서체** — Akzidenz-Grotesk·Optima는 공식몰이 불러오는 서체다. 사내 문서용 지정 서체가 따로 있는지는 모른다. 한글 Pretendard는 작업용 대체다
- **사내 문서 양식 미확인** — 재무팀·OMS팀이 실제로 주고받는 정산 조정 양식을 보지 못했다. 받으면 §8 SKU별 조정표의 열 순서를 그 양식에 맞춘다
- **다크 모드 미정의** — 인쇄·PDF 중심이라 밝은 화면 하나로 간다
