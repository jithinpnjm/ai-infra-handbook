#!/usr/bin/env python3
"""Install a written chapter over its scaffold: install.py <part.chapter> <file>.
Keeps the scaffold's front-matter lab_venue/level fields, copies body from <file>."""
import sys, re, glob, os
label, src = sys.argv[1], sys.argv[2]
part, ch = label.split('.')
pdir = glob.glob(f"docs/part-{int(part):02d}-*")[0]
target = glob.glob(f"{pdir}/{int(ch):02d}-*.md")[0]
old = open(target).read()
new = open(src).read()
def fm(t, k):
    m = re.search(rf'^{k}: (.*)$', t, re.M); return m.group(1) if m else None
for k in ("lab_venue", "level", "tier"):
    ov = fm(old, k)
    if ov is not None and fm(new, k) is not None:
        new = re.sub(rf'^{k}: .*$', f'{k}: {ov}', new, count=1, flags=re.M)
open(target, "w").write(new)
print(target, len(new.split()), "words")
