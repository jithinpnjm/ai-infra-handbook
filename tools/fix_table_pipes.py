#!/usr/bin/env python3
"""Escape unescaped | inside inline code spans on markdown table rows."""
import re, sys
def fix_line(l):
    out=[];i=0;n=len(l);changed=False
    while i<n:
        if l[i]=='`':
            j=i
            while j<n and l[j]=='`': j+=1
            run=l[i:j];k=l.find(run,j)
            while k!=-1 and (k+len(run)<n and l[k+len(run)]=='`'): k=l.find(run,k+len(run)+1) if False else l.find(run,k+1)
            if k==-1: out.append(l[i:j]);i=j;continue
            inner=l[j:k]
            new=re.sub(r'(?<!\\)\|',r'\\|',inner)
            if new!=inner: changed=True
            out.append(run+new+run);i=k+len(run)
        else: out.append(l[i]);i+=1
    return ''.join(out),changed
for p in sys.argv[1:]:
    inc=False;L=open(p).read().split('\n');ch=0
    for idx,l in enumerate(L):
        if l.startswith('```'): inc=not inc;continue
        if inc or not l.startswith('|'): continue
        nl,c=fix_line(l)
        if c: L[idx]=nl;ch+=1
    if ch: open(p,'w').write('\n'.join(L));print(p,ch)
