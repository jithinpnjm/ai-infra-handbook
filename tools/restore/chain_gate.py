#!/usr/bin/env python3
"""Template-prose gate. Usage: chain_gate.py FILE.md [FILE.md ...]  -> semicolon chains ('; the/every/each') per 1000 words of prose (code removed).
Target <= 1.5 for a rewritten section. Exit 1 if any file is above 1.5 (sections under 80 words are ignored)."""
import re, sys
bad = 0
for f in sys.argv[1:]:
    s = re.sub(r'```.*?```', '', open(f).read(), flags=re.S); w = len(s.split())
    if w < 80: continue
    d = len(re.findall(r'; (?:the|every|each|a|an) ', s)) / w * 1000
    print(f"{f.split('/')[-1]}: {d:.1f} per 1000 words ({w} words)" + ("  <-- too high, rewrite the semicolon chains" if d > 1.5 else ""))
    bad |= d > 1.5
sys.exit(1 if bad else 0)
