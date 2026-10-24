#!/usr/bin/env python3
"""Extract h1-h4 heading outlines per chapter from the books' XHTML (private research aid)."""
import glob, os, re, html
from html.parser import HTMLParser

CORPUS = os.path.expanduser(os.environ.get("STUDY_CORPUS", "~/Desktop/books-toon-rag"))
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "planning", "source-outlines")

class H(HTMLParser):
    def __init__(s): super().__init__(); s.cur=None; s.buf=[]; s.items=[]
    def handle_starttag(s,t,a):
        if t in ("h1","h2","h3","h4"): s.cur=int(t[1]); s.buf=[]
    def handle_endtag(s,t):
        if s.cur and t==f"h{s.cur}":
            txt=re.sub(r"\s+"," ","".join(s.buf)).strip()
            if txt: s.items.append((s.cur,txt))
            s.cur=None
    def handle_data(s,d):
        if s.cur: s.buf.append(d)

for book in sorted(glob.glob(os.path.join(CORPUS,"*/"))):
    slug=os.path.basename(book.rstrip("/"))
    files=sorted(glob.glob(book+"OEBPS/**/*.xhtml",recursive=True)+glob.glob(book+"OEBPS/**/*.html",recursive=True)+glob.glob(book+"OEBPS/**/*.htm",recursive=True))
    if not files: continue
    lines=[f"# {slug}\n"]; n=0
    for f in files:
        p=H(); p.feed(open(f,encoding="utf-8",errors="ignore").read())
        if not p.items: continue
        # drop pure front/back matter files with only one trivial heading
        lines.append(f"\n<!-- file: {os.path.basename(f)} -->")
        for lvl,t in p.items:
            if lvl<=1: lines.append(f"\n## {t}")
            else: lines.append("  "*(lvl-2)+f"- {t}"); n+=1
    open(os.path.join(OUT,slug+".md"),"w").write("\n".join(lines)+"\n")
    print(f"{slug}: {n} subsections")
