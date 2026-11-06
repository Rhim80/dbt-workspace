#!/usr/bin/env python3
"""핸드오프 파일(00-system/06-handoffs)의 목록·발췌·저장 검사·세션수·절 교체 — handoff 스킬이 부른다.
셈은 기계가, 해석은 Claude가.

왜 있나: 규칙만으로는 안 지켜진다 — "3~5줄"이라고 적어 둔 절이 수백 줄까지 쌓이고,
같은 숫자를 두 자리에 손으로 적으면 어긋난다. 세는 일과 막는 일을 여기로 내린다.
Python 3.9 이상, 표준 라이브러리만 쓴다 (추가 설치 없음).

사용:
  handoff.py list [--all]            진행 중 작업을 오래된 순으로 — 맨 아래 줄과 `가장 최근:` 줄이 마지막으로 손댄 작업 (--all: 완료·보류 포함)
  handoff.py show <파일>              재개용 발췌 (세션 로그 제외) + 재확인 힌트
  handoff.py check <파일> | --all     저장 검사 — [거부] 하나라도 있으면 rc 1
  handoff.py bump <파일>              세션수 +1 · updated = 지금 (한 핸드오프에 한 번)
  handoff.py close <파일> --status 완료|보류
  handoff.py replace <파일> --section "<절 이름 앞부분>" --content-file <새 절 파일 | ->   `## ` 절 하나만 갈아끼운다 (`-`는 표준입력)
  handoff.py said [--file <대화.jsonl>]  이번 세션에서 사용자가 직접 낸 말(친 말·작업 중 친 말·슬래시·!명령·고른 답·거절 사유)을 시간순으로
  handoff.py --selftest
공통: 맨 앞에 --root <워크스페이스 절대경로> (기본: 이 스크립트가 설치된 워크스페이스)
<파일>: 절대경로 · 워크스페이스 상대경로 · 파일명(핸드오프 폴더 기준, .md 생략 가능)
종료코드: 0 통과 / 1 거부 있음 / 2 못 돌림 (파일·머리말·인자·워크스페이스 — "0건"이 아니다)

못 잡는 것: 코드펜스 안의 `## `(절로 센다) · git을 안 쓰는 폴더의 목표 변경((h)는 git HEAD와 비교 — git이 없으면 건너뛴다)
· bump 두 번(출력 숫자로만 보인다) · 흐름 글이 맞는지(비었는지·자리표인지만 본다 — 이해는 기계가 못 잰다)
· said는 Claude Code 대화 기록만 읽는다(다른 도구의 기록 꼴은 모른다 — --file로 줘도 0건이면 rc 2)
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

HANDOFF_REL = "00-system/06-handoffs"
ENC_IN = "utf-8-sig"   # 읽을 때 — 메모장이 붙인 BOM이 있으면 떼고 읽는다 (쓸 때는 BOM 없이)
ROOT = None   # main이 --root로 정한다. None이면 이 스크립트가 설치된 워크스페이스
# (키, `## ` 뒤 접두) — 접두 일치. 순서가 곧 우선순위(판단물이 판단보다 먼저 — 접두가 겹친다)
KNOWN = [("목표", "목표 · 왜"), ("흐름", "흐름"), ("지난", "지난 스텝 vs 실제"), ("상태", "지금 상태"),
         ("다음", "다음 스텝"), ("대기", "확인 대기"), ("판단물", "판단물이 사는 곳"),
         ("판단", "판단 (뒤집지 말 것)"), ("반복", "반복하지 말 것"), ("로그", "세션 로그"),
         ("재개", "재개 방법")]
TITLE = dict(KNOWN)
SHOW_ORDER = ["목표", "흐름", "지난", "상태", "다음", "대기", "판단물", "판단", "반복"]
REPLACE = ["상태", "다음", "대기"]
REQUIRED = ["흐름", "상태", "다음", "대기", "로그"]   # (k) 없으면 replace가 rc 2로 죽는 자리
REPLACE_MAX, PREV_MAX, STALE_DAYS, SIZE_WARN, RECONFIRM = 10, 5, 14, 40 * 1024, 5
STATUSES = ("진행", "완료", "보류")
GOAL_MARKS = ("**완료 상태**", "**왜 지금**", "**사용자의 말**")
BANNED = ("편이 안전하다", "것이 안전하다")   # 재보지 않은 처방이 명령문처럼 읽히는 문구
PREV_PLACEHOLDER = ("다음 핸드오프에서 채운다", "<이전 다음 스텝")
RE_UPDATED = re.compile(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?$")
RE_YMD = re.compile(r"\d{4}-\d{2}-\d{2}")
RE_CONFIRM = re.compile(r"^>\s*마지막 확인:\s*(\d{4}-\d{2}-\d{2})\s*\(세션수\s*(\d+)\)")
RE_GOAL_META = re.compile(r"^>\s*(목표 블록 최초 작성|마지막 확인):")   # (h) 비교에서 뺀다
RE_LOG_N = re.compile(r"\d+세션째")
RE_PREV_BAD = re.compile(r"안 됨|틀림")


class HandoffError(Exception):
    """못 돌림 — rc 2."""


# ── 자리 ─────────────────────────────────────────────────────────────────────
def ws_root() -> Path:
    r = Path(ROOT).expanduser().resolve() if ROOT else Path(__file__).resolve().parents[4]
    if not (r / "CLAUDE.md").is_file():
        raise HandoffError(f"워크스페이스가 아님 — {r} 에 CLAUDE.md 없음 (--root <워크스페이스 절대경로>로 준다)")
    return r


def handoff_dir() -> Path:
    return ws_root() / HANDOFF_REL


def read_fm(path) -> dict:
    """머리말을 dict으로. 머리말이 없으면 빈 dict (없음을 0으로 위장하지 않는다)."""
    fm: dict = {}
    try:
        with open(path, encoding=ENC_IN) as f:
            if f.readline().rstrip("\r\n") != "---":
                return fm
            for line in f:
                line = line.rstrip("\r\n")
                if line == "---":
                    break
                k, sep, v = line.partition(":")
                if sep and k and not k.startswith((" ", "\t", "#")):
                    fm[k.strip()] = v.strip()
    except (OSError, UnicodeDecodeError):
        return {}
    return fm


def write_lf(path: Path, text: str) -> None:
    """줄 끝을 LF로 고정해 쓴다 — 기본값으로 쓰면 윈도우에서 파일 전체의 줄 끝이 CRLF로 바뀐다."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def resolve(arg: str) -> Path:
    p = Path(arg).expanduser()
    if p.is_absolute():
        cand = p
    elif "/" in arg or "\\" in arg:
        cand = ws_root() / arg.replace("\\", "/")
    else:
        cand = handoff_dir() / (arg if arg.endswith(".md") else arg + ".md")
    if cand.is_file():
        return cand
    for form in ("NFC", "NFD"):   # 맥 파일명 정규화가 갈릴 때
        alt = cand.parent / unicodedata.normalize(form, cand.name)
        if alt.is_file():
            return alt
    raise HandoffError(f"파일 없음 — {cand}")


def load(path: Path):
    fm = read_fm(path)
    if not fm:
        raise HandoffError(f"머리말 없음 — {path.name}")
    try:
        lines = path.read_text(encoding=ENC_IN).splitlines()
    except UnicodeDecodeError as e:
        raise HandoffError(f"UTF-8이 아님 — {path.name}: {e}")
    return fm, lines


def fm_value(fm: dict, key: str) -> str:
    return fm.get(key, "").split(" #")[0].strip()


def set_fm(path: Path, updates: dict) -> None:
    """머리말의 `키:` 줄만 바꾼다 — 나머지는 바이트 그대로."""
    lines = path.read_text(encoding=ENC_IN).splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != "---":
        raise HandoffError(f"머리말 없음 — {path.name}")
    left = dict(updates)
    for i in range(1, len(lines)):
        if lines[i].rstrip("\n") == "---":
            break
        k, sep, _ = lines[i].partition(":")
        if sep and k.strip() in left and not k.startswith((" ", "\t", "#")):
            nl = "\n" if lines[i].endswith("\n") else ""
            lines[i] = f"{k.strip()}: {left.pop(k.strip())}{nl}"
    if left:
        raise HandoffError(f"머리말에 {'·'.join(left)} 없음 — {path.name}")
    write_lf(path, "".join(lines))


# ── 절 ───────────────────────────────────────────────────────────────────────
def find_section(lines, prefix):
    """(시작 idx, 끝 idx-exclusive) — 끝은 다음 `## ` 줄 또는 EOF. 없으면 None.
    검사(check)와 교체(replace)가 같이 쓴다 — 검사가 보는 절과 교체가 바꾸는 절이 같아야 한다."""
    start = None
    for i, ln in enumerate(lines):
        if start is None:
            if ln.startswith("## ") and ln[3:].startswith(prefix):
                start = i
        elif ln.startswith("## "):
            return (start, i)
    return None if start is None else (start, len(lines))


def all_sections(lines):
    out, start = [], None
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            if start is not None:
                out.append((lines[start][3:].strip(), start, i))
            start = i
    if start is not None:
        out.append((lines[start][3:].strip(), start, len(lines)))
    return out


def classify(title: str):
    for key, prefix in KNOWN:
        if title.startswith(prefix):
            return key
    return None


def section_map(lines):
    known, adhoc = {}, []
    for title, s, e in all_sections(lines):
        key = classify(title)
        if key and key not in known:
            known[key] = (s, e)
        elif key is None:
            adhoc.append((title, s, e))
    return known, adhoc


def body(lines, span):
    s, e = span
    return [ln for ln in lines[s + 1:e] if ln.strip() and ln.strip() != "---"]


def goal_parts(lines, span):
    s, e = span
    core, hist, confirm, marks, placeholder = [], [], None, set(), []
    in_hist = False
    seg = lines[s + 1:e]
    for idx, ln in enumerate(seg):
        st = ln.strip()
        if st.startswith("### "):
            in_hist = st.startswith("### 목표가 바뀐 이력")
            continue
        if in_hist:
            if st.startswith("- ") and "(없음" not in st:
                hist.append(st)
            continue
        m = RE_CONFIRM.match(st)
        if m:
            confirm = (m.group(1), int(m.group(2)))
        if not st or st == "---" or RE_GOAL_META.match(st):
            continue
        core.append(st)
        for mark in GOAL_MARKS:
            if st.startswith(mark):
                marks.add(mark)
                text = st[len(mark):].lstrip(" —-:*\"“”'`").strip()
                if not text:   # 값이 다음 줄에 올 수도 있다
                    nxt = [x.strip() for x in seg[idx + 1:] if x.strip()]
                    text = nxt[0].lstrip(" *\"“”'`") if nxt else ""
                if not text or text.startswith("<"):
                    placeholder.append(mark)
    return {"core": core, "hist": hist, "confirm": confirm, "marks": marks,
            "placeholder": placeholder}


def newest_log_heading(lines, span):
    s, e = span
    for ln in lines[s + 1:e]:
        if ln.startswith("### "):
            return ln.strip()
    return None


def head_lines(path: Path):
    """HEAD 판. 추적 안 됨·저장소 아님이면 None (검사는 건너뛴다 — 통과가 아니라 미검사)."""
    try:
        r = subprocess.run(["git", "-C", str(path.parent), "show", "HEAD:./" + path.name],
                           capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", errors="replace").splitlines()


def updated_date(v: str):
    m = RE_YMD.search(v or "")
    return dt.date.fromisoformat(m.group(0)) if m else None


def updated_hm(v: str) -> str:
    m = re.search(r"\d{2}:\d{2}$", v or "")
    return m.group(0) if m else ""


def now_str() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def summary_line(lines, span) -> str:
    if span is None:
        return "(목표 절 없음)"
    s, e = span
    seg = lines[s + 1:e]
    for idx, ln in enumerate(seg):
        st = ln.strip()
        if st.startswith("**완료 상태**"):
            text = st[len("**완료 상태**"):].lstrip(" —-:").strip()
            if not text:
                nxt = [x.strip() for x in seg[idx + 1:] if x.strip()]
                text = nxt[0] if nxt else ""
            text = re.sub(r"\s+", " ", text.replace("*", "")).strip()
            return text[:60] + ("…" if len(text) > 60 else "")
    return "(완료 상태 줄 없음)"


# ── 검사 ─────────────────────────────────────────────────────────────────────
def check_file(path: Path, today=None):
    """(거부 [(글자, 문장)], 경고 [문장]). 못 돌리면 HandoffError."""
    fm, lines = load(path)
    rej, warn = [], []
    known, adhoc = section_map(lines)

    v = fm_value(fm, "status")
    if v not in STATUSES:
        rej.append(("a", f"status — '{v}' (진행·완료·보류만)"))
    v = fm_value(fm, "updated")
    if not RE_UPDATED.match(v):
        rej.append(("b", f"updated — '{v[:60]}' (YYYY-MM-DD HH:MM 꼴; 날짜만도 허용)"))
    v = fm_value(fm, "세션수")
    sessions = int(v) if v.isdigit() else None
    if sessions is None or sessions < 1:
        rej.append(("c", f"세션수 — '{v}' (1 이상 정수 — 0이면 bump를 안 돌린 것)"))
        sessions = sessions or 0

    for key in REQUIRED:
        if key not in known:
            rej.append(("k", f"절 없음 — ## {TITLE[key]}"))
    for key in REPLACE:
        if key in known:
            n = len(body(lines, known[key]))
            if n > REPLACE_MAX:
                rej.append(("d", f"{TITLE[key]} {n}줄 — {REPLACE_MAX}줄 이내 (빈 줄 제외)"))

    if "흐름" in known:
        fb = body(lines, known["흐름"])
        if not fb or any("<" in ln and ">" in ln and "`" not in ln for ln in fb):
            rej.append(("l", "흐름 — 비었거나 자리표 그대로 (칸보다 먼저, 이번 세션을 이해한 글로)"))

    if "지난" in known:
        pb = body(lines, known["지난"])
        empty = not pb or all(any(p in ln for p in PREV_PLACEHOLDER) for ln in pb)
        if empty and sessions >= 2:
            rej.append(("e", f"지난 스텝 vs 실제 — 절이 비었거나 자리표 그대로 (세션수 {sessions} ≥ 2)"))
        elif len(pb) > PREV_MAX:
            rej.append(("e", f"지난 스텝 vs 실제 {len(pb)}줄 — {PREV_MAX}줄 이내"))
    elif sessions >= 2:
        rej.append(("e", f"지난 스텝 vs 실제 — 절 없음 (세션수 {sessions} ≥ 2)"))

    if "목표" in known:
        g = goal_parts(lines, known["목표"])
        for mark in GOAL_MARKS:
            if mark not in g["marks"]:
                rej.append(("f", f"목표 조각 — {mark} 없음"))
            elif mark in g["placeholder"]:
                rej.append(("f", f"목표 조각 — {mark} 자리표 그대로 ('<…>')"))
        if g["confirm"] is None:
            rej.append(("f", "목표 조각 — 마지막 확인 줄 없음 (> 마지막 확인: YYYY-MM-DD (세션수 N))"))
        hl = head_lines(path)
        if hl is not None:
            hk, _ = section_map(hl)
            if "목표" in hk:
                h = goal_parts(hl, hk["목표"])
                if h["core"] != g["core"] and not [x for x in g["hist"] if x not in h["hist"]]:
                    diff = next((x for x in g["core"] if x not in h["core"]), "(줄이 빠짐)")
                    rej.append(("h", f"목표 바뀜 — HEAD와 다른데 목표가 바뀐 이력에 새 줄 없음 (첫 차이: '{diff[:60]}')"))
    else:
        for mark in GOAL_MARKS:
            rej.append(("f", f"목표 조각 — {mark} 없음 (목표 · 왜 절 없음)"))

    if "재개" in known:
        rej.append(("g", "재개 방법 절 — 남아 있음 (한 줄 포인터로 접는다)"))
    if "로그" in known:
        hd = newest_log_heading(lines, known["로그"])
        if hd and RE_LOG_N.search(hd):
            rej.append(("i", f"세션 로그 — 최신 항목에 N세션째 표기: '{hd[:60]}' (### YYYY-MM-DD · 한 줄)"))
    if "반복" in known:
        for ln in body(lines, known["반복"]):
            hit = next((p for p in BANNED if p in ln and not quoted(ln, p)), None)
            if hit:
                rej.append(("j", f"반복하지 말 것 — 안 재본 처방 문구 '{hit}': '{ln.strip()[:60]}'"))

    if adhoc:
        warn.append(f"규약 밖 절 {len(adhoc)}개 — " + ", ".join(t[:30] for t, _, _ in adhoc))
    size = path.stat().st_size
    if size > SIZE_WARN:
        warn.append(f"파일 {size // 1024}KB — {SIZE_WARN // 1024}KB 초과")
    return rej, warn


def quoted(line: str, phrase: str) -> bool:
    """문구의 모든 출현이 따옴표·백틱 안에 있나 — 나쁜 예로 인용한 것은 처방이 아니다.
    하나라도 밖에 있으면 처방."""
    idx = line.find(phrase)
    while idx >= 0:
        inside = (line.count('"', 0, idx) % 2 == 1
                  or line.count("“", 0, idx) > line.count("”", 0, idx)
                  or line.count("`", 0, idx) % 2 == 1)
        if not inside:
            return False
        idx = line.find(phrase, idx + 1)
    return True


def print_check(path: Path, rej, warn) -> None:
    for code, msg in rej:
        print(f"[거부] ({code}) {msg}")
    for msg in warn:
        print(f"[경고] {msg}")
    if rej:
        print(f"{path.name}: 거부 {len(rej)} · 경고 {len(warn)}")
    else:
        print(f"통과 — {path.name}" + (f" (경고 {len(warn)})" if warn else ""))


# ── 하위명령 ─────────────────────────────────────────────────────────────────
def scan(dir_path: Path):
    """(경로, fm) — 머리말 없는 파일은 stderr에 알리고 건너뛴다."""
    out = []
    for p in sorted(dir_path.glob("*.md")):
        fm = read_fm(p)
        if not fm:
            print(f"[정보] 머리말 없음 — 건너뜀: {p.name}", file=sys.stderr)
            continue
        out.append((p, fm))
    return out


def cmd_list(dir_path: Path, all_: bool, today=None, header=None) -> int:
    today = today or dt.date.today()
    if header:
        print(header)
    if not dir_path.is_dir():
        print(f"진행 0건 — 핸드오프 폴더가 아직 없다 (첫 저장 때 만든다: {dir_path})")
        return 0
    print(f"오늘 {today} 기준 · 오래된 순")
    rows, n_stale, counts = [], 0, {}
    for p, fm in scan(dir_path):
        st = fm_value(fm, "status")
        counts[st] = counts.get(st, 0) + 1
        if not all_ and st != "진행":
            continue
        d = updated_date(fm_value(fm, "updated"))
        days = (today - d).days if d else None
        rows.append((days, p, fm, st, updated_hm(fm_value(fm, "updated"))))
    # 같은 날 안에서는 시각 순(시각 없는 값은 그날의 맨 앞) — 날짜만 보면 맨 아래 줄이 가장 최근이 아니다
    rows.sort(key=lambda r: (0 if r[0] is None else 1, -(r[0] or 0), r[4], r[1].name))
    for days, p, fm, st, _hm in rows:
        _, lines = load(p)
        known, _ = section_map(lines)
        n = fm_value(fm, "세션수") or "?"
        day_s = "  ?" if days is None else f"{days:>3}"
        tail = " [updated 못 읽음]" if days is None else (f" [{STALE_DAYS}일+]" if days >= STALE_DAYS else "")
        if days is not None and days >= STALE_DAYS:
            n_stale += 1
        st_s = "" if st == "진행" else f" [{st}]"
        print(f"{day_s}일 · 세션 {n:>2} · {fm_value(fm, '작업') or '(작업 없음)'} · "
              f"{summary_line(lines, known.get('목표'))} · {p.name}{st_s}{tail}")
    if all_:
        print(f"전체 {len(rows)} · " + " · ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    else:
        print(f"진행 {len(rows)}건 · {STALE_DAYS}일+ {n_stale}건")
        if rows and rows[-1][0] is not None:
            print(f"가장 최근: {rows[-1][1].name}")
    return 0


def reconfirm_line(fm, lines, known) -> str:
    """'마지막 확인 … (세션수 k)' = 세션 k까지 겪고 사용자와 목표를 확인했다.
    재개 첫머리 확인은 아직 bump 전이라 지금 세션수, 세션 중 목표를 바꾸거나 다시 확인했으면 bump 뒤 값이 된다.
    그래서 k가 지금 세션수와 같으면 지난 스텝의 '안 됨/틀림'은 그 확인 전에 이미 드러난 것 — 다시 묻지 않는다
    (안 그러면 세션 중 목표를 바꾼 계기였던 '틀림' 때문에 다음 재개마다 목표를 또 묻는다)."""
    sessions = fm_value(fm, "세션수")
    n = int(sessions) if sessions.isdigit() else 0
    g = goal_parts(lines, known["목표"]) if "목표" in known else {"confirm": None}
    at_now = g["confirm"] is not None and g["confirm"][1] >= n
    if "지난" in known and not at_now:
        bad = sum(1 for ln in body(lines, known["지난"]) if RE_PREV_BAD.search(ln))
        if bad:
            return f"재확인: 필요 — 지난 스텝에 '안 됨/틀림' {bad}건"
    if g["confirm"] is None:
        return "재확인: 필요 — 마지막 확인 줄 없음"
    date, at = g["confirm"]
    if n - at >= RECONFIRM:
        return f"재확인: 필요 — 마지막 확인({date}, 세션수 {at}) 뒤 {n - at}세션"
    return f"재확인: 불필요 (마지막 확인 {date}, 세션수 {at} → 지금 {n})"


def cmd_show(path: Path) -> int:
    fm, lines = load(path)
    known, adhoc = section_map(lines)
    print(f"# {path.name}  ({path})")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), 0)
    print("\n".join(lines[:end + 1]))
    print(reconfirm_line(fm, lines, known))
    print()
    for key in SHOW_ORDER:
        if key in known:
            s, e = known[key]
            seg = lines[s:e]
            while seg and not seg[-1].strip():
                seg.pop()
            print("\n".join(seg))
            print()
        elif key == "지난":
            print(f"## {TITLE[key]}\n(절 없음 — 첫 세션이거나 이 규약 이전 파일)\n")
    for title, s, e in adhoc:
        seg = lines[s:e]
        while seg and not seg[-1].strip():
            seg.pop()
        print("\n".join(seg))
        print()
    log_n = (known["로그"][1] - known["로그"][0]) if "로그" in known else 0
    print(f"(생략: 세션 로그 {log_n}줄" + (" · 재개 방법" if "재개" in known else "") + ")")
    return 0


def cmd_check(path: Path) -> int:
    rej, warn = check_file(path)
    print_check(path, rej, warn)
    return 1 if rej else 0


def cmd_check_all(dir_path: Path) -> int:
    n = ok = 0
    tally = {}
    for p, fm in scan(dir_path):
        if fm_value(fm, "status") != "진행":
            continue
        n += 1
        rej, warn = check_file(p)
        print_check(p, rej, warn)
        if not rej:
            ok += 1
        for code, _ in rej:
            tally[code] = tally.get(code, 0) + 1
    codes = " ".join(f"({c}){tally.get(c, 0)}" for c in "abcdefghijkl")
    print(f"요약: {n}파일 · 통과 {ok} · 거부 {n - ok} · {codes}")
    return 1 if n - ok else 0


def cmd_bump(path: Path) -> int:
    fm, _ = load(path)
    v = fm_value(fm, "세션수")
    if not v.isdigit():
        raise HandoffError(f"세션수가 정수가 아님 — '{v}' ({path.name})")
    now = now_str()
    set_fm(path, {"세션수": int(v) + 1, "updated": now})
    print(f"세션수 {v} → {int(v) + 1} · updated {now} — {path.name}")
    return 0


def cmd_close(path: Path, status: str) -> int:
    if status not in ("완료", "보류"):
        raise HandoffError(f"--status는 완료|보류만 ('{status}')")
    load(path)
    now = now_str()
    set_fm(path, {"status": status, "updated": now})
    print(f"status → {status} · updated {now} — {path.name}")
    return 0


def read_content(src: str) -> str:
    """새 절의 글 — `-`면 표준입력(바이트로 받아 UTF-8로 푼다: 윈도우의 표준입력 기본 인코딩은 UTF-8이 아니다), 아니면 파일."""
    if src == "-":
        raw = sys.stdin.buffer.read()
    else:
        p = Path(src).expanduser()
        if not p.is_file():
            raise HandoffError(f"파일 없음 — {p}")
        raw = p.read_bytes()
    try:
        return raw.decode(ENC_IN).replace("\r\n", "\n")
    except UnicodeDecodeError as e:
        raise HandoffError(f"새 절이 UTF-8이 아님 — {e}")


def cmd_replace(path: Path, prefix: str, text: str) -> int:
    """`## <prefix>…` 절 하나만 갈아끼운다 — 범위는 그 헤딩부터 다음 `## ` 줄 직전까지.
    절이 없으면 멈춘다("없으니 덧붙이기" 같은 임의 해석 없음). 쓴 뒤 다른 절 목록이 그대로인지 스스로 확인한다."""
    new = text.splitlines(keepends=True)
    if not new or not (new[0].startswith("## ") and new[0][3:].startswith(prefix)):
        raise HandoffError(f"--content-file 첫 줄이 '## {prefix}…' 헤딩이 아님 (절 이름이 조용히 바뀌면 다음에 못 찾는다)")
    if not new[-1].endswith("\n"):
        new[-1] += "\n"
    if new[-1].strip():
        new.append("\n")
    lines = path.read_text(encoding=ENC_IN).splitlines(keepends=True)
    span = find_section([ln.rstrip("\r\n") for ln in lines], prefix)
    if span is None:
        raise HandoffError(f"'## {prefix}…' 절 없음 — {path.name} (아무것도 안 고침)")
    s, e = span
    others = [ln for i, ln in enumerate(lines) if ln.startswith("## ") and not (s <= i < e)]
    out = lines[:s] + new + lines[e:]
    after = [ln for i, ln in enumerate(out) if ln.startswith("## ") and not (s <= i < s + len(new))]
    if others != after or sum(1 for ln in new if ln.startswith("## ")) != 1:
        raise HandoffError(f"다른 절이 바뀌게 됨 — {path.name} (안 씀; 새 절 안에 `## ` 줄이 하나만 있어야 한다)")
    write_lf(path, "".join(out))
    print(f"교체: {path.name} [{s + 1}~{e}행] ## {prefix}")
    return 0


# ── selftest ─────────────────────────────────────────────────────────────────
SAID_MAX = 800   # 붙여넣은 긴 글은 앞만 — 흐름을 보는 데는 첫머리로 충분하다


def session_transcript() -> Path:
    """지금 세션의 대화 기록 — CLAUDE_CODE_SESSION_ID로 찾는다. '가장 최근 파일'로 고르지 않는다(옆 세션을 집는다)."""
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if not sid:
        raise HandoffError("CLAUDE_CODE_SESSION_ID 없음 — Claude Code 밖이면 --file <대화.jsonl>로 준다")
    hits = sorted((Path.home() / ".claude" / "projects").glob(f"*/{sid}.jsonl"))
    if len(hits) != 1:
        raise HandoffError(f"세션 {sid} 대화 기록 {len(hits)}개 — --file로 준다")
    return hits[0]


# Claude Code가 사용자 말 자리에 끼워 넣는 고정 문구 — 사용자가 한 말이 아니다
HARNESS_SAID = ("The user wants to clarify these questions.",)
# 선택지 답을 감싸는 고정 글 — 앞머리·꼬리를 떼고 "질문"="답"만 남긴다 (모양이 둘이다)
CHOICE_WRAP = re.compile(r"^(?:Your questions have been answered:|The user answered:)\s*"
                         r"|\s*(?:You can now continue with these answers in mind\.?|Read the answers carefully\b.*)$", re.S)
REJECT_SAID = re.compile(r"the user said:\s*(.*)", re.S | re.I)


def _utc(ts: str):
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _harness(t: str) -> bool:
    return t.lstrip().startswith(HARNESS_SAID)


def said_records(path: Path) -> list:
    """[{줄, ts(UTC datetime|None), 종류, 글}] — 사용자가 직접 낸 말 전부, 원문 줄 순서.
    종류: 말(typed) · 작업중(queued — 따로 돈 턴이든 작업 도중 흡수된 말이든) · 명령(슬래시) · !명령 · 고름(선택지 답) · 거절사유(도구 거절에 붙인 글).
    빼는 것: 고정 문구 · 시스템·다른 에이전트가 넣은 것(queued_command origin이 human 아님) · 옆 세션(isSidechain).
    같은 글이 10분 안에 두 번(흡수된 말과 그 턴) 잡히면 앞의 것만."""
    out, ask_ids = [], set()
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict) or d.get("isSidechain"):
                continue
            ts = _utc(d.get("timestamp", ""))
            msg = d.get("message") if isinstance(d.get("message"), dict) else {}
            c = msg.get("content")
            typ, src = d.get("type"), d.get("promptSource")
            got = []
            if typ == "assistant":
                for b in c or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "AskUserQuestion":
                        ask_ids.add(b.get("id"))
            elif typ == "attachment":
                a = d.get("attachment") or {}
                if a.get("type") == "queued_command" and (a.get("origin") or {}).get("kind") == "human":
                    got.append(("작업중", str(a.get("prompt", ""))))
            elif typ == "user" and src in ("typed", "queued"):
                t = c if isinstance(c, str) else "\n".join(
                    b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text")
                got.append(("말" if src == "typed" else "작업중", t))
            elif typ == "user" and isinstance(c, str) and "<command-name>" in c:
                m = re.search(r"<command-name>(.*?)</command-name>", c, re.S)
                a = re.search(r"<command-args>(.*?)</command-args>", c, re.S)
                got.append(("명령", (m.group(1).strip() + " " + (a.group(1).strip() if a else "")).strip()))   # 슬래시 명령은 promptSource가 안 붙는다
            elif typ == "user" and isinstance(c, str) and "<bash-input>" in c:
                m = re.search(r"<bash-input>(.*?)</bash-input>", c, re.S)
                got.append(("!명령", m.group(1).strip() if m else ""))
            elif typ == "user" and isinstance(c, list):
                for b in c:
                    if not (isinstance(b, dict) and b.get("type") == "tool_result"):
                        continue
                    r = b.get("content")
                    if isinstance(r, list):
                        r = " ".join(x.get("text", "") for x in r if isinstance(x, dict))
                    r = str(r or "").strip()
                    if b.get("tool_use_id") in ask_ids and not b.get("is_error"):
                        got.append(("고름", CHOICE_WRAP.sub("", r)))
                    elif b.get("is_error") and "doesn't want to proceed" in r:
                        m = REJECT_SAID.search(r)
                        if m:
                            got.append(("거절사유", m.group(1)))
            for kind, t in got:
                t = t.strip()
                if not t or _harness(t):
                    continue
                if kind == "작업중" and any(o["글"] == t and o["ts"] and ts and abs((ts - o["ts"]).total_seconds()) <= 600 for o in out[-5:]):
                    continue
                out.append({"줄": n, "ts": ts, "종류": kind, "글": t})
    return out


def said_items(path: Path, tz=None) -> list:
    """[(시각 'MM-DD HH:MM', 종류, 글)] — said_records를 표시용으로. 시각은 이 컴퓨터의 시간대(tz를 주면 그 시간대)."""
    return [(r["ts"].astimezone(tz).strftime("%m-%d %H:%M") if r["ts"] else "??", r["종류"], r["글"]) for r in said_records(path)]


def cmd_said(path: Path) -> int:
    items = said_items(path)
    if not items:
        raise HandoffError(f"사용자 말 0건 — {path.name} (읽는 꼴이 안 맞는 기록일 수 있다; '없음'이 아니다)")
    print(f"# 이번 세션 사용자의 말 {len(items)}건 — {path}")
    for i, (when, kind, t) in enumerate(items, 1):
        t = t if len(t) <= SAID_MAX else t[:SAID_MAX] + f" …(+{len(t) - SAID_MAX}자)"
        print(f"[{i}] {when} {'' if kind == '말' else f'({kind}) '}{t}")
    return 0


def fixture(**kw) -> str:
    o = {"status": "진행", "updated": "2026-09-02 10:00", "sessions": "3",
         "goal_done": "게이트가 저장을 막는다", "confirm": "> 마지막 확인: 2026-08-20 (세션수 2)",
         "voice": '**사용자의 말** — *"이대로 만들자"*', "hist": "- (없음)",
         "prev": "- 게이트 만들기 → 됨 — 셀프테스트 통과\n- 문서 고치기 → 됨\n- 훅 등록 → 안 함 — 다음 단계로 미룸",
         "state": "- 완료: 스크립트\n- 진행 중: 문서\n- 막힌 지점: (없음)",
         "nxt": "1. **check 돌리기** — 게이트 검증\n2. **문서 커밋** — 마감",
         "flow": "이번 세션의 중심은 게이트였다. 스크립트는 됐고 문서가 남았다 — 문서는 게이트가 확정돼야 쓸 수 있다.",
         "wait": "(없음)", "repeat": "1. sort|uniq로 한글 집계 → 합쳐진다 (실측)",
         "log_new": "### 2026-09-02 · 게이트 통과", "extra": "## 재료\n\n- 임의 절\n",
         "resume": False, "drop": ()}
    o.update(kw)
    parts = [
        ("머리", f"---\n작업: 시험 작업\nstatus: {o['status']}\n프로젝트: (없음)\n"
                f"updated: {o['updated']}\n세션수: {o['sessions']}\n---\n\n# 핸드오프 — 시험 작업\n"),
        ("목표", "## 목표 · 왜 (이게 흐려지면 다시 여기로)\n\n> 목표 블록 최초 작성: 2026-08-01\n"
                f"{o['confirm']}\n\n**완료 상태** — {o['goal_done']}\n\n**왜 지금** — 마찰 하나\n"
                f"근거: `00-system/06-handoffs/`\n\n{o['voice']}\n\n### 목표가 바뀐 이력\n\n{o['hist']}\n\n---\n"),
        ("흐름", f"## 흐름  *(매 세션 새로 씀)*\n\n{o['flow']}\n"),
        ("지난", f"## 지난 스텝 vs 실제  *(매 세션 교체, 5줄 이내)*\n\n{o['prev']}\n"),
        ("상태", f"## 지금 상태  *(매 세션 교체, 10줄 이내)*\n\n{o['state']}\n"),
        ("다음", f"## 다음 스텝  *(매 세션 교체, 10줄 이내)*\n\n{o['nxt']}\n"),
        ("대기", f"## 확인 대기  *(매 세션 교체, 10줄 이내)*\n\n{o['wait']}\n"),
        ("판단물", "## 판단물이 사는 곳\n\n- `x.md` — 원본\n\n---\n"),
        ("판단", "## 판단 (뒤집지 말 것)  *(누적)*\n\n1. 판단 하나 — 근거: 실측\n"),
        ("반복", f"## 반복하지 말 것  *(누적)*\n\n{o['repeat']}\n"),
        ("extra", o["extra"]),
        ("로그", f"## 세션 로그  *(누적, 최신이 위)*\n\n{o['log_new']}\n- 한 것 하나\n\n"
                "### 2026-08-20 (2세션째) · ~1h\n- 옛 항목 — 로그 문장\n\n---\n"),
        ("꼬리", "재개: 새 세션 첫 메시지로 `/handoff 재개 시험-작업.md`\n"),
    ]
    text = "\n".join(t for k, t in parts if k not in o["drop"] and t)
    if o["resume"]:
        text += "\n## 재개 방법\n\n이 파일을 받은 새 세션은:\n\n- 목표를 먼저 읽는다.\n"
    return text


def selftest() -> int:
    tmp = Path(tempfile.mkdtemp())
    fail = 0

    def case(name, cond):
        nonlocal fail
        if cond:
            print(f"ok  {name}")
        else:
            print(f"FAIL {name}")
            fail += 1

    def codes(text, name="f.md"):
        p = tmp / name
        p.write_text(text, encoding="utf-8")
        rej, warn = check_file(p, today=dt.date(2026, 9, 2))
        return [c for c, _ in rej], warn

    c, w = codes(fixture())
    case("F0 건강 파일 — 거부 0·경고 1(규약 밖 절)", c == [] and len(w) == 1 and "규약 밖 절" in w[0])
    case("(a) status 어휘", "a" in codes(fixture(status="진행중"))[0])
    case("(b) updated 꼴", "b" in codes(fixture(updated="2026-09-01 실행"))[0])
    case("(b) 날짜만은 허용", "b" not in codes(fixture(updated="2026-09-01"))[0])
    case("(c) 세션수 정수", "c" in codes(fixture(sessions="N"))[0])
    case("(c) 세션수 0 = bump 안 돌림", "c" in codes(fixture(sessions="0"))[0])
    eleven = "\n".join(f"- 줄 {i}" + ("\n" if i % 3 == 0 else "") for i in range(1, 12))
    c, _ = codes(fixture(state=eleven))
    case("(d) 11줄(빈 줄 섞임) 거부 — 한 번만", c.count("d") == 1)
    case("(d) 10줄은 통과", "d" not in codes(fixture(state="\n".join(f"- {i}" for i in range(10))))[0])
    case("(e) 세션수 2인데 절 없음", "e" in codes(fixture(sessions="2", drop=("지난",)))[0])
    case("(e) 6줄", "e" in codes(fixture(prev="\n".join(f"- s{i} → 됨" for i in range(6))))[0])
    case("(e) 세션수 1이면 절 없어도 통과", "e" not in codes(fixture(sessions="1", drop=("지난",)))[0])
    case("(e) 자리표 그대로면 거부", "e" in codes(fixture(prev="- (규약 이전 파일 — 다음 핸드오프에서 채운다)"))[0])
    case("(f) 완료 상태 자리표", "f" in codes(fixture(goal_done="<무엇이 되면 끝인가>"))[0])
    case("(f) 사용자의 말 없음", "f" in codes(fixture(voice=""))[0])
    case("(f) 마지막 확인 줄 없음", "f" in codes(fixture(confirm=""))[0])
    case("(g) 재개 방법 절", "g" in codes(fixture(resume=True))[0])
    case("(i) 최신 로그 헤딩에 N세션째", "i" in codes(fixture(log_new="### 2026-09-02 (4세션째) · 마감"))[0])
    case("(i) 옛 항목의 N세션째는 허용", "i" not in codes(fixture())[0])
    case("(j) 안 재본 처방 문구", "j" in codes(fixture(repeat="1. 대화별로 따로 가져오는 편이 안전하다"))[0])
    case("(j) 따옴표 안 인용은 처방이 아님",
         "j" not in codes(fixture(repeat='1. 교훈: *"따로 가져오는 편이 안전하다"*가 안 재본 처방이었다'))[0])
    case("(j) 백틱 안 인용도 처방이 아님",
         "j" not in codes(fixture(repeat="1. `하는 편이 안전하다`로 좁혀 등록 → \"가져오는 편이 안전하다\"를 못 잡음"))[0])
    case("(j) 인용 뒤에 맨 문구가 또 오면 처방",
         "j" in codes(fixture(repeat='1. "X 편이 안전하다"라고들 하는데, 실제로 따로 하는 편이 안전하다'))[0])
    case("(k) 확인 대기 절 없음", "k" in codes(fixture(drop=("대기",)))[0])

    # (h) — git이 있어야 돈다
    g = tmp / "repo"
    g.mkdir()
    git = ["git", "-C", str(g), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
    ok_git = subprocess.run(git + ["init", "-q"], capture_output=True).returncode == 0
    if ok_git:
        f = g / "h.md"
        f.write_text(fixture(), encoding="utf-8")
        subprocess.run(git + ["add", "h.md"], capture_output=True)
        ok_git = subprocess.run(git + ["commit", "-q", "-m", "x"], capture_output=True).returncode == 0
    if ok_git:
        f.write_text(fixture(goal_done="게이트가 저장을 막고 목록도 낸다"), encoding="utf-8")
        case("(h) 목표 바뀌고 이력 없음 → 거부", "h" in [c for c, _ in check_file(f)[0]])
        f.write_text(fixture(goal_done="게이트가 저장을 막고 목록도 낸다",
                             hist='- 2026-09-02 — "막는다"에서 "막고 목록도"로. 이유: 시험'), encoding="utf-8")
        case("(h) 이력 한 줄 있으면 통과", "h" not in [c for c, _ in check_file(f)[0]])
        f.write_text(fixture(confirm="> 마지막 확인: 2026-09-02 (세션수 3)"), encoding="utf-8")
        case("(h) 마지막 확인 줄만 바뀌면 통과", "h" not in [c for c, _ in check_file(f)[0]])
        u = g / "untracked.md"
        u.write_text(fixture(goal_done="완전히 다른 목표"), encoding="utf-8")
        case("(h) untracked는 건너뜀", "h" not in [c for c, _ in check_file(u)[0]])
    else:
        print("skip (h) — git을 못 돌림")

    # find_section 일치 — 검사가 보는 절 == 교체가 바꾸는 절 (EOF 끝 절 포함)
    lines = fixture(extra="## 재료\n\n- 임의 절\n").splitlines()
    known, adhoc = section_map(lines)
    par = all(find_section(lines, TITLE[k]) == known[k] for k in known) and \
        find_section(lines, "재료") == adhoc[0][1:]
    lines2 = "## 확인 대기\n- a\n## 재료\n- b\n".splitlines()
    k2, a2 = section_map(lines2)
    par = par and k2["대기"] == find_section(lines2, "확인 대기") == (0, 2) and a2[0][1:] == (2, 4)
    case("find_section == section_map (EOF 끝 절 포함)", par)

    # bump / close
    p = tmp / "b.md"
    p.write_text(fixture(), encoding="utf-8")
    before = p.read_text(encoding="utf-8").splitlines()
    with contextlib.redirect_stdout(io.StringIO()):
        cmd_bump(p)
    after = p.read_text(encoding="utf-8").splitlines()
    diff = [(a, b) for a, b in zip(before, after) if a != b]
    case("bump — 세션수 3→4·updated 갱신, 다른 줄 그대로",
         len(before) == len(after) and len(diff) == 2 and any(b == "세션수: 4" for _, b in diff)
         and any(b.startswith("updated: ") and RE_UPDATED.match(b[9:]) for _, b in diff))
    with contextlib.redirect_stdout(io.StringIO()):
        cmd_close(p, "보류")
    case("close — 보류", read_fm(p)["status"] == "보류")
    before_t = p.read_text(encoding="utf-8")
    try:
        cmd_close(p, "완료됨")
        case("close — 잘못된 status는 거부", False)
    except HandoffError:
        case("close — 잘못된 status는 거부·파일 불변", p.read_text(encoding="utf-8") == before_t)

    # show
    s = tmp / "s.md"
    s.write_text(fixture(), encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_show(s)
    out = buf.getvalue()
    case("show — 목표·다음 스텝·임의 절 포함, 세션 로그 문장 제외",
         "## 목표 · 왜" in out and "## 다음 스텝" in out and "- 임의 절" in out and "로그 문장" not in out)
    case("show — 재확인 불필요(F0)", "재확인: 불필요" in out)
    s.write_text(fixture(prev="- 훅 등록 → 안 됨 — 미룸"), encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_show(s)
    case("show — 지난 스텝에 '안 됨'이면 재확인 필요", "재확인: 필요 — 지난 스텝" in buf.getvalue())
    s.write_text(fixture(prev="- 목록 만들기 → 틀림 — 목표가 바뀜", confirm="> 마지막 확인: 2026-09-02 (세션수 3)"), encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_show(s)
    case("show — '틀림'이 있어도 이번 세션에 목표를 확인했으면(세션수 같음) 불필요", "재확인: 불필요" in buf.getvalue())
    s.write_text(fixture(sessions="8"), encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_show(s)
    case("show — 마지막 확인 뒤 5세션 넘으면 재확인 필요", "재확인: 필요 — 마지막 확인" in buf.getvalue())

    # list / check --all
    d = tmp / "dir"
    d.mkdir()
    (d / "old.md").write_text(fixture(updated="2026-08-13 09:00"), encoding="utf-8")
    (d / "new.md").write_text(fixture(updated="2026-09-02 09:00"), encoding="utf-8")
    (d / "done.md").write_text(fixture(status="완료"), encoding="utf-8")
    (d / "bad.md").write_text(fixture(updated="없음"), encoding="utf-8")
    (d / "nofm.md").write_text("# 머리말 없음\n", encoding="utf-8")
    buf, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        cmd_list(d, all_=False, today=dt.date(2026, 9, 2))
    rows = [ln for ln in buf.getvalue().splitlines() if "일 · 세션" in ln]
    case("list — 순서: 못 읽음 → 오래된 → 오늘, 완료 제외, 14일+ 표시",
         [r.split(" · ")[-1].split(" [")[0] for r in rows] == ["bad.md", "old.md", "new.md"]
         and "[14일+]" in rows[1] and "[14일+]" not in rows[2] and "진행 3건 · 14일+ 1건" in buf.getvalue())
    case("list — 머리말 없는 파일은 stderr로", "nofm.md" in err.getvalue())
    case("list — 가장 최근 줄", "가장 최근: new.md" in buf.getvalue().splitlines())
    d2 = tmp / "dir2"
    d2.mkdir()
    (d2 / "a-late.md").write_text(fixture(updated="2026-09-02 13:28"), encoding="utf-8")
    (d2 / "b-early.md").write_text(fixture(updated="2026-09-02 11:59"), encoding="utf-8")
    (d2 / "c-notime.md").write_text(fixture(updated="2026-09-02"), encoding="utf-8")
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2), contextlib.redirect_stderr(io.StringIO()):
        cmd_list(d2, all_=False, today=dt.date(2026, 9, 2))
    rows2 = [ln.split(" · ")[-1] for ln in buf2.getvalue().splitlines() if "일 · 세션" in ln]
    case("list — 같은 날은 시각 순(이름 순 아님), 시각 없는 값은 그날 맨 앞, 가장 최근 = 맨 아래",
         rows2 == ["c-notime.md", "b-early.md", "a-late.md"]
         and "가장 최근: a-late.md" in buf2.getvalue().splitlines())
    d3 = tmp / "dir3"
    d3.mkdir()
    (d3 / "bad.md").write_text(fixture(updated="없음"), encoding="utf-8")
    buf3 = io.StringIO()
    with contextlib.redirect_stdout(buf3), contextlib.redirect_stderr(io.StringIO()):
        cmd_list(d3, all_=False, today=dt.date(2026, 9, 2))
    case("list — updated를 못 읽은 파일뿐이면 가장 최근 줄을 내지 않는다", "가장 최근" not in buf3.getvalue())
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        cmd_list(d, all_=True, today=dt.date(2026, 9, 2))
    case("list --all — 완료 포함", "done.md [완료]" in buf.getvalue())
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        rc = cmd_check_all(d)
    case("check --all — rc 1 + 집계줄", rc == 1 and "요약: 3파일" in buf.getvalue() and "(b)1" in buf.getvalue())

    case("(k) 흐름 절 없음 거부", "k" in codes(fixture(drop=("흐름",)))[0])
    case("(l) 흐름 자리표 거부", "l" in codes(fixture(flow="<이번 세션의 중심>"))[0])
    case("(l) 흐름 빈 절 거부", "l" in codes(fixture(flow=""))[0])
    case("(l) 백틱 속 <…>는 통과", "l" not in codes(fixture(flow="`<파일>` 꼴로 부른다. 중심은 게이트였다."))[0])

    # replace
    r = tmp / "r.md"
    r.write_text(fixture(), encoding="utf-8")
    nf = tmp / "new.md"
    nf.write_text("## 지금 상태  *(매 세션 교체, 10줄 이내)*\n\n- 완료: 새 내용", encoding="utf-8")
    with contextlib.redirect_stdout(io.StringIO()):
        cmd_replace(r, "지금 상태", read_content(str(nf)))
    t = r.read_text(encoding="utf-8")
    case("replace — 그 절만 바뀌고 앞뒤 절은 그대로",
         "- 완료: 새 내용" in t and "- 완료: 스크립트" not in t and "## 다음 스텝" in t and "**check 돌리기**" in t
         and "게이트가 저장을 막는다" in t and check_file(r, today=dt.date(2026, 9, 2))[0] == [])
    before_t = r.read_text(encoding="utf-8")
    for label, prefix, text in (("없는 절", "없는 절", "## 없는 절\n- x\n"),
                                ("헤딩이 다른 새 절", "지금 상태", "## 다음 스텝\n- x\n"),
                                ("새 절 안에 `## `가 둘", "지금 상태", "## 지금 상태\n- x\n## 끼어든 절\n- y\n")):
        nf.write_text(text, encoding="utf-8")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                cmd_replace(r, prefix, read_content(str(nf)))
            case(f"replace — {label}은 거부", False)
        except HandoffError:
            case(f"replace — {label}은 거부·파일 불변", r.read_text(encoding="utf-8") == before_t)

    # 윈도우에서 생기는 모양 — CRLF·BOM 파일도 읽고, 쓴 뒤에는 LF·BOM 없음
    w = tmp / "win.md"
    w.write_bytes(b"\xef\xbb\xbf" + fixture().replace("\n", "\r\n").encode("utf-8"))
    case("윈도우 — BOM·CRLF 파일도 검사 통과", check_file(w, today=dt.date(2026, 9, 2))[0] == [])
    with contextlib.redirect_stdout(io.StringIO()):
        cmd_bump(w)
        cmd_replace(w, "지금 상태", "## 지금 상태  *(매 세션 교체, 10줄 이내)*\r\n\r\n- 완료: 새 내용\r\n".replace("\r\n", "\n"))
    raw = w.read_bytes()
    case("윈도우 — bump·replace 뒤 줄 끝은 LF, BOM 없음, 검사 통과",
         b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf") and read_fm(w)["세션수"] == "4"
         and check_file(w, today=dt.date(2026, 9, 2))[0] == [])
    nf.write_bytes("## 확인 대기\r\n\r\n- 한글 줄\r\n".encode("utf-8"))
    case("윈도우 — CRLF로 온 새 절 글은 LF로 받는다", read_content(str(nf)) == "## 확인 대기\n\n- 한글 줄\n")

    # 자리 — 워크스페이스가 아니면 멈춘다 / 폴더가 없으면 0건
    global ROOT
    keep = ROOT
    ROOT = str(tmp / "ws")
    (tmp / "ws").mkdir()
    try:
        handoff_dir()
        case("자리 — CLAUDE.md 없는 폴더는 거부", False)
    except HandoffError:
        case("자리 — CLAUDE.md 없는 폴더는 거부", True)
    (tmp / "ws" / "CLAUDE.md").write_text("# x\n", encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cmd_list(handoff_dir(), all_=False)
    case("자리 — 핸드오프 폴더가 없으면 0건으로 알리고 rc 0", rc == 0 and "진행 0건" in buf.getvalue() and "가장 최근" not in buf.getvalue())
    (tmp / "ws" / "00-system" / "06-handoffs").mkdir(parents=True)
    (tmp / "ws" / "00-system" / "06-handoffs" / "x.md").write_text(fixture(), encoding="utf-8")
    case("자리 — 역슬래시로 적은 상대경로도 찾는다",
         resolve("00-system\\06-handoffs\\x.md").name == "x.md" and resolve("x").name == "x.md")
    ROOT = keep

    j = tmp / "t.jsonl"
    recs = [{"type": "user", "timestamp": "2026-09-26T03:05:00Z", "message": {"content": "<command-message>handoff</command-message>\n<command-name>/handoff</command-name>\n<command-args>재개 x.md</command-args>"}},
            {"type": "user", "promptSource": "typed", "timestamp": "2026-09-26T03:06:00Z", "message": {"content": "1편부터 하자"}},
            {"type": "user", "promptSource": "system", "timestamp": "2026-09-26T03:07:00Z", "message": {"content": "훅 알림"}},
            {"type": "user", "promptSource": "typed", "isSidechain": True, "timestamp": "2026-09-26T03:07:00Z", "message": {"content": "옆"}},
            {"type": "assistant", "timestamp": "2026-09-26T03:08:00Z", "message": {"content": [{"type": "tool_use", "id": "q1", "name": "AskUserQuestion", "input": {}}]}},
            {"type": "user", "timestamp": "2026-09-26T03:09:00Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "q1", "content": "매번 새로 쓰기"}]}},
            {"type": "user", "timestamp": "2026-09-26T03:09:30Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "x9", "content": "ls 출력"}]}},
            {"type": "assistant", "timestamp": "2026-09-26T03:09:40Z", "message": {"content": [{"type": "tool_use", "id": "q2", "name": "AskUserQuestion", "input": {}}]}},
            {"type": "user", "timestamp": "2026-09-26T03:09:50Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "q2", "content": 'The user answered: "무엇부터?"="1편". Read the answers carefully — they may request clarification, changes, or that you not proceed — and follow what they actually say.'}]}},
            {"type": "user", "promptSource": "typed", "timestamp": "2026-09-26T03:10:00Z", "message": {"content": [{"type": "text", "text": "장기기억이 중요해"}]}},
            {"type": "user", "promptSource": "queued", "timestamp": "2026-09-26T03:11:00Z", "message": {"content": "작업 중에 친 말"}},
            {"type": "attachment", "timestamp": "2026-09-26T03:12:00Z", "attachment": {"type": "queued_command", "prompt": "흡수된 말", "origin": {"kind": "human"}}},
            {"type": "attachment", "timestamp": "2026-09-26T03:12:10Z", "attachment": {"type": "queued_command", "prompt": "<agent-message from=x>보고</agent-message>", "origin": {"kind": "peer"}}},
            {"type": "attachment", "timestamp": "2026-09-26T03:12:20Z", "attachment": {"type": "queued_command", "prompt": "<task-notification>끝</task-notification>"}},
            {"type": "user", "promptSource": "queued", "timestamp": "2026-09-26T03:13:00Z", "message": {"content": "흡수된 말"}},
            {"type": "user", "timestamp": "2026-09-26T03:14:00Z", "message": {"content": "<bash-input>git status</bash-input>"}},
            {"type": "user", "timestamp": "2026-09-26T03:15:00Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "b1", "is_error": True, "content": "The user doesn't want to proceed with this tool use. The tool use was rejected. the user said:\n세 세션으로 나누자"}]}},
            {"type": "user", "timestamp": "2026-09-26T03:16:00Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "b2", "is_error": True, "content": "The user doesn't want to proceed with this tool use. the user said:\nThe user wants to clarify these questions.\n    This means"}]}},
            {"type": "user", "timestamp": "2026-09-26T03:17:00Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "b3", "is_error": True, "content": "The user doesn't want to proceed with this tool use. STOP what you are doing"}]}}]
    j.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\nnot json\n", encoding="utf-8")
    it = said_items(j, dt.timezone(dt.timedelta(hours=9)))
    case("said — 명령·typed·작업중·!명령·고른 답·거절사유, 시스템·에이전트·고정 문구·옆 세션·도구 출력 제외, 흡수 중복 1번, 시간대 변환",
         [(k, t) for _, k, t in it] == [("명령", "/handoff 재개 x.md"), ("말", "1편부터 하자"), ("고름", "매번 새로 쓰기"), ("고름", '"무엇부터?"="1편".'), ("말", "장기기억이 중요해"),
                                        ("작업중", "작업 중에 친 말"), ("작업중", "흡수된 말"), ("!명령", "git status"), ("거절사유", "세 세션으로 나누자")]
         and it[1][0] == "09-26 12:06")
    e = tmp / "e.jsonl"
    e.write_text('{"type":"assistant"}\n', encoding="utf-8")
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_said(e)
        case("said — 0건이면 멈춤(rc 2 경로)", False)
    except HandoffError:
        case("said — 0건이면 멈춤(rc 2 경로)", True)

    print("전부 통과" if fail == 0 else f"실패 {fail}건")
    return 1 if fail else 0


# ── main ─────────────────────────────────────────────────────────────────────
def usage() -> int:
    print(__doc__.split("사용:")[1].split("못 잡는 것")[0].rstrip(), file=sys.stderr)
    return 2


def main(argv) -> int:
    global ROOT
    for stream in (sys.stdout, sys.stderr):   # 윈도우 콘솔이 한글을 못 찍어 죽는 것을 막는다
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) >= 2 and argv[0] == "--root":
        ROOT, argv = argv[1], argv[2:]
    if not argv:
        return usage()
    if argv[0] == "--selftest":
        return selftest()
    cmd, rest = argv[0], argv[1:]
    try:
        if cmd == "list":
            if rest and rest != ["--all"]:
                return usage()
            return cmd_list(handoff_dir(), all_="--all" in rest, header=f"핸드오프: {handoff_dir()}")
        if cmd == "check":
            if rest == ["--all"]:
                return cmd_check_all(handoff_dir())
            if len(rest) != 1:
                return usage()
            return cmd_check(resolve(rest[0]))
        if cmd in ("show", "bump") and len(rest) == 1:
            return {"show": cmd_show, "bump": cmd_bump}[cmd](resolve(rest[0]))
        if cmd == "said":
            if rest and (len(rest) != 2 or rest[0] != "--file"):
                return usage()
            if rest and not Path(rest[1]).expanduser().is_file():
                raise HandoffError(f"파일 없음 — {rest[1]}")
            return cmd_said(Path(rest[1]).expanduser() if rest else session_transcript())
        if cmd == "close" and len(rest) == 3 and rest[1] == "--status":
            return cmd_close(resolve(rest[0]), rest[2])
        if cmd == "replace" and len(rest) == 5 and rest[1] == "--section" and rest[3] == "--content-file":
            return cmd_replace(resolve(rest[0]), rest[2], read_content(rest[4]))
        return usage()
    except HandoffError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
