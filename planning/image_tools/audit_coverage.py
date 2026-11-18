#!/usr/bin/env python3
"""usage: audit_coverage.py part-03-python [chapterNN]
Lists teaching headings (##/###/####) with no figure before the next heading. Skips lab/exercises/checkpoint/sources/mistakes/interview."""
import sys,glob,re
part=sys.argv[1]; only=sys.argv[2] if len(sys.argv)>2 else None
skip=re.compile(r'lab|exercise|checkpoint|sources|common mistakes|interview|prerequisites|why this matters|how it fails',re.I)
for f in sorted(glob.glob(f'/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook/docs/{part}/[0-9]*.md')):
    nn=f.split('/')[-1][:2]
    if only and nn!=only[-2:]: continue
    lines=open(f).read().split('\n'); heads=[]; fence=False
    for i,l in enumerate(lines):
        if l.startswith('```'): fence=not fence
        if not fence and re.match(r'#{2,4} ',l): heads.append(i)
    miss=[]
    for k,h in enumerate(heads):
        end=heads[k+1] if k+1<len(heads) else len(lines)
        seg=lines[h:end]
        if skip.search(lines[h]): continue
        if any(s.startswith('![') for s in seg): continue
        # parent section covered if a child heading has a figure? keep strict: report anyway
        miss.append((h+1,lines[h]))
    print(f'== {nn}: {len(miss)} headings without a figure')
    for n,t in miss: print(f'  {n}: {t[:90]}')
