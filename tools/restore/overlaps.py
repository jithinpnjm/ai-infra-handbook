#!/usr/bin/env python3
"""Show paragraphs (outside code fences) that share 14-word runs with the book chapter. Usage: overlaps.py U079"""
import re,sys,json,subprocess,os,glob
u=next(x for x in json.load(open('planning/restore/QUEUE.json')) if x['id']==sys.argv[1])
bk=u['book']
if not glob.glob(os.path.expanduser(f'~/Desktop/books-toon-rag/{bk}/*_chunks.jsonl')):
    bk=[d for d in os.listdir(os.path.expanduser('~/Desktop/books-toon-rag')) if bk.startswith(d)][0]
w=lambda s:re.sub(r'[^a-z0-9 ]',' ',s.lower()).split()
bw=w(subprocess.run(['python3','tools/study_rag/bookch.py',bk,u['prefix'].strip()],capture_output=True,text=True).stdout)
sh={' '.join(bw[i:i+14]) for i in range(len(bw)-13)}
for f in u['files']:
    raw=re.sub(r'(?m)^\s*(\||- ).*$',' ',re.sub(r'```.*?```',' ',open(f,encoding='utf8').read(),flags=re.S))
    for para in raw.split('\n\n'):
        t=w(para); n=sum(1 for i in range(len(t)-13) if ' '.join(t[i:i+14]) in sh)
        if n: print(os.path.basename(f)[:14],n,para[:160].replace('\n',' '))
