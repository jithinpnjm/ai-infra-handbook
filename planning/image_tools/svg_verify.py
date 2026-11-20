#!/usr/bin/env python3
"""usage: svg_verify.py part-dir : for every svg referenced in a chapter, report fraction of its words found in that chapter (low = possible mismatch)."""
import sys,re,glob,html
part=sys.argv[1]; rows=[]
for f in sorted(glob.glob(f'docs/{part}/[0-9]*.md')):
    t=open(f).read(); low=t.lower()
    for m in re.finditer(r'!\[[^\]]*\]\(\./img/([^)]+\.svg)\)',t):
        s=open(f'docs/{part}/img/{m.group(1)}').read()
        words=set(w for x in re.findall(r'>([^<>]+)</',s) for w in re.findall(r'[a-z][a-z0-9_\-]{3,}',html.unescape(x).lower()))
        if not words: continue
        hit=sum(1 for w in words if w in low)/len(words)
        rows.append((hit,f.split('/')[-1][:2],m.group(1),len(words)))
rows.sort()
for r in rows[:int(sys.argv[2]) if len(sys.argv)>2 else 15]: print('%.2f ch%s %s (%d words)'%r)
print('median %.2f of %d'%(sorted(r[0] for r in rows)[len(rows)//2],len(rows)))
