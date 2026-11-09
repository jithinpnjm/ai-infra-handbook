#!/usr/bin/env python3
"""Make every doc code block that is headed '# code/partNN/<file>' equal that file's contents.
Run after editing code files. Blocks are rewritten as: first line '# code/partNN/<file>' + file body.
Files that cannot be shown whole (> 120 lines) are left alone and reported."""
import re,glob,os,sys
n=0
for f in sorted(glob.glob('docs/part-1[6-9]-*/*.md')):
    s=open(f).read()
    def fix(m):
        global n
        lang,body=m.group(1),m.group(2)
        first=body.split('\n',1)[0]
        p=re.match(r'\s*(?:#|//|--)\s*(code/part1[6-9]/[\w./-]+)',first)
        if not p or not os.path.exists(p[1]): return m.group(0)
        src=open(p[1]).read()
        if src.count('\n')>120: print('long, not synced:',p[1]); return m.group(0)
        c='//' if lang=='json' else '--' if lang=='sql' else '#'
        new=src if src.lstrip().startswith((f"{c} {p[1]}",)) else f"{c} {p[1]}\n"+src
        if not new.endswith('\n'): new+='\n'
        if new!=body: n+=1
        return f"```{lang}\n{new}```"
    t=re.sub(r'```(\w*)\n(.*?)```',fix,s,flags=re.S)
    if t!=s: open(f,'w').write(t)
print('blocks synced:',n)
