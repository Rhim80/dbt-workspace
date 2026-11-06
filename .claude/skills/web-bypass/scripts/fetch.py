#!/usr/bin/env python3
"""web-bypass: 막힌 웹 페이지를 3단계로 받는다 + 24h 캐시 + 워크스페이스 저장.

  1. curl          — 브라우저 이름을 단 일반 요청. 사이트가 열어 둔 길(Reddit .rss,
                     네이버 PostView)이 있으면 그 주소도 시도
  2. aside_fetch   — Aside 브라우저 안에서 요청 (탭 없음, 내 로그인 실림)
  3. aside_tab     — Aside 탭으로 열어 화면 글자를 읽음 (확인 화면 통과용, 8~11초)

단계마다 "받았다"를 판정한다: 200 + 화면 글자 MIN_CHARS 이상 + 막힘 문구 없음
(+ --grep을 줬으면 그 말이 있음). 아니면 다음 단계. 2·3단계는 내 계정으로
받은 것이라 결과에 used_login: true로 남긴다. --no-login이면 1단계에서 멈춘다.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "web-bypass"
DEFAULT_TTL = 86400  # 24h
PREVIEW_CHARS = 500
MIN_CHARS = 200        # 이보다 적으면 껍데기. 실측: Medium 첫 화면 310자(정상) / X 안내문 170자 / Reddit 차단 143자
BLOCK_SCAN_CHARS = 8000  # 막힘 문구는 이보다 짧은 페이지에서만 본다 — 긴 정상 글에 낱말만 있는 오탐 방지
GREP_CONTEXT = 200
GREP_MAX = 10
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

# 2026-10-21 실제로 받은 막힘·안내 화면의 문구 (소문자 비교)
BLOCK_PHRASES = [
    "just a moment",                       # Cloudflare 확인 화면
    "attention required",                  # Cloudflare 차단
    "sorry, you have been blocked",
    "access denied",                       # 쿠팡(Akamai)
    "please enable js",                    # G2
    "enable javascript and cookies",
    "blocked by network security",         # Reddit
    "something went wrong, but don",       # X 안내문 (2026-07-06)
    "비공개 글",                            # 네이버 비공개
    "비공개 게시물",
]


def visible_text(content: str) -> str:
    """HTML이면 script·style·태그를 걷어낸 화면 글자만. HTML이 아니면 그대로."""
    head = content[:3000].lower()
    if "<html" not in head and "<body" not in head and "<!doctype" not in head:
        return content.strip()
    t = re.sub(r"<(script|style|noscript|svg|template)\b.*?</\1\s*>", " ",
               content, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


# 안내 문구가 화면 글자에 안 나오는 사이트 — 원본 HTML에 본문 칸이 있어야 받은 것
# (네이버 비공개 글은 "비공개 글"이 스크립트 문자열 안에만 있고 postViewArea가 없다, 2026-10-21)
BODY_MARKERS = [
    (r"^https?://blog\.naver\.com/PostView\.naver", "postViewArea"),
]


def judge(status: int | None, text: str, grep: str | None,
          raw: str = "", target: str = "") -> str:
    """받았으면 "", 아니면 이유. raw·target은 BODY_MARKERS용 (Aside 탭은 raw가 없어 건너뜀)."""
    if status is not None and status != 200:
        return f"http {status}"
    # 찾는 말이 있으면 짧아도 받은 것 (Cloudflare 테스트 통과 화면은 78자)
    if len(text) < MIN_CHARS and not (grep and re.search(grep, text, re.I)):
        return f"thin ({len(text)}자)"
    if raw:
        for pat, marker in BODY_MARKERS:
            if re.match(pat, target) and marker not in raw:
                return f"no body marker: {marker}"
    if len(text) < BLOCK_SCAN_CHARS:
        low = text.lower()
        for p in BLOCK_PHRASES:
            if p in low:
                return f"block phrase: {p}"
    if grep and not re.search(grep, text, re.I):
        return "grep no match"
    return ""


# ---------- 사이트가 열어 둔 길 ----------

def site_routes(url: str) -> list[str]:
    m = re.match(r"https?://(www\.|old\.)?reddit\.com(/r/[^?#]+/comments/[^?#]+?)/?(\?.*)?$", url)
    if m:
        return [f"https://www.reddit.com{m.group(2)}/.rss"]
    m = re.match(r"https?://(m\.)?blog\.naver\.com/([A-Za-z0-9_-]+)/(\d+)", url)
    if m:
        return [f"https://blog.naver.com/PostView.naver?blogId={m.group(2)}&logNo={m.group(3)}"]
    return []


# ---------- 1단계: curl ----------

def step_curl(url: str, timeout: int) -> tuple[int | None, str]:
    try:
        p = subprocess.run(
            ["curl", "-sL", "--compressed", "--max-time", str(timeout), "-A", UA,
             "-w", "\n@@STATUS@@%{http_code}", url],
            capture_output=True, timeout=timeout + 5)
    except subprocess.TimeoutExpired:
        return None, ""
    out = p.stdout.decode("utf-8", errors="replace")
    body, _, code = out.rpartition("\n@@STATUS@@")
    try:
        return int(code.strip()), body
    except ValueError:
        return None, out


# ---------- 2·3단계: Aside ----------

def _local_path(p: str) -> Path:
    """Aside가 알려 준 파일 경로를 이 기계 경로로. WSL이면 Windows 경로를 /mnt/c로."""
    if re.match(r"^[A-Za-z]:\\", p) and shutil.which("wslpath"):
        return Path(subprocess.run(["wslpath", "-u", p], capture_output=True,
                                   text=True).stdout.strip())
    return Path(p)


def _aside(js: str) -> tuple[dict | None, str]:
    """aside repl을 부르고 @@{json}@@ 한 줄을 읽는다. 첫 호출 'not connected'는 한 번 더.

    repl은 긴 출력을 잘라 버리므로 본문은 Aside 세션 폴더에 파일로 쓰고 경로만 받는다."""
    last = ""
    for _ in range(2):
        try:
            p = subprocess.run(["aside", "repl", js], capture_output=True,
                               text=True, timeout=115, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return None, "aside timeout"
        last = p.stdout + p.stderr
        m = re.search(r"@@(\{.*?\})@@", last, re.S)
        if m:
            return json.loads(m.group(1)), ""
        if "not connected" not in last:
            break
    return None, "aside: " + last.strip()[-300:]


def _read_artifact(info: dict) -> str:
    path = _local_path(info["file"])
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        path.unlink(missing_ok=True)
        return text
    except OSError:
        return ""  # 못 읽으면 빈 글 — judge가 thin으로 떨군다


def step_aside_fetch(url: str, key: str) -> tuple[int | None, str, str]:
    js = (f"const u={json.dumps(url)}; const r=await fetch(u); const b=await r.text();"
          " await fs.mkdir('./artifacts',{recursive:true});"
          f" const f='./artifacts/wb_{key}_f.txt'; await fs.writeFile(f,b);"
          " console.log('@@'+JSON.stringify({status:r.status,file:path.resolve(f)})+'@@');")
    info, err = _aside(js)
    if not info:
        return None, "", err
    return info["status"], _read_artifact(info), ""


def step_aside_tab(url: str, key: str) -> tuple[str, str]:
    # 확인 화면이 넘어가길 기다린다: 2초마다 읽어 글자 수가 그대로이고 확인 문구가 없으면 멈춤 (최대 24초)
    js = (f"const u={json.dumps(url)}; const pg=await openTab(u); let prev=-1, tx='';"
          " for (let i=0;i<12;i++) { await sleep(2000); let best='';"
          " for (const fr of pg.frames()) { try { const t=await fr.evaluate(()=>document.body.innerText);"
          " if (t.length>best.length) best=t; } catch(e){} }"
          " tx=best; if (tx.length===prev && !/just a moment|잠시만 기다리/i.test(tx)) break; prev=tx.length; }"
          " await fs.mkdir('./artifacts',{recursive:true});"
          f" const f='./artifacts/wb_{key}_t.txt'; await fs.writeFile(f,tx);"
          " console.log('@@'+JSON.stringify({file:path.resolve(f)})+'@@');")
    info, err = _aside(js)
    if not info:
        return "", err
    return _read_artifact(info), ""


# ---------- 순서 ----------

def run_chain(url: str, *, grep: str | None, no_login: bool, timeout: int) -> dict:
    key = hashlib.sha256(url.encode()).hexdigest()[:12]
    attempts: list[dict] = []

    def record(step, target, status, content, err="", raw=True):
        text = visible_text(content)
        reason = err or judge(status, text, grep, content if raw else "", target)
        attempts.append({"step": step, "url": target, "status": status,
                         "visible_chars": len(text), "reason": reason or "ok"})
        return reason

    for step, target in [("curl", url)] + [("curl:route", r) for r in site_routes(url)]:
        status, body = step_curl(target, timeout)
        if not record(step, target, status, body):
            return _done(url, step, target, False, body, attempts)

    if no_login:
        return _fail(url, attempts, "--no-login: 1단계에서 멈춤")
    if not shutil.which("aside"):
        return _fail(url, attempts, "이 기계에 aside 없음 — 2·3단계 못 함")

    status, body, err = step_aside_fetch(url, key)
    if not record("aside_fetch", url, status, body, err):
        return _done(url, "aside_fetch", url, True, body, attempts)

    text, err = step_aside_tab(url, key)
    if not record("aside_tab", url, None, text, err, raw=False):
        return _done(url, "aside_tab", url, True, text, attempts)
    return _fail(url, attempts, "세 단계 모두 못 받음")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _done(url, step, target, used_login, content, attempts) -> dict:
    return {"url": url, "fetched_at": _now(), "ok": True, "step": step,
            "fetched_url": target, "used_login": used_login,
            "attempts": attempts, "summary": "", "content": content}


def _fail(url, attempts, summary) -> dict:
    return {"url": url, "fetched_at": _now(), "ok": False, "step": None,
            "fetched_url": None, "used_login": False,
            "attempts": attempts, "summary": summary, "content": ""}


# ---------- 캐시·저장 ----------

def cache_path(url: str) -> Path:
    return CACHE_DIR / f"{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}.json"


def read_cache(url: str, ttl: int) -> dict | None:
    p = cache_path(url)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if "step" not in data or not data.get("ok"):
            return None  # 옛 엔진 판 캐시는 다시 받는다
        fetched = datetime.fromisoformat(data["fetched_at"].replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - fetched).total_seconds()
        if age > ttl:
            return None
        data["cache_hit"] = True
        data["cache_age_seconds"] = int(age)
        return data
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def write_cache(url: str, payload: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path(url).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                               encoding="utf-8")


def yaml_quote(s) -> str:
    if s is None:
        return '""'
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def save_to_pkm(payload: dict, text: str, path: Path, force: bool) -> None:
    if path.exists() and not force:
        print(f"ERROR: {path} 이미 존재. --force 옵션으로 덮어쓰기 가능.", file=sys.stderr)
        sys.exit(3)
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = (
        "---\n"
        f"source: {yaml_quote(payload['url'])}\n"
        f"fetched_at: {yaml_quote(payload['fetched_at'])}\n"
        f"step: {yaml_quote(payload.get('step'))}\n"
        f"used_login: {str(payload.get('used_login', False)).lower()}\n"
        "---\n\n"
    )
    path.write_text(frontmatter + text + "\n", encoding="utf-8")
    print(f"saved: {path}", file=sys.stderr)


def main() -> int:
    p = argparse.ArgumentParser(prog="web-bypass",
                                description="막힌 페이지 3단계 받기 (curl → Aside fetch → Aside 탭).")
    p.add_argument("url")
    p.add_argument("--grep", metavar="REGEX",
                   help="찾을 말(대소문자 무시). 단계 판정에도 쓰이고, 앞뒤 문맥을 matches로 돌려준다.")
    p.add_argument("--no-login", action="store_true",
                   help="내 계정을 쓰지 않는다 — 1단계(curl·사이트 길)에서 멈춤.")
    p.add_argument("--save-to-pkm", metavar="PATH", help="화면 글자를 frontmatter와 함께 .md로 저장.")
    p.add_argument("--force", action="store_true", help="--save-to-pkm 경로 덮어쓰기 허용.")
    p.add_argument("--no-cache", action="store_true", help="캐시 무시하고 다시 받기.")
    p.add_argument("--ttl", type=int, default=DEFAULT_TTL, help=f"캐시 TTL 초 (기본 {DEFAULT_TTL}).")
    p.add_argument("--timeout", type=int, default=20, help="curl 한 번의 제한 시간(초).")
    args = p.parse_args()

    payload = None if args.no_cache else read_cache(args.url, args.ttl)
    if payload is not None and (
            (args.no_login and payload.get("used_login"))
            or (args.grep and not re.search(args.grep, visible_text(payload.get("content") or ""), re.I))):
        payload = None  # 계정으로 받은 캐시를 --no-login에 내주지 않는다 / 찾는 말이 없으면 다시 받는다
    if payload is None:
        payload = run_chain(args.url, grep=args.grep, no_login=args.no_login,
                            timeout=args.timeout)
        payload["cache_hit"] = False
        if payload["ok"]:
            write_cache(args.url, payload)

    text = visible_text(payload.get("content") or "")
    if args.save_to_pkm and payload["ok"]:
        save_to_pkm(payload, text, Path(args.save_to_pkm).expanduser(), args.force)

    summary = {
        "ok": payload["ok"],
        "step": payload.get("step"),
        "used_login": payload.get("used_login", False),
        "url": payload["url"],
        "fetched_url": payload.get("fetched_url"),
        "fetched_at": payload["fetched_at"],
        "cache_hit": payload.get("cache_hit", False),
        "visible_chars": len(text),
        "attempts": payload.get("attempts", []),
        "summary": payload.get("summary", ""),
        "cache_file": str(cache_path(args.url)) if payload["ok"] else None,
        "content_preview": text[:PREVIEW_CHARS],
    }
    if args.grep:
        rx = re.compile(args.grep, re.I)
        summary["matches"] = [text[max(0, m.start() - GREP_CONTEXT):m.end() + GREP_CONTEXT]
                              for m in list(rx.finditer(text))[:GREP_MAX]]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
