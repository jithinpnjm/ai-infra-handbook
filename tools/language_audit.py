#!/usr/bin/env python3
"""Readability metrics for every chapter (same formulas as validate_chapter.py). Usage: python3 tools/language_audit.py [csv_out]"""
import re, glob, sys, subprocess, os
def metrics(t):
    t = re.sub(r"<details>.*?</details>", " ", t, flags=re.S) if False else t
    body = re.sub(r"```.*?```", " ", t, flags=re.S)
    lines = [l for l in body.splitlines() if l.strip() and not l.lstrip().startswith(("|", "#", ">", ":::", "<", "---", "!["))]
    para = " ".join(lines)
    words = len(re.sub(r"`[^`]*`", "X", para).split()) or 1
    spans = len(re.findall(r"`[^`]+`", para))
    nums = len(re.findall(r"\b\d[\d,]*\.?\d*\b", re.sub(r"`[^`]*`", "", para)))
    sents = [x for x in re.split(r"(?<=[.!?])\s+", re.sub(r"`[^`]*`", "X", para)) if len(x.split()) > 3]
    n = len(sents) or 1
    avg = sum(len(x.split()) for x in sents) / n
    lng = 100 * sum(1 for x in sents if len(x.split()) > 35) / n
    par = sum(x.count("(") for x in sents) / n
    semi = 1000 * para.count(";") / words
    return words, 100*spans/words, 100*nums/words, avg, lng, par, semi
lim = (4.0, 6.0, 22.0, 3.0, 0.5, 1.5)
rows = []
for f in sorted(glob.glob("docs/part-*/*.md")):
    w, *m = metrics(open(f).read())
    warn = sum(1 for a, b in zip(m, lim) if a > b)
    rows.append((warn, f, w, *m))
rows.sort(key=lambda r: (-r[0], r[1]))
out = sys.argv[1] if len(sys.argv) > 1 else None
hdr = "warns,file,words,spans100,nums100,avg_sent,pct_long,paren_per_sent,semi_per_1000"
lines = [hdr] + [f"{r[0]},{r[1]},{r[2]},{r[3]:.1f},{r[4]:.1f},{r[5]:.1f},{r[6]:.1f},{r[7]:.2f},{r[8]:.1f}" for r in rows]
if out: open(out, "w").write("\n".join(lines) + "\n")
from collections import Counter
c = Counter(r[0] for r in rows)
print("chapters:", len(rows), "by warning count:", dict(sorted(c.items())))
print("\n".join(lines[:25]))
