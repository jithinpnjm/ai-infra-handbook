#!/usr/bin/env python3
"""Regenerate planning/CORPUS_MANIFEST.md from ~/Desktop/books-toon-rag (keeps the how-to header)."""
import glob, os, re
root = os.path.expanduser("~/Desktop/books-toon-rag")
out = os.path.join(os.path.dirname(__file__), "..", "..", "planning", "CORPUS_MANIFEST.md")
head = open(out).read().split("## Entries")[0]
rows = []
for d in sorted(glob.glob(root + "/*/")):
    slug = os.path.basename(d.rstrip("/"))
    if slug.startswith("_"): continue
    bid = open(d + ".book_id").read().strip() if os.path.exists(d + ".book_id") else ""
    toon = glob.glob(d + "*.toon"); title = ""
    if toon:
        m = re.search(r"title: (.*)", open(toon[0], encoding="utf-8").read(2000)); title = m.group(1).strip('"') if m else ""
    kind = "O'Reilly book" if bid else ("author's own volume" if slug.startswith("nvidia-devops") else "vendor PDF")
    rows.append(f"| {slug} | {title} | {bid or '-'} | {kind} |")
open(out, "w").write(head + "## Entries\n\n| Slug | Title | Book id | Kind |\n|---|---|---|---|\n" + "\n".join(rows) + "\n")
print(len(rows), "entries")
