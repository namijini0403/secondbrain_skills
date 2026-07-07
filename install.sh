#!/usr/bin/env bash
# install.sh — second brain / 교육과정 KB 설치기 (macOS/Linux)
# 사용법: ./install.sh <대상폴더> [second-brain|curriculum-kb|kg-research] [--with-security]
set -euo pipefail

TARGET="${1:?사용법: ./install.sh <대상폴더> [second-brain|curriculum-kb|kg-research] [--with-security]}"
KIND="${2:-second-brain}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
WITH_SECURITY=0
for a in "$@"; do [ "$a" = "--with-security" ] && WITH_SECURITY=1; done

copy_if_missing() { # $1=src dir, $2=dst dir — 기존 파일은 덮어쓰지 않음
  (cd "$1" && find . -type f) | while read -r rel; do
    rel="${rel#./}"
    if [ -e "$2/$rel" ]; then echo "  skip (이미 있음): $rel"
    else mkdir -p "$2/$(dirname "$rel")"; cp "$1/$rel" "$2/$rel"; echo "  + $rel"; fi
  done
}

echo "== secondbrain_skills 설치: $KIND → $TARGET =="
mkdir -p "$TARGET"
copy_if_missing "$ROOT/templates/$KIND" "$TARGET"
for skill in "$ROOT"/skills/*/; do
  copy_if_missing "$skill" "$TARGET/.claude/skills/$(basename "$skill")"
done
if [ "$WITH_SECURITY" = 1 ]; then
  copy_if_missing "$ROOT/security/agents" "$TARGET/.claude/agents"
  mkdir -p "$TARGET/.claude/skills/school-app-security"
  [ -e "$TARGET/.claude/skills/school-app-security/SKILL.md" ] || cp "$ROOT/security/SKILL.md" "$TARGET/.claude/skills/school-app-security/SKILL.md"
fi

echo ""
echo "설치 완료. 다음 단계:"
echo "  1. (권장) pip install olefile pypdf defusedxml   # HWP/PDF 추출용"
echo "  2. 소스 파일을 $TARGET/10-sources/ 에 넣기"
echo "  3. cd \"$TARGET\" && claude 실행 후 /setup (또는 /ingest <파일명>)"
