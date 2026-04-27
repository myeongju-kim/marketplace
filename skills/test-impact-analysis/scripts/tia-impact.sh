#!/usr/bin/env bash
set -euo pipefail

PR_URL="${1:-}"
DOMAIN_FILE="${2:-}"

if [ -z "$PR_URL" ]; then
  echo "사용법: ./tia-impact.sh <PR_URL> [DOMAIN_FILE]"
  exit 1
fi

if [ -n "$DOMAIN_FILE" ] && [ ! -f "$DOMAIN_FILE" ]; then
  echo "도메인 설명 파일을 찾을 수 없습니다: $DOMAIN_FILE"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
REPORT_PATH="${ROOT_DIR}/tia-report.md"
DOMAIN_FILE_ABS=""

if [ -n "$DOMAIN_FILE" ]; then
  DOMAIN_FILE_ABS="$(cd "$(dirname "$DOMAIN_FILE")" && pwd)/$(basename "$DOMAIN_FILE")"
fi

cd "$ROOT_DIR"

echo "TIA 분석을 시작합니다."
echo "PR 주소: ${PR_URL}"
if [ -n "$DOMAIN_FILE_ABS" ]; then
  echo "도메인 설명 파일: ${DOMAIN_FILE_ABS}"
else
  echo "도메인 설명 파일: 없음"
fi

BASE_REF=""
HEAD_REF=""

if command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI를 사용하여 PR 정보를 조회합니다."
  PR_NUMBER="$(echo "$PR_URL" | sed -E 's#.*/pull/([0-9]+).*#\1#')"

  if [ -n "$PR_NUMBER" ] && [ "$PR_NUMBER" != "$PR_URL" ]; then
    BASE_REF="$(gh pr view "$PR_NUMBER" --json baseRefName -q '.baseRefName' 2>/dev/null || true)"
    HEAD_REF="$(gh pr view "$PR_NUMBER" --json headRefName -q '.headRefName' 2>/dev/null || true)"
  fi
fi

if [ -z "$BASE_REF" ]; then
  BASE_REF="origin/main"
fi

if [ -z "$HEAD_REF" ]; then
  HEAD_REF="HEAD"
fi

echo "Base: ${BASE_REF}"
echo "Head: ${HEAD_REF}"

git fetch --all --quiet || true

DIFF_FILE="$(mktemp)"
git diff --name-only "${BASE_REF}...${HEAD_REF}" > "$DIFF_FILE" || git diff --name-only > "$DIFF_FILE"

if [ -n "$DOMAIN_FILE_ABS" ]; then
  python3 "${SCRIPT_DIR}/tia_callgraph.py" \
    --root "$ROOT_DIR" \
    --diff-file "$DIFF_FILE" \
    --pr-url "$PR_URL" \
    --base-ref "$BASE_REF" \
    --head-ref "$HEAD_REF" \
    --domain-file "$DOMAIN_FILE_ABS" \
    --output "$REPORT_PATH"
else
  python3 "${SCRIPT_DIR}/tia_callgraph.py" \
    --root "$ROOT_DIR" \
    --diff-file "$DIFF_FILE" \
    --pr-url "$PR_URL" \
    --base-ref "$BASE_REF" \
    --head-ref "$HEAD_REF" \
    --output "$REPORT_PATH"
fi

rm -f "$DIFF_FILE"

echo "분석 리포트 생성 완료: ${REPORT_PATH}"
