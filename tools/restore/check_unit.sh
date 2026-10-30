#!/bin/bash
# Usage: tools/restore/check_unit.sh 1.10 10   (label, chapter file prefix) -> re-wrap code format, run gate, list new numbers
cd "$(dirname "$0")/../.."; S=/private/tmp/claude-501/-Users-jithinpjoseph-Documents-GitHub-ai-infra-handbook/4207da9b-4841-4181-b14d-4ebf9acb1a7e/scratchpad/v
P=$(printf '%02d' "${1%%.*}"); C=$(printf '%02d' "${1##*.}"); f=$(ls docs/part-$P-*/$C-*.md | head -1)
python3 tools/restore/restore_code_format.py $S/$1/chapter_old.md "$f"
python3 tools/restore/voice_gate.py $S/$1/chapter_old.md "$f" | grep -E "FAIL|RESULT"
python3 - "$f" $S/$1/chapter_old.md <<'PY'
import re,sys
nums=lambda t:set(re.findall(r'\b\d+(?:\.\d+)?\b',re.sub(r'```.*?```','',t,flags=re.S).replace(',','')))
n,o=open(sys.argv[1]).read(),open(sys.argv[2]).read(); print('new numbers',sorted(nums(n)-nums(o)))
PY
