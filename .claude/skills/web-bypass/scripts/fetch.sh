#!/usr/bin/env bash
# web-bypass thin wrapper — fetch.py는 표준 라이브러리만 쓴다 (curl·aside는 외부 명령).
#
# 사용법:
#   bash .claude/skills/web-bypass/scripts/fetch.sh <URL> [--grep REGEX] [--no-login]
#        [--save-to-pkm PATH] [--force] [--no-cache] [--ttl SEC] [--timeout N]
#
# 종료 코드:
#   0  받음
#   1  못 받음 (세 단계 모두, 또는 --no-login·aside 없음으로 1단계에서 멈춤)
#   2  CLI 인자 오류 또는 파이썬 없음
#   3  --save-to-pkm 경로 충돌 (--force 없이 덮어쓰기 시도)

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 파이썬 이름은 OS마다 다르다. 윈도우에는 실행되지 않는 가짜 python3가 깔려 있어서
# 이름만 보지 않고 실제로 실행해 보고 되는 것을 쓴다.
PY=""
for c in python3 python py; do
  if "$c" -c 'import sys; assert sys.version_info >= (3, 9)' >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -z "$PY" ] && { echo "Python 3.9 이상이 필요합니다. setup-workspace의 Python 설치 안내를 따르세요." >&2; exit 2; }

exec "$PY" "$SKILL_DIR/scripts/fetch.py" "$@"
