---
name: setup-workspace
description: 첫 clone 후 워크스페이스 초기 설정. CLAUDE.md 프로필 작성 + Python venv 세팅 + 선택 도구(git·Aside·gws) 점검 + 첫 daily note 생성까지 한번에 진행. "워크스페이스 세팅", "초기 설정", "setup", "setup-workspace" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# setup-workspace

Do Better Workspace를 처음 clone한 사용자를 위한 초기 설정 스킬.
핵심 단계: **루트 확인 → 프로필 → Python 환경 → 선택 도구 → 저장 위치 확인 → 첫 Daily Note**.

## 수행 작업

### 1. 워크스페이스 루트 + 시드 무결성 확인

**1-1. 루트 여부**:

```bash
test -f CLAUDE.md && test -d 40-personal && test -d 30-knowledge/00-wiki \
  || { echo "ERROR: 워크스페이스 루트에서 실행하세요 (CLAUDE.md·40-personal·30-knowledge 없음)"; exit 1; }
```

루트가 아니면 종료.

**1-2. 시드 파일/폴더 무결성**:

각 스킬이 실제로 참조하는 시드가 살아있는지 일괄 체크. 누락된 건 경고로만 출력하고 자동 복원은 하지 않음 (clone이 불완전했거나 사용자가 실수로 지운 경우 빨리 감지).

```bash
echo "=== 시드 무결성 체크 ==="
missing=()

# 템플릿 (daily-note, weekly-synthesis, ripple이 읽음)
test -f 00-system/01-templates/daily-note-template.md   || missing+=("00-system/01-templates/daily-note-template.md")
test -f 00-system/01-templates/weekly-review-template.md || missing+=("00-system/01-templates/weekly-review-template.md")
test -f 00-system/01-templates/progress-template.md     || missing+=("00-system/01-templates/progress-template.md")

# Personal 디렉토리 (daily/weekly 스킬과 메모 저장 경로)
test -d 40-personal/41-daily    || missing+=("40-personal/41-daily/")
test -d 40-personal/42-weekly   || missing+=("40-personal/42-weekly/")
test -d 40-personal/43-ideas    || missing+=("40-personal/43-ideas/")
test -d 40-personal/46-todos    || missing+=("40-personal/46-todos/")

# Todo 시드 (todo 스킬 타깃)
test -f 40-personal/46-todos/active-todos.md || missing+=("40-personal/46-todos/active-todos.md")

# CLAUDE.md 프로필 마커 (3단이 이 사이만 교체한다. 절 제목이 아니라 마커로 찾는다)
grep -q "profile:start" CLAUDE.md && grep -q "profile:end" CLAUDE.md \
  || missing+=("CLAUDE.md의 <!-- profile:start -->/<!-- profile:end --> 마커")

# Wiki 시드 (wiki-ingest, wiki-lint가 읽고 씀)
test -f 30-knowledge/00-wiki/SCHEMA.md || missing+=("30-knowledge/00-wiki/SCHEMA.md")
test -f 30-knowledge/00-wiki/index.md  || missing+=("30-knowledge/00-wiki/index.md")
test -f 30-knowledge/00-wiki/log.md    || missing+=("30-knowledge/00-wiki/log.md")

if [ ${#missing[@]} -eq 0 ]; then
  echo "✓ 모든 시드 파일 정상"
else
  echo "⚠️  누락된 시드 (${#missing[@]}개):"
  printf '  - %s\n' "${missing[@]}"
  echo ""
  echo "이 상태로 진행 가능하나, 관련 스킬 실행 시 에러가 날 수 있습니다."
  echo "clone 상태를 확인하거나 원본 레포에서 누락된 파일을 가져오세요."
fi
```

누락이 있으면 사용자에게 "이대로 진행할까요? (y/N)" 확인. N이면 종료.

**단 프로필 마커 누락은 예외 — 진행하지 않고 멈춘다.** 다른 시드는 없으면 나중에 그 스킬이 에러를 내지만, 마커가 없으면 3단이 **조용히 프로필 섹션을 하나 더 만들어** CLAUDE.md에 같은 절이 둘 생긴다. 사용자는 알아채지 못하고 Claude는 어느 쪽을 읽을지 모른다.

```
CLAUDE.md에 프로필 마커(<!-- profile:start --> / <!-- profile:end -->)가 없습니다.
"## 내 프로필" 절의 항목들을 이 두 줄로 감싼 뒤 다시 실행해 주세요.
```

### 2. 대화형 프로필 질문

순서대로 하나씩 물어본다. 한 번에 하나씩 (일괄 질문 금지).

먼저 **마커 사이가 이미 채워져 있는지** 확인 (절 제목이 아니라 마커로 찾는다):
- 비어있으면 → 아래 질문 진행
- 이미 채워져 있으면 → "프로필이 이미 있어요. 다시 채울까요? (y/N)" → N이면 이 단계 스킵

**무엇을 묻는가** — 잘 안 바뀌고, 이 폴더의 파일을 읽어서는 알 수 없고, 거의 매번 쓰이는 것만 묻는다. 바뀌는 것(지금 하는 일·쓰는 도구·연락처)은 첫날 묻지 않고 **그 일이 생긴 순간** 적는다 — 도구는 연결한 뒤 "연결됨"을, 연락처는 처음 보낼 때 적을지 묻는다. 끝난 일·바뀐 역할이 남아 있으면 Claude가 계속 그 기준으로 일한다.

**어떻게 묻는가** — "보통 어떻게 하세요"가 아니라 **"지난번 한 번"**을 묻는다. 보통을 물으면 이상적인 모습이 나오고, 특정한 한 번을 물어야 실제가 나온다. 답이 아래 「모자란 답」이면 **칸마다 한 번만** 되묻고, 그래도 모자라면 받은 대로 적는다. 캐묻는 세팅이 되지 않게 한다. 답에 없는 말을 Claude가 채우지 않는다. 건너뛴 칸은 빈칸.

질문 목록:
1. **이름** — "어떻게 불러드릴까요?"
2. **하는 일** — "어떤 회사에서 무슨 역할이세요? 회사가 뭘 하는 곳인지도 한 줄로요."
   - 좋은 모양: "수입 식자재 유통사 구매팀 — 해외 거래처 견적·발주를 맡음"
   - 모자란 답: 직함만("마케터", "대표") → "지난주에 실제로 한 일 하나만 말씀해 주세요."
3. **결과물 받는 사람** — "저와 만들 결과물은 주로 누가 받나요? 가장 최근에 보낸 것 하나를 떠올려 보세요."
   - 좋은 모양: "팀장 보고(한 장 요약) · 해외 거래처 영어 메일"
   - 모자란 답: "여러 사람", "회사" → "지난주에 보낸 메일이나 보고서 하나는 누구에게 갔나요?"
4. **익숙한 정도** — "AI나 컴퓨터 작업에 얼마나 익숙하세요?" 보기를 보여준다: ① 챗GPT 같은 걸 거의 안 써 봤다 ② 챗GPT로 글·요약은 해 봤다 ③ 엑셀 함수나 자동화도 직접 해 봤다. **실제보다 높게 고르지 않게** "편한 쪽으로 고르시면 됩니다"를 붙인다 — 높게 적히면 Claude가 설명을 건너뛴다.
5. **답 받는 방식** — "답은 어떻게 받는 게 편하세요?" 보기: ① 결론만 짧게 ② 결론 먼저, 이유는 짧게 ③ 고를 거리 2~3개를 같이
6. **하지 말 것** — "제가 절대 하면 안 되는 것이나, 넣으면 안 되는 자료가 있나요? 없으면 넘어가도 됩니다."
   - 좋은 모양: "회사 대외비 자료는 넣지 않는다", "거래처에 내 확인 없이 보내지 않는다"
   - 모자란 답: "조심해서" → "예를 들면 어떤 자료나 어떤 일이요?"
7. **기준 결과물** (가능하면) — "잘됐다고 생각하는 보고서나 메일 하나를 `50-resources/`에 넣어 주시거나 파일 위치를 알려 주실래요? 비슷한 걸 만들 때 제가 먼저 열어 보겠습니다." 없으면 빈칸.

답변은 변수로 저장 (`USER_NAME`, `USER_WORK`, `USER_AUDIENCE`, `USER_LEVEL`, `USER_STYLE`, `USER_DONT`, `USER_EXAMPLE`).

**묻지 않는 것**
- **취미·가족·성격 같은 일과 관계없는 개인 정보** — 관계없는 정보가 있으면 Claude가 상관없는 일에 끌어다 쓴다(지난 캠프 참가자: "어설프게 자꾸 나에 대해 아는 것처럼"). 그래서 "관심사"도 묻지 않는다
- **요즘 걸려 있는 일** — 끝나면 지워야 하는데 남기 쉽다. 진행 중인 일은 `10-projects/`에 폴더로 남는다
- **판단 성향** — 첫날엔 답하기 어렵다. 자리만 두고 do-better-drive를 쓰며 채운다

다 받으면 **채울 내용을 한 번 보여주고** "이렇게 적을까요?"로 확인받은 뒤 3단으로 간다.

### 3. CLAUDE.md 업데이트

**`<!-- profile:start -->`와 `<!-- profile:end -->` 사이만** `Edit` 도구로 교체한다. 마커 두 줄은 남긴다. 파일 전체 덮어쓰기 금지.

**절 제목("## 내 프로필")으로 찾지 않는다.** 제목은 바뀔 수 있고, 바뀌면 이 단계가 섹션을 못 찾아 새로 만들어 버린다(실제로 그렇게 깨진 적이 있다). 마커는 바뀌지 않는다.

마커 사이를 이렇게 채운다:
```markdown
**이름**: {USER_NAME}
**하는 일**: {USER_WORK} <!-- 예시·용어 수준을 맞춤 -->
**결과물 받는 사람**: {USER_AUDIENCE} <!-- 말투·형식을 맞춤 -->
**익숙한 정도**: {USER_LEVEL} <!-- 설명 깊이를 맞춤 -->
**답 받는 방식**: {USER_STYLE} <!-- 답 길이·결론 위치 -->
**하지 말 것**: {USER_DONT} <!-- 요청이 있어도 먼저 묻는다 -->
**기준 결과물**: {USER_EXAMPLE} <!-- 비슷한 걸 만들 때 먼저 연다 -->
**판단 성향**: <!-- do-better-drive가 읽음 -->

_작성일: YYYY-MM-DD_
```

**줄 옆 `<!-- -->` 설명은 지우지 않는다.** 같은 줄에 붙은 주석은 Claude에게 보인다(2026-11-06 시험: 「하는 일」 옆 설명을 그대로 읽어 냈고, 따로 줄을 차지한 주석 덩어리만 안 보였다). 이 설명이 Claude가 그 값을 어디에 쓰는지 아는 유일한 자리다 — 예전 양식은 설명 없이 값만 넣어서 세팅을 마친 모든 사람에게서 설명이 지워졌다.

빈칸으로 남은 항목도 줄은 남긴다(값 자리만 비움).

**필드 이름은 CLAUDE.md에 있는 것과 글자까지 같아야 한다.** 한쪽만 바꾸면 다음 세션이 빈 값으로 읽는다.

**"판단 성향" 줄은 지우지 않는다.** 세팅에서 묻지 않는 항목이지만 `do-better-drive`가 이 줄을 읽는다. 섹션을 통째로 바꾸면서 이 줄을 빠뜨리면, 나중에 사용자가 채워 넣을 자리 자체가 사라진다.

### 4. Python 환경 세팅

위키 점검·handoff·카톡 읽기는 Python 3.9 이상·표준 라이브러리만 쓴다. 패키지가 필요한 것은 엑셀·CSV를 다루는 일(pandas·openpyxl — 스킬 없이 Claude가 코드를 짜서 쓴다)과 `pdf-to-md`(pymupdf4llm)다.

**4-1. Python 설치 확인**:

파이썬을 부르는 이름이 OS마다 다르다 — Mac·Linux는 `python3`, 윈도우는 보통 `python` 또는 `py`뿐이다. 그래서 **이름을 고정하지 않고 실제로 실행해 보고 되는 것을 고른다.**

```bash
PYBOOT=""
for c in python3 python py; do
  v=$("$c" --version 2>&1) || continue
  case "$v" in Python\ 3.*) PYBOOT="$c"; echo "Python: $v ($c)"; break ;; esac
done
[ -z "$PYBOOT" ] && echo "파이썬 3이 없습니다"
```

`command -v`로 있는지만 보지 않는 이유: **윈도우에는 `python3`라는 이름이 있는 척하는 가짜가 기본으로 깔려 있다.** 치면 Microsoft Store 창이 열리고 파이썬은 실행되지 않는다. 실제로 `--version`을 시켜 "Python 3."이 나오는 것만 고르면 이 가짜가 걸러진다.

없으면 **사용자에게 묻고 Claude가 설치한다** (사용자에게 설치 파일을 받으라고 넘기지 않는다):

- **윈도우**: `winget install --id Python.Python.3.12 -e` (관리자 권한 불필요). 끝나면 사용자에게 **"데스크탑 앱을 완전히 종료했다가 다시 열어 주세요"**라고 알린다 — 켜 둔 채 설치한 프로그램은 다시 열어야 앱이 찾는다. 다시 연 뒤 4-1을 돌린다. 그래도 가짜가 먼저 잡히면 실제 경로 `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`로 부른다.
- **Mac**: 캠프 설치 안내의 `xcode-select --install`(명령어 라인 개발자 도구)에 `python3`가 들어 있다. 없다고 나오면 그 설치가 안 끝난 것이니 먼저 마치게 한다.
- **Ubuntu·WSL**: `sudo apt install python3 python3-venv` (비밀번호가 필요하니 사용자가 직접 친다)

**4-2. venv 세팅 제안**:

```
엑셀·CSV 정리와 PDF 변환을 하려면 Python 패키지 3개가 필요합니다.
워크스페이스 전용 가상환경(.venv)을 지금 만들까요? (Y/n)
(이 셋 말고도 자기 패키지를 따로 쓰는 스킬이 있습니다 — 그건 그 스킬을 처음 쓸 때
 해당 SKILL.md의 설치 안내대로 깝니다. 목록은 `.claude/skills/README.md`의 「설치가 필요한 스킬」)
```

Yes (기본)면:

```bash
# 이미 .venv 있으면 스킵 (PYBOOT은 4-1에서 잡은 이름)
if [ ! -d .venv ]; then
  "$PYBOOT" -m venv .venv
fi

source .claude/venv.sh
python -m pip install --upgrade pip --quiet
python -m pip install pandas openpyxl -r .claude/skills/pdf-to-md/scripts/requirements.txt
```

설치 완료 후 확인:
```bash
source .claude/venv.sh && python -c "import pandas, openpyxl, pymupdf4llm; print('OK: pandas', pandas.__version__, '| openpyxl', openpyxl.__version__, '| pymupdf4llm imported')"
```

**안내 출력** (사용자가 따로 할 일은 없다):
```
✓ .venv/ 생성 및 패키지 설치 완료
파이썬이 필요한 일은 제가 이 가상환경을 켜고 실행합니다. 따로 하실 것은 없습니다.
```

Claude 쪽 규칙: 패키지를 쓰는 파이썬은 `source .claude/venv.sh` 뒤에 부르고, 켠 뒤에는 `python3`가 아니라 **`python`**으로 부른다(윈도우 가상환경에는 `python3`라는 이름이 없다).

No면 "나중에 필요할 때 말씀하시면 그때 설치합니다" 안내 후 다음 단계.

### 5. 선택 도구 점검 (설치 강제 X)

**어떤 도구가 어떤 일을 풀어주는지** 한번에 체크하고 보여준다:

```bash
echo "=== 선택 도구 상태 ==="
command -v git &>/dev/null && echo "✓ git: $(git --version)" || echo "✗ git: 미설치 (워크스페이스 받기·되돌리기에 씀)"
command -v aside &>/dev/null && echo "✓ aside: 설치됨" || echo "✗ aside: 미설치 (막힌 웹페이지 열기·구글 연결에 씀 — 캠프 설치 안내 4단계)"
command -v gws &>/dev/null && echo "✓ gws: $(gws --version 2>&1 | head -1)" || echo "✗ gws: 미설치 (daily-note의 구글 캘린더 일정, 메일·시트·드라이브 작업)"
case "$(uname -s)" in
  Darwin)
    command -v sqlcipher &>/dev/null && echo "✓ sqlcipher: $(sqlcipher --version 2>&1 | head -1)" \
      || echo "✗ sqlcipher: 미설치 (kakao-read 카톡 읽기 비활성 — brew install sqlcipher)" ;;
  MINGW*|MSYS*|CYGWIN*)
    echo "ℹ️  kakao-read: 윈도우는 sqlcipher가 필요 없습니다 (실행 중인 카톡 메모리를 읽는 방식)" ;;
  *)
    if [ -d /mnt/c ]; then
      echo "ℹ️  kakao-read: WSL — 윈도우 방식으로 동작합니다 (sqlcipher 불필요)"
    else
      echo "ℹ️  kakao-read: 이 OS($(uname -s))에선 비활성 — Mac·윈도우 전용 (다른 스킬엔 영향 없음)"
    fi ;;
esac
```

출력 후 설명:

```markdown
**git**: `git clone`으로 받았으면 이미 들어 있습니다 — 따로 할 것 없음

**Aside**: 클로드가 웹사이트를 열고 읽을 때 쓰는 브라우저입니다. 막힌 페이지 열기(`web-bypass`)와 구글 연결에 씁니다.
  - 없으면 캠프 설치 안내 「4단계: Aside 설치와 셋팅」을 마치고, 데스크탑 앱을 완전히 종료했다 다시 엽니다

**gws (구글 연결)**: 오늘 노트에 캘린더 일정이 들어가고, 메일·시트·드라이브를 말로 시킬 수 있습니다.
  - 연결은 이렇게 한마디만 하면 클로드가 설치부터 구글 인증까지 Aside로 진행합니다:
    "gws 설치하고 구글 OAuth 연결해줘. 브라우저는 Aside 써. 계정은 내이메일@gmail.com"
  - 약관 동의·로그인 허용은 클로드가 멈추고 눌러 달라고 합니다
  - 없어도 daily-note는 정상 동작하며 일정 칸만 비어 있음

**kakao-read (Mac·윈도우 둘 다 됩니다 — 읽는 방식이 다릅니다)**

- **Mac**: 카톡의 암호화된 로컬 DB를 직접 읽습니다.
  - 설치: `brew install sqlcipher`
  - 최초 1회: `python3 .claude/skills/kakao-read/scripts/kakao_read.py setup` (본인 userId 캐시)
  - 카카오톡 데스크톱 앱에 한 번 이상 로그인돼 있어야 함
- **윈도우·WSL**: 실행 중인 카톡의 메모리를 읽습니다. sqlcipher도 키도 필요 없습니다.
  - 파이썬만 있으면 됩니다(4단에서 세팅). 읽는 순간 **카톡이 켜져 있어야** 합니다.
  - 자세한 절차는 `kakao-read` 스킬을 부르면 안내합니다.
- 그 외 OS(순수 리눅스)에선 자동 비활성 — 다른 스킬엔 영향 없음
```

이 단계에서 설치·인증까지 하지는 않는다. 사용자가 원한다고 하면 그때 진행한다.

### 5-1. 저장 위치 확인 — 내 대화가 어디로 올라가는지 (중요)

이 워크스페이스에는 앞으로 카톡 요약·회신 초안·업무 기록 같은 **민감한 내용**이 쌓인다(예: kakao-read로 읽은 본인 카톡). git 원격(GitHub 등)에 올리는 순간 그 내용이 내 컴퓨터 밖의 서버로 복사되고, 저장소가 **공개(public)** 상태면 인터넷의 누구나 볼 수 있다. 그래서 세팅 때 딱 한 번, 기계가 검사한다:

```bash
echo "=== 저장 위치 확인 ==="
if git remote get-url origin 2>/dev/null | grep -qiE "Rhim80/dbt-workspace(\.git)?/?$"; then
  echo "ℹ️ 배포 원본(Rhim80/dbt-workspace)에서 받은 사본입니다 — 내 기록은 그쪽으로 올라가지 않습니다(올릴 권한 없음). 지금은 이 컴퓨터에만 저장됩니다"
elif git remote get-url origin &>/dev/null; then
  echo "원격 저장소: $(git remote get-url origin)"
  if command -v gh &>/dev/null; then
    vis=$(gh repo view --json visibility -q .visibility 2>/dev/null)
    case "$vis" in
      PRIVATE) echo "✓ 비공개(private) — 남이 볼 수 없습니다" ;;
      PUBLIC)  echo "🚨 공개(public)입니다! 여기 쌓이는 대화·통화 내용을 누구나 볼 수 있습니다" ;;
      *)       echo "⚠️ 공개 여부를 확인하지 못했습니다 (gh 로그인 필요) — 수동 확인으로" ;;
    esac
  else
    echo "ℹ️ gh 미설치 — 수동 확인: 브라우저로 저장소 페이지를 열어 이름 옆의 Public/Private 표시를 보세요"
  fi
else
  echo "ℹ️ 원격 저장소 없음 — 모든 것이 이 컴퓨터에만 저장됩니다"
fi
```

결과에 따라:

- **배포 원본에서 받은 사본이면** 멈추지 않는다. 원본의 공개 여부는 참가자가 바꿀 수 없고, 참가자 기록이 그쪽으로 올라가지도 않는다. "원격이 없으면"과 같은 안내를 하고, 백업을 원하면 내 계정에 **비공개** 저장소를 새로 만들어 연결하는 길이 있다고 한 줄 덧붙인다.
- **(내 저장소가) 공개(public)면 여기서 멈춘다.** 비공개로 바꾼 뒤에만 다음 단계로 간다. 바꾸는 법: GitHub 저장소 페이지 → Settings → 맨 아래 Danger Zone → "Change visibility" → Private.
- **비공개면** 한 문장 알려주고 넘어간다: "비공개라 남이 볼 수는 없지만, 내 GitHub 계정이 뚫리면 여기 쌓인 대화도 함께 노출됩니다. 계정에 2단계 인증을 켜두세요."
- **원격이 없으면** 사본이 한 벌뿐임을 알려준다: "이 컴퓨터가 고장 나면 되찾을 수 없습니다. 백업(비공개 원격 또는 주기적 외장 복사)을 권합니다."

### 6. 첫 Daily Note 생성 제안

"오늘의 첫 Daily Note를 만들까요? (Y/n)"
Yes면 `daily-note` 스킬 호출.

### 7. 다음 단계 안내

```
워크스페이스 세팅 완료!

다음에 해볼 것 (이름을 외울 필요 없이 그냥 말하면 됩니다):
1. "오늘 daily note 만들어줘" → 매일의 기록 시작
2. "할 일 추가해줘: XXX" → 첫 할 일
3. "새 프로젝트 시작" → 목적에서 완료까지 7단계로 밀어줍니다

CLAUDE.md에 Claude가 지킬 규칙이 적혀 있습니다. 그중 "항상 이렇게 해줘" 절은
비어 있는데, 여기가 이 워크스페이스가 당신 것이 되는 자리입니다 —
쓰다가 "아니 그렇게 말고" 하는 순간이 오면 Claude가 규칙으로 남길지 물어봅니다.

회사·역할이 바뀌거나 쓰는 도구를 새로 연결하면 "CLAUDE.md에 반영해줘"라고 말씀하세요.
예전 내용이 남아 있으면 Claude가 계속 그 기준으로 일합니다.

자세한 건 README.md 참고!
```

폴더 구조와 저장 위치는 `CLAUDE.md`의 "어디에 저장하나"에 있으므로 여기서 반복하지 않는다. Python 안내도 4단에서 이미 했다 — **같은 말을 두 번 하면 참가자는 둘 다 안 읽는다.**

## 원칙

- **일괄 질문 금지**. 하나씩 물어야 인지 부담 낮음.
- **답변은 짧게 유도**. 긴 자기소개 요구하지 말 것. 막연하면 "지난번 한 번"으로 한 번만 되묻는다.
- **CLAUDE.md 덮어쓰기 금지**. `profile:start`~`profile:end` 마커 사이만 `Edit`로 바꾼다. **절 제목으로 찾지 않는다** — 제목이 바뀌면 못 찾고 새로 만들어 중복시킨다.
- **이미 채워져 있으면** 덮어쓰기 전 사용자에게 확인.
- **프로필은 쓰이는 곳이 있는 항목만 묻는다.** 답이 Claude의 행동을 안 바꾸는 항목(취미·관심사류)은 세팅을 길게 만들 뿐이다.
- **Python 환경은 권장, 강제 X**. 데이터 스킬 안 쓸 사람도 있음.
- **선택 도구(git·Aside·gws)는 세팅 중엔 상태만 체크**. gws 연결은 사용자가 원할 때 한마디로 클로드가 Aside로 진행한다.
- **저장 위치는 숨기지 않는다**. 원격이 공개(public)면 세팅을 멈추고 비공개 전환부터. 대화 원문이 어디로 가는지 사용자가 모른 채 넘어가게 하지 않는다.
- **재실행 안전**. 이미 세팅된 항목은 스킵.

## CLAUDE.md와의 대응

이 스킬이 `CLAUDE.md`의 어디를 건드리는지. **절을 더하거나 이름을 바꾸면 이 표와 `CLAUDE.md` 쪽 같은 표를 함께 고친다.**

| CLAUDE.md 절 | 이 스킬 |
|---|---|
| 내 프로필 | 2·3단이 마커 사이를 채운다 |
| 일하는 방식 | 채우지 않는다 (고정) |
| 항상 이렇게 해줘 | 비워둔다. 7단이 존재만 알린다 |
| 어디에 저장하나 | 1단 시드 체크가 이 경로들을 검사 |
| 지식은 위키에 | 1단 시드 체크 (SCHEMA·index·log) |
| 스킬 | 4·5단 (venv·선택 도구) |

---

Made by Do Better Things
