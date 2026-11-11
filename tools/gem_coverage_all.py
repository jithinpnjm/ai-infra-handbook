#!/usr/bin/env python3
"""Whole-handbook gem-book coverage: share of each book chapter's distinctive content NOT found in any handbook chapter.
Usage (from repo root): python3 tools/gem_coverage_all.py <book-folder> [more book folders]
Lenient measure: shows presence anywhere, not depth in the right chapter."""
import subprocess,re,sys
import glob
labs=[]
for f in sorted(glob.glob('docs/part-*/[0-9][0-9]-*.md')):
    m=re.match(r'docs/part-(\d+)-[^/]*/(\d+)-',f)
    labs.append(f"{int(m[1])}.{int(m[2])}")
books=sys.argv[1:]
for b in books:
    out=subprocess.run(['python3','tools/study_rag/bookch.py',b,'--list'],capture_output=True,text=True).stdout.splitlines()
    chs=[l for l in out[1:] if re.match(r'^(\d+\.|Chapter \d+|Part|[A-Z]\w*)',l) and not re.match(r'^(Preface|Foreword|Index|About|Praise|Colophon|Copyright|Introduction$|Table of|Acknowledg)',l)]
    tw=uw=0; worst=[]
    for ch in chs:
        pref=ch.split(' ')[0]+' ' if re.match(r'^\d+\.',ch) else ch[:40]
        r=subprocess.run(['python3','tools/book_passages.py',b,pref,*labs,'--show','0'],capture_output=True,text=True).stdout
        m=re.search(r'(\d+) words\.? .*?checked|(\d+) paragraphs checked, (\d+) words',r)
        m2=re.search(r'paragraphs checked, (\d+) words',r); m3=re.search(r'= (\d+) words = (\d+)%',r)
        if m2 and m3:
            w=int(m2.group(1)); u=int(m3.group(1)); tw+=w; uw+=u
            if w and u/w>0.05: worst.append((round(100*u/w),ch[:60]))
    print(f"{b[:48]:48s} chapters={len(chs):3d} words={tw:7d} uncovered={uw:6d} ({100*uw/max(tw,1):.1f}%)  worst={sorted(worst,reverse=True)[:4]}")
