#!/usr/bin/env python3
"""Generate a heading-level coverage skeleton for one source: make_skeleton.py <outline-slug> <mapping.json>
mapping.json: {"<file-name>": {"label": "...", "target": "handbook chapters"}}  Output: planning/coverage/<slug>.md"""
import json, re, sys, os
slug, mp = sys.argv[1], json.load(open(sys.argv[2]))
base = os.path.join(os.path.dirname(__file__), "..", "..", "planning")
text = open(os.path.join(base, "source-outlines", slug + ".md")).read()
blocks = re.split(r"<!-- file: (.*?) -->", text)
out = [f"# Coverage: {slug}\n", "Status values: `todo` · `covered` (name the section) · `moved` (name the chapter) · `skipped` (reason) · `gap-doc`.",
       "Every row must leave `todo` before the mapped chapters are marked reviewed.\n"]
total = 0
for i in range(1, len(blocks), 2):
    f, body = blocks[i], blocks[i + 1]
    if f not in mp: continue
    m = mp[f]
    out.append(f"\n## {m['label']}  (`{f}`)\n**Target handbook chapters:** {m['target']}\n")
    out.append("| Source heading | Status | Where covered / note |\n|---|---|---|")
    for line in body.splitlines():
        h = re.match(r"^(\s*)- (.*)$", line)
        if h: out.append(f"| {'&nbsp;&nbsp;' * (len(h.group(1)) // 2)}{h.group(2).replace('|', '/')} | todo | |"); total += 1
        elif line.startswith("## ") and line[3:].strip(): out.append(f"| **{line[3:].strip().replace('|','/')}** | todo | |"); total += 1
open(os.path.join(base, "coverage", slug + ".md"), "w").write("\n".join(out) + f"\n\nTotal rows: {total}\n")
print(slug, "rows:", total)
