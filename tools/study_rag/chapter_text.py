#!/usr/bin/env python3
"""Print the FULL text of a source chapter (or a section of it) from a book's TOON file, without chunk overlap.
Usage: chapter_text.py <book-slug-substring> <chapter-title-substring> [--from "text"] [--to "text"] [--out file]
Example: chapter_text.py how-linux "Chapter 7" --from "7.3 User Management" --to "7.4 getty" """
import argparse, glob, json, os, re, sys
ap = argparse.ArgumentParser(); ap.add_argument("book"); ap.add_argument("chapter"); ap.add_argument("--from", dest="frm"); ap.add_argument("--to"); ap.add_argument("--out")
a = ap.parse_args()
root = os.path.expanduser("~/Desktop/books-toon-rag")
dirs = [d for d in sorted(glob.glob(root + "/*/")) if a.book in os.path.basename(d.rstrip("/"))]
if not dirs: sys.exit("no such book")
toon = glob.glob(dirs[0] + "*.toon")[0]
text = open(toon, encoding="utf-8").read()
for blk in re.split(r"\n  - index: ", text)[1:]:
    t = re.search(r"\n    title: (.*)", blk); c = re.search(r"\n    content: (\".*\")\s*\n    code_blocks", blk, re.S)
    if t and c and a.chapter.lower() in t.group(1).replace("\xa0", " ").lower():
        body = json.loads(c.group(1))
        i = body.find(a.frm) if a.frm else 0
        j = body.find(a.to, i + 1) if a.to else len(body)
        body = body[max(i, 0): j if j > 0 else len(body)]
        if a.out: open(a.out, "w").write(body); print(f"{len(body.split())} words -> {a.out}")
        else: print(body)
        break
else: sys.exit("no such chapter")
