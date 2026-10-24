#!/usr/bin/env python3
"""Record decisions for CHECK rows. Usage: decide.py 1.1 'regex@@status@@note' ['regex@@status@@note' ...]  then reruns the checker."""
import re, subprocess, sys, os
label = sys.argv[1]; rules = [r.split("@@", 2) for r in sys.argv[2:]]
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
part, ch = label.split("."); path = os.path.join(root, "planning", "coverage", "chapters", f"{int(part):02d}-{int(ch):02d}.md")
lines = open(path, encoding="utf-8").read().split("\n"); n = 0
for i, l in enumerate(lines):
    if l.startswith("| ") and re.search(r"\| CHECK \|\s*\|$", l):
        for pat, st, note in rules:
            if re.search(pat, l):
                lines[i] = re.sub(r"\| CHECK \|\s*\|$", f"| {st} | {note} |", l); n += 1; break
open(path, "w", encoding="utf-8").write("\n".join(lines))
print(subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "chapter_cov.py"), label], capture_output=True, text=True).stdout.strip(), f"(decided {n})")
