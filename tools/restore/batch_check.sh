#!/bin/bash
# Usage: tools/restore/batch_check.sh 2.9 2.10 ...  -> one line per chapter: CHANGED/UNCHANGED, gate result, new numbers
cd "$(dirname "$0")/../.."; S=/private/tmp/claude-501/-Users-jithinpjoseph-Documents-GitHub-trading-bot/edaf2c97-5b6e-4b55-b8a8-db04599ac342/scratchpad/v
for l in "$@"; do
  P=$(printf '%02d' "${l%%.*}"); C=$(printf '%02d' "${l##*.}"); f=$(ls docs/part-$P-*/$C-*.md | head -1)
  if cmp -s "$f" "$S/$l/chapter_old.md"; then echo "$l UNCHANGED"; continue; fi
  python3 tools/restore/restore_code_format.py $S/$l/chapter_old.md "$f" >/dev/null
  r=$(python3 tools/restore/voice_gate.py $S/$l/chapter_old.md "$f" | grep -E "FAIL|RESULT" | tr '\n' ' ')
  n=$(python3 - "$f" $S/$l/chapter_old.md <<'PY'
import re,sys
nums=lambda t:set(re.findall(r'\b\d+(?:\.\d+)?\b',re.sub(r'```.*?```','',t,flags=re.S).replace(',','')))
print(sorted(nums(open(sys.argv[1]).read())-nums(open(sys.argv[2]).read()))[:8])
PY
)
  echo "$l $r new=$n"
done
