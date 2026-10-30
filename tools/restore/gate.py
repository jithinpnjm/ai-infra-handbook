#!/usr/bin/env python3
"""Quality gate for one restoration unit.
Usage: python3 tools/restore/gate.py U012 [BACKUP_DIR]
Backups live in BACKUP_DIR/<unit id>/<basename>. Prints PASS/FAIL lines; exit 1 on any FAIL."""
import json, sys, os, re, subprocess, glob
uid=sys.argv[1]; bdir=sys.argv[2] if len(sys.argv)>2 else 'planning/restore/backup'
u=next(x for x in json.load(open('planning/restore/QUEUE.json')) if x['id']==uid)
ok=True
def say(good,msg):
    global ok; ok&=good; print(('PASS ' if good else 'FAIL ')+msg)
for f in u['files']:
    old=os.path.join(bdir,uid,os.path.basename(f))
    if not os.path.exists(old): continue
    new=open(f,encoding='utf8').read(); o=open(old,encoding='utf8').read()
    if new==o: continue
    r=subprocess.run(['python3','tools/loss_check.py',old,f],capture_output=True,text=True).stdout
    m=re.search(r'technical terms lost: (\d+).*numbers lost: (\d+)',r)
    say(m and m.group(1)=='0' and m.group(2)=='0', f'{os.path.basename(f)[:40]} loss_check {m.groups() if m else r[:100]}')
    say(new.count('```')%2==0, 'code fences balanced')
    say(new.count('<details>')==o.count('<details>') and new.count('<summary>')>=o.count('<summary>'), 'checkpoint questions kept')
    say('&lt;strong>' not in new and '&lt;code>' not in new, 'no escaped html')
    say(new.startswith('---') and new.split('---',2)[1]==o.split('---',2)[1], 'front matter unchanged')
    say(len(new.split())>=len(o.split()), f'words {len(o.split())} -> {len(new.split())}')
# coverage after
cmd=['python3','tools/book_passages.py',u['book'],u['prefix']]+u['labels']+['--show','0']
out=subprocess.run(cmd,capture_output=True,text=True).stdout
m=re.search(r'= \d+ words = (\d+)% of the checked text',out)
after=int(m.group(1)) if m else None
say(after is not None and after<=max(10,u['pct']-20), f'uncovered {u["pct"]}% -> {after}% (need <= {max(10,u["pct"]-20)}%)')
# verbatim copy check: 14-word shingles shared with the book chapter
book=subprocess.run(['python3','tools/study_rag/bookch.py',u['book'],u['prefix']],capture_output=True,text=True).stdout
w=lambda s:re.sub(r'[^a-z0-9 ]',' ',s.lower()).split()
bw=w(book); sh={' '.join(bw[i:i+14]) for i in range(len(bw)-13)}
hits=0
for f in u['files']:
    t=w(open(f,encoding='utf8').read()); hits+=sum(1 for i in range(len(t)-13) if ' '.join(t[i:i+14]) in sh)
say(hits<=25, f'verbatim 14-word overlaps with book: {hits} (limit 25)')
print('RESULT','PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
