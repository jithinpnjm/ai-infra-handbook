#!/usr/bin/env python3
"""Split a chapter into '## ' sections so an agent can rewrite one at a time, then join them back.
  sections.py split CHAPTER.md WORKDIR    -> WORKDIR/old/NN.md (NN=00 is front matter + title + intro)
  sections.py join  WORKDIR CHAPTER.md    -> uses WORKDIR/new/NN.md when present, else old/NN.md
  sections.py status WORKDIR              -> which sections are rewritten
Headings inside code fences are not split points."""
import sys, os, re
def split(text):
    parts, cur, fence = [], [], False
    for l in text.split('\n'):
        if l.lstrip().startswith(('```','~~~')): fence = not fence
        if not fence and l.startswith('## ') and cur: parts.append('\n'.join(cur)); cur=[]
        cur.append(l)
    parts.append('\n'.join(cur)); return parts
cmd = sys.argv[1]
if cmd == 'split':
    t = open(sys.argv[2], encoding='utf8').read(); d = sys.argv[3]
    os.makedirs(d+'/old', exist_ok=True); os.makedirs(d+'/new', exist_ok=True)
    ps = split(t)
    for i,p in enumerate(ps): open(f'{d}/old/{i:02d}.md','w',encoding='utf8').write(p)
    print(len(ps),'sections;', [len(p.split()) for p in ps])
elif cmd == 'join':
    d = sys.argv[2]; out=[]
    for f in sorted(os.listdir(d+'/old')):
        n = f'{d}/new/{f}'; out.append(open(n if os.path.exists(n) else f'{d}/old/{f}', encoding='utf8').read().rstrip('\n'))
    open(sys.argv[3],'w',encoding='utf8').write('\n\n'.join(out)+'\n'); print('joined',len(out))
elif cmd == 'status':
    d = sys.argv[2]
    for f in sorted(os.listdir(d+'/old')): print(f, 'DONE' if os.path.exists(f'{d}/new/{f}') else 'todo', len(open(f'{d}/old/{f}',encoding='utf8').read().split()))
