#!/usr/bin/env python3
"""Build the gem-book restoration work queue from planning/coverage/GEM_BOOKS_MASTER.md.
Usage: python3 tools/restore/manifest.py [--min 15]
Writes planning/restore/QUEUE.json: one unit per (book chapter -> primary handbook chapter)."""
import re, json, glob, sys
mn = int(sys.argv[sys.argv.index('--min')+1]) if '--min' in sys.argv else 15
units=[]; book=None
for l in open('planning/coverage/GEM_BOOKS_MASTER.md', encoding='utf8'):
    if l.startswith('## '): book=l[3:].strip()
    c=[x.strip() for x in l.strip().strip('|').split('|')]
    if len(c)!=5 or not c[4].endswith('%'): continue
    pct=int(c[4][:-1])
    if pct<mn or c[1]=='SKIP': continue
    labels=[x for x in re.findall(r'\b(\d{1,2}\.\d{1,2})\b', c[2].split('(and deferred')[0]) if int(x.split('.')[0])<=15]
    OV={('ai-systems-performance-engineering','15'):['15.9'],('ai-systems-performance-engineering','16'):['15.13'],('ai-systems-performance-engineering','17'):['15.8','15.10'],('ai-systems-performance-engineering','18'):['15.11'],('ai-systems-performance-engineering','19'):['15.12']}
    labels=OV.get((book,c[0].split('.')[0]),labels)
    labels=list(dict.fromkeys(labels))
    if not labels: continue
    files=[]
    for lb in labels:
        p,ch=lb.split('.'); g=glob.glob(f'docs/part-{int(p):02d}-*/{int(ch):02d}-*.md')
        if g: files.append(g[0])
    if not files: continue
    prefix=c[0].split('.')[0].strip()+'. ' if re.match(r'^\d+\.',c[0]) else c[0].split(':')[0]+':' if c[0].startswith('Chapter') else c[0]
    units.append(dict(book=book,book_chapter=c[0],prefix=prefix,pct=pct,labels=labels,primary=files[0],files=files))
# group units by primary file so one agent never races another on the same file
for i,u in enumerate(sorted(units,key=lambda u:(u['primary'],-u['pct']))): u['id']=f'U{i:03d}'
json.dump(units,open('planning/restore/QUEUE.json','w'),indent=1)
from collections import Counter
print(len(units),'units;',len({u['primary'] for u in units}),'distinct target files;', Counter(u['book'][:25] for u in units))
