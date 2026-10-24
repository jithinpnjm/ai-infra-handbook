#!/usr/bin/env bash
# Usage: tools/check_all.sh P.C /tmp/w/pPC.md [--no-build]
#   P.C   chapter number, e.g. 9.1
#   file  the drafted chapter
# Runs install, table-pipe fix, MDX lint, scaffold generate, lab(s), build, mermaid check.
# Prints one summary line per step. Run it ONCE per chapter, after the draft is finished.
set -u
CH="${1:?chapter e.g. 9.1}"; SRC="${2:?draft file}"; NOBUILD="${3:-}"
cd "$(dirname "$0")/.." || exit 1
P="${CH%%.*}"; C="${CH##*.}"
PP=$(printf '%02d' "$P"); CC=$(printf '%02d' "$C")
fail=0
step() { printf '%-14s' "$1"; shift; }

step install;  python3 tools/scaffold/install.py "$CH" "$SRC" 2>&1 | tail -1
DOC=$(ls docs/part-${PP}-*/${CC}-*.md 2>/dev/null | head -1)
[ -z "$DOC" ] && { echo "chapter file not found after install"; exit 1; }
step pipes;    python3 tools/fix_table_pipes.py "$DOC" 2>&1 | tail -1
step lint;     out=$(python3 tools/lint_mdx.py 2>&1); echo "$out" | tail -3; echo "$out" | grep -qiE "error|problem|[1-9][0-9]* issue" && fail=1
step generate; python3 tools/scaffold/generate.py 2>&1 | tail -1

step labs
for f in code/part${PP}/*lab*.py; do
  [ -f "$f" ] || continue
  r=$(python3 "$f" 2>&1 | tail -1); echo "$(basename "$f"): $r"
  python3 "$f" 2>&1 | grep -q "FAIL" && fail=1
done

if [ "$NOBUILD" != "--no-build" ]; then
  step build;   b=$(npm run build 2>&1 | grep -E "SUCCESS|ERROR|rror" | head -5); echo "$b"; echo "$b" | grep -q SUCCESS || fail=1
  step mermaid; m=$(node tools/check_mermaid.mjs | tail -1); echo "$m"; echo "$m" | grep -q " 0 failed\|0 failed" || fail=1
fi
words=$(wc -w < "$DOC")
echo "words: $words   file: $DOC"
[ $fail -eq 0 ] && echo "ALL CHECKS PASSED" || echo "SOME CHECKS FAILED - fix and re-run"
exit $fail
